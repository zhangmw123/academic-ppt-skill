"""Compile evidence-bound page content into dense editable slide compositions."""

from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path

from .autobuild import CompleteContentPackage
from .planning import PagePlan, PlannedPage


SPACE = re.compile(r"\s+")
SPLIT = re.compile(r"[。！？；;!?]+|(?<!\d)\.(?!\d)")
ARCHITECTURE_HINTS = ("架构", "系统", "链路", "流程", "路线", "框架", "方案", "知识图谱", "architecture", "pipeline")
INTERNAL_LABELS = (
    "证据、读图与边界",
    "核心判断",
    "证据依据",
    "机制解释",
    "边界与行动",
    "读图重点",
)


def text_units(value: str) -> float:
    """Count CJK as one unit and Latin text compactly for density checks."""
    return sum(1.0 if "\u4e00" <= char <= "\u9fff" else 0.55 for char in value if not char.isspace())


def _clean(value: str) -> str:
    return SPACE.sub(" ", str(value)).strip()


def _sentences(*values: str, limit: int = 5) -> list[str]:
    items: list[str] = []
    for value in values:
        for item in SPLIT.split(_clean(value)):
            item = item.strip(" ，、:：")
            if text_units(item) >= 6 and item not in items:
                items.append(item)
            if len(items) >= limit:
                return items
    return items


def _headline_detail(value: str, *, fallback: str = "要点") -> dict[str, str]:
    """Split authored evidence into a compact heading and its explanation."""
    cleaned = _clean(value)
    for separator in ("：", ":", "｜", "|"):
        if separator in cleaned:
            headline, detail = (_clean(item) for item in cleaned.split(separator, 1))
            if headline and detail:
                return {"title": headline[:18], "body": detail}
    for separator in ("，", ","):
        if separator in cleaned:
            headline, detail = (_clean(item) for item in cleaned.split(separator, 1))
            if 2 <= text_units(headline) <= 20 and text_units(detail) >= 6:
                return {"title": headline[:18], "body": detail}
    headline = cleaned[:16].rstrip("，,。；; ") or fallback
    return {"title": headline, "body": cleaned}


def _panel_boxes(archetype: dict) -> list[dict]:
    """Return meaningful template content panels, deduplicated by geometry."""
    candidates = []
    for item in (*archetype.get("picture_slots", ()), *archetype.get("decorative_assets", ())):
        box = item.get("box", {})
        area = float(item.get("area", float(box.get("width", 0)) * float(box.get("height", 0))))
        if float(box.get("top", 0)) < 0.18 or not 0.025 <= area <= 0.30:
            continue
        key = tuple(round(float(box.get(name, 0)), 3) for name in ("left", "top", "width", "height"))
        if key not in {entry[0] for entry in candidates}:
            candidates.append((key, box))
    return [box for _, box in candidates]


@dataclass(frozen=True)
class CompositionQualityResult:
    passed: bool
    errors: tuple[str, ...]
    observations: tuple[str, ...] = ()


