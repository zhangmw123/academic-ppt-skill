import tempfile
import unittest
from pathlib import Path

from academic_ppt.delivery import DeliveryBundle


class DeliveryBundleTests(unittest.TestCase):
    def test_exposes_only_pptx_and_docx_to_user_while_retaining_audit_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            inputs = Path(temp_dir) / "inputs"
            inputs.mkdir()
            pptx = inputs / "deck.pptx"
            script = inputs / "speech.docx"
            report = inputs / "render_report.json"
            pptx.write_bytes(b"pptx")
            script.write_bytes(b"docx")
            report.write_text("{}", encoding="utf-8")

            bundle = DeliveryBundle.create(root)
            delivery = bundle.publish(pptx, script, audit_artifacts=[report])

            self.assertEqual({path.suffix for path in delivery.visible_files}, {".pptx", ".docx"})
            self.assertTrue(all(path.parent == root / "deliverables" for path in delivery.visible_files))
            self.assertTrue((root / "audit" / "render_report.json").is_file())
            self.assertFalse(any(path.suffix == ".json" for path in delivery.visible_files))

    def test_retains_quality_summary_in_audit_without_exposing_it_to_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "presentation"
            inputs = Path(temp_dir) / "inputs"
            inputs.mkdir()
            pptx = inputs / "deck.pptx"
            script = inputs / "speech.docx"
            pptx.write_bytes(b"pptx")
            script.write_bytes(b"docx")

            delivery = DeliveryBundle.create(root).publish(
                pptx, script, quality_summary={"structural": True, "semantic": True, "visual": False}
            )

            summary = root / "audit" / "quality_summary.json"
            self.assertTrue(summary.is_file())
            self.assertNotIn(summary, delivery.visible_files)
            self.assertIn('"visual": false', summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
