import tempfile
import unittest
from pathlib import Path

from academic_ppt.ingest import SourceIngestor
from academic_ppt.profiles import ResearchMethodProfileResolver


class ResearchMethodProfileResolverTests(unittest.TestCase):
    def test_infers_computational_primary_engineering_secondary_and_allows_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            model_path = root / "模型实验.md"
            model_path.write_text(
                "模型算法训练数据集基线 F1 消融泛化结果。\n"
                "Transformer 模型在测试集上优于基线。\n",
                encoding="utf-8",
            )
            system_path = root / "系统验证.md"
            system_path.write_text(
                "系统架构 API 部署环境负载测试延迟吞吐量可靠性。\n",
                encoding="utf-8",
            )
            sources = [SourceIngestor().ingest(model_path), SourceIngestor().ingest(system_path)]

            inferred = ResearchMethodProfileResolver().infer(sources)
            overridden = ResearchMethodProfileResolver().infer(
                sources,
                primary_override="engineering_system_validation",
            )

            self.assertEqual(inferred.primary, "computational_modeling")
            self.assertEqual(inferred.secondary, ("engineering_system_validation",))
            self.assertIn("模型", inferred.basis["computational_modeling"])
            self.assertEqual(overridden.primary, "engineering_system_validation")
            self.assertTrue(overridden.user_overridden)

    def test_infers_each_remaining_supported_profile_from_its_evidence_language(self):
        cases = {
            "laboratory_experiment": "样本 对照 重复 实验条件 显微 试剂",
            "survey_empirical_analysis": "问卷 样本量 量表 信度 效度 回归",
            "literature_synthesis": "文献 综述 检索 引文 系统评价",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for profile, content in cases.items():
                path = root / f"{profile}.md"
                path.write_text(content, encoding="utf-8")

                resolution = ResearchMethodProfileResolver().infer([SourceIngestor().ingest(path)])

                self.assertEqual(resolution.primary, profile)
                self.assertEqual(resolution.secondary, ())
                self.assertTrue(resolution.basis[profile])

    def test_rejects_an_unsupported_user_profile_override(self):
        with self.assertRaisesRegex(ValueError, "unsupported research method profile"):
            ResearchMethodProfileResolver().infer([], primary_override="domain_taxonomy")


if __name__ == "__main__":
    unittest.main()
