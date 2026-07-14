"""Adapt PPTX validation into explicit reusable-Skill acceptance status."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .evidence import EvidenceGraph
from .planning import PagePlan
from .visuals import VisualTask


@dataclass(frozen=True)
class RenderQualityResult:
    report_path: Path
    structural_passed: bool
    real_render_passed: bool
    formal_accepted: bool
    runtime_status: str = "not_requested"


class RenderQualityGate:
    def inspect(
        self,
        pptx_path: Path | str,
        audit_dir: Path | str,
        *,
        require_runtime: bool,
        runtime: str = "powerpoint",
        layout_plan: Path | str | None = None,
        preview_dir: Path | str | None = None,
    ) -> RenderQualityResult:
        if runtime not in {"powerpoint", "wps", "portable"}:
            raise ValueError(f"unsupported runtime: {runtime}")
        skill_root = Path(__file__).resolve().parents[1]
        audit = Path(audit_dir)
        audit.mkdir(parents=True, exist_ok=True)
        report_path = audit / "render_report.json"
        resolved_preview = Path(preview_dir) if preview_dir else audit / "rendered-preview"
        render_engine = "auto" if runtime == "portable" else runtime
        command = [
            sys.executable, str(skill_root / "scripts" / "validate_pptx.py"), str(Path(pptx_path).resolve()),
            "--output", str(report_path), "--render-check", "required" if require_runtime else "off",
            "--render-engine", render_engine, "--preview-dir", str(resolved_preview),
        ]
        if layout_plan is not None:
            command.extend(("--layout-plan", str(Path(layout_plan).resolve())))
        subprocess.run(
            command, cwd=skill_root, check=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        real = next((check for check in report["checks"] if check["name"] == "Real application render succeeds"), None)
        real_render_passed = bool(real and real["passed"])
        structural_passed = report["failed_error"] == 0 and (not require_runtime or real_render_passed)
        runtime_status = self._runtime_status(require_runtime, real)
        formal_accepted = (
            require_runtime
            and runtime == "powerpoint"
            and structural_passed
            and real_render_passed
        )
        return RenderQualityResult(
            report_path,
            structural_passed,
            real_render_passed,
            formal_accepted,
            runtime_status,
        )

    @staticmethod
    def _runtime_status(require_runtime: bool, real_check: dict | None) -> str:
        if not require_runtime:
            return "not_requested"
        if real_check and real_check.get("passed"):
            return "passed"
        detail = str(real_check.get("detail", "")).lower() if real_check else ""
        unavailable_markers = ("not installed", "not registered", "not found", "no preview engine")
        return "unavailable" if any(marker in detail for marker in unavailable_markers) else "failed"


@dataclass(frozen=True)
class SemanticQualityResult:
    passed: bool
    errors: tuple[str, ...]
    observations: tuple[str, ...] = ()


class ScientificSemanticGate:
    """Reject unsupported page contracts and unresolved blocking evidence."""

    def inspect(self, plan: PagePlan, graph: EvidenceGraph) -> SemanticQualityResult:
        errors = []
        observations = []
        blocking = [conflict.conflict_id for conflict in graph.conflicts() if conflict.severity == "blocking"]
        if blocking:
            errors.append(f"blocking evidence conflicts: {', '.join(blocking)}")
        for page in plan.pages:
            expected_ids = tuple(node.evidence_id for node in graph.trace_claim(page.claim_id))
            if page.evidence_ids != expected_ids:
                errors.append(f"{page.page_id}: page evidence does not match claim provenance")
            if len(page.evidence_ids) == 1:
                observations.append(f"{page.page_id}: only one evidence unit supports the page claim")
        return SemanticQualityResult(
            passed=not errors,
            errors=tuple(errors),
            observations=tuple(observations),
        )


@dataclass(frozen=True)
class VisualQualityResult:
    passed: bool
    errors: tuple[str, ...]
    observations: tuple[str, ...] = ()


class VisualCompositionGate:
    """Require every planned scientific visual to complete its acceptance state."""

    def inspect(self, tasks: list[VisualTask], plan: PagePlan | None = None) -> VisualQualityResult:
        errors = []
        page_evidence = {
            page.page_id: set(page.evidence_ids)
            for page in plan.pages
        } if plan else None
        tasks_by_page: dict[str, int] = {}
        for task in tasks:
            tasks_by_page[task.page_id] = tasks_by_page.get(task.page_id, 0) + 1
            if task.status != "accepted":
                errors.append(f"{task.task_id}: visual task is {task.status}, not accepted")
            if page_evidence is None:
                continue
            if task.page_id not in page_evidence:
                errors.append(f"{task.task_id}: visual task page is not in the page plan: {task.page_id}")
                continue
            unbound = sorted(set(task.evidence_ids) - page_evidence[task.page_id])
            if unbound:
                errors.append(
                    f"{task.task_id}: visual evidence is not bound to the page contract: {', '.join(unbound)}"
                )
        observations = tuple(
            f"{page_id}: {count} visual tasks may compromise composition readability"
            for page_id, count in tasks_by_page.items()
            if count > 2
        )
        return VisualQualityResult(passed=not errors, errors=tuple(errors), observations=observations)


class QualitySummaryBuilder:
    """Combine hard QA gates without allowing one result to mask another."""

    def build(
        self,
        render: RenderQualityResult,
        semantic: SemanticQualityResult,
        visual: VisualQualityResult,
    ) -> dict:
        formal_accepted = render.formal_accepted and semantic.passed and visual.passed
        return {
            "structural": render.structural_passed,
            "semantic": semantic.passed,
            "visual": visual.passed,
            "real_render": render.real_render_passed,
            "formal_accepted": formal_accepted,
            "runtime_status": render.runtime_status,
            "semantic_errors": list(semantic.errors),
            "semantic_observations": list(semantic.observations),
            "visual_errors": list(visual.errors),
            "visual_observations": list(visual.observations),
            "render_report": str(render.report_path),
        }
