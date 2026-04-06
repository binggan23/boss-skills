"""Local file and image extractors."""

from __future__ import annotations

import csv
import json
import zipfile
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from .errors import ExtractionError
from .ocr import extract_image_text

CONTENT_KEYS = ("content", "text", "message", "body", "note")
TIMESTAMP_KEYS = ("timestamp", "time", "created_at", "sent_at", "date")
SPEAKER_KEYS = ("speaker", "author", "sender", "from", "name")
AUDIENCE_KEYS = ("audience", "to", "recipients", "channel")


@dataclass(slots=True)
class ExtractedSeed:
    text: str
    source_name: str
    speaker: str | None = None
    audience: str | None = None
    timestamp: str | None = None


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self.parts)


def _pick(row: dict[str, object], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _format_row(row: dict[str, object]) -> str:
    pairs = [f"{key}: {value}" for key, value in row.items() if value not in (None, "", [])]
    return "\n".join(pairs)


def _extract_json(path: Path) -> list[ExtractedSeed]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        seeds: list[ExtractedSeed] = []
        for index, item in enumerate(payload, start=1):
            if isinstance(item, dict):
                text = _pick(item, CONTENT_KEYS) or _format_row(item)
                seeds.append(
                    ExtractedSeed(
                        text=text,
                        source_name=f"{path.name}#{index}",
                        speaker=_pick(item, SPEAKER_KEYS),
                        audience=_pick(item, AUDIENCE_KEYS),
                        timestamp=_pick(item, TIMESTAMP_KEYS),
                    )
                )
            else:
                seeds.append(ExtractedSeed(text=str(item), source_name=f"{path.name}#{index}"))
        return seeds

    if isinstance(payload, dict):
        text = _pick(payload, CONTENT_KEYS) or _format_row(payload)
        return [
            ExtractedSeed(
                text=text,
                source_name=path.name,
                speaker=_pick(payload, SPEAKER_KEYS),
                audience=_pick(payload, AUDIENCE_KEYS),
                timestamp=_pick(payload, TIMESTAMP_KEYS),
            )
        ]

    return [ExtractedSeed(text=str(payload), source_name=path.name)]


def _extract_jsonl(path: Path) -> list[ExtractedSeed]:
    seeds: list[ExtractedSeed] = []
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if isinstance(item, dict):
                text = _pick(item, CONTENT_KEYS) or _format_row(item)
                seeds.append(
                    ExtractedSeed(
                        text=text,
                        source_name=f"{path.name}#{index}",
                        speaker=_pick(item, SPEAKER_KEYS),
                        audience=_pick(item, AUDIENCE_KEYS),
                        timestamp=_pick(item, TIMESTAMP_KEYS),
                    )
                )
            else:
                seeds.append(ExtractedSeed(text=str(item), source_name=f"{path.name}#{index}"))
    return seeds


def _extract_csv(path: Path) -> list[ExtractedSeed]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    seeds: list[ExtractedSeed] = []
    for index, row in enumerate(rows, start=1):
        text = _pick(row, CONTENT_KEYS) or _format_row(row)
        seeds.append(
            ExtractedSeed(
                text=text,
                source_name=f"{path.name}#{index}",
                speaker=_pick(row, SPEAKER_KEYS),
                audience=_pick(row, AUDIENCE_KEYS),
                timestamp=_pick(row, TIMESTAMP_KEYS),
            )
        )
    return seeds


def _extract_html(path: Path) -> list[ExtractedSeed]:
    parser = _HTMLTextExtractor()
    parser.feed(path.read_text(encoding="utf-8"))
    return [ExtractedSeed(text=parser.get_text(), source_name=path.name)]


def _extract_docx(path: Path) -> list[ExtractedSeed]:
    with zipfile.ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        texts = [node.text for node in paragraph.findall(".//w:t", ns) if node.text]
        joined = "".join(texts).strip()
        if joined:
            paragraphs.append(joined)
    return [ExtractedSeed(text="\n".join(paragraphs), source_name=path.name)]


def _extract_eml(path: Path) -> list[ExtractedSeed]:
    with path.open("rb") as handle:
        message = BytesParser(policy=policy.default).parse(handle)

    body = message.get_body(preferencelist=("plain", "html"))
    if body is None:
        text = message.as_string()
    elif body.get_content_type() == "text/html":
        parser = _HTMLTextExtractor()
        parser.feed(body.get_content())
        text = parser.get_text()
    else:
        text = body.get_content()

    return [
        ExtractedSeed(
            text=text,
            source_name=path.name,
            speaker=message.get("from"),
            audience=message.get("to"),
            timestamp=message.get("date"),
        )
    ]


def _extract_pdf(path: Path) -> list[ExtractedSeed]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise ExtractionError(
            "PDF import requires pypdf. Install dependencies from requirements.txt."
        ) from exc

    reader = PdfReader(str(path))
    chunks = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip())
    if not text:
        raise ExtractionError(f"No text could be extracted from PDF {path.name}.")
    return [ExtractedSeed(text=text, source_name=path.name)]


def extract_file_seeds(path: Path) -> list[ExtractedSeed]:
    if not path.exists():
        raise ExtractionError(f"Source file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".log"}:
        return [ExtractedSeed(text=path.read_text(encoding="utf-8"), source_name=path.name)]
    if suffix == ".json":
        return _extract_json(path)
    if suffix == ".jsonl":
        return _extract_jsonl(path)
    if suffix == ".csv":
        return _extract_csv(path)
    if suffix in {".html", ".htm"}:
        return _extract_html(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".eml":
        return _extract_eml(path)
    if suffix == ".pdf":
        return _extract_pdf(path)
    raise ExtractionError(f"Unsupported file type for import: {suffix or path.name}")


def extract_image_seed(path: Path) -> ExtractedSeed:
    if not path.exists():
        raise ExtractionError(f"Image file not found: {path}")
    text = extract_image_text(path)
    return ExtractedSeed(text=text, source_name=path.name)
