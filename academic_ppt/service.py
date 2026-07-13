"""User-facing orchestration for the first guided Skill checkpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .evidence import EvidenceGraph
from .delivery import DeliveryBundle
from .ingest import SourceIngestor
from .profiles import ResearchMethodProfileResolver
from .planning import PageDraft, PagePlan, PagePlanner
from .layout import LayoutCompiler
from .layout import LayoutDecision
from .qa import QualitySummaryBuilder, RenderQualityGate, ScientificSemanticGate, VisualCompositionGate
from .rendering import NativeRenderAdapter
from .scenes import SceneCatalog, ScenePlanContract
from .speaker import SpeakerScriptWriter
from .storylines import StorylinePlanner
from .templates import TemplateCapabilityGraph
from .visuals import VisualTask
from .workflow import ApprovalKind, ProjectWorkflow, WorkflowConfig


@dataclass(frozen=True)
class ContentPageDraft:
    page_id: str
    section: str
    title: str
    question_answered: str
    claim_text: str
    evidence_ids: tuple[str, ...]
    interpretation: str
    next_link: str
    time_seconds: int
    visual_strategy: str
    component_requirements: dict[str, int]
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()


class AcademicPptService:
    """Prepare a confirmable task summary without exposing internal CLI steps."""

    def prepare(self, root: Path | str, sources: Iterable[Path | str], *, scene: str) -> dict:
        source_documents = [SourceIngestor().ingest(path) for path in sources]
        if not source_documents:
            raise ValueError("at least one source is required")
        scene_profile = SceneCatalog.load().resolve(scene)
        workflow = ProjectWorkflow.create(Path(root), WorkflowConfig(scene=scene_profile.name))
        profiles = ResearchMethodProfileResolver().infer(source_documents)
        graph = EvidenceGraph.from_sources(source_documents)
        template = self._select_template(scene)
        summary = {
            "scene": workflow.config.scene,
            "source_count": len(source_documents),
            "sources": [source.to_dict() for source in source_documents],
            "method_profiles": {
                "primary": profiles.primary,
                "secondary": list(profiles.secondary),
                "basis": {key: list(value) for key, value in profiles.basis.items()},
            },
            "evidence": [node.to_dict() for node in graph.all()],
            "conflicts": [conflict.to_dict() for conflict in graph.conflicts()],
            "template": template,
            "scene_contract": {
                "family": scene_profile.family,
                "objective": scene_profile.objective,
                "complete_min": scene_profile.complete_min,
                "complete_max": scene_profile.complete_max,
                "evidence_states": list(scene_profile.evidence_states),
                "required_tags": list(scene_profile.required_tags),
                "argument_chain": list(scene_profile.argument_chain),
                "default_variants": {
                    name: list(sections)
                    for name, sections in scene_profile.default_variants.items()
                },
            },
        }
        summary_path = workflow.root / "audit" / "task_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        workflow.complete_phase("brief", [summary_path])
        return summary

    def confirm_brief(self, root: Path | str, note: str) -> None:
        workflow = ProjectWorkflow.open(root)
        workflow.approve_phase("brief", ApprovalKind.USER, note)
        workflow.begin_phase("evidence")

    def prepare_evidence(self, root: Path | str) -> dict:
        workflow = ProjectWorkflow.open(root)
        if workflow.phase("evidence").status != "draft":
            raise ValueError("evidence preparation requires an active evidence phase")
        summary_path = workflow.root / "audit" / "task_summary.json"
        if not summary_path.is_file():
            raise FileNotFoundError(summary_path)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        sources = [SourceIngestor().ingest(item["path"]) for item in summary["sources"]]
        graph = EvidenceGraph.from_sources(sources)
        options, recommended = StorylinePlanner().propose(workflow.config.scene, graph)
        evidence_path = workflow.root / "audit" / "evidence_summary.json"
        storyline_path = workflow.root / "audit" / "storyline_options.json"
        evidence_payload = {
            "evidence": [node.to_dict() for node in graph.all()],
            "conflicts": [conflict.to_dict() for conflict in graph.conflicts()],
        }
        storyline_payload = {
            "options": [option.to_dict() for option in options],
            "recommended": recommended.to_dict(),
        }
        evidence_path.write_text(json.dumps(evidence_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        storyline_path.write_text(json.dumps(storyline_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        workflow.complete_phase("evidence", [evidence_path, storyline_path])
        return storyline_payload

    def confirm_evidence(self, root: Path | str, note: str) -> None:
        workflow = ProjectWorkflow.open(root)
        workflow.approve_phase("evidence", ApprovalKind.USER, note)
        workflow.begin_phase("content_plan")

    def prepare_content_plan(
        self,
        root: Path | str,
        sections: list[str],
        drafts: list[ContentPageDraft],
        *,
        scene_contract: ScenePlanContract | None = None,
    ) -> PagePlan:
        workflow = ProjectWorkflow.open(root)
        if workflow.phase("content_plan").status != "draft":
            raise ValueError("content planning requires an active content_plan phase")
        graph = self._graph_from_task_summary(workflow.root)
        page_drafts = []
        for draft in drafts:
            claim = graph.add_claim(draft.claim_text, draft.evidence_ids)
            page_drafts.append(PageDraft(
                page_id=draft.page_id,
                section=draft.section,
                title=draft.title,
                question_answered=draft.question_answered,
                claim_id=claim.claim_id,
                interpretation=draft.interpretation,
                next_link=draft.next_link,
                time_seconds=draft.time_seconds,
                visual_strategy=draft.visual_strategy,
                component_requirements=draft.component_requirements,
                coverage_tags=draft.coverage_tags,
                argument_units=draft.argument_units,
            ))
        if scene_contract is None:
            profile = SceneCatalog.load().resolve(workflow.config.scene)
            scene_contract = ScenePlanContract.sample(profile.evidence_states[0])
        plan = PagePlanner().build(
            workflow.config.scene,
            sections,
            page_drafts,
            graph,
            scene_contract=scene_contract,
        )
        outputs = plan.write(workflow.root / "audit")
        workflow.complete_phase("content_plan", outputs)
        return plan

    def confirm_content_plan(self, root: Path | str, note: str) -> None:
        workflow = ProjectWorkflow.open(root)
        workflow.approve_phase("content_plan", ApprovalKind.USER, note)
        workflow.begin_phase("visual_plan")

    def prepare_visual_plan(self, root: Path | str) -> dict:
        workflow = ProjectWorkflow.open(root)
        if workflow.phase("visual_plan").status != "draft":
            raise ValueError("visual planning requires an active visual_plan phase")
        plan = PagePlan.load(workflow.root / "audit" / "page_plan.json")
        summary = json.loads((workflow.root / "audit" / "task_summary.json").read_text(encoding="utf-8"))
        template_graph = TemplateCapabilityGraph.from_presentation(summary["template"]["path"])
        compiler = LayoutCompiler(template_graph)
        decisions = {page.page_id: compiler.compile(page.contract) for page in plan.pages}
        tasks = [
            VisualTask.create(
                task_id=f"VIS_{page.page_id}",
                page_id=page.page_id,
                evidence_ids=page.evidence_ids,
                task_type=page.visual_strategy,
            )
            for page in plan.pages
            if page.visual_strategy != "text_only"
        ]
        layout_path = workflow.root / "audit" / "layout_decisions.json"
        task_path = workflow.root / "audit" / "visual_tasks.json"
        layout_payload = {
            page_id: {
                "render_mode": decision.render_mode,
                "source_slide_index": decision.source_slide_index,
                "fallback_reason": decision.fallback_reason,
                "component_bindings": {kind: list(ids) for kind, ids in decision.component_bindings.items()},
            }
            for page_id, decision in decisions.items()
        }
        task_payload = {
            "visual_tasks": [
                {"task_id": task.task_id, "page_id": task.page_id, "evidence_ids": list(task.evidence_ids),
                 "task_type": task.task_type, "status": task.status}
                for task in tasks
            ]
        }
        layout_path.write_text(json.dumps(layout_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        task_path.write_text(json.dumps(task_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        workflow.complete_phase("visual_plan", [layout_path, task_path])
        return {"layout_decisions": layout_payload, "visual_tasks": task_payload["visual_tasks"]}

    def confirm_visual_plan(self, root: Path | str, note: str) -> None:
        workflow = ProjectWorkflow.open(root)
        workflow.approve_phase("visual_plan", ApprovalKind.USER, note)
        workflow.begin_phase("sample")

    def render_sample(
        self,
        root: Path | str,
        text_content: dict[str, list[str]],
        image_content: dict[str, list[Path | str]],
    ) -> dict:
        workflow = ProjectWorkflow.open(root)
        if workflow.phase("sample").status != "draft":
            raise ValueError("sample rendering requires an active sample phase")
        plan = PagePlan.load(workflow.root / "audit" / "page_plan.json")
        decisions = self._load_layout_decisions(workflow.root / "audit" / "layout_decisions.json")
        if any(decision.render_mode not in {"template_native", "template_adaptive"} for decision in decisions.values()):
            raise ValueError("sample requires native-compatible layout decisions")
        summary = json.loads((workflow.root / "audit" / "task_summary.json").read_text(encoding="utf-8"))
        adapter = NativeRenderAdapter()
        layout_path = adapter.write_layout_plan(
            plan,
            decisions,
            text_content,
            workflow.root / "audit" / "sample_layout_plan.json",
            confirmed=True,
            image_content=image_content,
        )
        pptx_path = adapter.render(layout_path, summary["template"]["path"], workflow.root / "working" / "sample.pptx")
        quality = RenderQualityGate().inspect(pptx_path, workflow.root / "audit" / "sample_qa", require_runtime=False)
        task_payload = json.loads((workflow.root / "audit" / "visual_tasks.json").read_text(encoding="utf-8"))
        accepted_tasks = []
        for item in task_payload["visual_tasks"]:
            task = VisualTask.create(
                task_id=item["task_id"], page_id=item["page_id"], evidence_ids=item["evidence_ids"], task_type=item["task_type"]
            )
            images = image_content.get(task.page_id, [])
            if images:
                task = task.lock_semantics().mark_rendered(images[0]).bind_to_slide().mark_render_inspected().accept()
            accepted_tasks.append({
                "task_id": task.task_id, "page_id": task.page_id, "evidence_ids": list(task.evidence_ids),
                "task_type": task.task_type, "status": task.status, "output_path": task.output_path,
            })
        sample_task_path = workflow.root / "audit" / "sample_visual_tasks.json"
        sample_task_path.write_text(json.dumps({"visual_tasks": accepted_tasks}, ensure_ascii=False, indent=2), encoding="utf-8")
        workflow.complete_phase("sample", [layout_path, pptx_path, quality.report_path, sample_task_path])
        return {"pptx": str(pptx_path), "layout_plan": str(layout_path), "report": str(quality.report_path),
                "visual_tasks": str(sample_task_path)}

    def confirm_sample(self, root: Path | str, note: str) -> None:
        workflow = ProjectWorkflow.open(root)
        workflow.approve_phase("sample", ApprovalKind.USER, note)
        workflow.begin_phase("delivery")

    def publish_delivery(
        self,
        root: Path | str,
        *,
        require_runtime: bool = False,
        runtime: str | None = None,
    ) -> dict:
        workflow = ProjectWorkflow.open(root)
        if workflow.phase("delivery").status != "draft":
            raise ValueError("delivery publishing requires an active delivery phase")
        plan = PagePlan.load(workflow.root / "audit" / "page_plan.json")
        sample_pptx = workflow.root / "working" / "sample.pptx"
        script_path = SpeakerScriptWriter().write(plan, workflow.root / "working" / "speaker_script.docx")
        graph = self._graph_from_task_summary(workflow.root)
        for page in plan.pages:
            claim = graph.add_claim(page.claim_text, page.evidence_ids)
            if claim.claim_id != page.claim_id:
                raise ValueError(f"page claim provenance changed: {page.page_id}")
        semantic = ScientificSemanticGate().inspect(plan, graph)
        visual_payload = json.loads((workflow.root / "audit" / "sample_visual_tasks.json").read_text(encoding="utf-8"))
        visual_tasks = [
            VisualTask(
                task_id=item["task_id"], page_id=item["page_id"], evidence_ids=tuple(item["evidence_ids"]),
                task_type=item["task_type"], status=item["status"], output_path=item.get("output_path"),
            )
            for item in visual_payload["visual_tasks"]
        ]
        visual = VisualCompositionGate().inspect(visual_tasks, plan)
        selected_runtime = runtime or workflow.config.authoritative_runtime
        render = RenderQualityGate().inspect(
            sample_pptx,
            workflow.root / "audit" / "delivery_qa",
            require_runtime=require_runtime,
            runtime=selected_runtime,
        )
        quality_summary = QualitySummaryBuilder().build(render, semantic, visual)
        if not workflow.is_formally_confirmed():
            quality_summary["formal_accepted"] = False
            quality_summary["confirmation_status"] = "user_confirmation_incomplete"
        else:
            quality_summary["confirmation_status"] = "confirmed"
        quality_summary["status"] = (
            "formally_accepted"
            if quality_summary["formal_accepted"]
            else "draft_requires_authoritative_runtime" if not require_runtime
            else "formal_acceptance_failed"
        )
        bundle = DeliveryBundle.create(workflow.root)
        result = bundle.publish(
            sample_pptx,
            script_path,
            audit_artifacts=[workflow.root / "audit" / "page_plan.json", render.report_path],
            quality_summary=quality_summary,
        )
        workflow.complete_phase("delivery", [*result.visible_files, *result.audit_files])
        return {
            "visible_files": [str(path) for path in result.visible_files],
            "audit_files": [str(path) for path in result.audit_files],
            "formal_accepted": quality_summary["formal_accepted"],
            "quality": quality_summary,
        }

    @staticmethod
    def _select_template(scene: str) -> dict:
        skill_root = Path(__file__).resolve().parents[1]
        canonical_scene = SceneCatalog.load().resolve(scene).name
        catalog = json.loads((skill_root / "references" / "template-catalog.json").read_text(encoding="utf-8"))
        template = next(
            (item for item in catalog["templates"] if canonical_scene in item.get("recommended_scenes", [])),
            None,
        )
        if template is None:
            raise ValueError(f"no bundled template recommendation for scene: {canonical_scene}")
        return {
            "id": template["id"],
            "short_name": template["short_name"],
            "path": str((skill_root / template["path"]).resolve()),
        }

    @staticmethod
    def _graph_from_task_summary(root: Path) -> EvidenceGraph:
        summary_path = root / "audit" / "task_summary.json"
        if not summary_path.is_file():
            raise FileNotFoundError(summary_path)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        sources = [SourceIngestor().ingest(item["path"]) for item in summary["sources"]]
        return EvidenceGraph.from_sources(sources)

    @staticmethod
    def _load_layout_decisions(path: Path) -> dict[str, LayoutDecision]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            page_id: LayoutDecision(
                page_id=page_id,
                render_mode=item["render_mode"],
                source_slide_index=item["source_slide_index"],
                fallback_reason=item.get("fallback_reason"),
                component_bindings={kind: tuple(shape_ids) for kind, shape_ids in item["component_bindings"].items()},
            )
            for page_id, item in payload.items()
        }
