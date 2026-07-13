"""Adapt V2 page and layout contracts to the native PPTX renderer."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .layout import LayoutDecision
from .planning import PagePlan


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
    ) -> Path:
        image_content = image_content or {}
        pages = []
        for page in page_plan.pages:
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
            pages.append({
                "page_id": page.page_id,
                "section": page.section,
                "render_mode": decision.render_mode,
                "source_slide_index": decision.source_slide_index,
                "text_bindings": [
                    {"shape_id": shape_id, "content": content}
                    for shape_id, content in zip(text_shape_ids, values)
                ],
                "image_bindings": image_bindings,
                "speaker_notes": self._speaker_notes(page),
            })
        payload = {
            "confirmed": confirmed,
            "template_mode": "template_native",
            "sections": list(page_plan.sections),
            "pages": pages,
        }
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
