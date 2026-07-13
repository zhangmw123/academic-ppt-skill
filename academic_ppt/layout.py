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

    def compile(self, contract: ScientificPageContract) -> LayoutDecision:
        contract.validate()
        candidates = self.template_graph.find_compatible_slides(contract.component_requirements)
        if not candidates:
            return LayoutDecision(
                page_id=contract.page_id,
                render_mode="scientific_freeform",
                source_slide_index=None,
                fallback_reason="no compatible native template slide",
            )
        selected = min(candidates, key=lambda slide: self._excess_capacity(slide, contract))
        bindings = {
            kind: tuple(
                component.shape_id
                for component in selected.components
                if component.kind == kind
            )[:required]
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
