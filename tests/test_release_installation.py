import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InstalledSkillReleaseTests(unittest.TestCase):
    def test_canonical_skill_copy_runs_from_clean_codex_and_claude_workspaces(self):
        source_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "unrelated-workspace"
            workspace.mkdir()
            source = workspace / "paper.md"
            source.write_text("文献 综述 检索 引文 系统评价。", encoding="utf-8")
            for host_path in (
                root / "codex-home" / "skills" / "academic-ppt-skill",
                root / "claude-home" / "skills" / "academic-ppt-skill",
            ):
                self._copy_skill(source_root, host_path)
                analyzed = subprocess.run(
                    [
                        sys.executable,
                        str(host_path / "scripts" / "analyze_sources.py"),
                        str(source),
                    ],
                    cwd=workspace,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                resolved = subprocess.run(
                    [
                        sys.executable,
                        str(host_path / "scripts" / "resolve_template.py"),
                        "蓝色-学术答辩多版式通用模板 (Academic Defense Multi-Layout Template).pptx",
                        "--json",
                    ],
                    cwd=workspace,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

                analyzed_payload = json.loads(analyzed.stdout)
                resolved_payload = json.loads(resolved.stdout)
                self.assertEqual(analyzed_payload["source_count"], 1)
                self.assertEqual(analyzed_payload["method_profiles"]["primary"], "literature_synthesis")
                self.assertEqual(resolved_payload["id"], "T03")
                self.assertTrue(Path(resolved_payload["absolute_path"]).is_file())
                self.assertTrue((host_path / "SKILL.md").is_file())
                self.assertTrue((host_path / "agents" / "openai.yaml").is_file())
                for relative_path in (
                    "references/capability-contract.md",
                    "scripts/analyze_sources.py",
                    "scripts/extract_figures.py",
                    "scripts/extract_template_grammar.py",
                    "scripts/compile_bundled_source_templates.py",
                    "scripts/validate_template_spec.py",
                    "scripts/render_scientific_visuals.py",
                    "scripts/validate_visual_tasks.py",
                    "scripts/build_complete_deck.py",
                    "references/standard-template-spec.schema.json",
                    "references/object-binding-manifest.schema.json",
                    "references/template-semantic-prototypes.json",
                    "assets/template_specs/T01_green_research.semantic.json",
                    "assets/template_specs/T03_blue_defense.semantic.json",
                ):
                    self.assertTrue((host_path / relative_path).is_file(), relative_path)

    @staticmethod
    def _copy_skill(source_root: Path, destination: Path) -> None:
        destination.mkdir(parents=True)
        for directory in ("academic_ppt", "scripts", "references", "assets", "agents"):
            shutil.copytree(
                source_root / directory,
                destination / directory,
                ignore=shutil.ignore_patterns("__pycache__", ".wpp_backup"),
            )
        for filename in ("SKILL.md", "CONTEXT.md", "requirements.txt"):
            shutil.copy2(source_root / filename, destination / filename)


if __name__ == "__main__":
    unittest.main()
