"""Resolve a stable bundled template ID or alias to its asset path."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.templates import TemplateCatalog


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection")
    parser.add_argument("--catalog", default=str(SKILL_ROOT / "references" / "template-catalog.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    selection = TemplateCatalog.load(args.catalog).select("", args.selection)
    result = selection.to_dict()
    result["absolute_path"] = selection.path
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["absolute_path"])


if __name__ == "__main__":
    main()
