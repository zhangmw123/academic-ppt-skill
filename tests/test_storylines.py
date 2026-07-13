import tempfile
import unittest
from pathlib import Path

from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor
from academic_ppt.storylines import StorylinePlanner


class StorylinePlannerTests(unittest.TestCase):
    def test_produces_comparable_evidence_grounded_storyline_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "study.md"
            path.write_text("模型方法。\n模型 F1 为 92.9%。\n边界：仅一个数据集。", encoding="utf-8")
            graph = EvidenceGraph.from_sources([SourceIngestor().ingest(path)])

            options, recommended = StorylinePlanner().propose("毕业答辩", graph)

            self.assertEqual(len(options), 3)
            self.assertEqual(recommended.option_id, "problem_method_evidence")
            self.assertIn("EVD_", options[0].evidence_ids[0])


if __name__ == "__main__":
    unittest.main()
