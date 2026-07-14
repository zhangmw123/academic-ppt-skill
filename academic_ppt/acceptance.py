"""Evaluate complete-deck product acceptance without collapsing hard gates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .planning import PagePlan
from .scenes import SceneCatalog


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class AcceptanceGate:
    gate_id: str
    passed: bool
    detail: str

    def to_dict(self) -> dict:
        return {"gate_id": self.gate_id, "passed": self.passed, "detail": self.detail}


class ProductAcceptanceEvaluator:
    """Apply the release matrix to actual final artifacts, not test counters."""

    def evaluate(
        self,
        *,
        plan: PagePlan,
        sample_pptx: Path | str,
        final_pptx: Path | str,
        final_layout_plan: Path | str,
        preview_dir: Path | str,
        quality: dict,
        visual_review_path: Path | str | None = None,
        synthetic_fixture: bool = False,
        user_confirmed: bool = False,
    ) -> dict:
        sample = Path(sample_pptx).resolve()
        final = Path(final_pptx).resolve()
        layout = Path(final_layout_plan).resolve()
        preview = Path(preview_dir).resolve()
        profile = SceneCatalog.load().resolve(plan.scene)
        claims = [page.claim_id for page in plan.pages]
        evidence_sets = [tuple(page.evidence_ids) for page in plan.pages]
        preview_images = sorted({path.resolve() for pattern in ("*.png", "*.PNG") for path in preview.glob(pattern)}) if preview.is_dir() else []
        preview_images = [path for path in preview_images if path.name.casefold() != "contact-sheet.png"]

        gates = [
            AcceptanceGate(
                "real_source_material",
                not synthetic_fixture,
                "real source material" if not synthetic_fixture else "synthetic fixture is contract-only evidence",
            ),
            AcceptanceGate(
                "user_confirmation",
                user_confirmed,
                "the complete plan and representative render require explicit user confirmation",
            ),
            AcceptanceGate(
                "complete_scene_budget",
                plan.deck_scope == "complete" and profile.complete_min <= len(plan.pages) <= profile.complete_max,
                f"scope={plan.deck_scope}; pages={len(plan.pages)}; expected={profile.complete_min}-{profile.complete_max}",
            ),
            AcceptanceGate(
                "complete_scene_contract",
                set(profile.required_tags).issubset(plan.coverage_tags)
                and set(profile.argument_chain).issubset(plan.argument_units),
                "required scene coverage and argument units must all be present",
            ),
            AcceptanceGate(
                "non_repeating_page_arguments",
                len(set(claims)) == len(claims) and len(set(evidence_sets)) == len(evidence_sets),
                f"unique_claims={len(set(claims))}/{len(claims)}; unique_evidence_sets={len(set(evidence_sets))}/{len(evidence_sets)}",
            ),
            AcceptanceGate(
                "sample_final_separation",
                sample.is_file() and final.is_file() and sample != final and _sha256(sample) != _sha256(final)
                and "sample" not in final.name.casefold(),
                "representative sample and complete final deck must be different files and content",
            ),
            AcceptanceGate(
                "final_layout_is_complete",
                layout.is_file() and self._layout_page_count(layout) == len(plan.pages),
                f"final_layout_pages={self._layout_page_count(layout) if layout.is_file() else 0}; plan_pages={len(plan.pages)}",
            ),
            AcceptanceGate(
                "full_preview_exported",
                len(preview_images) == len(plan.pages),
                f"preview_slides={len(preview_images)}; plan_pages={len(plan.pages)}",
            ),
            AcceptanceGate("structural_qa", bool(quality.get("structural")), "PPTX structural hard gates"),
            AcceptanceGate("scientific_semantic_qa", bool(quality.get("semantic")), "evidence and claim provenance gates"),
            AcceptanceGate(
                "editable_template_manifest",
                bool(quality.get("composition")) and bool(quality.get("manifest")),
                "every content page must bind a template archetype and retain an editable information layer",
            ),
            AcceptanceGate("visual_task_qa", bool(quality.get("visual")), "all visual tasks rendered, bound, inspected, and accepted"),
            AcceptanceGate("powerpoint_real_render", bool(quality.get("formal_accepted")), "Windows PowerPoint authoritative render"),
            AcceptanceGate(
                "human_visual_review",
                self._visual_review_passed(visual_review_path, len(plan.pages)),
                "every final slide must have an explicit visual-review decision",
            ),
        ]
        return {
            "schema_version": 1,
            "scene": plan.scene,
            "page_count": len(plan.pages),
            "product_accepted": all(gate.passed for gate in gates),
            "gates": [gate.to_dict() for gate in gates],
        }

    @staticmethod
    def _layout_page_count(path: Path) -> int:
        try:
            return len(json.loads(path.read_text(encoding="utf-8")).get("pages", ()))
        except (OSError, json.JSONDecodeError):
            return 0

    @staticmethod
    def _visual_review_passed(path: Path | str | None, page_count: int) -> bool:
        if path is None:
            return False
        review_path = Path(path)
        if not review_path.is_file():
            return False
        try:
            payload = json.loads(review_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        pages = payload.get("pages", ())
        return (
            payload.get("reviewed") is True
            and len(pages) == page_count
            and all(item.get("passed") is True for item in pages)
        )
