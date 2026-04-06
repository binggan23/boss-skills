"""Markdown renderers for ready boss archives."""

from __future__ import annotations

from collections import Counter, defaultdict

from .evidence import excerpt

MAX_EVIDENCE = 5

OPERATOR_DIMENSIONS = {
    "Goal Order": {
        "Outcome-first": ("结果", "交付", "目标", "增长", "客户", "上线", "ROI"),
        "Risk-first": ("风险", "验证", "复盘", "稳定", "合规", "评审"),
    },
    "Decision Tempo": {
        "Fast-cycle": ("马上", "今天", "尽快", "先做", "先上"),
        "Deliberate": ("先验证", "评审", "复盘", "数据", "再决定"),
    },
    "Reporting Style": {
        "Conclusion-first": ("先给我结论", "结论", "数字", "汇报", "同步"),
        "Narrative-first": ("背景", "原因", "过程", "细节"),
    },
}

BOUNDARY_TOPICS = {
    "HR and compensation": ("薪资", "调薪", "offer", "裁员", "绩效", "招聘"),
    "Legal and contracts": ("法务", "律师", "合同", "签字", "签署"),
    "Finance and capital": ("融资", "付款", "转账", "股权", "期权"),
    "External commitments": ("媒体", "公关", "对外", "发布", "承诺"),
}


def _top_records(
    records: list[dict[str, object]],
    keywords: tuple[str, ...] | None = None,
    limit: int = MAX_EVIDENCE,
) -> list[dict[str, object]]:
    selected = []
    for record in records:
        if keywords is not None:
            lowered = str(record["content"]).lower()
            if not any(keyword.lower() in lowered for keyword in keywords):
                continue
        selected.append(record)
        if len(selected) >= limit:
            break
    return selected


def _bullet_evidence(records: list[dict[str, object]]) -> list[str]:
    lines = []
    for record in records:
        lines.append(f"- `{record['record_id']}` {excerpt(str(record['content']))}")
    return lines or ["- No explicit evidence was routed into this section."]


def _classify_dimension(records: list[dict[str, object]], options: dict[str, tuple[str, ...]]) -> tuple[str, int]:
    scores: dict[str, int] = {}
    for label, keywords in options.items():
        score = 0
        for record in records:
            lowered = str(record["content"]).lower()
            score += sum(1 for keyword in keywords if keyword.lower() in lowered)
        scores[label] = score
    best_label = max(scores, key=scores.get)
    return best_label, scores[best_label]


def build_operating_system(
    manifest: dict[str, object],
    records: list[dict[str, object]],
    router_rows: list[dict[str, object]],
    coverage: dict[str, object],
) -> str:
    operator_ids = {
        row["record_id"]
        for row in router_rows
        if "operator" in row["layers"] and row["source_type"] != "correction"
    }
    operator_records = [record for record in records if record["record_id"] in operator_ids]
    source_types = ", ".join(coverage["source_types"]) or "none"

    lines = [
        f"# Operating System: {manifest['display_name']}",
        "",
        "## Archive Status",
        f"- Boss type: {manifest['boss_type']}",
        f"- Coverage score: {manifest['coverage_score']}",
        f"- Source types: {source_types}",
        f"- Operator evidence count: {len(operator_records)}",
        "",
        "## Evidence-backed Operating Signals",
    ]

    for dimension, options in OPERATOR_DIMENSIONS.items():
        label, score = _classify_dimension(operator_records, options)
        lines.append(f"### {dimension}")
        lines.append(f"- Inference: {label}")
        lines.append(f"- Signal strength: {score}")
        lines.extend(_bullet_evidence(_top_records(operator_records, keywords=options[label], limit=3)))
        lines.append("")

    lines.extend(["## Decision Evidence", *_bullet_evidence(operator_records[:MAX_EVIDENCE])])
    return "\n".join(lines).strip() + "\n"


