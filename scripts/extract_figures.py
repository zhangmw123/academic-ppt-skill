"""Extract likely scientific figures from a PDF and write a reviewable manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import fitz
from PIL import Image


CAPTION_RE = re.compile(r"^(figure|fig\.|table|图|表)\s*[A-Za-z0-9一二三四五六七八九十.-]+", re.I)


def page_captions(page) -> list[str]:
    lines = [line.strip() for line in page.get_text("text").splitlines()]
    return [line for line in lines if CAPTION_RE.match(line)][:8]


def extract(pdf_path: Path, output_dir: Path, min_width: int, min_height: int, max_aspect: float):
    output_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    raw = []
    digest_counts = Counter()

    for page_index, page in enumerate(document, 1):
        page_area = page.rect.width * page.rect.height
        captions = page_captions(page)
        for info in page.get_image_info(xrefs=True):
            xref = info.get("xref", 0)
            if not xref:
                continue
            extracted = document.extract_image(xref)
            data = extracted["image"]
            digest = hashlib.sha256(data).hexdigest()
            digest_counts[digest] += 1
            bbox = fitz.Rect(info["bbox"])
            raw.append({
                "page": page_index, "xref": xref, "digest": digest,
                "data": data, "ext": extracted.get("ext", "png"),
                "pixel_width": extracted["width"], "pixel_height": extracted["height"],
                "bbox": [round(v, 2) for v in bbox],
                "bbox_area_ratio": round((bbox.width * bbox.height) / page_area, 4),
                "captions_on_page": captions,
            })

    manifest = []
    written = set()
    candidate_index = 0
    for item in raw:
        width, height = item["pixel_width"], item["pixel_height"]
        aspect = max(width / max(height, 1), height / max(width, 1))
        reasons = []
        if width < min_width or height < min_height:
            reasons.append("too_small")
        if aspect > max_aspect:
            reasons.append("extreme_aspect_ratio")
        if item["bbox_area_ratio"] < 0.025:
            reasons.append("small_page_furniture")
        if digest_counts[item["digest"]] > 1:
            reasons.append("repeated_asset")
        accepted = not reasons and item["digest"] not in written
        record = {key: value for key, value in item.items() if key != "data"}
        caption = item["captions_on_page"][0] if item["captions_on_page"] else ""
        asset_type = "table" if caption.lower().startswith("table") or caption.startswith("表") else "figure"
        record.update({"accepted": accepted, "rejection_reasons": reasons, "path": None})
        if accepted:
            candidate_index += 1
            filename = f"candidate_{candidate_index:03d}_p{item['page']:02d}.{item['ext']}"
            path = output_dir / filename
            path.write_bytes(item["data"])
            try:
                with Image.open(path) as image:
                    image.verify()
            except Exception as exc:
                path.unlink(missing_ok=True)
                record["accepted"] = False
                record["rejection_reasons"].append(f"invalid_image:{exc}")
            else:
                record["path"] = str(path.resolve())
                written.add(item["digest"])
        record.update({
            "asset_id": f"{'TAB' if asset_type == 'table' else 'FIG'}_{candidate_index:03d}" if record["accepted"] else None,
            "type": asset_type,
            "caption": caption,
            "source_page": item["page"],
            "editable": False,
            "review_required": True,
        })
        manifest.append(record)

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps({
        "source": str(pdf_path.resolve()),
        "page_count": len(document),
        "accepted_count": sum(1 for item in manifest if item["accepted"]),
        "items": manifest,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Accepted {sum(1 for item in manifest if item['accepted'])} of {len(manifest)} embedded images")
    print(f"Review manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--min-width", type=int, default=320)
    parser.add_argument("--min-height", type=int, default=180)
    parser.add_argument("--max-aspect", type=float, default=4.5)
    args = parser.parse_args()
    extract(Path(args.pdf), Path(args.output_dir), args.min_width, args.min_height, args.max_aspect)


if __name__ == "__main__":
    main()
