import tempfile
import unittest
from pathlib import Path

from academic_ppt.visuals import VisualTask


class VisualTaskTests(unittest.TestCase):
    def test_visual_task_must_complete_the_evidence_bound_acceptance_sequence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "chart.png"
            output.write_bytes(b"rendered")
            task = VisualTask.create(
                task_id="VIS_001",
                page_id="P001",
                evidence_ids=["EVD_001"],
                task_type="chart",
            )

            task = task.lock_semantics()
            task = task.mark_rendered(output)
            task = task.bind_to_slide()
            task = task.mark_render_inspected()
            task = task.accept()

            self.assertEqual(task.status, "accepted")
            self.assertEqual(task.output_path, str(output.resolve()))
            with self.assertRaisesRegex(ValueError, "cannot accept"):
                VisualTask.create(
                    task_id="VIS_002",
                    page_id="P001",
                    evidence_ids=["EVD_001"],
                    task_type="chart",
                ).accept()


if __name__ == "__main__":
    unittest.main()
