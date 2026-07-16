import json
from dataclasses import replace
from pathlib import Path

import pytest

from academic_ppt.authored_content import apply_authored_content
from academic_ppt.autobuild import CompleteContentDraft, CompleteContentPackage
from academic_ppt.content_adaptation import adapt_native_text_capacity, adapt_source_figure_text_capacity
from academic_ppt.planning import ScenePlanContract


def _package() -> CompleteContentPackage:
    drafts = tuple(
        CompleteContentDraft(
            page_id=f"P{index:03d}", section="Section", title=f"Old {index}",
            question_answered="Question", claim_text=f"Old claim {index}", evidence_ids=(f"E{index}",),
            interpretation="Old", next_link="Old next", time_seconds=60,
            visual_strategy="text_only", component_requirements={"text": 2},
        )
        for index in (1, 2)
    )
    return CompleteContentPackage(
        sections=("Section",), drafts=drafts,
        scene_contract=ScenePlanContract("complete", "published", "default", 2),
        text_content={draft.page_id: [draft.title, draft.claim_text] for draft in drafts},
        image_content={}, figure_manifests=(),
    )


def test_apply_authored_content_requires_complete_unique_plan(tmp_path: Path):
    path = tmp_path / "content.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "scene": "组会-文献精读",
        "pages": [
            {"page_id": "P001", "title": "Title 1", "claim": "Claim 1", "interpretation": "Read 1", "next_link": "Next 1", "text": ["Title 1", "Body 1"]},
            {"page_id": "P002", "title": "Title 2", "claim": "Claim 2", "interpretation": "Read 2", "next_link": "Next 2", "text": ["Title 2", "Body 2"]},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    result = apply_authored_content(_package(), path, expected_scene="组会-文献精读")
    assert result.drafts[0].title == "Title 1"
    assert result.text_content["P002"] == ["Title 2", "Body 2"]

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["pages"].pop()
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="every final page"):
        apply_authored_content(_package(), path, expected_scene="组会-文献精读")


def test_adapt_native_text_capacity_preserves_title_interpretation_and_transition():
    package = _package()
    draft = replace(
        package.drafts[0],
        visual_strategy="native_diagram",
        component_requirements={"text": 6},
    )
    package = replace(
        package,
        drafts=(draft, package.drafts[1]),
        text_content={
            **package.text_content,
            "P001": ["Title", "Step 1", "Step 2", "Step 3", "Interpretation", "Next"],
        },
    )
    result = adapt_native_text_capacity(package, 4)
    assert result.drafts[0].component_requirements["text"] == 4
    assert result.text_content["P001"][0] == "Title"
    assert result.text_content["P001"][-2:] == ["Interpretation", "Next"]


def test_adapt_source_figure_capacity_merges_claim_and_interpretation():
    package = _package()
    draft = replace(
        package.drafts[0],
        visual_strategy="source_figure",
        component_requirements={"text": 3, "picture": 1},
    )
    package = replace(
        package,
        drafts=(draft, package.drafts[1]),
        text_content={**package.text_content, "P001": ["Title", "Claim", "Interpretation"]},
    )
    result = adapt_source_figure_text_capacity(package, 2)
    assert result.drafts[0].component_requirements["text"] == 2
    assert result.text_content["P001"] == ["Title", "Claim\nInterpretation"]


def test_authored_content_can_suppress_an_irrelevant_extracted_figure(tmp_path: Path):
    package = _package()
    package = replace(
        package,
        image_content={"P001": ["irrelevant.png"]},
    )
    path = tmp_path / "content.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "scene": "组会-文献精读",
        "pages": [
            {"page_id": "P001", "title": "Title 1", "claim": "Claim 1", "interpretation": "Read 1", "next_link": "Next 1", "text": ["Title 1", "Body 1"], "suppress_image": True},
            {"page_id": "P002", "title": "Title 2", "claim": "Claim 2", "interpretation": "Read 2", "next_link": "Next 2", "text": ["Title 2", "Body 2"]},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    result = apply_authored_content(package, path, expected_scene="组会-文献精读")

    assert "P001" not in result.image_content
    assert result.drafts[0].visual_strategy == "text_only"


def test_authored_content_can_bind_an_exact_pdf_figure_page(tmp_path: Path):
    figure = tmp_path / "figure_p42.png"
    figure.write_bytes(b"image")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"items": [{
        "accepted": True,
        "source_page": 42,
        "path": str(figure),
        "pixel_width": 1200,
        "pixel_height": 700,
    }]}), encoding="utf-8")
    package = replace(_package(), figure_manifests=(str(manifest),))
    path = tmp_path / "content.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "scene": "组会-文献精读",
        "pages": [
            {"page_id": "P001", "title": "Title 1", "claim": "Claim 1", "interpretation": "Read 1", "next_link": "Next 1", "text": ["Title 1", "Body 1"], "image_source_page": 42},
            {"page_id": "P002", "title": "Title 2", "claim": "Claim 2", "interpretation": "Read 2", "next_link": "Next 2", "text": ["Title 2", "Body 2"]},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    result = apply_authored_content(package, path, expected_scene="组会-文献精读")

    assert result.image_content["P001"] == [str(figure.resolve())]
    assert result.drafts[0].visual_strategy == "source_figure"
    assert result.drafts[0].component_requirements["picture"] == 1


def test_authored_content_can_bind_one_source_figure_per_semantic_module(tmp_path: Path):
    items = []
    expected = []
    for page_number in (3, 4, 5, 6, 7):
        figure = tmp_path / f"figure_p{page_number}.png"
        figure.write_bytes(b"image")
        expected.append(str(figure.resolve()))
        items.append({
            "accepted": True,
            "source_page": page_number,
            "path": str(figure),
            "pixel_width": 1200,
            "pixel_height": 700,
        })
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"source": str(tmp_path / "paper.pdf"), "items": items}), encoding="utf-8")
    package = replace(_package(), figure_manifests=(str(manifest),))
    path = tmp_path / "content.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "scene": "组会-文献精读",
        "pages": [
            {
                "page_id": "P001", "title": "Title 1", "claim": "Claim 1",
                "interpretation": "Read 1", "next_link": "Next 1",
                "text": ["Title 1", "Body 1"],
                "image_source_pages": [3, 4, 5, 6, 7], "media_scope": "module",
            },
            {
                "page_id": "P002", "title": "Title 2", "claim": "Claim 2",
                "interpretation": "Read 2", "next_link": "Next 2",
                "text": ["Title 2", "Body 2"],
            },
        ],
    }, ensure_ascii=False), encoding="utf-8")

    result = apply_authored_content(package, path, expected_scene="组会-文献精读")

    assert result.image_content["P001"] == expected
    assert result.drafts[0].media_scope == "module"
    assert result.drafts[0].media_layout == "one_per_module"
    assert result.drafts[0].visual_strategy == "module_media"
    assert result.drafts[0].component_requirements["picture"] == 5
