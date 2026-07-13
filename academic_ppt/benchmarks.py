"""Run the fixed ten-scene suite through the shared Skill workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .profiles import PROFILE_KEYWORDS
from .scenes import SceneCatalog, ScenePlanContract
from .service import AcademicPptService, ContentPageDraft
from .workflow import ProjectWorkflow


@dataclass(frozen=True)
class SceneBenchmarkCase:
    case_id: str
    scene: str
    method_profile: str
    evidence_state: str
    section_variant: str
    target_pages: int
    duration_minutes: float
    template_id: str
    source_claims: tuple[str, ...]
    required_tags: tuple[str, ...]
    argument_units: tuple[str, ...]


class SceneBenchmarkSuite:
    """Materialize benchmark data, then delegate every production step to the service."""

    def __init__(self, cases: Iterable[SceneBenchmarkCase]):
        self.cases = tuple(cases)
        self._validate_manifest()

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SceneBenchmarkSuite":
        source = Path(path) if path else Path(__file__).resolve().parents[1] / "references" / "scene-benchmarks.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError(f"unsupported scene benchmark schema: {payload.get('schema_version')}")
        return cls(SceneBenchmarkCase(
            case_id=item["case_id"],
            scene=item["scene"],
            method_profile=item["method_profile"],
            evidence_state=item["evidence_state"],
            section_variant=item["section_variant"],
            target_pages=int(item["target_pages"]),
            duration_minutes=float(item["duration_minutes"]),
            template_id=item["template_id"],
            source_claims=tuple(item["source_claims"]),
            required_tags=tuple(item["required_tags"]),
            argument_units=tuple(item["argument_units"]),
        ) for item in payload["cases"])

    def case(self, case_id: str) -> SceneBenchmarkCase:
        try:
            return next(case for case in self.cases if case.case_id == case_id)
        except StopIteration as exc:
            raise ValueError(f"unknown scene benchmark: {case_id}") from exc

    def run_case(
        self,
        case: SceneBenchmarkCase,
        project_root: Path | str,
        *,
        require_runtime: bool = False,
        runtime: str = "powerpoint",
    ) -> dict:
        root = Path(project_root).resolve()
        if (root / ProjectWorkflow.state_relative_path).exists():
            raise FileExistsError(f"benchmark project already exists: {root}")
        root.mkdir(parents=True, exist_ok=True)
        source_path = root / "benchmark_source.md"
        source_path.write_text("\n".join(case.source_claims) + "\n", encoding="utf-8")

        service = AcademicPptService()
        summary = service.prepare(root, [source_path], scene=case.scene)
        if summary["method_profiles"]["primary"] != case.method_profile:
            raise ValueError(
                f"{case.case_id} expected method profile {case.method_profile}; "
                f"got {summary['method_profiles']['primary']}"
            )
        if summary["template"]["id"] != case.template_id:
            raise ValueError(
                f"{case.case_id} expected template {case.template_id}; got {summary['template']['id']}"
            )
        service.confirm_brief(root, "Benchmark task summary confirmed")
        service.prepare_evidence(root)
        service.confirm_evidence(root, "Benchmark evidence and storyline confirmed")

        profile = SceneCatalog.load().resolve(case.scene)
        sections = profile.default_variants[case.section_variant]
        evidence_payload = json.loads((root / "audit" / "evidence_summary.json").read_text(encoding="utf-8"))
        evidence = evidence_payload["evidence"]
        if not evidence:
            raise ValueError(f"{case.case_id} produced no evidence")
        durations = self._page_durations(case.target_pages, case.duration_minutes)
        drafts = []
        for index in range(case.target_pages):
            evidence_item = evidence[index % len(evidence)]
            drafts.append(ContentPageDraft(
                page_id=f"P{index + 1:03d}",
                section=sections[min(index * len(sections) // case.target_pages, len(sections) - 1)],
                title=case.source_claims[index % len(case.source_claims)],
                question_answered=f"本页证据如何支撑{case.scene}的核心判断？",
                claim_text=evidence_item["text"],
                evidence_ids=(evidence_item["evidence_id"],),
                interpretation="该证据支撑当前判断，其适用范围以基准素材记录为边界。",
                next_link="下一页继续完成场景论证链。",
                time_seconds=durations[index],
                visual_strategy="text_only",
                component_requirements={"text": 1},
                coverage_tags=self._members_for_page(case.required_tags, index, case.target_pages),
                argument_units=self._members_for_page(case.argument_units, index, case.target_pages),
            ))
        contract = ScenePlanContract(
            deck_scope="complete",
            evidence_state=case.evidence_state,
            section_variant=case.section_variant,
            duration_minutes=case.duration_minutes,
        )
        plan = service.prepare_content_plan(root, list(sections), drafts, scene_contract=contract)
        service.confirm_content_plan(root, "Benchmark complete page plan confirmed")
        visual_plan = service.prepare_visual_plan(root)
        non_native = [
            page_id
            for page_id, decision in visual_plan["layout_decisions"].items()
            if decision["render_mode"] not in {"template_native", "template_adaptive"}
        ]
        if non_native:
            raise ValueError(f"{case.case_id} has non-native benchmark pages: {non_native}")
        service.confirm_visual_plan(root, "Benchmark visual plan confirmed")
        text_content = {page.page_id: [page.title] for page in plan.pages}
        service.render_sample(root, text_content, {})
        service.confirm_sample(root, "Benchmark complete render confirmed")
        delivery = service.publish_delivery(root, require_runtime=require_runtime, runtime=runtime)

        quality = delivery["quality"]
        passed = bool(
            quality["structural"]
            and quality["semantic"]
            and quality["visual"]
            and (quality["formal_accepted"] if require_runtime else True)
        )
        result = {
            "case_id": case.case_id,
            "scene": plan.scene,
            "method_profile": summary["method_profiles"]["primary"],
            "evidence_state": plan.evidence_state,
            "page_count": len(plan.pages),
            "template_id": summary["template"]["id"],
            "require_runtime": require_runtime,
            "runtime": runtime if require_runtime else None,
            "formal_accepted": delivery["formal_accepted"],
            "passed": passed,
            "quality": quality,
            "visible_files": delivery["visible_files"],
            "audit_files": delivery["audit_files"],
        }
        result_path = root / "audit" / "benchmark_result.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def run(
        self,
        output_dir: Path | str,
        *,
        case_ids: Iterable[str] | None = None,
        require_runtime: bool = False,
        runtime: str = "powerpoint",
        keep_going: bool = True,
    ) -> dict:
        output = Path(output_dir).resolve()
        output.mkdir(parents=True, exist_ok=True)
        selected = [self.case(case_id) for case_id in case_ids] if case_ids else list(self.cases)
        results = []
        for case in selected:
            try:
                results.append(self.run_case(
                    case,
                    output / case.case_id,
                    require_runtime=require_runtime,
                    runtime=runtime,
                ))
            except Exception as exc:
                results.append({
                    "case_id": case.case_id,
                    "scene": case.scene,
                    "passed": False,
                    "formal_accepted": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
                if not keep_going:
                    break
        report = {
            "schema_version": 1,
            "require_runtime": require_runtime,
            "runtime": runtime if require_runtime else None,
            "passed": bool(results) and all(item["passed"] for item in results),
            "cases": results,
        }
        (output / "suite_result.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return report

    def _validate_manifest(self) -> None:
        catalog = SceneCatalog.load()
        case_ids = [case.case_id for case in self.cases]
        scenes = [case.scene for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("scene benchmark case IDs must be unique")
        if len(scenes) != len(set(scenes)):
            raise ValueError("each scene must have exactly one core benchmark")
        if set(scenes) != set(catalog.profiles):
            missing = sorted(set(catalog.profiles) - set(scenes))
            extra = sorted(set(scenes) - set(catalog.profiles))
            raise ValueError(f"scene benchmark coverage mismatch; missing={missing}, extra={extra}")
        for case in self.cases:
            profile = catalog.resolve(case.scene)
            if case.method_profile not in PROFILE_KEYWORDS:
                raise ValueError(f"{case.case_id} has unsupported method profile: {case.method_profile}")
            if case.evidence_state not in profile.evidence_states:
                raise ValueError(f"{case.case_id} has invalid evidence state: {case.evidence_state}")
            if not profile.complete_min <= case.target_pages <= profile.complete_max:
                raise ValueError(f"{case.case_id} target_pages is outside the complete-deck budget")
            if case.section_variant not in profile.default_variants:
                raise ValueError(f"{case.case_id} has unknown section variant: {case.section_variant}")
            if case.required_tags != profile.required_tags:
                raise ValueError(f"{case.case_id} required tags drifted from the scene contract")
            if case.argument_units != profile.argument_chain:
                raise ValueError(f"{case.case_id} argument units drifted from the scene contract")
            if not case.source_claims:
                raise ValueError(f"{case.case_id} requires representative source claims")
            if case.duration_minutes <= 0:
                raise ValueError(f"{case.case_id} requires a positive duration")

    @staticmethod
    def _members_for_page(values: tuple[str, ...], page_index: int, page_count: int) -> tuple[str, ...]:
        return tuple(value for index, value in enumerate(values) if index % page_count == page_index)

    @staticmethod
    def _page_durations(page_count: int, duration_minutes: float) -> list[int]:
        total_seconds = int(duration_minutes * 60)
        base, remainder = divmod(total_seconds, page_count)
        return [base + (1 if index < remainder else 0) for index in range(page_count)]
