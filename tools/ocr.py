"""OCR helpers for screenshot imports."""

from __future__ import annotations

from pathlib import Path

from .errors import ExtractionError


def extract_image_text(image_path: Path) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ModuleNotFoundError as exc:
        raise ExtractionError(
            "OCR import requires rapidocr-onnxruntime. Install dependencies from requirements.txt."
        ) from exc

    engine = RapidOCR()
    result, _ = engine(str(image_path))
    if not result:
        raise ExtractionError(f"OCR extracted no text from {image_path.name}.")

    lines: list[str] = []
    for item in result:
        text = ""
        if isinstance(item, dict):
            text = str(item.get("text", ""))
        elif hasattr(item, "text"):
            text = str(getattr(item, "text"))
        elif isinstance(item, (list, tuple)):
            if len(item) >= 3 and isinstance(item[1], str):
                text = item[1]
            elif len(item) >= 2 and isinstance(item[1], (list, tuple)) and item[1]:
                text = str(item[1][0])
        if text.strip():
            lines.append(text.strip())

    if not lines:
        raise ExtractionError(f"OCR returned an unexpected result shape for {image_path.name}.")
    return "\n".join(lines)
