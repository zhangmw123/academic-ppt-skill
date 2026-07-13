"""Validate and persist evidence-bound scientific page plans."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .evidence import EvidenceGraph
from .layout import ScientificPageContract
from .scenes import SceneCatalog, ScenePlanContract


@dataclass(frozen=True)
class PageDraft:
    page_id: str
    section: str
    title: str
    question_answered: str
    claim_id: str
    interpretation: str
    next_link: str
    time_seconds: int
    visual_strategy: str
    component_requirements: dict[str, int]
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlannedPage:
    page_id: str
    section: str
    title: str
    question_answered: str
    claim_id: str
    claim_text: str
    evidence_ids: tuple[str, ...]
    interpretation: str
    next_link: str
    time_seconds: int
    visual_strategy: str
    contract: ScientificPageContract
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "contract": asdict(self.contract),
        }


@dataclass(frozen=True)
class PagePlan:
    scene: str
    sections: tuple[str, ...]
    pages: tuple[PlannedPage, ...]
    deck_scope: str = "sample"
    evidence_state: str = ""
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()
    section_variant: str | None = None
    duration_minutes: float | None = None
    scene_warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "sections": list(self.sections),
            "deck_scope": self.deck_scope,
            "evidence_state": self.evidence_state,
            "coverage_tags": list(self.coverage_tags),
            "argument_units": list(self.argument_units),
            "section_variant": self.section_variant,
            "duration_minutes": self.duration_minutes,
            "scene_warnings": list(self.scene_warnings),
            "pages": [page.to_dict() for page in self.pages],
        }

    def write(self, audit_dir: Path | str) -> tuple[Path, Path]:
        destination = Path(audit_dir)
        destination.mkdir(parents=True, exist_ok=True)
        json_path = destination / "page_plan.json"
        markdown_path = destination / "presentation_prd.md"
        json_path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# Presentation PRD",
            "",
            f"- Scene: {self.scene}",
            f"- Scope: {self.deck_scope}",
            f"- Evidence state: {self.evidence_state}",
            f"- Pages: {len(self.pages)}",
            "",
        ]
        for page in self.pages:
            lines.extend([
                f"## {page.page_id} {page.title}",
                "",
                f"- Section: {page.section}",
                f"- Question: {page.question_answered}",
                f"- Claim: {page.claim_id}",
                f"- Evidence: {', '.join(page.evidence_ids)}",
                f"- Scene coverage: {', '.join(page.coverage_tags)}",
                f"- Argument units: {', '.join(page.argument_units)}",
                f"- Interpretation or boundary: {page.interpretation}",
                f"- Visual: {page.visual_strategy}",
                f"- Time: {page.time_seconds}s",
                f"- Transition: {page.next_link}",
                "",
            ])
        markdown_path.write_text("\n".join(lines), encoding="utf-8")
        return json_path, markdown_path

    @classmethod
    def load(cls, path: Path | str) -> "PagePlan":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        pages = tuple(
            PlannedPage(
                page_id=item["page_id"],
                section=item["section"],
                title=item["title"],
                question_answered=item["question_answered"],
                claim_id=item["claim_id"],
                claim_text=item["claim_text"],
                evidence_ids=tuple(item["evidence_ids"]),
                interpretation=item["interpretation"],
                next_link=item["next_link"],
                time_seconds=item["time_seconds"],
                visual_strategy=item["visual_strategy"],
                contract=ScientificPageContract(**item["contract"]),
                coverage_tags=tuple(item.get("coverage_tags", ())),
                argument_units=tuple(item.get("argument_units", ())),
            )
            for item in payload["pages"]
        )
        return cls(
            scene=payload["scene"],
            sections=tuple(payload["sections"]),
            pages=pages,
            deck_scope=payload.get("deck_scope", "sample"),
            evidence_state=payload.get("evidence_state", ""),
            coverage_tags=tuple(payload.get("coverage_tags", ())),
            argument_units=tuple(payload.get("argument_units", ())),
            section_variant=payload.get("section_variant"),
            duration_minutes=payload.get("duration_minutes"),
            scene_warnings=tuple(payload.get("scene_warnings", ())),
        )


class PagePlanner:
    """Turn authored page drafts into validated Scientific Page Contracts."""

    def build(
        self,
        scene: str,
        sections: Iterable[str],
        drafts: Iterable[PageDraft],
        evidence_graph: EvidenceGraph,
        *,
        scene_contract: ScenePlanContract | None = None,
    ) -> PagePlan:
        catalog = SceneCatalog.load()
        profile = catalog.resolve(scene)
        resolved_scene = profile.name
        resolved_sections = tuple(section.strip() for section in sections if section.strip())
        resolved_drafts = tuple(drafts)
        if not resolved_scene:
            raise ValueError("scene is required")
        if not resolved_sections:
            raise ValueError("page plan requires sections")
        if not resolved_drafts:
            raise ValueError("page plan requires at least one page")
        pages = []
        seen_page_ids = set()
        for draft in resolved_drafts:
            self._validate_draft(draft, resolved_sections, seen_page_ids)
            claim = evidence_graph.trace_claim(draft.claim_id)
            claim_text = evidence_graph.claim(draft.claim_id).text
            evidence_ids = tuple(node.evidence_id for node in claim)
            contract = ScientificPageContract(
                page_id=draft.page_id,
                claim_id=draft.claim_id,
                component_requirements=dict(draft.component_requirements),
            )
            contract.validate()
            evidence_graph.add_page(draft.page_id, [draft.claim_id])
            pages.append(PlannedPage(
                page_id=draft.page_id,
                section=draft.section,
                title=draft.title,
                question_answered=draft.question_answered,
                claim_id=draft.claim_id,
                claim_text=claim_text,
                evidence_ids=evidence_ids,
                interpretation=draft.interpretation,
                next_link=draft.next_link,
                time_seconds=draft.time_seconds,
                visual_strategy=draft.visual_strategy,
                contract=contract,
                coverage_tags=tuple(draft.coverage_tags),
                argument_units=tuple(draft.argument_units),
            ))
        coverage_tags = tuple(dict.fromkeys(
            value
            for page in pages
            for value in page.coverage_tags
        ))
        argument_units = tuple(dict.fromkeys(
            value
            for page in pages
            for value in page.argument_units
        ))
        requested = scene_contract or ScenePlanContract.sample(profile.evidence_states[0])
        effective_contract = ScenePlanContract(
            deck_scope=requested.deck_scope,
            evidence_state=requested.evidence_state,
            coverage_tags=tuple(dict.fromkeys((*requested.coverage_tags, *coverage_tags))),
            argument_units=tuple(dict.fromkeys((*requested.argument_units, *argument_units))),
            section_variant=requested.section_variant,
            duration_minutes=requested.duration_minutes,
        )
        validation = catalog.validate_plan(
            resolved_scene,
            effective_contract,
            sections=resolved_sections,
            page_count=len(pages),
            total_seconds=sum(page.time_seconds for page in pages),
        )
        validation.require_passed()
        return PagePlan(
            scene=resolved_scene,
            sections=resolved_sections,
            pages=tuple(pages),
            deck_scope=effective_contract.deck_scope,
            evidence_state=effective_contract.evidence_state,
            coverage_tags=effective_contract.coverage_tags,
            argument_units=effective_contract.argument_units,
            section_variant=effective_contract.section_variant,
            duration_minutes=effective_contract.duration_minutes,
            scene_warnings=validation.warnings,
        )

    @staticmethod
    def _validate_draft(draft: PageDraft, sections: tuple[str, ...], seen_page_ids: set[str]) -> None:
        required = {
            "page ID": draft.page_id,
            "section": draft.section,
            "title": draft.title,
            "question": draft.question_answered,
            "claim": draft.claim_id,
            "interpretation": draft.interpretation,
            "transition": draft.next_link,
            "visual strategy": draft.visual_strategy,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"page draft missing: {', '.join(missing)}")
        if draft.section not in sections:
            raise ValueError(f"page section is not confirmed: {draft.section}")
        if draft.page_id in seen_page_ids:
            raise ValueError(f"duplicate page ID: {draft.page_id}")
        if draft.time_seconds < 1:
            raise ValueError("page time must be positive")
        seen_page_ids.add(draft.page_id)
