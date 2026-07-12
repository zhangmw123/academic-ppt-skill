"""Validate scene contract, page/time budget, evidence state, and argument coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_plan(plan, profiles):
    scene_raw = plan.get("scene")
    scene = profiles.get("aliases", {}).get(scene_raw, scene_raw)
    profile = profiles.get("profiles", {}).get(scene)
    errors, warnings = [], []
    if not profile:
        errors.append(f"unknown scene profile: {scene_raw}")
    else:
        scope = plan.get("deck_scope", "complete")
        page_count = len(plan.get("pages", []))
        if scope == "complete" and not (profile["complete_min"] <= page_count <= profile["complete_max"]):
            errors.append(f"{scene} complete deck requires {profile['complete_min']}-{profile['complete_max']} pages; got {page_count}")
        elif scope == "sample" and page_count > 7:
            warnings.append(f"sample deck has {page_count} pages; consider short_version or complete")
        evidence_state = plan.get("evidence_state")
        if evidence_state not in profile["evidence_states"]:
            errors.append(f"{scene} does not allow evidence_state={evidence_state}; expected {profile['evidence_states']}")
        tags = set(plan.get("coverage_tags", []))
        argument_units = set(plan.get("argument_units", []))
        total_seconds = 0
        for page in plan.get("pages", []):
            tags.update(page.get("coverage_tags", []))
            argument_units.update(page.get("argument_units", []))
            total_seconds += int(page.get("time_seconds", 0) or 0)

            binding_texts = [
                str(binding.get("content", "")).strip()
                for binding in page.get("text_bindings", [])
                if str(binding.get("content", "")).strip()
            ]
            binding_chars = sum(len(text) for text in binding_texts)
            images = page.get("image_bindings", [])
            page_role = page.get("page_role", page.get("layout"))
            density_exception = page.get("density_exception")
            payload = page.get("page_payload", {})
            is_content = page_role not in {"cover", "agenda", "section", "ending"}
            support_ids = payload.get("supporting_unit_ids", [])
            carriers = payload.get("evidence_carriers", [])
            interpretation = payload.get("interpretation") or payload.get("mechanism") or payload.get("comparison")
            boundary = payload.get("boundary")

            if is_content and not density_exception:
                if not payload.get("claim"):
                    errors.append(f"{page.get('page_id')} missing page_payload.claim")
                if not 2 <= len(support_ids) <= 4:
                    errors.append(
                        f"{page.get('page_id')} requires 2-4 supporting evidence units; "
                        "record density_exception when the page role justifies another composition"
                    )
                if not 1 <= len(carriers) <= 2 and page.get("visual_strategy") != "intentional_text_only":
                    errors.append(f"{page.get('page_id')} requires 1-2 evidence carriers or intentional_text_only")
                if not (interpretation or boundary):
                    errors.append(f"{page.get('page_id')} requires interpretation, mechanism, comparison, or boundary")

            if len(images) == 1 and not (interpretation or boundary or page.get("visual_takeaway")):
                errors.append(
                    f"{page.get('page_id')} has one image but insufficient interpretation; "
                    "add an interpretation/boundary in page_payload"
                )

            need = page.get("template_layout_need", {})
            components = int(need.get("component_count", 0) or 0)
            module_count = int(payload.get("density", {}).get("module_count", 0) or 0)
            if (components >= 3 and module_count and module_count < components
                    and not page.get("adjustments") and not page.get("density_rationale")):
                errors.append(
                    f"{page.get('page_id')} maps {module_count} semantic modules to a "
                    f"{components}-component layout; choose a compact layout, resize native slots, "
                    "or record density_rationale"
                )
            for addition in page.get("additions", []):
                if not addition.get("fallback_reason"):
                    errors.append(f"{page.get('page_id')} addition requires fallback_reason")
            visible_text = " ".join(binding_texts)
            forbidden_labels = ("读图结论", "如何读图", "讲述重点")
            if any(label in visible_text for label in forbidden_labels):
                errors.append(f"{page.get('page_id')} exposes an internal planning label on-slide")
        missing = sorted(set(profile["required_tags"]) - tags)
        if missing:
            errors.append(f"{scene} missing coverage tags: {missing}")
        missing_arguments = sorted(set(profile.get("argument_chain", [])) - argument_units)
        if missing_arguments:
            errors.append(f"{scene} missing argument units: {missing_arguments}")

        variant = plan.get("section_variant")
        variants = profile.get("default_variants", {})
        if variant and variant != "custom" and variant not in variants:
            errors.append(f"{scene} unknown section_variant={variant}; expected one of {sorted(variants)} or custom")
        sections = plan.get("sections", [])
        if not sections:
            errors.append(f"{scene} requires user-visible sections")
        if variant in variants and sections != variants[variant]:
            warnings.append(
                f"{scene} sections differ from variant {variant}; set section_variant=custom if this is intentional"
            )

        duration_minutes = plan.get("duration_minutes")
        if duration_minutes:
            expected = int(float(duration_minutes) * 60)
            if total_seconds == 0:
                errors.append(f"{scene} pages require time_seconds for a {duration_minutes}-minute talk")
            elif abs(total_seconds - expected) > max(60, expected * 0.12):
                warnings.append(
                    f"planned speaking time is {total_seconds}s, expected about {expected}s"
                )

        if scene == "组会-文献精读":
            transfer_pages = [page for page in plan.get("pages", []) if page.get("page_role") == "transfer"]
            if not transfer_pages:
                errors.append("组会-文献精读 requires a page_role=transfer page")
            else:
                transfer_text = " ".join(
                    str(binding.get("content", ""))
                    for page in transfer_pages
                    for binding in page.get("text_bindings", [])
                )
                action_terms = ("复现", "消融", "验证", "实验", "指标", "下一步")
                if len(transfer_text) < 120 or sum(term in transfer_text for term in action_terms) < 2:
                    errors.append(
                        "组会-文献精读 transfer page must map the paper to a concrete validation or experiment plan"
                    )
            ending_text = " ".join(
                str(binding.get("content", ""))
                for page in plan.get("pages", []) if page.get("page_role") == "ending"
                for binding in page.get("text_bindings", [])
            )
            if any(term in ending_text for term in ("请讨论", "希望讨论", "课堂讨论")):
                errors.append("组会-文献精读 ending must not use classroom-style discussion prompts unless requested")

        navigation_contract = plan.get("navigation_contract", {})
        if navigation_contract:
            font = navigation_contract.get("font", {})
            if navigation_contract.get("active_state", {}).get("rule") not in {"dark_fill_only", "template_dark_fill_only"}:
                warnings.append("navigation should identify only the current section with a dark fill")
            if not font.get("size_pt"):
                errors.append("navigation_contract requires one global font.size_pt")
            if navigation_contract.get("clear_protection") is not True:
                errors.append("navigation_contract must protect members from clear_unbound_text")
        elif plan.get("replace_raster_navigation"):
            navigation_style = plan.get("navigation_style", {})
            if navigation_style.get("active_state") != "dark_fill_only":
                warnings.append("navigation should identify only the current section with a dark fill")
            if not navigation_style.get("font_size_pt"):
                errors.append("rebuilt navigation requires one global font_size_pt")
    result = {"scene": scene, "scope": plan.get("deck_scope", "complete"), "pages": len(plan.get("pages", [])), "errors": errors, "warnings": warnings, "passed": not errors}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan")
    parser.add_argument("--profiles", default=str(Path(__file__).resolve().parents[1] / "references" / "scene-profiles.json"))
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    result = validate_plan(plan, profiles)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
