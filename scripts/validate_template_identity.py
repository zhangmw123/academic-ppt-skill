"""Compare two template grammars and reject superficial color-only differentiation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.object_qa import TemplateIdentityDifferenceGate


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
    if first.get("contract") == second.get("contract") == "standard_template_specification":
        checked = TemplateIdentityDifferenceGate().compare([first, second])
        first_id = first["template"]["id"]
        second_id = second["template"]["id"]
        first_features = set(first["template_identity"]["identity_features"])
        second_features = set(second["template_identity"]["identity_features"])
        union = first_features | second_features
        similarity = len(first_features & second_features) / max(len(union), 1)
        value = round(1 - similarity, 3)
        result = {
            "contract": "standard_template_identity_difference",
            "first": first_id,
            "second": second_id,
            "identity_distance": value,
            "minimum": args.minimum,
            "signatures": checked.signatures,
            "errors": list(checked.errors),
            "passed": checked.passed and value >= args.minimum,
            "product_accepted": False,
        }
    else:
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
