"""Adapt authored page payload density to a template's visible native capacity."""

from __future__ import annotations

from dataclasses import replace

from .autobuild import CompleteContentPackage


def adapt_native_text_capacity(
    package: CompleteContentPackage,
    capacity: int,
) -> CompleteContentPackage:
    if capacity < 4:
        raise ValueError("a reusable scientific template needs at least four visible text slots")
    drafts = []
    text_content = dict(package.text_content)
    for draft in package.drafts:
        current = int(draft.component_requirements.get("text", 0))
        if draft.visual_strategy != "native_diagram" or current <= capacity:
            drafts.append(draft)
            continue
        target = min(current, capacity)
        values = text_content[draft.page_id]
        middle = "；".join(value.strip(" ；") for value in values[1:-2] if value.strip())
        chunk_count = target - 3
        chunks = _split_evenly(middle, chunk_count)
        text_content[draft.page_id] = [values[0], *chunks, values[-2], values[-1]]
        requirements = dict(draft.component_requirements)
        requirements["text"] = target
        drafts.append(replace(draft, component_requirements=requirements))
    return replace(package, drafts=tuple(drafts), text_content=text_content)


def adapt_source_figure_text_capacity(
    package: CompleteContentPackage,
    capacity: int,
) -> CompleteContentPackage:
    if capacity < 2:
        raise ValueError("a source-figure page needs at least a title and one evidence text slot")
    drafts = []
    text_content = dict(package.text_content)
    for draft in package.drafts:
        current = int(draft.component_requirements.get("text", 0))
        if draft.visual_strategy != "source_figure" or current <= capacity:
            drafts.append(draft)
            continue
        values = text_content[draft.page_id]
        text_content[draft.page_id] = [values[0], "\n".join(values[1:])]
        requirements = dict(draft.component_requirements)
        requirements["text"] = 2
        drafts.append(replace(draft, component_requirements=requirements))
    return replace(package, drafts=tuple(drafts), text_content=text_content)


def _split_evenly(text: str, count: int) -> list[str]:
    if count <= 0:
        return []
    if not text:
        return ["证据要点" for _ in range(count)]
    size = max(1, (len(text) + count - 1) // count)
    chunks = [text[index * size:(index + 1) * size].strip(" ；") for index in range(count)]
    return [chunk or "证据要点" for chunk in chunks]
