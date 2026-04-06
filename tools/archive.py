"""Archive management for boss-skills."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from .errors import (
    ArchiveExistsError,
    ArchiveNotFoundError,
    ArchiveNotReadyError,
    InvalidCommandError,
)
from .evidence import build_record, calculate_coverage, route_record, utc_now, validate_slug
from .extractors import extract_file_seeds, extract_image_seed
from .renderers import (
    build_boundary,
    build_corrections,
    build_operating_system,
    build_prompt_pack,
    build_voice,
)


class BossArchiveManager:
    def __init__(self, skill_root: Path) -> None:
        self.skill_root = skill_root
        self.boss_root = skill_root / "bosses"
        self.boss_root.mkdir(parents=True, exist_ok=True)

    def init_archive(self, slug: str, display_name: str, boss_type: str) -> dict[str, object]:
        slug = validate_slug(slug)
        archive_dir = self._archive_dir(slug)
        if archive_dir.exists():
            raise ArchiveExistsError(f"Archive already exists for slug '{slug}'.")

        (archive_dir / "records").mkdir(parents=True)
        (archive_dir / "analysis").mkdir()
        (archive_dir / "versions").mkdir()

        now = utc_now()
        manifest = {
            "slug": slug,
            "display_name": display_name.strip(),
            "boss_type": boss_type.strip(),
            "status": "collecting",
            "coverage_score": 0,
            "evidence_counts": {},
            "missing_evidence": [
                "Add a second distinct source type.",
                "Add at least one direct-expression record from the boss.",
                "Add at least one decision or management-action record.",
            ],
            "created_at": now,
            "last_updated_at": now,
            "current_version": "",
            "record_files": [],
        }
        self._write_json(archive_dir / "manifest.json", manifest)
        self._write_json(
            archive_dir / "analysis" / "coverage.json",
            {
                "ready": False,
                "coverage_score": 0,
                "source_types": [],
                "evidence_counts": {},
                "missing_evidence": manifest["missing_evidence"],
                "direct_expression_count": 0,
                "decision_signal_count": 0,
                "boundary_signal_count": 0,
                "layer_counts": {},
            },
        )
        self._write_json(archive_dir / "analysis" / "router.json", {"records": []})
        self._snapshot(slug, event="init")
        return self.status(slug)

    def status(self, slug: str) -> dict[str, object]:
        archive_dir = self._require_archive(slug)
        return {
            "manifest": self._read_json(archive_dir / "manifest.json"),
            "coverage": self._read_json(archive_dir / "analysis" / "coverage.json"),
        }

    def list_archives(self) -> list[dict[str, object]]:
        manifests: list[dict[str, object]] = []
        for manifest_path in sorted(self.boss_root.glob("*/manifest.json")):
            manifests.append(self._read_json(manifest_path))
        return manifests

    def import_text(
        self,
        *,
        slug: str,
        source_type: str,
        source_name: str,
        text: str,
        speaker: str | None,
        audience: str | None,
        privacy: str,
        confidence: float,
        timestamp: str | None = None,
    ) -> dict[str, object]:
        record = build_record(
            source_type=source_type,
            source_name=source_name,
            content=text,
            speaker=speaker,
            audience=audience,
            attachment_refs=[],
            confidence=confidence,
            privacy=privacy,
            timestamp=timestamp,
        )
        return self._ingest_records(validate_slug(slug), [record], event="import-text")

    def import_file(
        self,
        *,
        slug: str,
        file_path: Path,
        source_type: str,
        source_name: str | None,
        speaker: str | None,
        audience: str | None,
        privacy: str,
        confidence: float,
    ) -> dict[str, object]:
        seeds = extract_file_seeds(file_path)
        records = [
            build_record(
                source_type=source_type,
                source_name=source_name or seed.source_name,
                content=seed.text,
                speaker=speaker or seed.speaker,
                audience=audience or seed.audience,
                attachment_refs=[str(file_path)],
                confidence=confidence,
                privacy=privacy,
                timestamp=seed.timestamp,
            )
            for seed in seeds
        ]
        return self._ingest_records(validate_slug(slug), records, event="import-file")

    def import_image(
        self,
        *,
        slug: str,
        image_path: Path,
        source_type: str,
        source_name: str | None,
        speaker: str | None,
        audience: str | None,
        privacy: str,
        confidence: float,
    ) -> dict[str, object]:
        seed = extract_image_seed(image_path)
        record = build_record(
            source_type=source_type,
            source_name=source_name or seed.source_name,
            content=seed.text,
            speaker=speaker or seed.speaker,
            audience=audience or seed.audience,
            attachment_refs=[str(image_path)],
            confidence=confidence,
            privacy=privacy,
        )
        return self._ingest_records(validate_slug(slug), [record], event="import-image")

    def apply_correction(
        self,
        *,
        slug: str,
        correction_type: str,
        text: str,
        source_name: str,
        privacy: str,
    ) -> dict[str, object]:
        status = self.status(slug)
        manifest = status["manifest"]
        if manifest["status"] != "ready":
            raise ArchiveNotReadyError("Corrections are allowed only on ready archives.")
        if correction_type not in {"operator", "voice", "boundary"}:
            raise InvalidCommandError("Correction type must be operator, voice, or boundary.")

        record = build_record(
            source_type="correction",
            source_name=source_name,
            content=text,
            speaker="user",
            audience="archive",
            attachment_refs=[],
            confidence=1.0,
            privacy=privacy,
            forced_layer=correction_type,
        )
        return self._ingest_records(validate_slug(slug), [record], event="correction")

    def render_prompt_pack(self, slug: str, mode: str) -> str:
        slug = validate_slug(slug)
        if mode not in {"full", "operator", "voice", "pua"}:
            raise InvalidCommandError("Mode must be full, operator, voice, or pua.")

        status = self.status(slug)
        manifest = status["manifest"]
        if manifest["status"] != "ready":
            missing = "; ".join(status["coverage"]["missing_evidence"])
            raise ArchiveNotReadyError(
                f"Archive '{slug}' is not ready. Missing evidence: {missing}"
            )

        archive_dir = self._archive_dir(slug)
        boundary_text = (archive_dir / "boundary.md").read_text(encoding="utf-8")
        operating_text = None
        voice_text = None
        if mode in {"full", "operator", "pua"}:
            operating_text = (archive_dir / "operating-system.md").read_text(encoding="utf-8")
        if mode in {"full", "voice", "pua"}:
            voice_text = (archive_dir / "voice.md").read_text(encoding="utf-8")
        return build_prompt_pack(manifest, boundary_text, operating_text, voice_text, mode)

    def rollback(self, slug: str, version: str) -> dict[str, object]:
        slug = validate_slug(slug)
        archive_dir = self._require_archive(slug)
        snapshot_path = archive_dir / "versions" / f"{version}.zip"
        if not snapshot_path.exists():
            raise ArchiveNotFoundError(f"Snapshot {version} does not exist for '{slug}'.")

        self._remove_ready_outputs(archive_dir)
        with zipfile.ZipFile(snapshot_path, "r") as archive:
            archive.extractall(archive_dir)

        manifest = self._read_json(archive_dir / "manifest.json")
        manifest["last_updated_at"] = utc_now()
        manifest["restored_from_version"] = version
        self._write_json(archive_dir / "manifest.json", manifest)
        self._snapshot(slug, event=f"rollback:{version}")
        return self.status(slug)

    def delete_archive(self, slug: str) -> None:
        archive_dir = self._require_archive(slug)
        shutil.rmtree(archive_dir)

    def _ingest_records(
        self,
        slug: str,
        records: list[dict[str, object]],
        *,
        event: str,
    ) -> dict[str, object]:
        if not records:
            raise InvalidCommandError("No records were produced for ingestion.")

        archive_dir = self._require_archive(slug)
        batch_name = f"{utc_now().replace(':', '').replace('+00:00', 'Z')}-{records[0]['record_id']}.jsonl"
        with (archive_dir / "records" / batch_name).open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        manifest = self._read_json(archive_dir / "manifest.json")
        manifest["record_files"] = list(
            dict.fromkeys([*manifest.get("record_files", []), batch_name])
        )
        self._write_json(archive_dir / "manifest.json", manifest)
        changed_layers = {route_record(record)["primary_layer"] for record in records}
        self._rebuild_archive(slug, changed_layers, event=event)
        return self.status(slug)

    def _rebuild_archive(self, slug: str, changed_layers: set[str], *, event: str) -> None:
        archive_dir = self._require_archive(slug)
        manifest = self._read_json(archive_dir / "manifest.json")
        records = self._load_records(archive_dir, manifest)
        router_rows = [route_record(record) for record in records]
        coverage = calculate_coverage(records, router_rows).to_dict()

        self._write_json(archive_dir / "analysis" / "router.json", {"records": router_rows})
        self._write_json(archive_dir / "analysis" / "coverage.json", coverage)

        manifest["coverage_score"] = coverage["coverage_score"]
        manifest["evidence_counts"] = coverage["evidence_counts"]
        manifest["missing_evidence"] = coverage["missing_evidence"]
        manifest["last_updated_at"] = utc_now()
        manifest["record_files"] = sorted(path.name for path in (archive_dir / "records").glob("*.jsonl"))

        status_changed = manifest["status"] != ("ready" if coverage["ready"] else "collecting")
        manifest["status"] = "ready" if coverage["ready"] else "collecting"

        if manifest["status"] == "ready":
            self._write_ready_outputs(
                archive_dir,
                manifest,
                records,
                router_rows,
                coverage,
                changed_layers,
                force_all=status_changed or event.startswith("rollback"),
            )
        else:
            self._remove_ready_outputs(archive_dir)

        self._write_json(archive_dir / "manifest.json", manifest)
        self._snapshot(slug, event=event)

    def _write_ready_outputs(
        self,
        archive_dir: Path,
        manifest: dict[str, object],
        records: list[dict[str, object]],
        router_rows: list[dict[str, object]],
        coverage: dict[str, object],
        changed_layers: set[str],
        *,
        force_all: bool,
    ) -> None:
        if force_all or "operator" in changed_layers or "mixed" in changed_layers:
            (archive_dir / "operating-system.md").write_text(
                build_operating_system(manifest, records, router_rows, coverage),
                encoding="utf-8",
            )
        if force_all or "voice" in changed_layers or "mixed" in changed_layers:
            (archive_dir / "voice.md").write_text(
                build_voice(manifest, records, router_rows),
                encoding="utf-8",
            )
        if force_all or "boundary" in changed_layers or "mixed" in changed_layers:
            (archive_dir / "boundary.md").write_text(
                build_boundary(manifest, records, router_rows),
                encoding="utf-8",
            )

        corrections = [record for record in records if record["source_type"] == "correction"]
        (archive_dir / "corrections.md").write_text(
            build_corrections(corrections),
            encoding="utf-8",
        )

    def _remove_ready_outputs(self, archive_dir: Path) -> None:
        for filename in ("operating-system.md", "voice.md", "boundary.md", "corrections.md"):
            target = archive_dir / filename
            if target.exists():
                try:
                    target.unlink()
                except PermissionError:
                    pass

    def _snapshot(self, slug: str, *, event: str) -> None:
        archive_dir = self._require_archive(slug)
        manifest = self._read_json(archive_dir / "manifest.json")
        next_version = self._next_version(archive_dir)
        manifest["current_version"] = next_version
        manifest["last_event"] = event
        self._write_json(archive_dir / "manifest.json", manifest)

        snapshot_path = archive_dir / "versions" / f"{next_version}.zip"
        with zipfile.ZipFile(snapshot_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in archive_dir.rglob("*"):
                if "versions" in path.parts:
                    continue
                if path.is_file():
                    archive.write(path, path.relative_to(archive_dir))

    def _next_version(self, archive_dir: Path) -> str:
        versions = sorted(path.stem for path in (archive_dir / "versions").glob("v*.zip"))
        if not versions:
            return "v0001"
        current = int(versions[-1][1:])
        return f"v{current + 1:04d}"

    def _load_records(
        self, archive_dir: Path, manifest: dict[str, object] | None = None
    ) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        filenames: list[str] | None = None
        if manifest is not None:
            raw_filenames = manifest.get("record_files")
            if isinstance(raw_filenames, list) and raw_filenames:
                filenames = [str(name) for name in raw_filenames]

        paths = (
            [archive_dir / "records" / name for name in filenames]
            if filenames is not None
            else sorted((archive_dir / "records").glob("*.jsonl"))
        )
        for path in paths:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        records.append(json.loads(stripped))
        return records

    def _archive_dir(self, slug: str) -> Path:
        return self.boss_root / slug

    def _require_archive(self, slug: str) -> Path:
        archive_dir = self._archive_dir(validate_slug(slug))
        if not archive_dir.exists():
            raise ArchiveNotFoundError(f"Archive not found for slug '{slug}'.")
        return archive_dir

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
