import tempfile
import unittest
from pathlib import Path

from academic_ppt.benchmarks import SceneBenchmarkSuite
from academic_ppt.scenes import SceneCatalog


class SceneBenchmarkSuiteTests(unittest.TestCase):
    def test_manifest_covers_each_supported_scene_exactly_once(self):
        suite = SceneBenchmarkSuite.load()
        self.assertEqual(len(suite.cases), 10)
        self.assertEqual({case.scene for case in suite.cases}, set(SceneCatalog.load().profiles))

    def test_synthetic_fixture_passes_contract_but_never_product_acceptance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            suite = SceneBenchmarkSuite.load()
            case = suite.case("lab-weekly-progress")
            result = suite.run_case(case, Path(temp_dir) / case.case_id)

            self.assertTrue(result["contract_passed"])
            self.assertFalse(result["pipeline_completed"])
            self.assertFalse(result["product_accepted"])
            self.assertFalse(result["passed"])
            self.assertIn("synthetic", result["benchmark_class"])

    def test_full_synthetic_matrix_accepts_keep_going_without_claiming_products(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = SceneBenchmarkSuite.load().run(Path(temp_dir), keep_going=True)

            self.assertTrue(report["contract_matrix_passed"])
            self.assertFalse(report["product_suite_passed"])
            self.assertFalse(report["passed"])
            self.assertEqual(len(report["cases"]), 10)


if __name__ == "__main__":
    unittest.main()
