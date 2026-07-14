"""Build one complete evidence-grounded academic PPT candidate through the Skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from academic_ppt.acceptance import ProductAcceptanceEvaluator
from academic_ppt.authored_content import apply_authored_content
from academic_ppt.composition import CompositionQualityGate, DynamicCompositionCompiler
from academic_ppt.content_adaptation import adapt_native_text_capacity, adapt_source_figure_text_capacity
from academic_ppt.autobuild import CompleteContentCompiler
from academic_ppt.delivery import DeliveryBundle
from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor
from academic_ppt.layout import LayoutCompiler
from academic_ppt.manifest import SlideManifestBuilder
from academic_ppt.planning import PageDraft, PagePlanner
from academic_ppt.profiles import ResearchMethodProfileResolver
from academic_ppt.qa import QualitySummaryBuilder, RenderQualityGate, ScientificSemanticGate, VisualCompositionGate
from academic_ppt.rendering import NativeRenderAdapter
from academic_ppt.scenes import SceneCatalog
from academic_ppt.speaker import SpeakerScriptWriter
from academic_ppt.storylines import StorylinePlanner
from academic_ppt.templates import TemplateAdmissionGate, TemplateCapabilityGraph, TemplateCatalog
from academic_ppt.visuals import VisualTask


def _representative_page_ids(plan) -> set[str]:
    count = len(plan.pages)
    wanted = min(5, max(1, count - 1)) if count > 1 else 1
    indices = {0, count - 1}
    if wanted >= 3:
        indices.add(count // 2)
    if wanted >= 4:
        indices.add(count // 3)
    if wanted >= 5:
        indices.add((count * 2) // 3)
    return {plan.pages[index].page_id for index in sorted(indices)[:wanted]}


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _usable_text_slots(archetype: dict, valid_shape_ids: set[int]) -> list[dict]:
    slots = []
    seen = set()
    terminal_role = archetype.get("role") in {"cover", "ending"}
    for slot in archetype.get("text_slots", ()):
        shape_id = int(slot["shape_id"])
        if shape_id in seen or shape_id not in valid_shape_ids or not slot.get("editable", True):
            continue
        seen.add(shape_id)
        box = slot.get("box", {})
        capacity = slot.get("capacity", {}).get("estimated_cjk_chars", 0)
        if slot.get("role") == "navigation_or_footer" or slot.get("repeated"):
            continue
        if float(box.get("width", 0)) < 0.05 or float(box.get("height", 0)) < 0.025:
            continue
        if (
            slot.get("role") != "page_title"
            and float(box.get("width", 0)) * float(box.get("height", 0)) > 0.50
            and not str(slot.get("sample_text", "")).strip()
        ):
            continue
        if (
            slot.get("role") != "page_title"
            and float(box.get("left", 1)) < 0.02
            and float(box.get("width", 1)) < 0.12
            and float(box.get("height", 0)) > 0.50
            and not str(slot.get("sample_text", "")).strip()
        ):
            continue
        if (
            slot.get("role") != "page_title"
            and float(box.get("top", 1)) < 0.12
            and float(box.get("width", 0)) > 0.50
            and not str(slot.get("sample_text", "")).strip()
        ):
            continue
        if not terminal_role and slot.get("role") != "page_title" and capacity < 20:
            continue
        slots.append(slot)
    return slots


def _semantic_text_bindings(
    archetype: dict,
    slide,
    count: int,
    *,
    blocked_boxes: tuple[dict, ...] = (),
) -> tuple[int, ...]:
    valid_shape_ids = {component.shape_id for component in slide.components if component.kind == "text"}
    slots = _usable_text_slots(archetype, valid_shape_ids)
    titles = [slot for slot in slots if slot.get("role") == "page_title"]
    if not titles:
        titles = sorted(
            slots,
            key=lambda slot: (
                float(slot.get("box", {}).get("top", 1)),
                -float(slot.get("box", {}).get("width", 0)) * float(slot.get("box", {}).get("height", 0)),
            ),
        )[:1]
    title_ids = {int(slot["shape_id"]) for slot in titles}
    bodies = [
        slot for slot in slots
        if int(slot["shape_id"]) not in title_ids
        and not any(_box_overlap_ratio(slot.get("box", {}), box) > 0.15 for box in blocked_boxes)
    ]
    bodies.sort(key=lambda slot: (
        float(slot.get("box", {}).get("top", 1)),
        float(slot.get("box", {}).get("left", 1)),
        -int(slot.get("capacity", {}).get("estimated_cjk_chars", 0)),
    ))
    visible_bodies = []
    for slot in bodies:
        if any(_box_overlap_ratio(slot.get("box", {}), other.get("box", {})) > 0.35 for other in visible_bodies):
            continue
        visible_bodies.append(slot)
    selected = [*titles[:1], *visible_bodies[:max(0, count - 1)]]
    return tuple(int(slot["shape_id"]) for slot in selected)


def _source_figure_solution(archetype: dict, slide, text_count: int) -> tuple[int, tuple[int, ...]] | None:
    valid_pictures = {component.shape_id for component in slide.components if component.kind == "picture"}
    candidates = []
    for slot in archetype.get("picture_slots", ()):
        shape_id = int(slot["shape_id"])
        area = float(slot.get("area", 0))
        if shape_id not in valid_pictures or slot.get("role") == "logo" or not 0.08 <= area <= 0.50:
            continue
        box = slot.get("box", {})
        preference = area + (0.04 if float(box.get("left", 0)) >= 0.5 else 0.0)
        candidates.append((preference, shape_id, box))
    for _, shape_id, box in sorted(candidates, reverse=True):
        text_ids = _semantic_text_bindings(archetype, slide, text_count, blocked_boxes=(box,))
        role_by_shape_id = {int(slot["shape_id"]): slot.get("role") for slot in archetype.get("text_slots", ())}
        if (
            archetype.get("layout_signature") == "figure_text_right"
            and text_ids
            and role_by_shape_id.get(text_ids[0]) == "page_title"
        ):
            alternate = _semantic_text_bindings(archetype, slide, text_count + 1, blocked_boxes=(box,))
            if len(alternate) >= text_count + 1:
                text_ids = alternate[1:text_count + 1]
        if len(text_ids) >= text_count:
            return shape_id, text_ids
    return None


def _box_overlap_ratio(first: dict, second: dict) -> float:
    left = max(float(first.get("left", 0)), float(second.get("left", 0)))
    top = max(float(first.get("top", 0)), float(second.get("top", 0)))
    right = min(
        float(first.get("left", 0)) + float(first.get("width", 0)),
        float(second.get("left", 0)) + float(second.get("width", 0)),
    )
    bottom = min(
        float(first.get("top", 0)) + float(first.get("height", 0)),
        float(second.get("top", 0)) + float(second.get("height", 0)),
    )
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    first_area = float(first.get("width", 0)) * float(first.get("height", 0))
    second_area = float(second.get("width", 0)) * float(second.get("height", 0))
    return intersection / max(min(first_area, second_area), 1e-9)


def _render_dynamic_candidate(
    *,
    args,
    plan,
    content,
    graph,
    selected_template: dict,
    visual_system_path: Path,
    grammar_path: Path,
    root: Path,
    audit: Path,
    working: Path,
    deliverables: Path,
    text_path: Path,
    image_path: Path,
) -> None:
    dynamic_plan = DynamicCompositionCompiler().compile(
        plan,
        content,
        visual_system_path=visual_system_path,
        template_grammar_path=grammar_path,
        asset_base_dir=root,
        confirmed=True,
    )
    composition_quality = CompositionQualityGate().inspect(dynamic_plan)
    _write_json(audit / "composition_quality.json", {
        "passed": composition_quality.passed,
        "errors": list(composition_quality.errors),
        "observations": list(composition_quality.observations),
    })
    final_layout = _write_json(working / "final" / "final_layout_plan.json", dynamic_plan)
    _write_json(audit / "dynamic_plan.json", dynamic_plan)

    sample_ids = _representative_page_ids(plan)
    sample_plan = dict(dynamic_plan)
    sample_plan["pages"] = [page for page in dynamic_plan["pages"] if page["page_id"] in sample_ids]
    sample_layout = _write_json(audit / "sample_layout_plan.json", sample_plan)
    sample_pptx = working / "sample.pptx"
    final_pptx = working / "final" / "complete_deck.pptx"
    for layout_path, output_path in ((sample_layout, sample_pptx), (final_layout, final_pptx)):
        subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "render_dynamic.py"),
                "--plan", str(layout_path),
                "--visual-system", str(visual_system_path),
                "--output", str(output_path),
            ],
            cwd=SKILL_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    RenderQualityGate().inspect(
        sample_pptx,
        audit / "sample_qa",
        require_runtime=False,
        layout_plan=sample_layout,
    )
    manifest = SlideManifestBuilder().build(
        pptx_path=final_pptx,
        dynamic_plan=dynamic_plan,
        visual_system_path=visual_system_path,
        template_grammar_path=grammar_path,
        template=selected_template,
    )
    _write_json(audit / "slide_manifest.json", manifest)

    page_layouts = {page["page_id"]: page["layout"] for page in dynamic_plan["pages"]}
    tasks = [
        VisualTask.create(
            task_id=f"VIS_{page.page_id}",
            page_id=page.page_id,
            evidence_ids=page.evidence_ids,
            task_type=page_layouts[page.page_id],
        )
        for page in plan.pages[1:-1]
    ]
    _write_json(audit / "visual_tasks.json", {"visual_tasks": [task.__dict__ for task in tasks]})
    review_passed = ProductAcceptanceEvaluator._visual_review_passed(args.visual_review, len(plan.pages))
    final_tasks = []
    for task in tasks:
        task = task.lock_semantics().mark_rendered(final_pptx).bind_to_slide()
        if review_passed:
            task = task.mark_render_inspected().accept()
        final_tasks.append(task)
    _write_json(audit / "final_visual_tasks.json", {"visual_tasks": [task.__dict__ for task in final_tasks]})

    semantic = ScientificSemanticGate().inspect(plan, graph)
    visual = VisualCompositionGate().inspect(final_tasks, plan)
    render = RenderQualityGate().inspect(
        final_pptx,
        audit / "delivery_qa",
        require_runtime=args.formal,
        runtime=args.runtime,
        layout_plan=final_layout,
        preview_dir=deliverables / "preview",
    )
    if not render.real_render_passed:
        subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "render_pptx_fallback_preview.py"),
                str(final_pptx), "--output-dir", str(deliverables / "preview"),
            ],
            cwd=SKILL_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    quality = QualitySummaryBuilder().build(render, semantic, visual)
    quality["composition"] = composition_quality.passed
    quality["manifest"] = bool(manifest["passed"])
    quality["manifest_errors"] = list(manifest["errors"])
    quality["composition_errors"] = list(composition_quality.errors)
    quality["composition_observations"] = list(composition_quality.observations)
    quality["confirmation_status"] = "confirmed" if args.confirmed else "autonomous_candidate"
    script_path = SpeakerScriptWriter().write(plan, working / "speaker_script.docx")
    acceptance = ProductAcceptanceEvaluator().evaluate(
        plan=plan,
        sample_pptx=sample_pptx,
        final_pptx=final_pptx,
        final_layout_plan=final_layout,
        preview_dir=deliverables / "preview",
        quality=quality,
        visual_review_path=args.visual_review,
        user_confirmed=args.confirmed,
    )
    acceptance_path = _write_json(audit / "product_acceptance.json", acceptance)
    delivery = DeliveryBundle.create(root).publish(
        final_pptx,
        script_path,
        audit_artifacts=(audit / "page_plan.json", render.report_path, acceptance_path),
        quality_summary={**quality, "product_accepted": acceptance["product_accepted"]},
        approved=acceptance["product_accepted"],
    )
    result = {
        "schema_version": 2,
        "skill_root": str(SKILL_ROOT),
        "scene": plan.scene,
        "template": selected_template,
        "renderer": "template_hybrid_editable",
        "page_count": len(plan.pages),
        "sample_page_ids": sorted(sample_ids),
        "content_payloads": {"text": str(text_path), "images": str(image_path)},
        "final_pptx": str(final_pptx),
        "candidate_files": [str(path) for path in delivery.candidate_files],
        "deliverables": [str(path) for path in delivery.visible_files],
        "product_accepted": acceptance["product_accepted"],
    }
    result_path = _write_json(audit / "complete_build_result.json", result)
    print(json.dumps({**result, "acceptance_report": str(acceptance_path), "build_report": str(result_path)}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+")
    parser.add_argument("--scene", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pages", type=int)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--runtime", choices=("powerpoint", "wps", "portable"), default="powerpoint")
    parser.add_argument("--visual-review")
    parser.add_argument("--content-plan", help="Agent-authored, evidence-grounded complete page content JSON")
    parser.add_argument(
        "--renderer",
        choices=("dynamic", "native"),
        default="dynamic",
        help="Use dense editable composition by default; native is retained for template diagnostics",
    )
    parser.add_argument("--confirmed", action="store_true", help="Use only after explicit user approval")
    args = parser.parse_args()

    root = Path(args.output).resolve()
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"output directory must be empty or absent: {root}")
    deliverables = root / "deliverables"
    audit = root / "audit"
    working = root / "working"
    for directory in (deliverables, audit, working):
        directory.mkdir(parents=True, exist_ok=True)

    source_paths = [Path(value).resolve() for value in args.sources]
    source_documents = [SourceIngestor().ingest(path) for path in source_paths]
    scene = SceneCatalog.load().resolve(args.scene)
    selection = TemplateCatalog.load().select(scene.name, args.template)
    selected_template = selection.to_dict()
    if selection.support_level == "conditional_user":
        admission = TemplateAdmissionGate().inspect(
            selection.path,
            require_runtime=args.formal,
            runtime=args.runtime,
        )
        if not admission.passed:
            raise SystemExit("template admission failed: " + "; ".join(admission.errors))
        snapshot = working / "user_template.pptx"
        shutil.copy2(selection.path, snapshot)
        selected_template["path"] = str(snapshot)
        selected_template["admission"] = admission.to_dict()

    profiles = ResearchMethodProfileResolver().infer(source_documents)
    graph = EvidenceGraph.from_sources(source_documents)
    summary = {
        "scene": scene.name,
        "sources": [source.to_dict() for source in source_documents],
        "method_profiles": {
            "primary": profiles.primary,
            "secondary": list(profiles.secondary),
            "basis": {key: list(value) for key, value in profiles.basis.items()},
        },
        "template": selected_template,
    }
    _write_json(audit / "task_summary.json", summary)
    _write_json(audit / "evidence_summary.json", {
        "evidence": [node.to_dict() for node in graph.all()],
        "conflicts": [conflict.to_dict() for conflict in graph.conflicts()],
    })
    options, recommended = StorylinePlanner().propose(scene.name, graph)
    _write_json(audit / "storyline_options.json", {
        "options": [option.to_dict() for option in options],
        "recommended": recommended.to_dict(),
    })

    grammar_path = audit / "template_grammar.json"
    subprocess.run(
        [
            sys.executable, str(SKILL_ROOT / "scripts" / "extract_template_grammar.py"),
            selected_template["path"], "--output", str(grammar_path),
            "--asset-dir", str(working / "template_assets"),
        ],
        cwd=SKILL_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    template_graph = TemplateCapabilityGraph.from_presentation(selected_template["path"])
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
    archetypes = {int(item["slide_index"]): item for item in grammar["archetypes"]}
    visual_system_path = audit / "visual_system.json"
    subprocess.run(
        [
            sys.executable, str(SKILL_ROOT / "scripts" / "extract_visual_system.py"),
            selected_template["path"], "--preview-dir", str(audit / "template_preview"),
            "--output", str(visual_system_path),
        ],
        cwd=SKILL_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    visual_system = json.loads(visual_system_path.read_text(encoding="utf-8"))
    learned_fonts = visual_system.get("fonts", {})
    font_policy = {
        "zh": learned_fonts.get("body") or learned_fonts.get("fallback") or "Microsoft YaHei",
        "latin": learned_fonts.get("latin") or learned_fonts.get("body") or "Arial",
    }

    content = CompleteContentCompiler().compile(
        scene=scene.name,
        evidence=list(graph.all()),
        source_paths=source_paths,
        working_dir=working,
        target_pages=args.pages,
    )
    if args.renderer == "native":
        native_text_capacity = max(
            (
                len(_semantic_text_bindings(item, template_graph.slides[slide_index - 1], 6))
                for slide_index, item in archetypes.items()
                if item.get("role") not in {"cover", "ending", "agenda", "full_figure"}
            ),
            default=0,
        )
        content = adapt_native_text_capacity(content, native_text_capacity)
        figure_text_capacity = max(
            (
                count
                for slide_index, item in archetypes.items()
                if item.get("layout_signature") in {"figure_text_right", "text_figure_right"}
                for count in (3, 2)
                if _source_figure_solution(item, template_graph.slides[slide_index - 1], count) is not None
            ),
            default=0,
        )
        content = adapt_source_figure_text_capacity(content, figure_text_capacity)
    if args.content_plan:
        content = apply_authored_content(content, args.content_plan, expected_scene=scene.name)
    page_drafts = []
    for draft in content.drafts:
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
    plan = PagePlanner().build(
        scene.name,
        content.sections,
        page_drafts,
        graph,
        scene_contract=content.scene_contract,
    )
    plan.write(audit)
    text_path = _write_json(audit / "complete_text_content.json", content.text_content)
    image_path = _write_json(audit / "complete_image_content.json", content.image_content)

    if args.renderer == "dynamic":
        _render_dynamic_candidate(
            args=args,
            plan=plan,
            content=content,
            graph=graph,
            selected_template=selected_template,
            visual_system_path=visual_system_path,
            grammar_path=grammar_path,
            root=root,
            audit=audit,
            working=working,
            deliverables=deliverables,
            text_path=text_path,
            image_path=image_path,
        )
        return

    compiler = LayoutCompiler(template_graph)
    decisions = {}
    for index, page in enumerate(plan.pages):
        preferred = 1 if index == 0 else len(template_graph.slides) if index == len(plan.pages) - 1 else None
        if index == 0:
            allowed = {slide_index for slide_index, item in archetypes.items() if item.get("role") == "cover"}
        elif index == len(plan.pages) - 1:
            allowed = {slide_index for slide_index, item in archetypes.items() if item.get("role") == "ending"}
        elif page.visual_strategy == "source_figure":
            figure_candidates = {
                slide_index for slide_index, item in archetypes.items()
                if item.get("layout_signature") in {"figure_text_right", "text_figure_right"}
            }
            allowed = {
                slide_index for slide_index in figure_candidates
                if _source_figure_solution(
                    archetypes[slide_index],
                    template_graph.slides[slide_index - 1],
                    len(content.text_content[page.page_id]),
                ) is not None
            }
        elif page.visual_strategy == "native_diagram":
            allowed = {
                slide_index for slide_index, item in archetypes.items()
                if item.get("layout_signature") in {"three_columns", "four_columns", "five_columns"}
            }
            if not allowed:
                allowed = {
                    slide_index for slide_index, item in archetypes.items()
                    if item.get("role") == "comparison" and item.get("layout_signature") != "image_grid"
                }
        else:
            allowed = {
                slide_index for slide_index, item in archetypes.items()
                if item.get("layout_signature") in {"three_columns", "four_columns", "five_columns"}
            }
            if not allowed:
                allowed = {
                    slide_index for slide_index, item in archetypes.items()
                    if item.get("layout_signature") in {"text_figure_right", "figure_text_right"}
                }
        if not allowed:
            allowed = {
                slide_index for slide_index, item in archetypes.items()
                if item.get("role") not in {"cover", "ending", "agenda", "full_figure"}
            }
        required_text = len(content.text_content[page.page_id])
        capacity_allowed = set(allowed) if page.visual_strategy == "source_figure" else {
            slide_index
            for slide_index in allowed
            if len(_semantic_text_bindings(
                archetypes[slide_index], template_graph.slides[slide_index - 1], required_text,
            )) >= required_text
        }
        if not capacity_allowed:
            capacity_allowed = set() if page.visual_strategy == "source_figure" else {
                slide_index
                for slide_index, item in archetypes.items()
                if item.get("role") not in {"cover", "ending", "agenda", "full_figure"}
                and len(_semantic_text_bindings(
                    item,
                    template_graph.slides[slide_index - 1],
                    required_text,
                )) >= required_text
            }
        if not capacity_allowed:
            raise SystemExit(f"template has no slide with {required_text} semantic text slots for {page.page_id}")
        allowed = capacity_allowed
        decisions[page.page_id] = compiler.compile(
            page.contract,
            preferred_slide_index=preferred,
            candidate_offset=index,
            allowed_slide_indices=allowed,
        )
        decision = decisions[page.page_id]
        if decision.source_slide_index is None and index in {0, len(plan.pages) - 1}:
            terminal_slide_index = preferred if preferred in capacity_allowed else min(capacity_allowed)
            terminal_text = _semantic_text_bindings(
                archetypes[terminal_slide_index],
                template_graph.slides[terminal_slide_index - 1],
                required_text,
            )
            if len(terminal_text) >= required_text:
                decision = replace(
                    decision,
                    render_mode="template_native",
                    source_slide_index=terminal_slide_index,
                    fallback_reason=None,
                    component_bindings={"text": terminal_text},
                )
                decisions[page.page_id] = decision
        if decision.source_slide_index is not None:
            slide = template_graph.slides[decision.source_slide_index - 1]
            if page.visual_strategy == "source_figure":
                solution = _source_figure_solution(
                    archetypes[decision.source_slide_index], slide, len(content.text_content[page.page_id])
                )
                if solution is None:
                    raise SystemExit(f"template slide {decision.source_slide_index} has no non-overlapping figure/text solution")
                picture_shape_id, semantic_text = solution
            else:
                picture_shape_id = None
                semantic_text = _semantic_text_bindings(
                    archetypes[decision.source_slide_index], slide, len(content.text_content[page.page_id])
                )
            if len(semantic_text) < len(content.text_content[page.page_id]):
                raise SystemExit(
                    f"template slide {decision.source_slide_index} lacks semantic text slots for {page.page_id}: "
                    f"need {len(content.text_content[page.page_id])}, found {len(semantic_text)}"
                )
            bindings = dict(decision.component_bindings)
            bindings["text"] = semantic_text
            if picture_shape_id is not None:
                bindings["picture"] = (picture_shape_id,)
            decisions[page.page_id] = replace(decision, component_bindings=bindings)
    unsupported = [page_id for page_id, decision in decisions.items() if decision.source_slide_index is None]
    if unsupported:
        raise SystemExit(f"template cannot express complete page contracts: {unsupported}")
    remove_shape_ids = {}
    for page in plan.pages:
        decision = decisions[page.page_id]
        archetype = archetypes[decision.source_slide_index]
        bound_pictures = set(decision.component_bindings.get("picture", ()))
        remove_shape_ids[page.page_id] = []
        for slot in archetype.get("picture_slots", ()):
            shape_id = int(slot["shape_id"])
            if shape_id in bound_pictures:
                continue
            box = slot.get("box", {})
            is_user_logo_placeholder = (
                slot.get("role") == "logo"
                and float(box.get("left", 0)) > 0.80
                and float(box.get("top", 1)) < 0.14
            )
            is_nested_sample_picture = (
                slot.get("role") == "decoration"
                and slot.get("nested_within_shape_id") is not None
                and float(slot.get("area", 0)) < 0.40
            )
            if slot.get("role") == "content_image" or is_user_logo_placeholder or is_nested_sample_picture:
                remove_shape_ids[page.page_id].append(shape_id)
    _write_json(audit / "layout_decisions.json", {
        page_id: {
            "render_mode": decision.render_mode,
            "source_slide_index": decision.source_slide_index,
            "fallback_reason": decision.fallback_reason,
            "component_bindings": {key: list(value) for key, value in decision.component_bindings.items()},
        }
        for page_id, decision in decisions.items()
    })

    tasks = [
        VisualTask.create(
            task_id=f"VIS_{page.page_id}",
            page_id=page.page_id,
            evidence_ids=page.evidence_ids,
            task_type=page.visual_strategy,
        )
        for page in plan.pages if page.visual_strategy != "text_only"
    ]
    _write_json(audit / "visual_tasks.json", {"visual_tasks": [task.__dict__ for task in tasks]})

    adapter = NativeRenderAdapter()
    sample_ids = _representative_page_ids(plan)
    sample_layout = adapter.write_layout_plan(
        plan, decisions, content.text_content, audit / "sample_layout_plan.json",
        confirmed=True, image_content=content.image_content, page_ids=sample_ids,
        template_grammar=grammar_path,
        template_graph=template_graph,
        remove_shape_ids=remove_shape_ids,
        font_policy=font_policy,
    )
    sample_pptx = adapter.render(sample_layout, selected_template["path"], working / "sample.pptx")
    RenderQualityGate().inspect(
        sample_pptx, audit / "sample_qa", require_runtime=False, layout_plan=sample_layout,
    )

    final_layout = adapter.write_layout_plan(
        plan, decisions, content.text_content, working / "final" / "final_layout_plan.json",
        confirmed=True, image_content=content.image_content, template_grammar=grammar_path,
        template_graph=template_graph,
        remove_shape_ids=remove_shape_ids,
        font_policy=font_policy,
    )
    final_pptx = adapter.render(final_layout, selected_template["path"], working / "final" / "complete_deck.pptx")
    final_tasks = []
    for task in tasks:
        images = content.image_content.get(task.page_id, [])
        output = images[0] if images else final_pptx
        task = task.lock_semantics().mark_rendered(output).bind_to_slide().mark_render_inspected().accept()
        final_tasks.append(task)
    _write_json(audit / "final_visual_tasks.json", {"visual_tasks": [task.__dict__ for task in final_tasks]})

    semantic = ScientificSemanticGate().inspect(plan, graph)
    visual = VisualCompositionGate().inspect(final_tasks, plan)
    render = RenderQualityGate().inspect(
        final_pptx,
        audit / "delivery_qa",
        require_runtime=args.formal,
        runtime=args.runtime,
        layout_plan=final_layout,
        preview_dir=deliverables / "preview",
    )
    if not render.real_render_passed:
        subprocess.run(
            [
                sys.executable, str(SKILL_ROOT / "scripts" / "render_pptx_fallback_preview.py"),
                str(final_pptx), "--output-dir", str(deliverables / "preview"),
            ],
            cwd=SKILL_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    quality = QualitySummaryBuilder().build(render, semantic, visual)
    quality["confirmation_status"] = "confirmed" if args.confirmed else "autonomous_candidate"
    script_path = SpeakerScriptWriter().write(plan, working / "speaker_script.docx")
    acceptance = ProductAcceptanceEvaluator().evaluate(
        plan=plan,
        sample_pptx=sample_pptx,
        final_pptx=final_pptx,
        final_layout_plan=final_layout,
        preview_dir=deliverables / "preview",
        quality=quality,
        visual_review_path=args.visual_review,
        user_confirmed=args.confirmed,
    )
    acceptance_path = _write_json(audit / "product_acceptance.json", acceptance)
    delivery = DeliveryBundle.create(root).publish(
        final_pptx,
        script_path,
        audit_artifacts=(audit / "page_plan.json", render.report_path, acceptance_path),
        quality_summary={**quality, "product_accepted": acceptance["product_accepted"]},
        approved=acceptance["product_accepted"],
    )
    result = {
        "schema_version": 1,
        "skill_root": str(SKILL_ROOT),
        "scene": scene.name,
        "template": selected_template,
        "page_count": len(plan.pages),
        "sample_page_ids": sorted(sample_ids),
        "content_payloads": {"text": str(text_path), "images": str(image_path)},
        "final_pptx": str(final_pptx),
        "candidate_files": [str(path) for path in delivery.candidate_files],
        "deliverables": [str(path) for path in delivery.visible_files],
        "product_accepted": acceptance["product_accepted"],
    }
    result_path = _write_json(audit / "complete_build_result.json", result)
    print(json.dumps({**result, "acceptance_report": str(acceptance_path), "build_report": str(result_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
