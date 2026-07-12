"""Validate that a complete deck uses enough of the selected template's grammar."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from render_dynamic import scaffold_for_page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan")
    parser.add_argument("grammar")
    parser.add_argument("--minimum-source-slides", type=int, default=3)
    parser.add_argument("--output")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    grammar = json.loads(Path(args.grammar).read_text(encoding="utf-8"))
    usage = []
    for page in plan.get("pages", []):
        scaffold = scaffold_for_page(grammar, page)
        usage.append({
            "page_id": page.get("page_id"), "layout": page.get("layout"),
            "source_slide": scaffold.get("slide_index") if scaffold else None,
            "source_role": scaffold.get("role") if scaffold else None,
            "decorative_asset_count": len(scaffold.get("decorative_assets", [])) if scaffold else 0,
        })
    source_slides = {item["source_slide"] for item in usage if item["source_slide"] is not None}
    required = min(args.minimum_source_slides, len(grammar.get("archetypes", [])))
    errors = []
    if plan.get("deck_scope") == "complete" and len(source_slides) < required:
        errors.append(f"complete deck uses only {len(source_slides)} template source slides; requires {required}")
    if not any(item["decorative_asset_count"] for item in usage):
        errors.append("no decorative scaffold assets were used")
    report = {
        "template": grammar.get("template_name"), "deck_pages": len(usage),
        "distinct_source_slides": sorted(source_slides),
        "source_role_counts": dict(Counter(item["source_role"] for item in usage if item["source_role"])),
        "errors": errors, "passed": not errors, "usage": usage,
    }
    print(json.dumps({key: report[key] for key in ("template", "deck_pages", "distinct_source_slides", "source_role_counts", "errors", "passed")}, ensure_ascii=False, indent=2))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
