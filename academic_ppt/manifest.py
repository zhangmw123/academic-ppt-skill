"""Build a per-slide editability, density, and template-identity manifest."""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from .composition import CompositionQualityGate, text_units


class SlideManifestBuilder:
    """Measure the actual PPTX against the template-guided composition contract."""

    def build(
        self,
        *,
        pptx_path: Path | str,
        dynamic_plan: dict,
        visual_system_path: Path | str,
        template_grammar_path: Path | str,
        template: dict,
    ) -> dict:
        presentation = Presentation(pptx_path)
        visual_system = json.loads(Path(visual_system_path).read_text(encoding="utf-8"))
        grammar = json.loads(Path(template_grammar_path).read_text(encoding="utf-8"))
        pages = dynamic_plan.get("pages", ())
        errors: list[str] = []
        slides = []
        if len(presentation.slides) != len(pages):
            errors.append(f"manifest page count mismatch: pptx={len(presentation.slides)} plan={len(pages)}")
        for index, page in enumerate(pages):
            if index >= len(presentation.slides):
                break
            slide = presentation.slides[index]
            text_shapes = [
                shape for shape in slide.shapes
                if getattr(shape, "has_text_frame", False) and shape.text.strip()
            ]
            pictures = [shape for shape in slide.shapes if getattr(shape, "shape_type", None) == 13]
            native_shapes = [shape for shape in slide.shapes if getattr(shape, "shape_type", None) != 13]
            editable_frames = [
                shape for shape in slide.shapes
                if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.AUTO_SHAPE
            ]
            modules = [value for value in CompositionQualityGate._modules(page) if str(value).strip()]
            density_units = round(sum(text_units(str(value)) for value in modules), 1)
            layout = page.get("layout")
            content_page = layout not in {"cover", "ending", "section", "agenda"}
            reference = page.get("template_reference")
            page_errors = []
            if content_page and not reference:
                page_errors.append("missing template archetype reference")
            if content_page and len(text_shapes) < 5:
                page_errors.append(f"only {len(text_shapes)} non-empty editable text objects")
            if content_page and density_units < 55:
                page_errors.append(f"density {density_units:g} below 55")
            if layout == "text_figure" and not pictures:
                page_errors.append("text_figure has no picture asset")
            if layout == "media_gallery" and len(pictures) < len(page.get("media_items", ())):
                page_errors.append(
                    f"media_gallery has {len(pictures)} pictures for {len(page.get('media_items', ()))} slots"
                )
            if layout == "module_media" and len(pictures) < len(page.get("modules", ())):
                page_errors.append(
                    f"module_media has {len(pictures)} pictures for {len(page.get('modules', ()))} modules"
                )
            expected_frames = self._expected_editable_frames(page)
            if content_page and len(editable_frames) < expected_frames:
                page_errors.append(
                    f"only {len(editable_frames)} separately editable frame objects; require {expected_frames}"
                )
            if content_page and any(
                (shape.width * shape.height) / (presentation.slide_width * presentation.slide_height) > 0.72
                for shape in pictures
            ):
                page_errors.append("content page contains an unjustified near-full-slide picture")
            errors.extend(f"{page.get('page_id')}: {message}" for message in page_errors)
            slides.append({
                "slide_number": index + 1,
                "page_id": page.get("page_id"),
                "layout": layout,
                "template_reference": reference,
                "density_target": "high" if content_page else "intentional_sparse",
                "density_units": density_units,
                "visible_module_count": len(modules),
                "component_inventory": {
                    "editable_text_objects": len(text_shapes),
                    "native_non_picture_objects": len(native_shapes),
                    "editable_frame_objects": len(editable_frames),
                    "pictures": len(pictures),
                },
                "editable_information_layer_pass": len(text_shapes) >= (5 if content_page else 1),
                "template_identity_bound": bool(reference) if content_page else True,
                "page_errors": page_errors,
            })
        return {
            "schema_version": 1,
            "composition_mode": dynamic_plan.get("composition_mode"),
            "template": template,
            "template_identity": grammar.get("identity", {}),
            "visual_system": {
                "fonts": visual_system.get("fonts", {}),
                "typography": visual_system.get("typography", {}),
                "colors": visual_system.get("colors", {}),
            },
            "qa_expectations": {
                "dual_gate_required": True,
                "template_identity_required": True,
                "all_key_text_editable": True,
                "full_render_required": True,
            },
            "passed": not errors,
            "errors": errors,
            "slides": slides,
        }

    @staticmethod
    def _expected_editable_frames(page: dict) -> int:
        layout = page.get("layout")
        if layout == "text_figure":
            return 3
        if layout == "media_gallery":
            return len(page.get("media_items", ()))
        if layout == "module_media":
            return len(page.get("modules", ())) * 2
        if layout == "points":
            return len(page.get("points", ())) * 2
        if layout == "process":
            return len(page.get("steps", ())) * 2
        if layout == "architecture":
            columns = page.get("architecture", {}).get("columns", ())
            nodes = sum(len(column.get("nodes", ())) for column in columns)
            return len(columns) * 2 + nodes
        return 1
