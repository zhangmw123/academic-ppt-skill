"""Validate a standard template semantic specification against its bundled PPTX."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from pptx import Presentation


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.template_semantics import StandardTemplateSpecValidator


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_spec(path: Path, root: Path) -> dict:
    specification = json.loads(path.read_text(encoding="utf-8"))
    result = StandardTemplateSpecValidator().validate(specification)
    errors = list(result.errors)
    template = specification.get("template", {})
    pptx = (root / template.get("standard_editable_pptx", "")).resolve()
    if not pptx.is_file():
        errors.append(f"standard editable PPTX not found: {pptx}")
    else:
        if _sha256(pptx) != template.get("standard_pptx_sha256"):
            errors.append("standard editable PPTX hash does not match the semantic specification")
        try:
            slide_count = len(Presentation(pptx).slides)
        except Exception as exc:
            errors.append(f"standard editable PPTX cannot be parsed: {exc}")
        else:
            if slide_count != len(specification.get("pages", ())):
                errors.append(f"PPTX has {slide_count} slides; specification has {len(specification.get('pages', ())) }")
    return {
        "specification": str(path.resolve()),
        "template_id": template.get("id"),
        "passed": not errors,
        "errors": errors,
        "observations": list(result.observations),
        "page_count": len(specification.get("pages", ())),
        "module_count": sum(len(page.get("semantic_modules", ())) for page in specification.get("pages", ())),
        "child_slot_count": sum(
            len(module.get("child_slots", ()))
            for page in specification.get("pages", ())
            for module in page.get("semantic_modules", ())
        ),
        "product_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specifications", nargs="+")
    parser.add_argument("--skill-root", default=str(SKILL_ROOT))
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.skill_root).resolve()
    results = [validate_spec(Path(value), root) for value in args.specifications]
    report = {
        "schema_version": 1,
        "passed": all(result["passed"] for result in results),
        "results": results,
        "product_accepted": False,
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"[{status}] {result['template_id']}: pages={result['page_count']} "
            f"modules={result['module_count']} slots={result['child_slot_count']}"
        )
        for error in result["errors"]:
            print(f"       {error}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
