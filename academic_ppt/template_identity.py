"""Compute palette-insensitive PPTX structure identity fingerprints."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image


COLOR_TAGS = {"srgbClr", "schemeClr", "sysClr", "prstClr", "scrgbClr", "hslClr"}
COLOR_ATTRIBUTES = {"val", "lastClr"}


def _canonical_xml(data: bytes) -> bytes:
    root = ElementTree.fromstring(data)
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        if local in COLOR_TAGS:
            for key in tuple(element.attrib):
                if key.rsplit("}", 1)[-1] in COLOR_ATTRIBUTES:
                    element.set(key, "COLOR")
    return ElementTree.tostring(root, encoding="utf-8")


def structure_manifest(path: Path | str) -> dict:
    source = Path(path).resolve()
    parts = []
    media = []
    with zipfile.ZipFile(source) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            data = archive.read(info.filename)
            if info.filename.endswith((".xml", ".rels")):
                try:
                    digest = hashlib.sha256(_canonical_xml(data)).hexdigest()
                except ElementTree.ParseError:
                    digest = hashlib.sha256(data).hexdigest()
                parts.append({"name": info.filename, "sha256_without_palette": digest})
            elif info.filename.startswith("ppt/media/"):
                dimensions = None
                try:
                    with Image.open(io.BytesIO(data)) as image:
                        dimensions = [image.width, image.height, image.format]
                except Exception:
                    pass
                media.append({"name": info.filename, "dimensions": dimensions})
            else:
                parts.append({"name": info.filename, "sha256": hashlib.sha256(data).hexdigest()})
    payload = {"parts": parts, "media": media}
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def compare_structure(first: Path | str, second: Path | str) -> dict:
    left = structure_manifest(first)
    right = structure_manifest(second)
    return {
        "first": str(Path(first).resolve()),
        "second": str(Path(second).resolve()),
        "first_fingerprint": left["fingerprint"],
        "second_fingerprint": right["fingerprint"],
        "passed": left["fingerprint"] == right["fingerprint"],
        "first_media": left["media"],
        "second_media": right["media"],
    }