def build_voice(
    manifest: dict[str, object],
    records: list[dict[str, object]],
    router_rows: list[dict[str, object]],
) -> str:
    voice_ids = {
        row["record_id"]
        for row in router_rows
        if "voice" in row["layers"] and row["source_type"] != "correction"
    }
    voice_records = [record for record in records if record["record_id"] in voice_ids]
    combined_text = "\n".join(str(record["content"]) for record in voice_records)
    questions = combined_text.count("?") + combined_text.count("？")
    exclamations = combined_text.count("!") + combined_text.count("！")
    average_length = (
        round(sum(len(str(record["content"])) for record in voice_records) / len(voice_records), 1)
        if voice_records
        else 0
    )

    openers = Counter()
    for record in voice_records:
        first_line = str(record["content"]).splitlines()[0].strip()
        if first_line:
            openers[first_line[:16]] += 1

    lines = [
        f"# Voice: {manifest['display_name']}",
        "",
        "## Observable Style",
        f"- Average message length: {average_length}",
        f"- Question markers: {questions}",
        f"- Exclamation markers: {exclamations}",
        "",
        "## Common Openers",
    ]

    for opener, count in openers.most_common(5):
        lines.append(f"- `{opener}` x{count}")
    if not openers:
        lines.append("- No repeated opener detected yet.")

    lines.extend(["", "## Representative Voice Evidence", *_bullet_evidence(voice_records[:MAX_EVIDENCE])])
    return "\n".join(lines).strip() + "\n"


def build_boundary(
    manifest: dict[str, object],
    records: list[dict[str, object]],
    router_rows: list[dict[str, object]],
) -> str:
    boundary_ids = {
        row["record_id"]
        for row in router_rows
        if "boundary" in row["layers"] and row["source_type"] != "correction"
    }
    boundary_records = [record for record in records if record["record_id"] in boundary_ids]
    topic_hits: dict[str, list[dict[str, object]]] = defaultdict(list)

    for topic, keywords in BOUNDARY_TOPICS.items():
        topic_hits[topic] = _top_records(boundary_records, keywords=keywords, limit=3)

    lines = [
        f"# Boundary: {manifest['display_name']}",
        "",
        "## Hard Refusals",
        "- Do not impersonate the boss for approvals, signatures, or authorizations.",
        "- Do not make HR, legal, finance, or compensation decisions as if they are binding.",
        "- Do not issue external promises, media statements, or customer commitments as the real boss.",
        "- Do not convert sparse evidence into certainty.",
        "",
        "## Evidence-backed Risk Areas",
    ]

    for topic, matches in topic_hits.items():
        lines.append(f"### {topic}")
        lines.extend(_bullet_evidence(matches))
        lines.append("")

    lines.extend(
        [
            "## Escalate Instead",
            "- Escalate HR and compensation topics to HR or the real boss.",
            "- Escalate legal or contract language to legal counsel.",
            "- Escalate finance, transfer, or fundraising commitments to the authorized owner.",
            "- Frame any remaining answer as a simulated recommendation.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_corrections(corrections: list[dict[str, object]]) -> str:
    lines = ["# Corrections", ""]
    if not corrections:
        lines.append("No formal corrections have been recorded.")
        return "\n".join(lines).strip() + "\n"

    for record in corrections:
        lines.append(
            f"- `{record['record_id']}` [{record['timestamp']}] ({record['layer_hint']}) {excerpt(str(record['content']), limit=220)}"
        )
    return "\n".join(lines).strip() + "\n"


def build_prompt_pack(
    manifest: dict[str, object],
    boundary_text: str,
    operating_text: str | None,
    voice_text: str | None,
    mode: str,
) -> str:
    lines = [
        f"# Boss Invocation Pack: {manifest['display_name']}",
        "",
        f"- Slug: {manifest['slug']}",
        f"- Status: {manifest['status']}",
        f"- Boss type: {manifest['boss_type']}",
        "",
        "## Boundary",
        boundary_text.strip(),
    ]
    if mode in {"full", "operator"} and operating_text:
        lines.extend(["", "## Operating System", operating_text.strip()])
    if mode in {"full", "voice"} and voice_text:
        lines.extend(["", "## Voice", voice_text.strip()])
    if mode == "pua":
        if operating_text:
            lines.extend(["", "## Operating System", operating_text.strip()])
        if voice_text:
            lines.extend(["", "## Voice", voice_text.strip()])
        lines.extend(
            [
                "",
                "## PUA Mode",
                "- Use high-pressure, boss-style challenge aimed at execution quality, speed, clarity, and accountability.",
                "- Speak in a compressed, skeptical, demanding cadence. Push the user to commit to owner, deadline, metric, and next action.",
                "- Break vague language, excuses, and narrative drift. Force prioritization and concrete tradeoffs.",
                "- Keep the pressure work-focused. Do not attack identity, dignity, appearance, relationships, or mental health.",
                "- Do not fabricate real authority, approvals, punishments, or binding decisions.",
                "- End with an explicit commitment request or next checkpoint.",
            ]
        )
    return "\n".join(lines).strip() + "\n"
