#!/usr/bin/env python3
"""Command runner for the boss-skills skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.archive import BossArchiveManager
from tools.errors import BossArchiveError, InvalidCommandError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage boss-skills archives.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Create a boss archive and optionally ingest first evidence."
    )
    init_parser.add_argument("--slug", required=True)
    init_parser.add_argument("--display-name", required=True)
    init_parser.add_argument("--boss-type", required=True)
    _add_ingest_args(init_parser)
    init_parser.add_argument("--json", action="store_true")

    update_parser = subparsers.add_parser(
        "update-boss", help="Ingest evidence or apply a correction."
    )
    update_parser.add_argument("--slug", required=True)
    _add_ingest_args(update_parser, include_corrections=True)
    update_parser.add_argument("--json", action="store_true")

    list_parser = subparsers.add_parser("list-bosses", help="List all boss archives.")
    list_parser.add_argument("--json", action="store_true")

    status_parser = subparsers.add_parser("status", help="Inspect one archive.")
    status_parser.add_argument("--slug", required=True)
    status_parser.add_argument("--json", action="store_true")

    render_parser = subparsers.add_parser("render", help="Render the prompt pack.")
    render_parser.add_argument("--slug", required=True)
    render_parser.add_argument("--mode", choices=("full", "operator", "voice", "pua"), required=True)

    pua_parser = subparsers.add_parser("pua", help="Render the high-pressure boss prompt pack.")
    pua_parser.add_argument("--slug", required=True)

    rollback_parser = subparsers.add_parser(
        "boss-rollback", help="Rollback an archive to a prior snapshot."
    )
    rollback_parser.add_argument("--slug", required=True)
    rollback_parser.add_argument("--version", required=True)
    rollback_parser.add_argument("--json", action="store_true")

    delete_parser = subparsers.add_parser("delete-boss", help="Delete an archive.")
    delete_parser.add_argument("--slug", required=True)
    delete_parser.add_argument("--yes", action="store_true", required=True)

    return parser.parse_args()


def _add_ingest_args(parser: argparse.ArgumentParser, *, include_corrections: bool = False) -> None:
    parser.add_argument(
        "--ingestion-mode",
        choices=("describe", "paste-chat", "import-file", "import-image"),
        help="Logical ingestion mode for this command.",
    )
    parser.add_argument("--source-type", help="Normalized source type.")
    parser.add_argument("--source-name", help="Display label for the source.")
    parser.add_argument("--speaker", help="Speaker when known.")
    parser.add_argument("--audience", help="Audience when known.")
    parser.add_argument(
        "--privacy", default="internal", choices=("internal", "restricted", "sensitive")
    )
    parser.add_argument("--confidence", type=float, default=0.85)
    parser.add_argument("--timestamp", help="Original timestamp in ISO format.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", help="Inline evidence text.")
    group.add_argument("--file", help="Path to a structured or document file.")
    group.add_argument("--image", help="Path to an image for OCR import.")
    if include_corrections:
        group.add_argument("--correction-text", help="Formal correction text for a ready archive.")
        parser.add_argument(
            "--correction-type",
            choices=("operator", "voice", "boundary"),
            help="Correction target layer.",
        )


def _default_source_type(args: argparse.Namespace) -> str:
    if args.source_type:
        return args.source_type
    if getattr(args, "correction_text", None):
        return "correction"
    if args.ingestion_mode == "paste-chat":
        return "chat"
    if args.ingestion_mode == "describe":
        return "description"
    if args.ingestion_mode == "import-image":
        return "screenshot"
    if args.file:
        suffix = Path(args.file).suffix.lower()
        if suffix in {".json", ".jsonl", ".csv", ".html", ".htm", ".docx", ".pdf"}:
            return "document"
        if suffix == ".eml":
            return "email"
    if args.image:
        return "screenshot"
    return "document" if args.file else "description"


def _print_payload(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _ingest_or_status(manager: BossArchiveManager, args: argparse.Namespace) -> dict[str, object]:
    source_type = _default_source_type(args)
    source_name = args.source_name or Path(args.file or args.image or "inline-input").name
    if args.text:
        return manager.import_text(
            slug=args.slug,
            source_type=source_type,
            source_name=source_name,
            text=args.text,
            speaker=args.speaker,
            audience=args.audience,
            privacy=args.privacy,
            confidence=args.confidence,
            timestamp=args.timestamp,
        )
    if args.file:
        return manager.import_file(
            slug=args.slug,
            file_path=Path(args.file),
            source_type=source_type,
            source_name=args.source_name,
            speaker=args.speaker,
            audience=args.audience,
            privacy=args.privacy,
            confidence=args.confidence,
        )
    if args.image:
        return manager.import_image(
            slug=args.slug,
            image_path=Path(args.image),
            source_type=source_type,
            source_name=args.source_name,
            speaker=args.speaker,
            audience=args.audience,
            privacy=args.privacy,
            confidence=args.confidence,
        )
    if getattr(args, "correction_text", None):
        if not args.correction_type:
            raise InvalidCommandError("--correction-type is required with --correction-text.")
        return manager.apply_correction(
            slug=args.slug,
            correction_type=args.correction_type,
            text=args.correction_text,
            source_name=args.source_name or "formal-correction",
            privacy=args.privacy,
        )
    return manager.status(args.slug)


def main() -> int:
    args = parse_args()
    manager = BossArchiveManager(ROOT)

    try:
        if args.command == "init":
            result = manager.init_archive(args.slug, args.display_name, args.boss_type)
            if args.text or args.file or args.image:
                result = _ingest_or_status(manager, args)
            _print_payload(result)
            return 0

        if args.command == "update-boss":
            _print_payload(_ingest_or_status(manager, args))
            return 0

        if args.command == "list-bosses":
            _print_payload(manager.list_archives())
            return 0

        if args.command == "status":
            _print_payload(manager.status(args.slug))
            return 0

        if args.command == "render":
            print(manager.render_prompt_pack(args.slug, args.mode))
            return 0

        if args.command == "pua":
            print(manager.render_prompt_pack(args.slug, "pua"))
            return 0

        if args.command == "boss-rollback":
            _print_payload(manager.rollback(args.slug, args.version))
            return 0

        if args.command == "delete-boss":
            manager.delete_archive(args.slug)
            print(f"Deleted archive '{args.slug}'.")
            return 0
    except BossArchiveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
