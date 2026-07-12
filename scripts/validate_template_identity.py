"""Compare two template grammars and reject superficial color-only differentiation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def distance(first, second):
    a, b = first["identity"], second["identity"]
    score = 0.0
    score += 0.3 if a["navigation"] != b["navigation"] else 0.0
    score += 0.2 if a["composition"] != b["composition"] else 0.0
    score += 0.1 if a["panel_mode"] != b["panel_mode"] else 0.0
    ta, tb = first["geometry"]["title_box"], second["geometry"]["title_box"]
    score += min(0.2, math.sqrt(sum((ta[key] - tb[key]) ** 2 for key in ("left", "top", "width", "height"))))
    ratio_gap = abs(a["picture_to_text_ratio"] - b["picture_to_text_ratio"])
    score += min(0.2, ratio_gap / 2)
    return round(score, 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first")
    parser.add_argument("second")
    parser.add_argument("--minimum", type=float, default=0.12)
    parser.add_argument("--output")
    args = parser.parse_args()
    first = json.loads(Path(args.first).read_text(encoding="utf-8"))
    second = json.loads(Path(args.second).read_text(encoding="utf-8"))
    value = distance(first, second)
    result = {
        "first": first["template_name"], "second": second["template_name"],
        "identity_distance": value, "minimum": args.minimum, "passed": value >= args.minimum,
        "first_identity": first["identity"], "second_identity": second["identity"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
