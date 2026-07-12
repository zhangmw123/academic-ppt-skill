"""Export PPTX slides to PNG with PowerPoint, WPS Presentation, or LibreOffice."""

from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_powerpoint() -> bool:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft Office/root/Office16/POWERPNT.EXE",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft Office/root/Office16/POWERPNT.EXE",
    ]
    return sys.platform == "win32" and any(path.exists() for path in candidates)


def find_wps() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"KWPP.Application\CLSID"):
            return True
    except OSError:
        return False


def export_with_powerpoint(pptx: Path, output_dir: Path, width: int, height: int) -> None:
    safe_in = str(pptx.resolve()).replace("'", "''")
    safe_out = str(output_dir.resolve()).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop'; $ppt=$null; $pres=$null; "
        "try { "
        "$ppt=New-Object -ComObject PowerPoint.Application; "
        f"$pres=$ppt.Presentations.Open('{safe_in}',$true,$true,$false); "
        f"$pres.Export('{safe_out}','PNG',{width},{height}); "
        "} finally { "
        "if($pres){$pres.Close(); [Runtime.InteropServices.Marshal]::ReleaseComObject($pres)|Out-Null}; "
        "if($ppt){$ppt.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($ppt)|Out-Null} "
        "}"
    )
    encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], check=True,
                   timeout=120, capture_output=True)


def export_with_wps(pptx: Path, output_dir: Path, width: int, height: int) -> None:
    safe_in = str(pptx.resolve()).replace("'", "''")
    safe_out = str(output_dir.resolve()).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop'; $app=$null; $pres=$null; "
        "try { "
        "$app=New-Object -ComObject KWPP.Application; "
        f"$pres=$app.Presentations.Open('{safe_in}',$true,$false,$false); "
        f"$pres.Export('{safe_out}','PNG',{width},{height}); "
        "} finally { "
        "if($pres){$pres.Close(); [Runtime.InteropServices.Marshal]::ReleaseComObject($pres)|Out-Null}; "
        "if($app){$app.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null} "
        "}"
    )
    encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
    subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded], check=True,
                   timeout=120, capture_output=True)


def export_with_libreoffice(pptx: Path, output_dir: Path, width: int, height: int) -> None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        raise RuntimeError("LibreOffice and pdftoppm are required for this preview engine")
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", temp, str(pptx)], check=True)
        pdf = Path(temp) / f"{pptx.stem}.pdf"
        scale = max(width / 13.333, height / 7.5) / 72
        subprocess.run([pdftoppm, "-png", "-r", str(round(scale * 72)), str(pdf), str(output_dir / "slide")], check=True)


def natural_key(path: Path):
    import re
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def build_contact_sheet(images: list[Path], output: Path, columns: int = 3) -> None:
    if not images:
        raise RuntimeError("No slide images were exported")
    thumb_w = 480
    with Image.open(images[0]) as first:
        thumb_h = round(thumb_w * first.height / first.width)
    label_h, gap = 34, 18
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w + (columns + 1) * gap,
                              rows * (thumb_h + label_h) + (rows + 1) * gap), "#E8EAED")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, path in enumerate(images):
        row, column = divmod(index, columns)
        x = gap + column * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h)
        with Image.open(path) as slide:
            thumb = slide.convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(thumb, (x, y + label_h))
        draw.text((x + 4, y + 8), f"Slide {index + 1}", fill="#202124", font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def export_preview(pptx: Path, output_dir: Path, engine: str, width: int, height: int):
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("*.PNG"):
        old.unlink()
    for old in output_dir.glob("*.png"):
        old.unlink()

    if engine == "auto":
        candidates = []
        if find_powerpoint():
            candidates.append(("powerpoint", export_with_powerpoint))
        if find_wps():
            candidates.append(("wps", export_with_wps))
        candidates.append(("libreoffice", export_with_libreoffice))
        failures = []
        selected = None
        for name, exporter in candidates:
            try:
                exporter(pptx, output_dir, width, height)
                selected = name
                break
            except Exception as exc:
                failures.append(f"{name}: {exc}")
        if selected is None:
            raise RuntimeError("No preview engine succeeded: " + " | ".join(failures))
    else:
        selected = engine
        if selected == "powerpoint":
            if not find_powerpoint():
                raise RuntimeError("PowerPoint is not installed")
            export_with_powerpoint(pptx, output_dir, width, height)
        elif selected == "wps":
            if not find_wps():
                raise RuntimeError("WPS Presentation COM is not registered")
            export_with_wps(pptx, output_dir, width, height)
        else:
            export_with_libreoffice(pptx, output_dir, width, height)

    images = sorted({path.resolve() for path in [*output_dir.glob("*.PNG"), *output_dir.glob("*.png")]}, key=natural_key)
    contact_sheet = output_dir / "contact-sheet.jpg"
    build_contact_sheet(images, contact_sheet)
    print(f"Exported {len(images)} slides with {selected}")
    print(f"Contact sheet: {contact_sheet}")
    return contact_sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--engine", choices=["auto", "powerpoint", "wps", "libreoffice"], default="auto")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()
    export_preview(Path(args.pptx), Path(args.output_dir), args.engine, args.width, args.height)


if __name__ == "__main__":
    main()
