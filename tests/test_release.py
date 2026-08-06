import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from academic_ppt.benchmarks import SceneBenchmarkSuite
from academic_ppt.release import GLOBAL_TEMPLATE_GATE, ReleaseEvidenceAuditor, TEMPLATE_IDS


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseEvidenceAuditorTests(unittest.TestCase):
    def test_repository_manifest_covers_the_complete_surface_without_claiming_release(self):
        root = Path(__file__).resolve().parents[1]
        report = ReleaseEvidenceAuditor(root).audit(root / "references" / "release-evidence.json")

        self.assertTrue(report["coverage"]["passed"])
        self.assertEqual(len(report["scene_benchmarks"]), 10)
        self.assertEqual(len(report["template_regressions"]), 8)
        self.assertFalse(report["release_accepted"])
        self.assertTrue(report["blockers"])
        compiled = json.loads(
            (root / "references" / "compiled-template-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(tuple(compiled["requested_templates"]), TEMPLATE_IDS)
        self.assertTrue(compiled["all_eight_templates_complete"])

    def test_complete_hash_bound_fixture_passes_and_stale_review_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            hard_gate_ids = [
                "real_source_material",
                "user_confirmation",
                "complete_scene_budget",
                "complete_scene_contract",
                "non_repeating_page_arguments",
                "sample_final_separation",
                "final_layout_is_complete",
                "full_preview_exported",
                "structural_qa",
                "scientific_semantic_qa",
                "visual_task_qa",
                "editable_template_manifest",
                GLOBAL_TEMPLATE_GATE,
                "powerpoint_real_render",
                "human_visual_review",
            ]
            _write_json(
                root / "references" / "product-acceptance-matrix.json",
                {"hard_gates": [{"id": gate_id} for gate_id in hard_gate_ids]},
            )
            scene_items = []
            confirmation_hashes = {}
            case_by_template = {}
            for case in SceneBenchmarkSuite.load().cases:
                template_id = case.template_id
                case_root = root / "evidence" / case.case_id
                source = case_root / "source.md"
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"real evidence for {case.scene}", encoding="utf-8")
                candidate = case_root / "candidate.pptx"
                candidate.write_bytes(f"candidate-{case.case_id}".encode("utf-8"))
                candidate_hash = _sha256(candidate)
                confirmation_hashes[case.case_id] = candidate_hash
                case_by_template.setdefault(template_id, case_root)
                acceptance = _write_json(case_root / "acceptance.json", {
                    "scene": case.scene,
                    "page_count": 1,
                    "product_accepted": True,
                    "gates": [
                        {"gate_id": gate_id, "passed": True}
                        for gate_id in hard_gate_ids
                        if gate_id != GLOBAL_TEMPLATE_GATE
                    ],
                })
                build = _write_json(case_root / "build.json", {
                    "page_count": 1,
                    "template": {"id": template_id},
                })
                runtime = _write_json(case_root / "runtime.json", {
                    "contract": "repeatable_powerpoint_com_control",
                    "candidate": {"sha256": candidate_hash, "slide_count": 1},
                    "rounds_requested": 3,
                    "rounds_completed": 3,
                    "passed": True,
                })
                review = _write_json(case_root / "review.json", {
                    "reviewed": True,
                    "candidate_sha256": candidate_hash,
                    "pages": [{"page_id": "P001", "passed": True}],
                })
                _write_json(case_root / "object.json", {"passed": True})
                _write_json(case_root / "composition.json", {"passed": True})
                scene_items.append({
                    "case_id": case.case_id,
                    "scene": case.scene,
                    "template_id": template_id,
                    "source_path": str(source.relative_to(root)),
                    "source_sha256": _sha256(source),
                    "candidate_pptx": str(candidate.relative_to(root)),
                    "acceptance_report": str(acceptance.relative_to(root)),
                    "build_report": str(build.relative_to(root)),
                    "runtime_report": str(runtime.relative_to(root)),
                    "visual_review": str(review.relative_to(root)),
                })

            template_items = []
            for template_id in TEMPLATE_IDS:
                case_root = case_by_template[template_id]
                candidate = case_root / "candidate.pptx"
                confirmation_hashes[template_id] = _sha256(candidate)
                specification = _write_json(root / "specs" / f"{template_id}.json", {
                    "template": {"id": template_id},
                    "acceptance": {
                        "semantic_compile_passed": True,
                        "powerpoint_visual_review": "passed",
                    },
                })
                template_items.append({
                    "template_id": template_id,
                    "semantic_spec": str(specification.relative_to(root)),
                    "candidate_pptx": str(candidate.relative_to(root)),
                    "build_report": str((case_root / "build.json").relative_to(root)),
                    "object_qa_report": str((case_root / "object.json").relative_to(root)),
                    "composition_report": str((case_root / "composition.json").relative_to(root)),
                    "runtime_report": str((case_root / "runtime.json").relative_to(root)),
                    "visual_review": str((case_root / "review.json").relative_to(root)),
                })

            verification = []
            for verification_id in (
                "full_test_suite",
                "skill_validation",
                "clean_host_installation",
                "release_documentation",
            ):
                report = _write_json(root / "verification" / f"{verification_id}.json", {"passed": True})
                verification.append({"id": verification_id, "report": str(report.relative_to(root))})
            confirmation = _write_json(root / "confirmation.json", {
                "release": "1.0",
                "confirmed": True,
                "confirmed_by": "release-owner",
                "confirmed_at": "2026-08-06T12:00:00+08:00",
                "artifact_sha256": confirmation_hashes,
            })
            manifest = _write_json(root / "manifest.json", {
                "schema_version": 1,
                "release": "1.0",
                "scene_benchmarks": scene_items,
                "template_regressions": template_items,
                "verification": verification,
                "release_confirmation": str(confirmation.relative_to(root)),
            })

            auditor = ReleaseEvidenceAuditor(root)
            report = auditor.audit(manifest)
            self.assertTrue(report["release_accepted"], report["blockers"])

            stale_review = root / template_items[0]["visual_review"]
            payload = json.loads(stale_review.read_text(encoding="utf-8"))
            payload["candidate_sha256"] = "0" * 64
            _write_json(stale_review, payload)
            stale = auditor.audit(manifest)
            self.assertFalse(stale["release_accepted"])
            self.assertTrue(any("different candidate" in item for item in stale["blockers"]))


if __name__ == "__main__":
    unittest.main()
