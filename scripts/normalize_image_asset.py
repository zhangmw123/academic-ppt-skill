"""Normalize an external or generated image for reliable PowerPoint embedding."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def normalize(source: Path, output: Path, max_side: int = 3200):
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        if max(image.size) > max_side:
            image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() in {".jpg", ".jpeg"}:
            image.save(output, "JPEG", quality=92, optimize=True, progressive=False)
        else:
            image.save(output, "PNG", optimize=True)
    print(f"Normalized {source} -> {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--max-side", type=int, default=3200)
    args = parser.parse_args()
    normalize(Path(args.source), Path(args.output), args.max_side)


if __name__ == "__main__":
    main()
