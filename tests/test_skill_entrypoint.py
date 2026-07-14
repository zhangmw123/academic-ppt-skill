import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SkillEntrypointTests(unittest.TestCase):
    def test_portable_skill_entrypoint_runs_from_a_user_project_directory(self):
        skill_root = Path(__file__).resolve().parents[1]
        entrypoint = skill_root / "scripts" / "analyze_sources.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            source = project / "实验.md"
            source.write_text("模型 算法 训练 数据集 基线 消融 泛化。", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(entrypoint), str(source)],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            report = json.loads(result.stdout)
            self.assertEqual(report["source_count"], 1)
            self.assertEqual(report["method_profiles"]["primary"], "computational_modeling")


if __name__ == "__main__":
    unittest.main()
