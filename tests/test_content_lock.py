import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ContentLockScriptTests(unittest.TestCase):
    def test_freezes_a_confirmed_evidence_bound_legacy_plan(self):
        skill_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = root / "plan.json"
            evidence = root / "evidence.json"
            output = root / "slide_content_lock.json"
            plan.write_text(json.dumps({
                "confirmed": True,
                "confirmation_note": "Confirmed",
                "sections": ["结果"],
                "pages": [{
                    "page_id": "P01",
                    "layout": "evidence",
                    "page_role": "evidence",
                    "section": "结果",
                    "title": "结果支持当前结论",
                    "visual_strategy": "intentional_text_only",
                    "evidence_ids": ["E01"],
                    "page_payload": {
                        "claim": "结果支持当前结论",
                        "supporting_unit_ids": ["E01"],
                        "density": {"status": "intentional_sparse"},
                    },
                }],
            }, ensure_ascii=False), encoding="utf-8")
            evidence.write_text(json.dumps({
                "items": [{"id": "E01", "claim": "结果支持当前结论"}],
            }, ensure_ascii=False), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(skill_root / "scripts" / "build_content_lock.py"),
                    "--plan", str(plan),
                    "--evidence", str(evidence),
                    "--output", str(output),
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(payload["confirmed"])
            self.assertEqual(payload["pages"][0]["evidence_ids"], ["E01"])
            self.assertEqual(len(payload["pages"][0]["content_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
