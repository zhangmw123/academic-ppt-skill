"""Compile Scientific Page Contracts into template layout decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .templates import TemplateCapabilityGraph, TemplateSlideCapability


@dataclass(frozen=True)
class ScientificPageContract:
    page_id: str
    claim_id: str
    component_requirements: dict[str, int]

    def validate(self) -> None:
        if not self.page_id.strip():
            raise ValueError("page ID is required")
        if not self.claim_id.strip():
            raise ValueError("page claim is required")
        if not self.component_requirements:
            raise ValueError("page requires component requirements")
        invalid = {kind: count for kind, count in self.component_requirements.items() if count < 1}
        if invalid:
            raise ValueError(f"component requirements must be positive: {invalid}")


@dataclass(frozen=True)
class LayoutDecision:
    page_id: str
    render_mode: str
    source_slide_index: int | None
    fallback_reason: str | None = None
    component_bindings: dict[str, tuple[int, ...]] = field(default_factory=dict)


class LayoutCompiler:
    """Choose a native template page before considering a freeform fallback."""

    def __init__(self, template_graph: TemplateCapabilityGraph):
        self.template_graph = template_graph

    def compile(
        self,
        contract: ScientificPageContract,
        *,
        preferred_slide_index: int | None = None,
        candidate_offset: int = 0,
        allowed_slide_indices: set[int] | None = None,
    ) -> LayoutDecision:
        contract.validate()
        candidates = tuple(
            slide for slide in self.template_graph.find_compatible_slides(contract.component_requirements)
            if allowed_slide_indices is None or slide.slide_index in allowed_slide_indices
            if all(
                len(self._select_components(slide, kind, required)) == required
                for kind, required in contract.component_requirements.items()
            )
        )
        if not candidates:
            return LayoutDecision(
                page_id=contract.page_id,
                render_mode="scientific_freeform",
                source_slide_index=None,
                fallback_reason="no compatible native template slide",
            )
        ordered = sorted(candidates, key=lambda slide: self._candidate_rank(slide, contract))
        selected = next(
            (slide for slide in ordered if slide.slide_index == preferred_slide_index),
            ordered[candidate_offset % len(ordered)],
        )
        bindings = {
            kind: tuple(
                component.shape_id
                for component in self._select_components(selected, kind, required)
            )
            for kind, required in contract.component_requirements.items()
        }
        return LayoutDecision(
            page_id=contract.page_id,
            render_mode="template_native",
            source_slide_index=selected.slide_index,
            component_bindings=bindings,
        )

    @staticmethod
    def _excess_capacity(
        slide: TemplateSlideCapability,
        contract: ScientificPageContract,
    ) -> tuple[int, int]:
        counts = slide.component_counts
        excess = sum(counts.get(kind, 0) - required for kind, required in contract.component_requirements.items())
        return excess, slide.slide_index

    @classmethod
    def _candidate_rank(
        cls,
        slide: TemplateSlideCapability,
        contract: ScientificPageContract,
    ) -> tuple[float, int, int]:
        useful_area = 0
        for kind, required in contract.component_requirements.items():
            components = cls._select_components(slide, kind, required)
            useful_area += sum(cls._component_capacity(component) for component in components)
        excess, _ = cls._excess_capacity(slide, contract)
        return -useful_area, excess, slide.slide_index

    @staticmethod
    def _component_capacity(component) -> int:
        return int(component.geometry["width"]) * int(component.geometry["height"])

    @classmethod
    def _select_components(cls, slide, kind: str, required: int):
        ordered = sorted(
            (component for component in slide.components if component.kind == kind),
            key=cls._component_capacity,
            reverse=True,
        )
        if kind != "text":
            return ordered[:required]
        selected = []
        for component in ordered:
            if any(cls._overlap_ratio(component.geometry, existing.geometry) > 0.1 for existing in selected):
                continue
            selected.append(component)
            if len(selected) == required:
                break
        return selected

    @staticmethod
    def _overlap_ratio(first: dict[str, int], second: dict[str, int]) -> float:
        left = max(first["left"], second["left"])
        top = max(first["top"], second["top"])
        right = min(first["left"] + first["width"], second["left"] + second["width"])
        bottom = min(first["top"] + first["height"], second["top"] + second["height"])
        if right <= left or bottom <= top:
            return 0.0
        overlap = (right - left) * (bottom - top)
        smaller = min(first["width"] * first["height"], second["width"] * second["height"])
        return overlap / max(smaller, 1)
