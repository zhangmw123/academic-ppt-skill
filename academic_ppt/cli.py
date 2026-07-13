"""Command-line interface for the Academic PPT v2 core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evidence import EvidenceGraph
from .ingest import SourceIngestor
from .profiles import ResearchMethodProfileResolver
from .revisions import AuthoritativeEditBaseline
from .service import AcademicPptService, ContentPageDraft
from .workflow import PHASES, ProjectWorkflow, WorkflowConfig


def _print(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="academic-ppt")
    commands = parser.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("init", help="Create a v2 presentation project")
    initialize.add_argument("project")
    initialize.add_argument("--scene", required=True)
    initialize.add_argument("--interaction", choices=("guided", "autonomous_draft"), default="guided")
    initialize.add_argument("--rigor", choices=("lean", "standard", "strict"), default="standard")
    initialize.add_argument("--runtime", choices=("powerpoint", "wps", "portable"), default="powerpoint")

    status = commands.add_parser("status", help="Show persisted workflow status")
    status.add_argument("project")

    analyze = commands.add_parser("analyze", help="Inspect sources without creating a presentation")
    analyze.add_argument("sources", nargs="+")
    analyze.add_argument("--primary-profile")

    prepare = commands.add_parser("prepare", help="Create the first guided task summary from supplied sources")
    prepare.add_argument("project")
    prepare.add_argument("sources", nargs="+")
    prepare.add_argument("--scene", required=True)

    confirm_brief = commands.add_parser("confirm-brief", help="Record Phase 0 confirmation and begin evidence work")
    confirm_brief.add_argument("project")
    confirm_brief.add_argument("--note", required=True)

    prepare_evidence = commands.add_parser("prepare-evidence", help="Create Phase 1 evidence and storyline artifacts")
    prepare_evidence.add_argument("project")

    confirm_evidence = commands.add_parser("confirm-evidence", help="Record Phase 1 confirmation and begin content planning")
    confirm_evidence.add_argument("project")
    confirm_evidence.add_argument("--note", required=True)

    prepare_content = commands.add_parser("prepare-content-plan", help="Create an evidence-bound Phase 2 page plan")
    prepare_content.add_argument("project")
    prepare_content.add_argument("--sections", required=True, help="Comma-separated confirmed sections")
    prepare_content.add_argument("--drafts", required=True, help="JSON file containing content page drafts")

    confirm_content = commands.add_parser("confirm-content-plan", help="Record Phase 2 confirmation and begin visual planning")
    confirm_content.add_argument("project")
    confirm_content.add_argument("--note", required=True)

    prepare_visual = commands.add_parser("prepare-visual-plan", help="Create Phase 3 layout decisions and visual tasks")
    prepare_visual.add_argument("project")

    adopt_baseline = commands.add_parser("adopt-baseline", help="Adopt a generated PPTX as the revision baseline")
    adopt_baseline.add_argument("project")
    adopt_baseline.add_argument("pptx")
    adopt_baseline.add_argument("--page-ids", required=True, help="Comma-separated page IDs in slide order")

    plan_revision = commands.add_parser("plan-revision", help="Plan a protected revision from an adopted baseline")
    plan_revision.add_argument("project")
    plan_revision.add_argument("edited_pptx")
    plan_revision.add_argument("--targets", required=True, help="Comma-separated page IDs to rebuild")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    if args.command == "init":
        workflow = ProjectWorkflow.create(
            Path(args.project),
            WorkflowConfig(
                scene=args.scene,
                interaction_mode=args.interaction,
                rigor_profile=args.rigor,
                authoritative_runtime=args.runtime,
            ),
        )
        _print({
            "project": str(workflow.root),
            "scene": workflow.config.scene,
            "interaction_mode": workflow.config.interaction_mode,
            "rigor_profile": workflow.config.rigor_profile,
            "authoritative_runtime": workflow.config.authoritative_runtime,
        })
        return 0
    if args.command == "status":
        workflow = ProjectWorkflow.open(Path(args.project))
        changed = workflow.refresh_artifacts()
        _print({
            "project": str(workflow.root),
            "scene": workflow.config.scene,
            "changed_artifacts": changed,
            "phases": {name: workflow.phase(name).status for name in PHASES},
            "formally_confirmed": workflow.is_formally_confirmed(),
        })
        return 0
    if args.command == "analyze":
        sources = [SourceIngestor().ingest(Path(path)) for path in args.sources]
        profiles = ResearchMethodProfileResolver().infer(sources, args.primary_profile)
        graph = EvidenceGraph.from_sources(sources)
        _print({
            "source_count": len(sources),
            "sources": [source.to_dict() for source in sources],
            "method_profiles": {
                "primary": profiles.primary,
                "secondary": profiles.secondary,
                "basis": profiles.basis,
                "user_overridden": profiles.user_overridden,
            },
            "evidence": [node.to_dict() for node in graph.all()],
            "conflicts": [conflict.to_dict() for conflict in graph.conflicts()],
        })
        return 0
    if args.command == "prepare":
        service = AcademicPptService()
        summary = service.prepare(Path(args.project), [Path(path) for path in args.sources], scene=args.scene)
        workflow = ProjectWorkflow.open(Path(args.project))
        _print({
            "project": str(workflow.root),
            "phase": workflow.phase("brief").status,
            "task_summary": summary,
        })
        return 0
    if args.command == "confirm-brief":
        service = AcademicPptService()
        service.confirm_brief(Path(args.project), args.note)
        workflow = ProjectWorkflow.open(Path(args.project))
        _print({
            "project": str(workflow.root),
            "brief": workflow.phase("brief").status,
            "evidence": workflow.phase("evidence").status,
        })
        return 0
    if args.command == "prepare-evidence":
        workflow = ProjectWorkflow.open(Path(args.project))
        payload = AcademicPptService().prepare_evidence(workflow.root)
        _print({"project": str(workflow.root), **payload, "phase": "awaiting_confirmation"})
        return 0
    if args.command == "confirm-evidence":
        service = AcademicPptService()
        service.confirm_evidence(Path(args.project), args.note)
        workflow = ProjectWorkflow.open(Path(args.project))
        _print({"project": str(workflow.root), "evidence": workflow.phase("evidence").status,
                "content_plan": workflow.phase("content_plan").status})
        return 0
    if args.command == "prepare-content-plan":
        draft_payload = json.loads(Path(args.drafts).read_text(encoding="utf-8"))
        values = draft_payload["drafts"] if isinstance(draft_payload, dict) else draft_payload
        drafts = [
            ContentPageDraft(
                **{**item, "evidence_ids": tuple(item["evidence_ids"])}
            )
            for item in values
        ]
        sections = [value.strip() for value in args.sections.split(",") if value.strip()]
        plan = AcademicPptService().prepare_content_plan(Path(args.project), sections, drafts)
        _print({"project": str(Path(args.project).resolve()), "phase": "awaiting_confirmation", "page_plan": plan.to_dict()})
        return 0
    if args.command == "confirm-content-plan":
        service = AcademicPptService()
        service.confirm_content_plan(Path(args.project), args.note)
        workflow = ProjectWorkflow.open(Path(args.project))
        _print({"project": str(workflow.root), "content_plan": workflow.phase("content_plan").status,
                "visual_plan": workflow.phase("visual_plan").status})
        return 0
    if args.command == "prepare-visual-plan":
        workflow = ProjectWorkflow.open(Path(args.project))
        payload = AcademicPptService().prepare_visual_plan(workflow.root)
        _print({"project": str(workflow.root), **payload, "phase": "awaiting_confirmation"})
        return 0
    if args.command == "adopt-baseline":
        root = Path(args.project).resolve()
        page_ids = tuple(value.strip() for value in args.page_ids.split(",") if value.strip())
        baseline = AuthoritativeEditBaseline.adopt(args.pptx, page_ids)
        baseline_path = baseline.write(root / "audit")
        _print({"project": str(root), "baseline": str(baseline_path), "page_ids": list(page_ids)})
        return 0
    if args.command == "plan-revision":
        root = Path(args.project).resolve()
        baseline = AuthoritativeEditBaseline.load(root / "audit" / "authoritative_edit_baseline.json")
        targets = tuple(value.strip() for value in args.targets.split(",") if value.strip())
        plan = baseline.plan_revision(args.edited_pptx, target_page_ids=targets)
        plan_path = root / "audit" / "revision_plan.json"
        plan_path.write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        _print(plan.to_dict())
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
