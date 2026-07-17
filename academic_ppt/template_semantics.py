"""Compile low-level template grammar into stable semantic template contracts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SPEC_SCHEMA_VERSION = 1
EXCLUSIVE_RENDER_MODES = ("native_reuse", "full_reconstruction")
REMOVAL_POLICY = "remove_complete_ownership_group"
MEDIA_PROVENANCE_FIELDS = ("source_id", "source_path", "pdf_page", "semantic_use")

TYPOGRAPHY_POLICY = {
    "cover_title": {"min_pt": 28.0, "max_pt": 32.0, "target_pt": 30.0},
    "cover_subtitle": {"min_pt": 14.0, "max_pt": 18.0, "target_pt": 16.0},
    "page_title": {"min_pt": 20.0, "max_pt": 24.0, "target_pt": 22.0},
    "module_heading": {"min_pt": 13.0, "max_pt": 16.0, "target_pt": 14.0},
    "body": {"min_pt": 11.0, "max_pt": 13.0, "target_pt": 12.0},
    "caption": {"min_pt": 8.5, "max_pt": 10.0, "target_pt": 9.0},
    "normal_content_min_pt": 10.5,
    "overflow_order": ["shorten", "split_module", "select_larger_archetype", "reflow"],
    "unbounded_shrink_forbidden": True,
}


@dataclass(frozen=True)
class TemplateSpecValidationResult:
    passed: bool
    errors: tuple[str, ...]
    observations: tuple[str, ...] = ()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _center(box: dict) -> tuple[float, float]:
    return box["left"] + box["width"] / 2, box["top"] + box["height"] / 2


def _union(boxes: Iterable[dict], fallback: dict | None = None) -> dict:
    values = list(boxes)
    if not values:
        return dict(fallback or {"left": 0.05, "top": 0.2, "width": 0.9, "height": 0.68})
    left = min(box["left"] for box in values)
    top = min(box["top"] for box in values)
    right = max(box["left"] + box["width"] for box in values)
    bottom = max(box["top"] + box["height"] for box in values)
    return {
        "left": round(left, 4),
        "top": round(top, 4),
        "width": round(right - left, 4),
        "height": round(bottom - top, 4),
    }


def _box_distance(first: dict, second: dict) -> float:
    x1, y1 = _center(first)
    x2, y2 = _center(second)
    return math.hypot(x1 - x2, y1 - y2)


def _component_shape_ids(components: Iterable[dict]) -> list[int]:
    return sorted({int(shape_id) for item in components for shape_id in item.get("shape_ids", ())})


def _capacity(slots: Iterable[dict]) -> dict:
    values = list(slots)
    return {
        "estimated_lines": sum(int(item.get("capacity", {}).get("estimated_lines", 0)) for item in values),
        "estimated_cjk_chars": sum(
            int(item.get("capacity", {}).get("estimated_cjk_chars", 0)) for item in values
        ),
    }


def _sample_fingerprints(slots: Iterable[dict]) -> list[dict]:
    values = []
    for item in slots:
        sample = " ".join(str(item.get("sample_text", "")).split())
        if not sample:
            continue
        values.append({
            "shape_id": int(item["shape_id"]),
            "sha256": hashlib.sha256(sample.encode("utf-8")).hexdigest(),
        })
    return values


def _synthetic_box(box: dict, *, top_ratio: float, height_ratio: float) -> dict:
    return {
        "left": round(box["left"] + box["width"] * 0.06, 4),
        "top": round(box["top"] + box["height"] * top_ratio, 4),
        "width": round(box["width"] * 0.88, 4),
        "height": round(box["height"] * height_ratio, 4),
    }


def _cluster_records(records: list[dict], count: int, fallback_box: dict) -> list[list[dict]]:
    if count <= 1:
        return [records]
    if not records:
        return [[] for _ in range(count)]
    points = [_center(item["box"]) for item in records]
    seeds = [min(range(len(points)), key=lambda index: (points[index][0], points[index][1]))]
    while len(seeds) < min(count, len(points)):
        candidate = max(
            (index for index in range(len(points)) if index not in seeds),
            key=lambda index: min(
                math.hypot(points[index][0] - points[seed][0], points[index][1] - points[seed][1])
                for seed in seeds
            ),
        )
        seeds.append(candidate)
    centroids = [points[index] for index in seeds]
    while len(centroids) < count:
        position = len(centroids)
        columns = math.ceil(math.sqrt(count))
        rows = math.ceil(count / columns)
        column = position % columns
        row = position // columns
        centroids.append((
            fallback_box["left"] + fallback_box["width"] * (column + 0.5) / columns,
            fallback_box["top"] + fallback_box["height"] * (row + 0.5) / rows,
        ))

    assignments = [0] * len(records)
    for _ in range(12):
        new_assignments = [
            min(
                range(count),
                key=lambda index: math.hypot(point[0] - centroids[index][0], point[1] - centroids[index][1]),
            )
            for point in points
        ]
        if new_assignments == assignments:
            break
        assignments = new_assignments
        for index in range(count):
            members = [points[item_index] for item_index, value in enumerate(assignments) if value == index]
            if members:
                centroids[index] = (
                    sum(point[0] for point in members) / len(members),
                    sum(point[1] for point in members) / len(members),
                )
    order = sorted(range(count), key=lambda index: (round(centroids[index][1] / 0.18), centroids[index][0]))
    remap = {old: new for new, old in enumerate(order)}
    groups = [[] for _ in range(count)]
    for item, assignment in zip(records, assignments):
        groups[remap[assignment]].append(item)
    return groups


class StandardTemplateCompiler:
    """Build a page/module/slot contract from extracted grammar plus curated prototypes."""

    def compile(
        self,
        *,
        template_id: str,
        catalog_entry: dict,
        grammar: dict,
        prototype: dict,
        skill_root: Path | str,
    ) -> dict:
        if int(grammar.get("schema_version", 0)) < 3:
            raise ValueError("template grammar schema 3 or newer is required")
        root = Path(skill_root).resolve()
        pptx_path = (root / catalog_entry["path"]).resolve()
        source_path = (root / catalog_entry["source_path"]).resolve()
        if not pptx_path.is_file():
            raise FileNotFoundError(pptx_path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        page_overrides = prototype.get("pages", {})
        pages = []
        for archetype in grammar.get("archetypes", ()):
            slide_index = int(archetype["slide_index"])
            override = page_overrides.get(str(slide_index))
            if not override:
                raise ValueError(f"{template_id} slide {slide_index} has no semantic prototype")
            pages.append(self._compile_page(template_id, archetype, override, grammar))

        identity_features = list(dict.fromkeys([
            *grammar.get("identity", {}).get("signature_features", ()),
            *prototype.get("identity_features", ()),
        ]))
        identity_seed = json.dumps(
            {
                "features": identity_features,
                "navigation": grammar.get("identity", {}).get("navigation"),
                "composition": grammar.get("identity", {}).get("composition"),
                "title_box": grammar.get("geometry", {}).get("title_box"),
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        specification = {
            "schema_version": SPEC_SCHEMA_VERSION,
            "contract": "standard_template_specification",
            "template": {
                "id": template_id,
                "short_name": catalog_entry["short_name"],
                "standard_editable_pptx": catalog_entry["path"].replace("\\", "/"),
                "source_template": catalog_entry["source_path"].replace("\\", "/"),
                "standard_pptx_sha256": _sha256(pptx_path),
                "source_pptx_sha256": _sha256(source_path),
                "slide_count": len(pages),
                "source_fidelity": catalog_entry.get("source_fidelity"),
                "semantic_compile_status": "compiled_not_release_accepted",
            },
            "template_identity": {
                **grammar.get("identity", {}),
                "identity_features": identity_features,
                "identity_signature": hashlib.sha256(identity_seed).hexdigest(),
                "minimum_preserved_features": 4,
                "reconstruction_rule": "preserve_navigation_title_geometry_panel_language_and_two_decorative_features",
            },
            "typography_capacity_policy": TYPOGRAPHY_POLICY,
            "render_contract": {
                "allowed_region_modes": list(EXCLUSIVE_RENDER_MODES),
                "mutually_exclusive": True,
                "native_reuse_rule": "reuse_the_complete_owned_native_component",
                "full_reconstruction_rule": "delete_complete_ownership_group_before_rebuild",
                "masking_forbidden": True,
                "stacking_old_and_new_forbidden": True,
            },
            "media_contract": {
                "page_level_layouts": [
                    "one_image", "two_image", "three_image", "four_image", "six_image",
                    "primary_plus_supporting", "verified_multi_panel_evidence",
                ],
                "module_level_media": True,
                "provenance_required_fields": list(MEDIA_PROVENANCE_FIELDS),
                "pdf_page_required_for_pdf_assets": True,
                "empty_slot_behavior": "remove_or_reflow",
                "unbound_visual_forbidden": True,
            },
            "navigation_contract": grammar.get("navigation_contract", {}),
            "geometry": grammar.get("geometry", {}),
            "pages": pages,
            "acceptance": {
                "semantic_compile_passed": False,
                "powerpoint_visual_review": "pending",
                "product_accepted": False,
                "release_blocker": "T01-T08 and formal PowerPoint review must all pass",
            },
        }
        validation = StandardTemplateSpecValidator().validate(specification)
        specification["acceptance"]["semantic_compile_passed"] = validation.passed
        specification["acceptance"]["semantic_compile_errors"] = list(validation.errors)
        if not validation.passed:
            raise ValueError("semantic specification failed: " + "; ".join(validation.errors))
        return specification

    def _compile_page(self, template_id: str, archetype: dict, override: dict, grammar: dict) -> dict:
        slide_index = int(archetype["slide_index"])
        components = list(archetype.get("components", ()))
        component_by_shape = {
            int(shape_id): component
            for component in components
            for shape_id in component.get("shape_ids", ())
        }
        text_slots = list(archetype.get("text_slots", ()))
        page_title_slots = [item for item in text_slots if item.get("role") == "page_title"]
        separate_header = bool(
            page_title_slots and override.get("page_role") not in {"cover", "ending"}
        )
        identity_shape_ids = self._identity_shape_ids(archetype, text_slots)
        identity_shape_ids.difference_update(int(item["shape_id"]) for item in page_title_slots)
        title_shape_ids = {
            int(item["shape_id"]) for item in page_title_slots
        } if separate_header else set()
        content_text = [
            item for item in text_slots
            if int(item["shape_id"]) not in identity_shape_ids | title_shape_ids
            and item.get("role") not in {"navigation_or_footer", "page_number_or_footer"}
        ]
        source_content_region = grammar.get("geometry", {}).get(
            "content_region", {"left": 0.05, "top": 0.19, "width": 0.9, "height": 0.7}
        )
        title_bottom = max(
            (
                float(item["box"]["top"]) + float(item["box"]["height"])
                for item in page_title_slots
            ),
            default=0.19,
        )
        content_top = max(0.22, title_bottom + 0.02, float(source_content_region.get("top", 0.19)))
        content_bottom = min(
            0.90,
            float(source_content_region.get("top", 0.19))
            + float(source_content_region.get("height", 0.7)),
        )
        content_region = {
            "left": max(0.04, float(source_content_region.get("left", 0.05))),
            "top": round(content_top, 4),
            "width": min(0.92, float(source_content_region.get("width", 0.9))),
            "height": round(max(0.48, content_bottom - content_top), 4),
        }
        expected_count = int(override.get("expected_module_count", 1))
        media_scope = override.get("media_scope", "none")
        page_media_count = int(override.get("page_media_count", 0))

        semantic_records = [
            {"kind": "text", "shape_id": int(item["shape_id"]), "box": item["box"], "payload": item}
            for item in content_text
        ]
        picture_records = [
            {"kind": "picture", "shape_id": int(item["shape_id"]), "box": item["box"], "payload": item}
            for item in archetype.get("picture_slots", ())
            if int(item["shape_id"]) not in identity_shape_ids
            and item.get("role") != "logo"
            and item.get("box", {}).get("top", 0) >= 0.14
        ]
        semantic_records.extend(picture_records)

        page_role = override.get("page_role")
        if page_role in {"cover", "ending", "section"}:
            groups = [semantic_records]
            group_boxes = [
                _union((item["box"] for item in semantic_records), content_region)
            ]
        else:
            group_boxes = [
                self._grid_box(content_region, index, expected_count)
                for index in range(expected_count)
            ]
            groups = [[] for _ in group_boxes]
            for record in semantic_records:
                target = min(
                    range(len(group_boxes)),
                    key=lambda index: _box_distance(record["box"], group_boxes[index]),
                )
                groups[target].append(record)
        assignment = self._assign_components(
            components,
            group_boxes,
            identity_shape_ids=identity_shape_ids,
            title_shape_ids=title_shape_ids,
        )

        modules = []
        if separate_header:
            header_components = [
                component_by_shape[int(item["shape_id"])]
                for item in page_title_slots
                if int(item["shape_id"]) in component_by_shape
            ]
            modules.append(self._header_module(template_id, slide_index, page_title_slots, header_components))

        selected_media = self._select_page_media(
            archetype,
            page_media_count,
            allow_synthetic=not bool(override.get("page_media_native_reuse")),
            fallback_box=content_region,
        ) if page_media_count else []
        module_roles = list(override.get("module_roles", ()))
        for index, (records, box) in enumerate(zip(groups, group_boxes), 1):
            owned_components = assignment[index - 1]
            text_values = [item["payload"] for item in records if item["kind"] == "text"]
            role = module_roles[index - 1] if index <= len(module_roles) else override.get(
                "default_module_role", "evidence_module"
            )
            modules.append(self._content_module(
                template_id=template_id,
                slide_index=slide_index,
                module_index=index,
                role=role,
                box=box,
                text_slots=text_values,
                components=owned_components,
                media_scope=media_scope,
                module_media_supported=bool(override.get("module_media_supported")),
                selected_page_media=selected_media if media_scope == "page" else [],
                page_media_native_reuse=bool(override.get("page_media_native_reuse")),
            ))

        identity_components = [
            component for component in components
            if any(int(shape_id) in identity_shape_ids for shape_id in component.get("shape_ids", ()))
        ]
        identity_regions = self._identity_regions(identity_components, archetype)
        owned_component_ids = {
            component_id
            for module in modules
            for component_id in module["ownership_group"]["component_ids"]
        }
        identity_component_ids = {
            component_id
            for region in identity_regions
            for component_id in region["ownership_group"]["component_ids"]
        }
        all_component_ids = {item["component_id"] for item in components}
        unowned = sorted(all_component_ids - owned_component_ids - identity_component_ids)
        duplicates = sorted(owned_component_ids & identity_component_ids)
        page = {
            "page_id": f"{template_id}_P{slide_index:02d}",
            "source_slide_index": slide_index,
            "page_role": override.get("page_role", archetype.get("role")),
            "page_archetype": override["page_archetype"],
            "layout_signature": archetype.get("layout_signature"),
            "prototype": {
                "relationship": override.get("relationship", "claim_support_interpretation"),
                "recommended_argument_units": list(override.get("recommended_argument_units", ())),
                "content_module_count": expected_count,
                "media_scope": media_scope,
            },
            "media_layout": {
                "scope": media_scope,
                "kind": override.get(
                    "media_layout",
                    "one_per_module" if media_scope == "module" and override.get("module_media_supported") else "none",
                ),
                "slot_count": page_media_count if media_scope == "page" else (
                    expected_count if override.get("module_media_supported") else 0
                ),
                "native_reuse_supported": bool(override.get("page_media_native_reuse")),
                "missing_asset_behavior": "remove_or_reflow",
            },
            "semantic_modules": modules,
            "identity_regions": identity_regions,
            "ownership_audit": {
                "component_count": len(all_component_ids),
                "semantic_owned_component_count": len(owned_component_ids),
                "identity_owned_component_count": len(identity_component_ids),
                "unowned_component_ids": unowned,
                "duplicate_component_ids": duplicates,
            },
        }
        return page

    @staticmethod
    def _identity_shape_ids(archetype: dict, text_slots: list[dict]) -> set[int]:
        values = {
            int(item["shape_id"])
            for item in text_slots
            if item.get("role") in {"navigation_or_footer", "page_number_or_footer"}
        }
        for item in archetype.get("components", ()):
            if item.get("component_role") == "navigation":
                values.update(int(shape_id) for shape_id in item.get("shape_ids", ()))
        for item in archetype.get("picture_slots", ()):
            box = item.get("box", {})
            if item.get("role") in {"logo", "navigation"} or (
                item.get("role") == "decoration"
                and (box.get("top", 0) < 0.14 or box.get("top", 0) + box.get("height", 0) > 0.96)
            ):
                values.add(int(item["shape_id"]))
        return values

    @staticmethod
    def _grid_box(region: dict, index: int, count: int) -> dict:
        columns = count if count <= 5 else 3
        rows = math.ceil(count / columns)
        column = index % columns
        row = index // columns
        gap_x = 0.018
        gap_y = 0.025
        width = (region["width"] - gap_x * (columns - 1)) / columns
        height = (region["height"] - gap_y * (rows - 1)) / rows
        return {
            "left": round(region["left"] + column * (width + gap_x), 4),
            "top": round(region["top"] + row * (height + gap_y), 4),
            "width": round(width, 4),
            "height": round(height, 4),
        }

    @staticmethod
    def _assign_components(
        components: list[dict],
        boxes: list[dict],
        *,
        identity_shape_ids: set[int],
        title_shape_ids: set[int],
    ) -> list[list[dict]]:
        assignments = [[] for _ in boxes]
        for component in components:
            shape_ids = {int(value) for value in component.get("shape_ids", ())}
            if shape_ids & identity_shape_ids or shape_ids & title_shape_ids:
                continue
            target = min(range(len(boxes)), key=lambda index: _box_distance(component["box"], boxes[index]))
            assignments[target].append(component)
        return assignments

    @staticmethod
    def _header_module(
        template_id: str,
        slide_index: int,
        title_slots: list[dict],
        components: list[dict],
    ) -> dict:
        shape_ids = sorted(int(item["shape_id"]) for item in title_slots)
        component_ids = sorted(item["component_id"] for item in components)
        return {
            "module_id": f"{template_id}_P{slide_index:02d}_HEADER",
            "role": "page_header",
            "semantic_region": "header",
            "box": _union(item["box"] for item in title_slots),
            "render_contract": StandardTemplateCompiler._render_contract(native_reuse=True),
            "ownership_group": StandardTemplateCompiler._ownership(component_ids, shape_ids),
            "child_slots": [StandardTemplateCompiler._text_child(
                slot_id=f"{template_id}_P{slide_index:02d}_HEADER_TITLE",
                role="page_title",
                slots=title_slots,
                required=True,
            )],
        }

    def _content_module(
        self,
        *,
        template_id: str,
        slide_index: int,
        module_index: int,
        role: str,
        box: dict,
        text_slots: list[dict],
        components: list[dict],
        media_scope: str,
        module_media_supported: bool,
        selected_page_media: list[dict],
        page_media_native_reuse: bool,
    ) -> dict:
        prefix = f"{template_id}_P{slide_index:02d}_M{module_index:02d}"
        heading, captions, explanations = self._partition_text_slots(text_slots)
        children = []
        heading_role = {
            "cover_identity": "cover_title",
            "ending_summary": "page_title",
        }.get(role, "module_heading")
        if heading:
            children.append(self._text_child(f"{prefix}_HEADING", heading_role, heading, True))
        else:
            children.append(self._synthetic_text_child(
                f"{prefix}_HEADING", "module_heading", _synthetic_box(box, top_ratio=0.04, height_ratio=0.16), True
            ))
        if explanations:
            explanation = self._text_child(
                f"{prefix}_EXPLANATION", "explanation", explanations, True
            )
            if role == "cover_identity":
                explanation["typography"] = {
                    **explanation["typography"],
                    "policy_role": "cover_subtitle",
                    **TYPOGRAPHY_POLICY["cover_subtitle"],
                }
            children.append(explanation)
        elif role not in {"cover_identity", "ending_summary"}:
            children.append(self._synthetic_text_child(
                f"{prefix}_EXPLANATION", "explanation", _synthetic_box(box, top_ratio=0.23, height_ratio=0.34), True
            ))

        if media_scope == "page":
            for media_index, media in enumerate(selected_page_media, 1):
                children.append(self._media_child(
                    slot_id=f"{prefix}_MEDIA_{media_index:02d}",
                    role="image_or_chart",
                    box=media["box"],
                    shape_ids=[int(media["shape_id"])] if media.get("shape_id") is not None else [],
                    required=True,
                    native_reuse=page_media_native_reuse and bool(media.get("replaceable")),
                    scope="page",
                ))
                nearest_caption = min(captions, key=lambda item: _box_distance(item["box"], media["box"]), default=None)
                if nearest_caption:
                    children.append(self._text_child(
                        f"{prefix}_CAPTION_{media_index:02d}", "caption", [nearest_caption], True
                    ))
                    captions.remove(nearest_caption)
                else:
                    children.append(self._synthetic_text_child(
                        f"{prefix}_CAPTION_{media_index:02d}",
                        "caption",
                        _synthetic_box(media["box"], top_ratio=0.88, height_ratio=0.1),
                        True,
                    ))
        elif module_media_supported:
            children.append(self._media_child(
                slot_id=f"{prefix}_MEDIA",
                role="image_or_chart",
                box=_synthetic_box(box, top_ratio=0.58, height_ratio=0.32),
                shape_ids=[],
                required=False,
                native_reuse=False,
                scope="module",
            ))
            children.append(self._synthetic_text_child(
                f"{prefix}_CAPTION",
                "caption",
                _synthetic_box(box, top_ratio=0.91, height_ratio=0.07),
                True,
            ))
        for caption_index, caption in enumerate(captions, 1):
            children.append(self._text_child(
                f"{prefix}_CAPTION_{caption_index:02d}", "caption", [caption], False
            ))

        shape_ids = _component_shape_ids(components)
        component_ids = sorted(item["component_id"] for item in components)
        return {
            "module_id": prefix,
            "role": role,
            "semantic_region": "content",
            "box": box,
            "render_contract": self._render_contract(native_reuse=bool(component_ids)),
            "ownership_group": self._ownership(component_ids, shape_ids),
            "capacity": {
                "heading": _capacity(heading),
                "explanation": _capacity(explanations),
                "overflow_action": "shorten_split_or_reflow",
            },
            "child_slots": children,
        }

    @staticmethod
    def _partition_text_slots(slots: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
        if not slots:
            return [], [], []
        captions = [
            item for item in slots
            if str(item.get("sample_text", "")).strip().casefold().startswith(
                ("图", "表", "figure", "table", "a:", "b:", "c:", "d:", "e:", "f:")
            )
        ]
        remaining = [item for item in slots if item not in captions]
        heading = []
        if remaining:
            heading_item = max(
                remaining,
                key=lambda item: (float(item.get("font_size_pt") or 0), -float(item["box"]["top"])),
            )
            heading = [heading_item]
        explanations = [item for item in remaining if item not in heading]
        return heading, captions, explanations

    @staticmethod
    def _text_child(slot_id: str, role: str, slots: list[dict], required: bool) -> dict:
        policy_role = {
            "cover_title": "cover_title",
            "page_title": "page_title",
            "module_heading": "module_heading",
            "caption": "caption",
        }.get(role, "body")
        return {
            "slot_id": slot_id,
            "role": role,
            "content_types": ["text"],
            "required": required,
            "native_shape_ids": sorted(int(item["shape_id"]) for item in slots),
            "box": _union(item["box"] for item in slots),
            "capacity": _capacity(slots),
            "source_sample_fingerprints": _sample_fingerprints(slots),
            "typography": {
                "policy_role": policy_role,
                **TYPOGRAPHY_POLICY[policy_role],
                "source_font_sizes_pt": sorted({
                    float(item["font_size_pt"]) for item in slots if item.get("font_size_pt")
                }),
                "source_font_families": sorted({
                    item["font_family"] for item in slots if item.get("font_family")
                }),
            },
            "omission_policy": "remove_owned_text_shape_or_reflow" if not required else "must_bind_or_select_another_archetype",
        }

    @staticmethod
    def _synthetic_text_child(slot_id: str, role: str, box: dict, required: bool) -> dict:
        policy_role = {
            "module_heading": "module_heading",
            "page_title": "page_title",
            "cover_title": "cover_title",
            "caption": "caption",
        }.get(role, "body")
        return {
            "slot_id": slot_id,
            "role": role,
            "content_types": ["text"],
            "required": required,
            "native_shape_ids": [],
            "box": box,
            "capacity": {"estimated_lines": 3 if role == "explanation" else 2, "estimated_cjk_chars": 72 if role == "explanation" else 24},
            "source_sample_fingerprints": [],
            "typography": {"policy_role": policy_role, **TYPOGRAPHY_POLICY[policy_role]},
            "binding_mode": "full_reconstruction_only",
            "omission_policy": "must_bind_or_select_another_archetype",
        }

    @staticmethod
    def _media_child(
        *,
        slot_id: str,
        role: str,
        box: dict,
        shape_ids: list[int],
        required: bool,
        native_reuse: bool,
        scope: str,
    ) -> dict:
        ratio = round(box["width"] / max(box["height"], 0.0001), 3)
        return {
            "slot_id": slot_id,
            "role": role,
            "content_types": ["source_figure", "chart", "table", "photo", "diagram"],
            "required": required,
            "native_shape_ids": sorted(shape_ids),
            "box": box,
            "media_scope": scope,
            "binding_mode": "native_replace_or_full_reconstruction" if native_reuse else "full_reconstruction_only",
            "aspect_ratio": {
                "preferred": ratio,
                "accepted_min": round(ratio * 0.75, 3),
                "accepted_max": round(ratio * 1.25, 3),
                "fit": "contain",
            },
            "source_binding": {
                "required_fields": list(MEDIA_PROVENANCE_FIELDS),
                "pdf_page_required_for_pdf_assets": True,
                "semantic_match_required": True,
            },
            "empty_behavior": "remove_or_reflow",
        }

    @staticmethod
    def _render_contract(*, native_reuse: bool) -> dict:
        return {
            "allowed_modes": list(EXCLUSIVE_RENDER_MODES if native_reuse else ("full_reconstruction",)),
            "mutually_exclusive": True,
            "selected_mode_required": True,
            "masking_forbidden": True,
        }

    @staticmethod
    def _ownership(component_ids: list[str], shape_ids: list[int]) -> dict:
        return {
            "component_ids": sorted(component_ids),
            "shape_ids": sorted(shape_ids),
            "complete_delete_shape_ids": sorted(shape_ids),
            "removal_policy": REMOVAL_POLICY,
            "remove_companions": ["frame", "heading", "explanation", "image", "chart", "icon", "caption", "connector", "placeholder"],
        }

    @staticmethod
    def _identity_regions(components: list[dict], archetype: dict) -> list[dict]:
        grouped: dict[str, list[dict]] = {}
        picture_roles = {
            int(item["shape_id"]): item.get("role")
            for item in archetype.get("picture_slots", ())
        }
        for component in components:
            shape_ids = [int(value) for value in component.get("shape_ids", ())]
            if component.get("component_role") == "navigation":
                role = "navigation"
            elif any(picture_roles.get(shape_id) == "navigation" for shape_id in shape_ids):
                role = "navigation"
            elif any(picture_roles.get(shape_id) == "logo" for shape_id in shape_ids):
                role = "logo"
            elif component.get("component_role") in {"textbox", "autoshape"}:
                role = "footer_or_navigation_label"
            else:
                role = "decoration"
            grouped.setdefault(role, []).append(component)
        return [
            {
                "region_id": f"IDENTITY_{role.upper()}",
                "role": role,
                "preserve_for_template_identity": True,
                "ownership_group": StandardTemplateCompiler._ownership(
                    sorted(item["component_id"] for item in values),
                    _component_shape_ids(values),
                ),
            }
            for role, values in sorted(grouped.items())
        ]

    @staticmethod
    def _select_page_media(
        archetype: dict,
        count: int,
        *,
        allow_synthetic: bool,
        fallback_box: dict,
    ) -> list[dict]:
        candidates = [
            item for item in archetype.get("picture_slots", ())
            if item.get("role") != "logo"
            and item.get("box", {}).get("top", 0) >= 0.18
            and float(item.get("area", 0)) >= 0.018
            and float(item.get("area", 0)) <= 0.42
        ]
        if len(candidates) < count and not allow_synthetic:
            raise ValueError(
                f"slide {archetype.get('slide_index')} needs {count} media slots but only {len(candidates)} were found"
            )
        if len(candidates) < count:
            return [
                {
                    "shape_id": None,
                    "role": "synthetic_media_slot",
                    "replaceable": False,
                    "box": StandardTemplateCompiler._grid_box(fallback_box, index, count),
                }
                for index in range(count)
            ]
        area_buckets: dict[float, list[dict]] = {}
        for item in candidates:
            area_buckets.setdefault(round(float(item["area"]), 3), []).append(item)
        bucket = max(
            (values for values in area_buckets.values() if len(values) >= count),
            key=lambda values: (len(values) == count, sum(float(item["area"]) for item in values[:count])),
            default=None,
        )
        selected = (bucket or sorted(candidates, key=lambda item: float(item["area"]), reverse=True))[:count]
        return sorted(selected, key=lambda item: (item["box"]["top"], item["box"]["left"]))


class StandardTemplateSpecValidator:
    """Validate semantic ownership, media provenance, typography, and identity contracts."""

    def validate(self, specification: dict) -> TemplateSpecValidationResult:
        errors: list[str] = []
        observations: list[str] = []
        if specification.get("schema_version") != SPEC_SCHEMA_VERSION:
            errors.append(f"unsupported semantic specification schema: {specification.get('schema_version')}")
        template = specification.get("template", {})
        pages = specification.get("pages", ())
        if not template.get("id"):
            errors.append("template ID is required")
        if int(template.get("slide_count", -1)) != len(pages):
            errors.append("template slide count does not match semantic pages")
        identity = specification.get("template_identity", {})
        if len(identity.get("identity_features", ())) < int(identity.get("minimum_preserved_features", 4)):
            errors.append("template identity does not record enough distinguishing features")
        typography = specification.get("typography_capacity_policy", {})
        if float(typography.get("normal_content_min_pt", 0)) < 10.5:
            errors.append("normal content minimum font must be at least 10.5 pt")
        if not typography.get("unbounded_shrink_forbidden"):
            errors.append("unbounded font shrinking must be forbidden")

        page_ids: set[str] = set()
        global_module_ids: set[str] = set()
        global_slot_ids: set[str] = set()
        for page in pages:
            page_id = str(page.get("page_id", ""))
            if not page_id or page_id in page_ids:
                errors.append(f"duplicate or missing page ID: {page_id!r}")
            page_ids.add(page_id)
            modules = page.get("semantic_modules", ())
            if not modules:
                errors.append(f"{page_id}: page has no semantic modules")
            semantic_owned: set[str] = set()
            for module in modules:
                module_id = str(module.get("module_id", ""))
                if not module_id or module_id in global_module_ids:
                    errors.append(f"{page_id}: duplicate or missing module ID: {module_id!r}")
                global_module_ids.add(module_id)
                render = module.get("render_contract", {})
                modes = set(render.get("allowed_modes", ()))
                if not modes or not modes <= set(EXCLUSIVE_RENDER_MODES):
                    errors.append(f"{module_id}: invalid region render modes")
                if not render.get("mutually_exclusive") or not render.get("masking_forbidden"):
                    errors.append(f"{module_id}: native and reconstructed regions are not exclusive")
                ownership = module.get("ownership_group", {})
                if ownership.get("removal_policy") != REMOVAL_POLICY:
                    errors.append(f"{module_id}: incomplete component removal policy")
                if sorted(ownership.get("shape_ids", ())) != sorted(ownership.get("complete_delete_shape_ids", ())):
                    errors.append(f"{module_id}: complete deletion does not include the whole ownership group")
                component_ids = set(ownership.get("component_ids", ()))
                duplicated_components = semantic_owned & component_ids
                if duplicated_components:
                    errors.append(f"{page_id}: duplicated semantic ownership {sorted(duplicated_components)}")
                semantic_owned.update(component_ids)
                slot_shapes: set[int] = set()
                children = module.get("child_slots", ())
                if not children:
                    errors.append(f"{module_id}: module has no child slots")
                for slot in children:
                    slot_id = str(slot.get("slot_id", ""))
                    if not slot_id or slot_id in global_slot_ids:
                        errors.append(f"{module_id}: duplicate or missing child slot ID: {slot_id!r}")
                    global_slot_ids.add(slot_id)
                    shape_ids = {int(value) for value in slot.get("native_shape_ids", ())}
                    overlap = slot_shapes & shape_ids
                    if overlap:
                        errors.append(f"{module_id}: child slots share native shape IDs {sorted(overlap)}")
                    slot_shapes.update(shape_ids)
                    if slot.get("role") == "image_or_chart":
                        source = slot.get("source_binding", {})
                        if tuple(source.get("required_fields", ())) != MEDIA_PROVENANCE_FIELDS:
                            errors.append(f"{slot_id}: media source binding is incomplete")
                        if slot.get("empty_behavior") != "remove_or_reflow":
                            errors.append(f"{slot_id}: empty media slot is not removed or reflowed")
                        if not source.get("semantic_match_required"):
                            errors.append(f"{slot_id}: media semantic purpose is not required")
                    elif "typography" not in slot:
                        errors.append(f"{slot_id}: text slot has no typography capacity policy")

            identity_owned = {
                component_id
                for region in page.get("identity_regions", ())
                for component_id in region.get("ownership_group", {}).get("component_ids", ())
            }
            duplicates = semantic_owned & identity_owned
            if duplicates:
                errors.append(f"{page_id}: components are both semantic and identity owned: {sorted(duplicates)}")
            audit = page.get("ownership_audit", {})
            if audit.get("unowned_component_ids"):
                errors.append(f"{page_id}: unowned components remain: {audit['unowned_component_ids']}")
            if audit.get("duplicate_component_ids"):
                errors.append(f"{page_id}: duplicate component ownership remains")
            media = page.get("media_layout", {})
            if media.get("scope") == "page":
                media_slots = [
                    slot for module in modules for slot in module.get("child_slots", ())
                    if slot.get("role") == "image_or_chart" and slot.get("media_scope") == "page"
                ]
                if len(media_slots) != int(media.get("slot_count", -1)):
                    errors.append(f"{page_id}: page media slot count does not match the prototype")
            content_modules = [
                module for module in modules if module.get("semantic_region") == "content"
            ]
            if page.get("page_role") not in {"cover", "ending", "section"}:
                for module in content_modules:
                    box = module.get("box", {})
                    if (
                        float(box.get("top", 0)) < 0.20
                        or float(box.get("width", 0)) < 0.12
                        or float(box.get("height", 0)) < 0.12
                        or float(box.get("left", 0)) < 0
                        or float(box.get("left", 0)) + float(box.get("width", 0)) > 1.001
                        or float(box.get("top", 0)) + float(box.get("height", 0)) > 1.001
                    ):
                        errors.append(f"{module.get('module_id')}: content module geometry is unusable")
                for index, first in enumerate(content_modules):
                    for second in content_modules[index + 1:]:
                        first_box, second_box = first.get("box", {}), second.get("box", {})
                        left = max(float(first_box.get("left", 0)), float(second_box.get("left", 0)))
                        top = max(float(first_box.get("top", 0)), float(second_box.get("top", 0)))
                        right = min(
                            float(first_box.get("left", 0)) + float(first_box.get("width", 0)),
                            float(second_box.get("left", 0)) + float(second_box.get("width", 0)),
                        )
                        bottom = min(
                            float(first_box.get("top", 0)) + float(first_box.get("height", 0)),
                            float(second_box.get("top", 0)) + float(second_box.get("height", 0)),
                        )
                        if right > left and bottom > top:
                            errors.append(
                                f"{page_id}: content modules {first.get('module_id')}/{second.get('module_id')} overlap"
                            )
            if page.get("page_role") not in {"cover", "ending", "agenda", "section"}:
                if not content_modules:
                    errors.append(f"{page_id}: content page has no content modules")
        if not pages:
            errors.append("semantic specification has no pages")
        if any(page.get("media_layout", {}).get("scope") == "page" for page in pages):
            observations.append("page-level media archetypes require evidence-bound assets at render time")
        return TemplateSpecValidationResult(not errors, tuple(errors), tuple(observations))


def load_semantic_prototypes(path: Path | str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported template semantic prototype schema")
    return payload["templates"]