class DynamicCompositionCompiler:
    """Create editable, content-driven pages while retaining template visual DNA."""

    def compile(
        self,
        plan: PagePlan,
        package: CompleteContentPackage,
        *,
        visual_system_path: Path | str,
        template_grammar_path: Path | str,
        asset_base_dir: Path | str,
        confirmed: bool,
        footer: str = "",
    ) -> dict:
        grammar = json.loads(Path(template_grammar_path).read_text(encoding="utf-8"))
        pages = []
        for index, page in enumerate(plan.pages):
            values = [_clean(value) for value in package.text_content.get(page.page_id, ()) if _clean(value)]
            images = [str(Path(value).resolve()) for value in package.image_content.get(page.page_id, ())]
            if index == 0:
                composed = self._cover(page, values)
            elif index == len(plan.pages) - 1:
                composed = self._ending(page, values)
            elif images:
                composed = self._text_figure(page, values, images[0])
            elif self._is_architecture(page):
                composed = self._architecture(page, values)
            elif page.visual_strategy == "native_diagram":
                composed = self._process(page, values)
            else:
                composed = self._points(page, values)
            composed.update({
                "page_id": page.page_id,
                "section": page.section,
                "speaker_notes": self._speaker_notes(page),
            })
            template_reference = self._template_reference(composed, grammar)
            if template_reference:
                composed["template_reference"] = template_reference
                composed["scaffold_slide"] = template_reference["source_slide_index"]
                if composed.get("layout") not in {"cover", "ending"}:
                    composed["use_template_scaffold"] = (
                        "structure"
                        if grammar.get("identity", {}).get("panel_mode") == "image_scaffold"
                        else "identity"
                    )
            pages.append(composed)
        payload = {
            "schema_version": 2,
            "confirmed": confirmed,
            "composition_mode": "template_hybrid_editable",
            "sections": list(plan.sections),
            "footer": footer,
            "visual_system": str(Path(visual_system_path).resolve()),
            "template_grammar": str(Path(template_grammar_path).resolve()),
            "asset_base_dir": str(Path(asset_base_dir).resolve()),
            "pages": pages,
        }
        quality = CompositionQualityGate().inspect(payload)
        if not quality.passed:
            raise ValueError("composition contract failed: " + "; ".join(quality.errors))
        return payload

    @staticmethod
    def _cover(page: PlannedPage, values: list[str]) -> dict:
        return {
            "layout": "cover",
            "title": values[0] if values else page.title,
            "subtitle": values[1] if len(values) > 1 else page.claim_text,
            "metadata": [],
            "use_template_scaffold": True,
        }

    @staticmethod
    def _ending(page: PlannedPage, values: list[str]) -> dict:
        return {
            "layout": "ending",
            "title": values[0] if values else page.title,
            "subtitle": values[1] if len(values) > 1 else page.interpretation,
            "use_template_scaffold": True,
        }

    @staticmethod
    def _text_figure(page: PlannedPage, values: list[str], image: str) -> dict:
        body = values[1:]
        bullet_values = _sentences(*body, page.claim_text, page.interpretation, limit=4)
        bullets = [_headline_detail(value) for value in bullet_values]
        while len(bullets) < 3:
            candidates = (page.claim_text, page.interpretation, page.next_link)
            candidate = _clean(candidates[len(bullets) % len(candidates)])
            module = _headline_detail(candidate)
            if candidate and module not in bullets:
                bullets.append(module)
            else:
                break
        source_page = re.search(r"_p(\d+)", Path(image).stem, re.IGNORECASE)
        return {
            "layout": "text_figure",
            "title": page.title,
            "lead": _headline_detail(page.claim_text, fallback="核心要点")["title"],
            "bullets": bullets,
            "image": image,
            "image_fit": "contain",
            "caption": f"论文原图 | PDF 第{int(source_page.group(1))}页" if source_page else "论文原图",
            "page_conclusion": page.interpretation,
        }

    @staticmethod
    def _process(page: PlannedPage, values: list[str]) -> dict:
        steps = _sentences(*values[1:], page.claim_text, limit=5)
        if len(steps) < 3:
            steps = _sentences(page.claim_text, page.interpretation, page.next_link, limit=5)
        return {
            "layout": "process",
            "title": page.title,
            "steps": [_headline_detail(step, fallback=f"步骤 {index + 1}") for index, step in enumerate(steps[:5])],
            "page_conclusion": page.interpretation,
        }

    @staticmethod
    def _architecture(page: PlannedPage, values: list[str]) -> dict:
        node_values = _sentences(*values[1:], page.claim_text, page.interpretation, limit=6)
        while len(node_values) < 4:
            node_values.extend(_sentences(page.next_link, page.interpretation, limit=4))
            node_values = list(dict.fromkeys(node_values))
            if len(node_values) < 4:
                node_values.append(f"验证环节 {len(node_values) + 1}")
        modules = [_headline_detail(value) for value in node_values]
        column_count = 3 if len(modules) >= 4 else 2
        columns = []
        node_ids = []
        for column_index in range(column_count):
            selected = modules[column_index::column_count]
            column_nodes = []
            for node_index, module in enumerate(selected):
                node_id = f"N{column_index + 1}_{node_index + 1}"
                node_ids.append(node_id)
                column_nodes.append({
                    "id": node_id,
                    "label": module["body"],
                })
            columns.append({"title": selected[0]["title"], "nodes": column_nodes})
        edges = [
            {"source": source, "target": target}
            for source, target in zip(node_ids, node_ids[1:])
        ]
        return {
            "layout": "architecture",
            "title": page.title,
            "architecture": {"columns": columns, "edges": edges},
            "page_conclusion": page.interpretation,
        }

    @staticmethod
    def _points(page: PlannedPage, values: list[str]) -> dict:
        bodies = _sentences(*values[1:], page.claim_text, page.interpretation, page.next_link, limit=4)
        while len(bodies) < 4:
            bodies.append((page.claim_text, page.interpretation, page.next_link)[len(bodies) % 3])
        return {
            "layout": "points",
            "title": page.title,
            "points": [_headline_detail(body, fallback=f"要点 {index + 1}") for index, body in enumerate(bodies[:4])],
            "page_conclusion": page.claim_text,
        }

    @staticmethod
    def _is_architecture(page: PlannedPage) -> bool:
        lowered = page.title.casefold()
        return page.visual_strategy == "native_diagram" and any(hint in lowered for hint in ARCHITECTURE_HINTS)

    @staticmethod
    def _speaker_notes(page: PlannedPage) -> str:
        return "\n".join((
            f"讲解：{page.interpretation}",
            f"转场：{page.next_link}",
            f"建议时长：{page.time_seconds} 秒",
        ))

    @staticmethod
    def _template_reference(page: dict, grammar: dict) -> dict | None:
        layout = page.get("layout")
        if layout in {"cover", "ending"}:
            desired_roles = (layout,)
            desired_signatures = (layout,)
        elif layout == "text_figure":
            desired_roles = ("text_figure", "gallery", "comparison")
            desired_signatures = ("text_figure_right", "figure_text_right")
        elif layout in {"process", "architecture"}:
            count = len(page.get("steps", ())) or sum(
                len(column.get("nodes", ())) for column in page.get("architecture", {}).get("columns", ())
            )
            names = {3: "three_columns", 4: "four_columns", 5: "five_columns"}
            preferred = names.get(min(5, max(3, count)), "three_columns")
            desired_roles = ("process", "comparison", "gallery", "title_body")
            desired_signatures = (preferred, "three_columns", "four_columns", "five_columns")
        elif layout == "points":
            desired_roles = ("comparison", "grid", "gallery", "title_body")
            desired_signatures = ("four_columns", "three_columns", "image_grid", "text_figure_right")
        else:
            return None
        candidates = grammar.get("archetypes", ())
        target_panels = 0
        if layout == "points":
            target_panels = 4
        elif layout == "process":
            target_panels = len(page.get("steps", ()))
        elif layout == "architecture":
            target_panels = len(page.get("architecture", {}).get("columns", ()))

        def score(item: dict) -> float:
            signature = item.get("layout_signature")
            role = item.get("role")
            signature_score = 30 - desired_signatures.index(signature) * 4 if signature in desired_signatures else 0
            role_score = 4 if role in desired_roles or role in desired_signatures else 0
            panel_score = 0
            if target_panels:
                panels = _panel_boxes(item)
                panel_score = 24 - abs(len(panels) - target_panels) * 8
                if layout == "points" and len(panels) >= 4:
                    rows = {round(float(box.get("top", 0)), 1) for box in panels[:4]}
                    panel_score += 4 if len(rows) in {1, 2} else 0
            return signature_score + role_score + panel_score

        match = max(candidates, key=score, default=None)
        if not match:
            return None
        return {
            "source_slide_index": int(match["slide_index"]),
            "source_role": match.get("role"),
            "layout_signature": match.get("layout_signature"),
            "panel_count": len(_panel_boxes(match)),
        }


