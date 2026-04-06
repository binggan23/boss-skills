from __future__ import annotations

import csv
import shutil
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.archive import BossArchiveManager
from tools.errors import ArchiveNotReadyError


class BossArchiveManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base_tmp = ROOT / "tests" / ".tmp"
        self.base_tmp.mkdir(parents=True, exist_ok=True)
        self.root = self.base_tmp / f"case-{uuid.uuid4().hex}"
        self.root.mkdir()
        (self.root / "bosses").mkdir(parents=True, exist_ok=True)
        self.manager = BossArchiveManager(self.root)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_init_creates_collecting_archive(self) -> None:
        status = self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        archive_dir = self.root / "bosses" / "founder-alpha"

        self.assertEqual(status["manifest"]["status"], "collecting")
        self.assertTrue((archive_dir / "manifest.json").exists())
        self.assertTrue((archive_dir / "analysis" / "coverage.json").exists())
        self.assertTrue((archive_dir / "versions" / "v0001.zip").exists())
        self.assertFalse((archive_dir / "voice.md").exists())

    def test_ready_gate_generates_docs(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        self.manager.import_text(
            slug="founder-alpha",
            source_type="chat",
            source_name="chat-1",
            text="先给我结论，今天把方案推进完。",
            speaker="老板",
            audience="团队",
            privacy="internal",
            confidence=0.9,
        )
        status = self.manager.import_text(
            slug="founder-alpha",
            source_type="meeting-note",
            source_name="weekly-note",
            text="老板否决了扩招，要求先验证风险，再审批预算。",
            speaker="运营",
            audience="管理层",
            privacy="internal",
            confidence=0.9,
        )

        archive_dir = self.root / "bosses" / "founder-alpha"
        self.assertEqual(status["manifest"]["status"], "ready")
        self.assertTrue((archive_dir / "operating-system.md").exists())
        self.assertTrue((archive_dir / "voice.md").exists())
        self.assertTrue((archive_dir / "boundary.md").exists())
        self.assertTrue((archive_dir / "corrections.md").exists())

    def test_render_requires_ready_archive(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        with self.assertRaises(ArchiveNotReadyError):
            self.manager.render_prompt_pack("founder-alpha", "full")

    def test_render_pua_mode_includes_pressure_overlay(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        self.manager.import_text(
            slug="founder-alpha",
            source_type="chat",
            source_name="chat-1",
            text="Give me the conclusion first. Ship today.",
            speaker="boss",
            audience="team",
            privacy="internal",
            confidence=0.9,
        )
        self.manager.import_text(
            slug="founder-alpha",
            source_type="meeting-note",
            source_name="weekly-note",
            text="The boss rejected extra hiring and asked for a risk review before budget approval.",
            speaker="ops",
            audience="management",
            privacy="internal",
            confidence=0.9,
        )

        prompt = self.manager.render_prompt_pack("founder-alpha", "pua")

        self.assertIn("## Boundary", prompt)
        self.assertIn("## Operating System", prompt)
        self.assertIn("## Voice", prompt)
        self.assertIn("## PUA Mode", prompt)
        self.assertIn("high-pressure, boss-style challenge", prompt)

    def test_import_file_from_csv_contributes_records(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        csv_path = self.root / "chat.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["speaker", "content", "timestamp"])
            writer.writeheader()
            writer.writerow(
                {
                    "speaker": "老板",
                    "content": "先给我数字和结论。",
                    "timestamp": "2026-04-05T12:00:00+08:00",
                }
            )

        status = self.manager.import_file(
            slug="founder-alpha",
            file_path=csv_path,
            source_type="chat",
            source_name=None,
            speaker=None,
            audience=None,
            privacy="internal",
            confidence=0.88,
        )
        self.assertEqual(status["coverage"]["direct_expression_count"], 1)

    def test_import_image_uses_ocr_backend(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        image_path = self.root / "capture.png"
        image_path.write_bytes(b"fake-image")

        with patch("tools.extractors.extract_image_text", return_value="马上同步结果，先处理客户问题。"):
            status = self.manager.import_image(
                slug="founder-alpha",
                image_path=image_path,
                source_type="screenshot",
                source_name=None,
                speaker="老板",
                audience="团队",
                privacy="internal",
                confidence=0.8,
            )

        self.assertEqual(status["coverage"]["direct_expression_count"], 1)

    def test_rollback_restores_previous_state(self) -> None:
        self.manager.init_archive("founder-alpha", "Founder Alpha", "founder")
        self.manager.import_text(
            slug="founder-alpha",
            source_type="chat",
            source_name="chat-1",
            text="先给我结论。",
            speaker="老板",
            audience="团队",
            privacy="internal",
            confidence=0.9,
        )
        status = self.manager.import_text(
            slug="founder-alpha",
            source_type="meeting-note",
            source_name="weekly-note",
            text="老板要求本周先验证风险再审批预算。",
            speaker="运营",
            audience="管理层",
            privacy="internal",
            confidence=0.9,
        )
        self.assertEqual(status["manifest"]["current_version"], "v0003")

        rolled_back = self.manager.rollback("founder-alpha", "v0002")

        self.assertEqual(rolled_back["manifest"]["status"], "collecting")
        self.assertEqual(rolled_back["manifest"]["current_version"], "v0004")
        with self.assertRaises(ArchiveNotReadyError):
            self.manager.render_prompt_pack("founder-alpha", "full")


if __name__ == "__main__":
    unittest.main()
