"""Adapt page and layout contracts to the native PPTX renderer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .layout import LayoutDecision
from .planning import PagePlan
from .templates import TemplateCapabilityGraph


class NativeRenderAdapter:
    """Write a legacy-compatible native layout plan and execute its renderer."""

    def write_layout_plan(
        self,
        page_plan: PagePlan,
        decisions: dict[str, LayoutDecision],
        text_content: dict[str, list[str]],
        output_path: Path | str,
        *,
        confirmed: bool,
        image_content: dict[str, list[Path | str]] | None = None,
        page_ids: set[str] | None = None,
        template_grammar: Path | str | None = None,
        template_graph: TemplateCapabilityGraph | None = None,
        remove_shape_ids: dict[str, list[int]] | None = None,
        font_policy: dict[str, str] | None = None,
    ) -> Path:
        image_content = image_content or {}
        remove_shape_ids = remove_shape_ids or {}
        pages = []
        for page_index, page in enumerate(page_plan.pages):
            if page_ids is not None and page.page_id not in page_ids:
                continue
            try:
                decision = decisions[page.page_id]
            except KeyError as exc:
                raise ValueError(f"missing layout decision: {page.page_id}") from exc
            if decision.render_mode not in {"template_native", "template_adaptive"}:
                raise ValueError(f"native renderer cannot render {decision.render_mode}: {page.page_id}")
            text_shape_ids = decision.component_bindings.get("text", ())
            values = text_content.get(page.page_id, [])
            if len(values) > len(text_shape_ids):
                raise ValueError(f"too many text values for native bindings: {page.page_id}")
            picture_shape_ids = decision.component_bindings.get("picture", ())
            images = image_content.get(page.page_id, [])
            if len(images) > len(picture_shape_ids):
                raise ValueError(f"too many images for native bindings: {page.page_id}")
            image_bindings = []
            for shape_id, image_path in zip(picture_shape_ids, images):
                resolved_image_path = Path(image_path).resolve()
                if not resolved_image_path.is_file():
                    raise FileNotFoundError(resolved_image_path)
                image_bindings.append({
                    "path": str(resolved_image_path),
                    "replace_shape_id": shape_id,
                    "fit": "contain",
                })
            text_bindings = []
            adjustments = []
            geometry_by_id = {
                component.shape_id: component.geometry
                for slide in (template_graph.slides if template_graph else ())
                if slide.slide_index == decision.source_slide_index
                for component in slide.components
            }
            for value_index, (shape_id, content) in enumerate(zip(text_shape_ids, values)):
                resolved_content = str(content)
                geometry = geometry_by_id.get(shape_id)
                if geometry:
                    resolved_content, font_size = self._fit_text(
                        resolved_content,
                        geometry,
                        value_index == 0,
                        is_cover_title=value_index == 0 and page_index == 0,
                    )
                    adjustments.append({"shape_id": shape_id, "font_size_pt": font_size})
                text_bindings.append({"shape_id": shape_id, "content": resolved_content})
            pages.append({
                "page_id": page.page_id,
                "section": page.section,
                "render_mode": decision.render_mode,
                "source_slide_index": decision.source_slide_index,
                "text_bindings": text_bindings,
                "image_bindings": image_bindings,
                "adjustments": adjustments,
                "remove_shape_ids": remove_shape_ids.get(page.page_id, []),
                "speaker_notes": self._speaker_notes(page),
                "navigation_enabled": page_index not in {0, len(page_plan.pages) - 1},
            })
        payload = {
            "confirmed": confirmed,
            "template_mode": "template_native",
            "deck_scope": "sample" if page_ids is not None else page_plan.deck_scope,
            "sections": list(page_plan.sections),
            "replace_raster_navigation": True,
            "pages": pages,
        }
        if font_policy:
            payload["font_policy"] = dict(font_policy)
        if template_grammar is not None:
            payload["template_grammar"] = str(Path(template_grammar).resolve())
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output.resolve()

    def render(self, layout_plan_path: Path | str, template_path: Path | str, output_path: Path | str) -> Path:
        skill_root = Path(__file__).resolve().parents[1]
        renderer = skill_root / "scripts" / "render_pptx.py"
        layout_plan = Path(layout_plan_path).resolve()
        template = Path(template_path).resolve()
        output = Path(output_path).resolve()
        subprocess.run(
            [
                sys.executable,
                str(renderer),
                "--layout-plan", str(layout_plan),
                "--template", str(template),
                "--output", str(output),
            ],
            cwd=skill_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if not output.is_file():
            raise RuntimeError(f"native renderer did not create output: {output}")
        return output

    @staticmethod
    def _speaker_notes(page) -> str:
        return "\n".join((
            f"讲解：{page.interpretation}",
            f"转场：{page.next_link}",
            f"建议时长：{page.time_seconds} 秒",
        ))

    @staticmethod
    def _fit_text(
        content: str,
        geometry: dict[str, int],
        is_title: bool,
        *,
        is_cover_title: bool = False,
    ) -> tuple[str, float]:
        width_pt = geometry["width"] / 12700
        height_pt = geometry["height"] / 12700
        if is_cover_title:
            minimum, maximum = 28.0, 32.0
        elif is_title:
            minimum, maximum = 20.0, 24.0
        else:
            minimum, maximum = 11.0, 13.0
        units = max(1.0, sum(1.0 if "\u4e00" <= char <= "\u9fff" else 0.55 for char in content))
        estimated = ((width_pt * height_pt) / max(units * 0.96, 1)) ** 0.5
        font_size = max(minimum, min(maximum, estimated))
        capacity = max(4.0, (width_pt / (font_size * 0.9)) * (height_pt / (font_size * 1.2)))
        if units > capacity:
            retained = []
            used = 0.0
            for char in content:
                cost = 1.0 if "\u4e00" <= char <= "\u9fff" else 0.55
                if used + cost > max(1.0, capacity - 1.0):
                    break
                retained.append(char)
                used += cost
            content = "".join(retained).rstrip() + "…"
        return content, round(font_size, 1)
