import unittest
import json
from pathlib import Path

from academic_ppt.scenes import SceneCatalog, ScenePlanContract
from scripts.validate_scene_plan import validate_plan


class SceneCatalogTests(unittest.TestCase):
    def test_resolves_aliases_and_accepts_a_complete_scene_contract(self):
        catalog = SceneCatalog.load()
        profile = catalog.resolve("开题")
        contract = ScenePlanContract(
            deck_scope="complete",
            evidence_state="planned",
            coverage_tags=profile.required_tags,
            argument_units=profile.argument_chain,
            section_variant="standard_6",
            duration_minutes=12,
        )

        result = catalog.validate_plan(
            profile.name,
            contract,
            sections=profile.default_variants["standard_6"],
            page_count=profile.complete_min,
            total_seconds=12 * 60,
        )

        self.assertEqual(profile.name, "开题答辩")
        self.assertTrue(result.passed)
        self.assertEqual(result.errors, ())

    def test_rejects_an_incomplete_complete_deck_with_actionable_errors(self):
        catalog = SceneCatalog.load()
        contract = ScenePlanContract(
            deck_scope="complete",
            evidence_state="published",
            coverage_tags=("research_background",),
            argument_units=("problem",),
            section_variant="classic_5",
        )

        result = catalog.validate_plan(
            "毕业答辩",
            contract,
            sections=("研究背景与问题",),
            page_count=1,
            total_seconds=60,
        )

        self.assertFalse(result.passed)
        self.assertTrue(any("requires 18-30 pages" in error for error in result.errors))
        self.assertTrue(any("does not allow evidence_state=published" in error for error in result.errors))
        self.assertTrue(any("missing coverage tags" in error for error in result.errors))
        self.assertTrue(any("missing argument units" in error for error in result.errors))
        self.assertTrue(any("sections differ" in error for error in result.errors))

    def test_rejects_unknown_scene_instead_of_silently_falling_back(self):
        catalog = SceneCatalog.load()

        with self.assertRaisesRegex(ValueError, "unknown scene profile"):
            catalog.resolve("通用汇报")

    def test_legacy_validator_uses_the_same_alias_and_complete_contract(self):
        profiles = json.loads(
            (Path(__file__).resolve().parents[1] / "references" / "scene-profiles.json").read_text(encoding="utf-8")
        )
        profile = SceneCatalog.load().resolve("组会周报")
        plan = {
            "scene": "组会周报",
            "deck_scope": "complete",
            "evidence_state": "interim",
            "coverage_tags": list(profile.required_tags),
            "argument_units": list(profile.argument_chain),
            "section_variant": "weekly_5",
            "sections": list(profile.default_variants["weekly_5"]),
            "duration_minutes": 8,
            "pages": [
                {"page_id": f"P{index + 1:03d}", "page_role": "section", "time_seconds": 60}
                for index in range(8)
            ],
        }

        result = validate_plan(plan, profiles)

        self.assertTrue(result["passed"])
        self.assertEqual(result["scene"], "组会-周报进展")

    def test_legacy_validator_rejects_explicit_variant_drift_like_the_v2_service(self):
        profiles = json.loads(
            (Path(__file__).resolve().parents[1] / "references" / "scene-profiles.json").read_text(encoding="utf-8")
        )
        profile = SceneCatalog.load().resolve("组会-周报进展")
        plan = {
            "scene": profile.name,
            "deck_scope": "complete",
            "evidence_state": "interim",
            "coverage_tags": list(profile.required_tags),
            "argument_units": list(profile.argument_chain),
            "section_variant": "weekly_5",
            "sections": ["自定义板块"],
            "pages": [
                {"page_id": f"P{index + 1:03d}", "page_role": "section", "time_seconds": 60}
                for index in range(5)
            ],
        }

        result = validate_plan(plan, profiles)

        self.assertFalse(result["passed"])
        self.assertTrue(any("sections differ" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
