"""Evidence normalization, routing, and coverage helpers."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from .errors import InvalidCommandError

SLUG_RE = re.compile(r"^[a-z0-9-]+$")

DIRECT_EXPRESSION_TYPES = {
    "chat",
    "email",
    "speech",
    "interview",
    "all-hands",
    "memo",
    "annotation",
    "screenshot",
}
DECISION_SOURCE_TYPES = {
    "meeting-note",
    "annotation",
    "memo",
    "document",
    "email",
}
BOUNDARY_SOURCE_TYPES = {"email", "document", "meeting-note", "annotation"}

OPERATOR_KEYWORDS = (
    "优先",
    "先做",
    "先给我结论",
    "结论",
    "目标",
    "结果",
    "交付",
    "上线",
    "风险",
    "验证",
    "复盘",
    "审批",
    "预算",
    "招聘",
    "绩效",
    "汇报",
    "周报",
    "数字",
    "ROI",
    "owner",
    "deadline",
    "milestone",
)
BOUNDARY_KEYWORDS = (
    "法务",
    "律师",
    "合同",
    "签字",
    "签署",
    "授权",
    "offer",
    "薪资",
    "调薪",
    "裁员",
    "解雇",
    "解聘",
    "融资",
    "股权",
    "期权",
    "媒体",
    "公关",
    "对外",
    "发布",
    "付款",
    "转账",
    "承诺",
)
VOICE_KEYWORDS = (
    "马上",
    "今天",
    "尽快",
    "辛苦",
    "不错",
    "很好",
    "不行",
    "为什么",
    "重做",
    "先给我",
    "同步",
    "结论",
)


@dataclass(slots=True)
class CoverageResult:
    ready: bool
    coverage_score: int
    source_types: list[str]
    evidence_counts: dict[str, int]
    missing_evidence: list[str]
    direct_expression_count: int
    decision_signal_count: int
    boundary_signal_count: int
    layer_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "coverage_score": self.coverage_score,
            "source_types": self.source_types,
            "evidence_counts": self.evidence_counts,
            "missing_evidence": self.missing_evidence,
            "direct_expression_count": self.direct_expression_count,
            "decision_signal_count": self.decision_signal_count,
            "boundary_signal_count": self.boundary_signal_count,
            "layer_counts": self.layer_counts,
        }


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def validate_slug(slug: str) -> str:
    normalized = slug.strip().lower()
    if not SLUG_RE.match(normalized):
        raise InvalidCommandError(
            f"Invalid slug '{slug}'. Use lowercase letters, digits, and hyphens only."
        )
    return normalized


def clean_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def infer_layers(source_type: str, content: str, speaker: str | None = None) -> list[str]:
    layers: set[str] = set()
    lowered = content.lower()
    speaker_lower = (speaker or "").lower()

    if source_type in DIRECT_EXPRESSION_TYPES or "boss" in speaker_lower or "老板" in speaker_lower:
        layers.add("voice")

    if source_type in DECISION_SOURCE_TYPES or any(keyword.lower() in lowered for keyword in OPERATOR_KEYWORDS):
        layers.add("operator")

    if source_type in BOUNDARY_SOURCE_TYPES or any(keyword.lower() in lowered for keyword in BOUNDARY_KEYWORDS):
        layers.add("boundary")

    if not layers and any(keyword.lower() in lowered for keyword in VOICE_KEYWORDS):
        layers.add("voice")

    if not layers:
        layers.add("voice" if source_type in {"description", "chat"} else "operator")

    return [layer for layer in ("boundary", "operator", "voice") if layer in layers]


def primary_layer(layers: Iterable[str]) -> str:
    ordered = list(dict.fromkeys(layers))
    if len(ordered) == 1:
        return ordered[0]
    return "mixed"


def build_record(
    *,
    source_type: str,
    source_name: str,
    content: str,
    speaker: str | None,
    audience: str | None,
    attachment_refs: list[str] | None,
    confidence: float,
    privacy: str,
    timestamp: str | None = None,
    forced_layer: str | None = None,
) -> dict[str, object]:
    normalized_content = clean_text(content)
    layers = [forced_layer] if forced_layer else infer_layers(source_type, normalized_content, speaker)
    payload = {
        "source_type": source_type,
        "source_name": source_name,
        "timestamp": timestamp or utc_now(),
        "speaker": speaker or "unknown",
        "audience": audience or "unknown",
        "content": normalized_content,
        "attachment_refs": attachment_refs or [],
        "confidence": round(float(confidence), 3),
        "privacy": privacy,
        "layer_hint": primary_layer(layers),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["record_id"] = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:12]
    return payload


def is_direct_expression(record: dict[str, object]) -> bool:
    source_type = str(record.get("source_type", ""))
    speaker = str(record.get("speaker", "")).lower()
    return (
        source_type in DIRECT_EXPRESSION_TYPES
        or "boss" in speaker
        or "founder" in speaker
        or "老板" in speaker
        or "创始人" in speaker
    )


def has_decision_signal(record: dict[str, object], layers: Iterable[str]) -> bool:
    source_type = str(record.get("source_type", ""))
    if source_type == "correction":
        return False
    if "operator" in set(layers):
        return True
    lowered = str(record.get("content", "")).lower()
    return any(keyword.lower() in lowered for keyword in OPERATOR_KEYWORDS)


def has_boundary_signal(record: dict[str, object], layers: Iterable[str]) -> bool:
    if "boundary" in set(layers):
        return True
    lowered = str(record.get("content", "")).lower()
    return any(keyword.lower() in lowered for keyword in BOUNDARY_KEYWORDS)


def route_record(record: dict[str, object]) -> dict[str, object]:
    layers = infer_layers(
        str(record.get("source_type", "")),
        str(record.get("content", "")),
        str(record.get("speaker", "")),
    )
    return {
        "record_id": record["record_id"],
        "source_type": record["source_type"],
        "source_name": record["source_name"],
        "layers": layers,
        "primary_layer": primary_layer(layers),
        "direct_expression": is_direct_expression(record),
        "decision_signal": has_decision_signal(record, layers),
        "boundary_signal": has_boundary_signal(record, layers),
    }


def calculate_coverage(
    records: list[dict[str, object]],
    router_rows: list[dict[str, object]],
) -> CoverageResult:
    counted_records = [record for record in records if record.get("source_type") != "correction"]
    source_counter = Counter(str(record["source_type"]) for record in counted_records)
    source_types = sorted(source_counter.keys())

    direct_expression_count = sum(1 for row in router_rows if row["direct_expression"])
    decision_signal_count = sum(1 for row in router_rows if row["decision_signal"])
    boundary_signal_count = sum(1 for row in router_rows if row["boundary_signal"])
    layer_counter = Counter(
        layer
        for row in router_rows
        for layer in row["layers"]
        if row["source_type"] != "correction"
    )

    missing_evidence: list[str] = []
    if len(source_types) < 2:
        missing_evidence.append("Add a second distinct source type.")
    if direct_expression_count < 1:
        missing_evidence.append("Add at least one direct-expression record from the boss.")
    if decision_signal_count < 1:
        missing_evidence.append("Add at least one decision or management-action record.")

    ready = not missing_evidence

    source_score = min(35, len(source_types) * 18)
    direct_score = 35 if direct_expression_count >= 1 else 0
    decision_score = 30 if decision_signal_count >= 1 else 0
    coverage_score = min(100, source_score + direct_score + decision_score)

    return CoverageResult(
        ready=ready,
        coverage_score=coverage_score,
        source_types=source_types,
        evidence_counts=dict(source_counter),
        missing_evidence=missing_evidence,
        direct_expression_count=direct_expression_count,
        decision_signal_count=decision_signal_count,
        boundary_signal_count=boundary_signal_count,
        layer_counts=dict(layer_counter),
    )


def excerpt(text: str, limit: int = 140) -> str:
    cleaned = clean_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
