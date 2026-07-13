import tempfile
import unittest
from pathlib import Path

from academic_ppt.benchmarks import SceneBenchmarkSuite
from academic_ppt.scenes import SceneCatalog


class SceneBenchmarkSuiteTests(unittest.TestCase):
    def test_manifest_covers_each_supported_scene_exactly_once(self):
        suite = SceneBenchmarkSuite.load()

        self.assertEqual(len(suite.cases), 10)
        self.assertEqual(
            {case.scene for case in suite.cases},
            set(SceneCatalog.load().profiles),
        )
        self.assertEqual(len({case.case_id for case in suite.cases}), 10)

    def test_runs_one_complete_scene_through_the_shared_delivery_workflow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            suite = SceneBenchmarkSuite.load()
            case = suite.case("lab-weekly-progress")

            result = suite.run_case(case, Path(temp_dir) / case.case_id)

            self.assertTrue(result["passed"])
            self.assertEqual(result["scene"], "组会-周报进展")
            self.assertEqual(result["page_count"], 5)
            self.assertEqual(result["template_id"], "T01")
            self.assertFalse(result["formal_accepted"])
            self.assertEqual({Path(path).suffix for path in result["visible_files"]}, {".pptx", ".docx"})
            self.assertTrue((Path(temp_dir) / case.case_id / "audit" / "benchmark_result.json").is_file())


if __name__ == "__main__":
    unittest.main()
