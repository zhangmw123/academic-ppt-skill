"""Inspect editable PPTX components for native template reuse."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateComponent:
    kind: str
    shape_id: int
    geometry: dict[str, int]
    parent_group_shape_id: int | None = None


@dataclass(frozen=True)
class TemplateSlideCapability:
    slide_index: int
    components: tuple[TemplateComponent, ...]

    @property
    def component_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(component.kind for component in self.components).items()))


@dataclass(frozen=True)
class TemplateCapabilityGraph:
    template_path: str
    slides: tuple[TemplateSlideCapability, ...]

    @classmethod
    def from_presentation(cls, path: Path | str) -> "TemplateCapabilityGraph":
        try:
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
        except ImportError as exc:
            raise RuntimeError("python-pptx is required to inspect templates") from exc

        template_path = Path(path).resolve()
        if not template_path.is_file():
            raise FileNotFoundError(template_path)
        presentation = Presentation(template_path)
        slides = []
        for slide_index, slide in enumerate(presentation.slides, 1):
            components = []
            for shape in slide.shapes:
                geometry = {
                    "left": int(shape.left),
                    "top": int(shape.top),
                    "width": int(shape.width),
                    "height": int(shape.height),
                }
                if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                    components.append(TemplateComponent(
                        kind="group",
                        shape_id=shape.shape_id,
                        geometry=geometry,
                    ))
                elif getattr(shape, "has_table", False):
                    components.append(TemplateComponent("table", shape.shape_id, geometry))
                elif getattr(shape, "has_chart", False):
                    components.append(TemplateComponent("chart", shape.shape_id, geometry))
                elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    components.append(TemplateComponent("picture", shape.shape_id, geometry))
                elif getattr(shape, "has_text_frame", False):
                    components.append(TemplateComponent("text", shape.shape_id, geometry))
            slides.append(TemplateSlideCapability(
                slide_index=slide_index,
                components=tuple(components),
            ))
        return cls(template_path=str(template_path), slides=tuple(slides))

    def find_compatible_slides(
        self,
        required_components: dict[str, int],
    ) -> tuple[TemplateSlideCapability, ...]:
        invalid = {kind: count for kind, count in required_components.items() if count < 1}
        if invalid:
            raise ValueError(f"component requirements must be positive: {invalid}")
        return tuple(
            slide for slide in self.slides
            if all(slide.component_counts.get(kind, 0) >= count for kind, count in required_components.items())
        )
