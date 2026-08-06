"""Audit the complete 1.0 release surface against exact artifact hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .benchmarks import SceneBenchmarkSuite
from .scenes import SceneCatalog


TEMPLATE_IDS = tuple(f"T{index:02d}" for index in range(1, 9))
GLOBAL_TEMPLATE_GATE = "all_bundled_templates_accepted"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReleaseEvidenceAuditor:
    """Reject incomplete, stale, synthetic, or cross-candidate release evidence."""

    def __init__(self, skill_root: Path | str):
        self.root = Path(skill_root).resolve()

    def audit(self, manifest_path: Path | str) -> dict[str, Any]:
        manifest = self._load_json(self._resolve(manifest_path))
        if manifest.get("schema_version") != 1:
            raise ValueError(f"unsupported release evidence schema: {manifest.get('schema_version')}")

        coverage = self._coverage(manifest)
        scenes = [self._audit_scene(item) for item in manifest.get("scene_benchmarks", ())]
        templates = [self._audit_template(item) for item in manifest.get("template_regressions", ())]
        verification = [self._audit_verification(item) for item in manifest.get("verification", ())]
        confirmation = self._audit_confirmation(
            manifest.get("release_confirmation"),
            scenes,
            templates,
        )
        gates = [
            self._gate("supported_surface_coverage", coverage["passed"], coverage["blockers"]),
            self._gate("ten_real_scene_benchmarks", bool(scenes) and all(item["passed"] for item in scenes), self._item_blockers(scenes)),
            self._gate("eight_template_regressions", bool(templates) and all(item["passed"] for item in templates), self._item_blockers(templates)),
            self._gate("release_verification", bool(verification) and all(item["passed"] for item in verification), self._item_blockers(verification)),
            self._gate("user_release_confirmation", confirmation["passed"], confirmation["blockers"]),
        ]
        blockers = [
            blocker
            for gate in gates
            for blocker in gate["blockers"]
        ]
        return {
            "schema_version": 1,
            "release": str(manifest.get("release", "")),
            "release_accepted": all(gate["passed"] for gate in gates),
            "gates": gates,
            "coverage": coverage,
            "scene_benchmarks": scenes,
            "template_regressions": templates,
            "verification": verification,
            "release_confirmation": confirmation,
            "blockers": blockers,
        }

    def _coverage(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        expected_cases = {
            case.case_id: {"scene": case.scene, "template_id": case.template_id}
            for case in SceneBenchmarkSuite.load().cases
        }
        scene_items = manifest.get("scene_benchmarks", ())
        actual_cases = {
            str(item.get("case_id")): {
                "scene": str(item.get("scene")),
                "template_id": str(item.get("template_id")),
            }
            for item in scene_items
        }
        expected_scenes = set(SceneCatalog.load().profiles)
        template_items = manifest.get("template_regressions", ())
        actual_templates = [str(item.get("template_id")) for item in template_items]
        blockers = []
        if actual_cases != expected_cases:
            blockers.append("scene benchmark manifest must cover the canonical ten cases exactly once")
        if {item["scene"] for item in actual_cases.values()} != expected_scenes:
            blockers.append("scene benchmark manifest does not match the supported scene catalog")
        if len(actual_cases) != len(scene_items):
            blockers.append("scene benchmark case IDs must be unique")
        if tuple(sorted(actual_templates)) != TEMPLATE_IDS or len(set(actual_templates)) != 8:
            blockers.append("template regression manifest must cover T01-T08 exactly once")
        return {"passed": not blockers, "blockers": blockers}

    def _audit_scene(self, item: Mapping[str, Any]) -> dict[str, Any]:
        case_id = str(item.get("case_id", ""))
        scene = str(item.get("scene", ""))
        blockers = []
        source = self._required_file(item.get("source_path"), f"{case_id}: source", blockers)
        if source:
            expected = str(item.get("source_sha256", ""))
            actual = sha256(source)
            if not expected or actual != expected:
                blockers.append(f"{case_id}: source SHA-256 is missing or stale")

        candidate = self._required_file(item.get("candidate_pptx"), f"{case_id}: candidate PPTX", blockers)
        candidate_hash = sha256(candidate) if candidate else None
        acceptance = self._required_json(item.get("acceptance_report"), f"{case_id}: acceptance report", blockers)
        page_count = int(acceptance.get("page_count", 0)) if acceptance else 0
        if acceptance:
            if acceptance.get("scene") != scene:
                blockers.append(f"{case_id}: acceptance scene does not match the manifest")
            self._check_deck_acceptance(case_id, acceptance, blockers)

        build = self._required_json(item.get("build_report"), f"{case_id}: build report", blockers)
        if build and build.get("template", {}).get("id") != item.get("template_id"):
            blockers.append(f"{case_id}: build selected a different template")
        self._check_runtime(item.get("runtime_report"), case_id, candidate_hash, page_count, blockers)
        self._check_visual_review(item.get("visual_review"), case_id, candidate_hash, page_count, blockers)
        return {
            "case_id": case_id,
            "scene": scene,
            "template_id": item.get("template_id"),
            "candidate_sha256": candidate_hash,
            "passed": not blockers,
            "blockers": blockers,
        }

    def _audit_template(self, item: Mapping[str, Any]) -> dict[str, Any]:
        template_id = str(item.get("template_id", ""))
        blockers = []
        specification = self._required_json(
            item.get("semantic_spec"),
            f"{template_id}: semantic specification",
            blockers,
        )
        if specification:
            acceptance = specification.get("acceptance", {})
            if specification.get("template", {}).get("id") != template_id:
                blockers.append(f"{template_id}: semantic specification ID mismatch")
            if acceptance.get("semantic_compile_passed") is not True:
                blockers.append(f"{template_id}: semantic compilation is not accepted")
            if acceptance.get("powerpoint_visual_review") != "passed":
                blockers.append(f"{template_id}: standard template PowerPoint review is not passed")

        candidate = self._required_file(item.get("candidate_pptx"), f"{template_id}: candidate PPTX", blockers)
        candidate_hash = sha256(candidate) if candidate else None
        build = self._required_json(item.get("build_report"), f"{template_id}: build report", blockers)
        page_count = int(build.get("page_count", 0)) if build else 0
        if build and build.get("template", {}).get("id") != template_id:
            blockers.append(f"{template_id}: candidate uses a different template")
        object_qa = self._required_json(item.get("object_qa_report"), f"{template_id}: object QA", blockers)
        if object_qa and object_qa.get("passed") is not True:
            blockers.append(f"{template_id}: object QA did not pass")
        composition = self._required_json(item.get("composition_report"), f"{template_id}: composition QA", blockers)
        if composition and composition.get("passed") is not True:
            blockers.append(f"{template_id}: composition QA did not pass")
        self._check_runtime(item.get("runtime_report"), template_id, candidate_hash, page_count, blockers)
        self._check_visual_review(item.get("visual_review"), template_id, candidate_hash, page_count, blockers)
        return {
            "template_id": template_id,
            "candidate_sha256": candidate_hash,
            "passed": not blockers,
            "blockers": blockers,
        }

    def _audit_verification(self, item: Mapping[str, Any]) -> dict[str, Any]:
        verification_id = str(item.get("id", ""))
        blockers = []
        report = self._required_json(item.get("report"), f"verification {verification_id}", blockers)
        if report and report.get("passed") is not True:
            blockers.append(f"verification {verification_id}: report is not passed")
        return {"id": verification_id, "passed": not blockers, "blockers": blockers}

    def _audit_confirmation(
        self,
        path_value: Any,
        scenes: list[dict[str, Any]],
        templates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        blockers = []
        confirmation = self._required_json(path_value, "release confirmation", blockers)
        if confirmation:
            if confirmation.get("release") != "1.0" or confirmation.get("confirmed") is not True:
                blockers.append("release confirmation is not an explicit 1.0 approval")
            if not str(confirmation.get("confirmed_by", "")).strip() or not str(confirmation.get("confirmed_at", "")).strip():
                blockers.append("release confirmation requires confirmed_by and confirmed_at")
            hashes = confirmation.get("artifact_sha256", {})
            expected = {
                **{item["case_id"]: item["candidate_sha256"] for item in scenes},
                **{item["template_id"]: item["candidate_sha256"] for item in templates},
            }
            if any(not value for value in expected.values()) or hashes != expected:
                blockers.append("release confirmation is missing exact scene or template candidate hashes")
        return {"passed": not blockers, "blockers": blockers}

    def _check_deck_acceptance(self, label: str, payload: Mapping[str, Any], blockers: list[str]) -> None:
        matrix = self._load_json(self.root / "references" / "product-acceptance-matrix.json")
        expected = {
            str(item["id"])
            for item in matrix.get("hard_gates", ())
            if item.get("id") != GLOBAL_TEMPLATE_GATE
        }
        gates = {str(item.get("gate_id")): item.get("passed") for item in payload.get("gates", ())}
        if expected - set(gates):
            blockers.append(f"{label}: acceptance report is missing hard gates")
        if any(gates.get(gate_id) is not True for gate_id in expected):
            blockers.append(f"{label}: one or more complete-deck hard gates did not pass")
        if payload.get("product_accepted") is not True:
            blockers.append(f"{label}: complete deck is not product accepted")

    def _check_runtime(
        self,
        path_value: Any,
        label: str,
        candidate_hash: str | None,
        page_count: int,
        blockers: list[str],
    ) -> None:
        report = self._required_json(path_value, f"{label}: PowerPoint runtime report", blockers)
        if not report:
            return
        candidate = report.get("candidate", {})
        if report.get("contract") != "repeatable_powerpoint_com_control" or report.get("passed") is not True:
            blockers.append(f"{label}: PowerPoint runtime control did not pass")
        if candidate.get("sha256") != candidate_hash or int(candidate.get("slide_count", 0)) != page_count:
            blockers.append(f"{label}: PowerPoint report targets a different candidate")
        if int(report.get("rounds_completed", 0)) != int(report.get("rounds_requested", 0)) or int(report.get("rounds_completed", 0)) < 3:
            blockers.append(f"{label}: PowerPoint runtime requires three complete rounds")

    def _check_visual_review(
        self,
        path_value: Any,
        label: str,
        candidate_hash: str | None,
        page_count: int,
        blockers: list[str],
    ) -> None:
        review = self._required_json(path_value, f"{label}: visual review", blockers)
        if not review:
            return
        pages = review.get("pages", ())
        if review.get("reviewed") is not True or review.get("candidate_sha256") != candidate_hash:
            blockers.append(f"{label}: visual review is absent or bound to a different candidate")
        if len(pages) != page_count or any(item.get("passed") is not True for item in pages):
            blockers.append(f"{label}: visual review must pass every final slide")

    def _required_file(self, value: Any, label: str, blockers: list[str]) -> Path | None:
        if not value:
            blockers.append(f"{label} path is missing")
            return None
        path = self._resolve(value)
        if not path.is_file() or path.stat().st_size == 0:
            blockers.append(f"{label} is missing or empty: {path}")
            return None
        return path

    def _required_json(self, value: Any, label: str, blockers: list[str]) -> dict[str, Any]:
        path = self._required_file(value, label, blockers)
        if path is None:
            return {}
        try:
            return self._load_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            blockers.append(f"{label} is not valid JSON: {exc}")
            return {}

    def _resolve(self, value: Path | str) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (self.root / path).resolve()

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"expected a JSON object: {path}")
        return payload

    @staticmethod
    def _item_blockers(items: list[dict[str, Any]]) -> list[str]:
        return [blocker for item in items for blocker in item["blockers"]]

    @staticmethod
    def _gate(gate_id: str, passed: bool, blockers: list[str]) -> dict[str, Any]:
        return {"gate_id": gate_id, "passed": bool(passed), "blockers": list(blockers)}
