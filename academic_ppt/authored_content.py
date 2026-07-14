"""Validate and apply an agent-authored complete slide content plan."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .autobuild import CompleteContentPackage


def _figure_for_source_page(package: CompleteContentPackage, source_page: int) -> str:
    matches = []
    for manifest_path in package.figure_manifests:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        for item in payload.get("items", ()):
            path = item.get("path")
            if item.get("accepted") and path and int(item.get("source_page", 0)) == source_page:
                matches.append(item)
    if not matches:
        raise ValueError(f"no accepted source figure found on PDF page {source_page}")
    selected = max(matches, key=lambda item: int(item.get("pixel_width", 0)) * int(item.get("pixel_height", 0)))
    return str(Path(selected["path"]).resolve())


def apply_authored_content(
    package: CompleteContentPackage,
    plan_path: Path | str,
    *,
    expected_scene: str,
) -> CompleteContentPackage:
    payload = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("authored content plan requires schema_version 1")
    if payload.get("scene") != expected_scene:
        raise ValueError(f"authored content scene mismatch: expected {expected_scene}")
    items = payload.get("pages")
    if not isinstance(items, list):
        raise ValueError("authored content plan requires a pages array")
    by_id = {item.get("page_id"): item for item in items if isinstance(item, dict)}
    expected_ids = [draft.page_id for draft in package.drafts]
    if set(by_id) != set(expected_ids) or len(items) != len(expected_ids):
        raise ValueError("authored content plan must cover every final page exactly once")

    drafts = []
    text_content = dict(package.text_content)
    image_content = dict(package.image_content)
    for draft in package.drafts:
        item = by_id[draft.page_id]
        required = ("title", "claim", "interpretation", "next_link", "text")
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError(f"{draft.page_id}: missing authored fields {missing}")
        values = item["text"]
        if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError(f"{draft.page_id}: text must be a non-empty string array")
        expected_text_count = int(draft.component_requirements.get("text", 0))
        if len(values) != expected_text_count:
            raise ValueError(
                f"{draft.page_id}: authored text count {len(values)} does not match component contract {expected_text_count}"
            )
        if values[0].strip() != str(item["title"]).strip():
            raise ValueError(f"{draft.page_id}: first text value must equal the authored title")
        suppress_image = item.get("suppress_image") is True
        image_source_page = item.get("image_source_page")
        if suppress_image and image_source_page is not None:
            raise ValueError(f"{draft.page_id}: suppress_image and image_source_page are mutually exclusive")
        requirements = dict(draft.component_requirements)
        visual_strategy = str(item.get("visual_strategy") or draft.visual_strategy)
        if suppress_image:
            image_content.pop(draft.page_id, None)
            requirements.pop("picture", None)
            if "visual_strategy" not in item:
                visual_strategy = "text_only"
        elif image_source_page is not None:
            image_content[draft.page_id] = [_figure_for_source_page(package, int(image_source_page))]
            requirements["picture"] = 1
            if "visual_strategy" not in item:
                visual_strategy = "source_figure"
        drafts.append(replace(
            draft,
            title=str(item["title"]).strip(),
            claim_text=str(item["claim"]).strip(),
            interpretation=str(item["interpretation"]).strip(),
            next_link=str(item["next_link"]).strip(),
            visual_strategy=visual_strategy,
            component_requirements=requirements,
        ))
        text_content[draft.page_id] = [value.strip() for value in values]

    titles = [draft.title.casefold() for draft in drafts]
    claims = [draft.claim_text.casefold() for draft in drafts]
    if len(set(titles)) != len(titles):
        raise ValueError("authored content plan contains repeated page titles")
    if len(set(claims)) != len(claims):
        raise ValueError("authored content plan contains repeated claims")
    return replace(
        package,
        drafts=tuple(drafts),
        text_content=text_content,
        image_content=image_content,
    )
