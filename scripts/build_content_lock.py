"""Validate evidence references and freeze the approved dynamic slide content."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    ledger = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    evidence_ids = {item["id"] for item in ledger["items"]}
    sections = set(plan.get("sections", []))
    errors = []
    locked_pages = []
    used_images = {}
    for page in plan.get("pages", []):
        page_id = page.get("page_id", "UNKNOWN")
        layout = page.get("layout")
        page_role = page.get("page_role", layout)
        is_content = page_role not in {"cover", "agenda", "section", "ending"}
        if is_content and page.get("section") not in sections:
            errors.append(f"{page_id}: invalid section {page.get('section')}")
        if is_content and not page.get("visual_strategy"):
            errors.append(f"{page_id}: missing visual_strategy")
        if is_content and page.get("visual_strategy") in {
            "matplotlib_chart", "native_diagram", "web_image", "generated_image"
        } and not page.get("visual_task_id"):
            errors.append(f"{page_id}: visual_strategy requires visual_task_id")
        payload = page.get("page_payload", {})
        if is_content and not page.get("density_exception"):
            if not payload.get("claim") or not payload.get("supporting_unit_ids"):
                errors.append(f"{page_id}: incomplete page_payload")
            if not payload.get("density", {}).get("status"):
                errors.append(f"{page_id}: missing page_payload.density.status")
        image = page.get("image")
        if image:
            if image in used_images and not page.get("allow_image_reuse"):
                errors.append(f"{page_id}: image already used by {used_images[image]}: {image}")
            used_images[image] = page_id
        referenced_evidence = set(page.get("evidence_ids", []))
        referenced_evidence.update(page.get("page_payload", {}).get("supporting_unit_ids", []))
        missing = sorted(referenced_evidence - evidence_ids)
        if missing:
            errors.append(f"{page_id}: unknown evidence IDs {missing}")
        content = {key: value for key, value in page.items() if key != "speaker_notes"}
        digest = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        locked_pages.append({
            "page_id": page_id,
            "title": page.get("title"),
            "section": page.get("section"),
            "layout": layout,
            "visual_strategy": page.get("visual_strategy"),
            "evidence_ids": page.get("evidence_ids", []),
            "content_sha256": digest,
        })
    if errors:
        raise SystemExit("\n".join(errors))
    output = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_plan": str(Path(args.plan).resolve()),
        "source_evidence": str(Path(args.evidence).resolve()),
        "sections": plan.get("sections", []),
        "pages": locked_pages,
        "confirmed": plan.get("confirmed") is True,
        "confirmation_note": plan.get("confirmation_note", ""),
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Locked {len(locked_pages)} pages: {target}")


if __name__ == "__main__":
    main()
