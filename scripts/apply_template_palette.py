"""Prepare a PPTX by normalizing media and optionally recoloring editable objects."""

from __future__ import annotations

import argparse
import colorsys
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image


SRGB = re.compile(rb'(<a:srgbClr\b[^>]*\bval=")([0-9A-Fa-f]{6})(")')


def rgb(hex_value: str) -> tuple[float, float, float]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hue_distance(first: float, second: float) -> float:
    delta = abs(first - second)
    return min(delta, 1 - delta)


def discover_accent(xml_parts: list[bytes]) -> str:
    colors = Counter(match.group(2).decode("ascii").upper() for data in xml_parts for match in SRGB.finditer(data))
    candidates = []
    for value, count in colors.items():
        red, green, blue = rgb(value)
        hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
        if saturation >= 0.2 and 0.12 <= lightness <= 0.78:
            candidates.append((count * (0.5 + saturation), value))
    return max(candidates, default=(0, "2B579A"))[1]


def recolor(value: str, source_hue: float, target_hue: float, tolerance: float) -> str:
    red, green, blue = rgb(value)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    if saturation < 0.12 or hue_distance(hue, source_hue) > tolerance:
        return value.upper()
    distance = (hue - source_hue + 0.5) % 1 - 0.5
    new_hue = (target_hue + distance * 0.25) % 1
    new_saturation = min(0.78, max(0.18, saturation))
    converted = colorsys.hls_to_rgb(new_hue, lightness, new_saturation)
    return "".join(f"{round(channel * 255):02X}" for channel in converted)


def normalize_media(data: bytes, suffix: str, source_hue: float | None = None,
                    target_hue: float | None = None, tolerance: float = 0.12) -> tuple[bytes, bool, bool]:
    if suffix.lower() != ".png":
        return data, False, False
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            clean = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            recolored = False
            # Recolor flat icons and template ornaments, not photographs.
            probe = clean.copy()
            probe.thumbnail((128, 128))
            flat_graphic = probe.convert("RGB").getcolors(maxcolors=4096) is not None
            if flat_graphic and source_hue is not None and target_hue is not None:
                rgba = clean.convert("RGBA")
                pixels = []
                for red, green, blue, alpha in rgba.getdata():
                    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
                    if alpha and saturation >= 0.16 and hue_distance(hue, source_hue) <= tolerance:
                        converted = colorsys.hls_to_rgb(target_hue, lightness, min(0.78, max(0.18, saturation)))
                        red, green, blue = (round(channel * 255) for channel in converted)
                        recolored = True
                    pixels.append((red, green, blue, alpha))
                rgba.putdata(pixels)
                clean = rgba
            buffer = io.BytesIO()
            clean.save(buffer, format="PNG", optimize=False)
            return buffer.getvalue(), True, recolored
    except Exception:
        return data, False, False


def transform(input_path: Path, output_path: Path, palette: dict | None, source_accent: str | None, tolerance: float):
    with zipfile.ZipFile(input_path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    xml_parts = [data for info, data in entries if info.filename.endswith((".xml", ".rels"))]
    source = (source_accent or discover_accent(xml_parts)).lstrip("#")
    target = palette["colors"]["primary"].lstrip("#") if palette else source
    source_hue = colorsys.rgb_to_hls(*rgb(source))[0]
    target_hue = colorsys.rgb_to_hls(*rgb(target))[0]
    replacements = Counter()
    normalized_media = 0
    recolored_media = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as target_zip:
        for info, data in entries:
            if info.is_dir():
                continue
            if info.filename.startswith("ppt/media/"):
                data, changed, raster_recolored = normalize_media(
                    data, Path(info.filename).suffix,
                    source_hue if palette else None, target_hue if palette else None, tolerance,
                )
                normalized_media += int(changed)
                recolored_media += int(raster_recolored)
            if palette is not None and info.filename.endswith(".xml"):
                def replace(match):
                    old = match.group(2).decode("ascii")
                    new = recolor(old, source_hue, target_hue, tolerance)
                    if new != old.upper():
                        replacements[(old.upper(), new)] += 1
                    return match.group(1) + new.encode("ascii") + match.group(3)
                data = SRGB.sub(replace, data)
            target_zip.writestr(info, data)
    return source.upper(), target.upper(), replacements, normalized_media, recolored_media


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--palette", default="preserve", help="Academic palette ID or preserve")
    parser.add_argument("--palettes", default=str(Path(__file__).resolve().parents[1] / "references" / "academic-palettes.json"))
    parser.add_argument("--source-accent", help="Optional source template accent such as #1F5B4D")
    parser.add_argument("--hue-tolerance", type=float, default=0.12)
    parser.add_argument("--report")
    args = parser.parse_args()
    palettes = json.loads(Path(args.palettes).read_text(encoding="utf-8"))["palettes"]
    if args.palette != "preserve" and args.palette not in palettes:
        raise SystemExit(f"unknown palette {args.palette}; choose from {sorted(palettes)}")
    selected_palette = None if args.palette == "preserve" else palettes[args.palette]
    source, target, replacements, normalized_media, recolored_media = transform(
        Path(args.input), Path(args.output), selected_palette, args.source_accent, args.hue_tolerance
    )
    report = {
        "input": str(Path(args.input).resolve()), "output": str(Path(args.output).resolve()),
        "palette": args.palette, "source_accent": f"#{source}", "target_accent": f"#{target}",
        "editable_color_replacements": [
            {"from": f"#{old}", "to": f"#{new}", "count": count}
            for (old, new), count in replacements.most_common()
        ],
        "normalized_png_count": normalized_media,
        "recolored_flat_png_count": recolored_media,
        "raster_warning": "Only flat PNG accents are hue-mapped; inspect photographs and complex colored sample images separately."
    }
    if args.report:
        output = Path(args.report)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"palette": args.palette, "source_accent": f"#{source}", "target_accent": f"#{target}", "replacement_pairs": len(replacements), "normalized_png_count": normalized_media, "recolored_flat_png_count": recolored_media}, ensure_ascii=False))


if __name__ == "__main__":
    main()