class CompositionQualityGate:
    """Reject sparse or incomplete editable compositions before rendering."""

    def inspect(self, payload: dict) -> CompositionQualityResult:
        errors: list[str] = []
        observations: list[str] = []
        pages = payload.get("pages", ())
        for index, page in enumerate(pages):
            page_id = page.get("page_id", f"page-{index + 1}")
            layout = page.get("layout")
            if layout in {"cover", "ending", "section", "agenda"}:
                continue
            reference = page.get("template_reference")
            if not isinstance(reference, dict) or not reference.get("source_slide_index") or not reference.get("layout_signature"):
                errors.append(f"{page_id}: content page is not bound to a template layout archetype")
            if page.get("use_template_scaffold") not in {"identity", "structure"}:
                errors.append(f"{page_id}: template structure layer is not enabled")
            modules = [value for value in self._modules(page) if _clean(value)]
            leaked = sorted({label for label in INTERNAL_LABELS for value in modules if label in value})
            if leaked:
                errors.append(f"{page_id}: internal composition labels leaked into visible content: {leaked}")
            if len(modules) < 3:
                errors.append(f"{page_id}: content page has only {len(modules)} visible modules")
            units = sum(text_units(value) for value in modules)
            if units < 55:
                errors.append(f"{page_id}: visible content density is {units:.0f} units; require at least 55")
            if layout == "text_figure":
                if not page.get("image"):
                    errors.append(f"{page_id}: text_figure requires an evidence image")
                if len(page.get("bullets", ())) < 3:
                    errors.append(f"{page_id}: text_figure requires at least three reading/interpretation bullets")
            elif layout == "process" and not 3 <= len(page.get("steps", ())) <= 5:
                errors.append(f"{page_id}: process requires three to five editable steps")
            elif layout == "process" and any(
                not isinstance(step, dict) or not _clean(step.get("title", "")) or not _clean(step.get("body", ""))
                for step in page.get("steps", ())
            ):
                errors.append(f"{page_id}: every process step requires a specific heading and explanation")
            elif layout == "points" and len(page.get("points", ())) != 4:
                errors.append(f"{page_id}: points layout requires four editable evidence modules")
            elif layout == "points" and any(
                not _clean(item.get("title", "")) or not _clean(item.get("body", ""))
                for item in page.get("points", ())
            ):
                errors.append(f"{page_id}: every point requires a specific heading and explanation")
            elif layout == "architecture":
                columns = page.get("architecture", {}).get("columns", ())
                node_count = sum(len(column.get("nodes", ())) for column in columns)
                if len(columns) < 2 or node_count < 4:
                    errors.append(f"{page_id}: architecture requires at least two columns and four editable nodes")
            if units > 210:
                observations.append(f"{page_id}: dense composition has {units:.0f} units; inspect readability")
        return CompositionQualityResult(not errors, tuple(errors), tuple(observations))

    @staticmethod
    def _modules(page: dict) -> list[str]:
        layout = page.get("layout")
        if layout == "text_figure":
            bullets = [
                f"{item.get('title', '')} {item.get('body', '')}" if isinstance(item, dict) else str(item)
                for item in page.get("bullets", ())
            ]
            return [page.get("lead", ""), *bullets, page.get("page_conclusion", "")]
        if layout == "process":
            return [
                f"{item.get('title', '')} {item.get('body', '')}" if isinstance(item, dict) else str(item)
                for item in page.get("steps", ())
            ] + [page.get("page_conclusion", "")]
        if layout == "points":
            return [
                f"{item.get('title', '')} {item.get('body', '')}"
                for item in page.get("points", ())
            ]
        if layout == "architecture":
            return [
                f"{node.get('label', '')} {node.get('detail', '')}"
                for column in page.get("architecture", {}).get("columns", ())
                for node in column.get("nodes", ())
            ] + [page.get("page_conclusion", "")]
        if layout == "comparison":
            return [
                " ".join((item.get("title", ""), item.get("lead", ""), *item.get("bullets", ())))
                for item in page.get("columns", ())
            ]
        return []
