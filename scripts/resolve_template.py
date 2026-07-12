"""Resolve a stable bundled template ID or alias to its asset path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize(value: str) -> str:
    return "".join(value.strip().lower().split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection")
    parser.add_argument("--catalog", default=str(Path(__file__).resolve().parents[1] / "references" / "template-catalog.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    catalog_path = Path(args.catalog)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    wanted = normalize(args.selection)
    matches = []
    for item in catalog["templates"]:
        names = [item["id"], item["short_name"], *item.get("aliases", [])]
        if wanted in {normalize(name) for name in names}:
            matches.append(item)
    if len(matches) != 1:
        choices = ", ".join(f"{item['id']} {item['short_name']}" for item in catalog["templates"])
        raise SystemExit(f"template selection must match exactly one entry; choices: {choices}")
    result = dict(matches[0])
    result["absolute_path"] = str((catalog_path.resolve().parents[1] / result["path"]).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["absolute_path"])


if __name__ == "__main__":
    main()
