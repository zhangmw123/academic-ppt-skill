"""Compile bundled PPTX templates into standard editable packages and semantic specs."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from academic_ppt.template_identity import compare_structure
from academic_ppt.object_qa import ObjectLevelQualityGate
from academic_ppt.template_semantics import (
    StandardTemplateCompiler,
    StandardTemplateSpecValidator,
    load_semantic_prototypes,
)
from apply_template_palette import transform
from export_preview import export_preview
from extract_template_grammar import extract as extract_template_grammar


DEFAULT_TEMPLATE_IDS = ("T01", "T03")


def _summarize_runtime_error(exc: Exception) -> str:
    value = " ".join(str(exc).split())
    if "0x80070570" in value:
        return (
            "PowerPoint image-render path failed with 0x80070570: file or directory is corrupted "
            "and unreadable (BadImageFormatException)."
        )
    return value[:600]


def _load_catalog(root: Path) -> list[dict]:
    payload = json.loads((root / "references" / "template-catalog.json").read_text(encoding="utf-8"))
    return payload["templates"]


def _identity_summary(source: Path, output: Path) -> dict:
    identity = compare_structure(source, output)
    return {
        "passed": identity["passed"],
        "source_fingerprint": identity["first_fingerprint"],
        "standard_fingerprint": identity["second_fingerprint"],
    }


def compile_template(
    *,
    root: Path,
    entry: dict,
    prototype: dict,
    work_dir: Path,
    repackage: bool,
    render_check: bool,
) -> dict:
    template_id = entry["id"]
    source = (root / entry["source_path"]).resolve()
    standard = (root / entry["path"]).resolve()
    semantic_path_value = entry.get("semantic_spec_path")
    if not semantic_path_value:
        raise ValueError(f"{template_id} has no semantic_spec_path in template-catalog.json")
    semantic_path = (root / semantic_path_value).resolve()
    if repackage:
        if entry.get("source_fidelity") != "complete_structure_recompile":
            raise ValueError(f"{template_id} cannot be repackaged as complete source structure")
        transform(source, standard, None, None, 0.12)
    if not source.is_file() or not standard.is_file():
        raise FileNotFoundError(source if not source.is_file() else standard)

    identity = _identity_summary(source, standard)
    if entry.get("source_fidelity") == "complete_structure_recompile" and not identity["passed"]:
        raise ValueError(f"{template_id} standard package changed source structure")

    template_work = work_dir / template_id
    grammar_path = template_work / "template_grammar.json"
    extract_template_grammar(standard, grammar_path, template_work / "grammar_assets")
    grammar = json.loads(grammar_path.read_text(encoding="utf-8"))
    specification = StandardTemplateCompiler().compile(
        template_id=template_id,
        catalog_entry=entry,
        grammar=grammar,
        prototype=prototype,
        skill_root=root,
    )
    validation = StandardTemplateSpecValidator().validate(specification)
    if not validation.passed:
        raise ValueError("; ".join(validation.errors))
    semantic_path.parent.mkdir(parents=True, exist_ok=True)
    semantic_path.write_text(json.dumps(specification, ensure_ascii=False, indent=2), encoding="utf-8")
    object_qa = ObjectLevelQualityGate().inspect(standard, specification)
    if not object_qa.passed:
        raise ValueError("object-level template QA failed: " + "; ".join(object_qa.errors))

    render_status = "not_run"
    render_error = None
    preview_count = 0
    if render_check:
        try:
            preview_dir = template_work / "powerpoint_preview"
            export_preview(standard, preview_dir, "powerpoint", 1600, 900)
            preview_count = len(list(preview_dir.glob("slide-*.png")))
            render_status = "passed" if preview_count == len(specification["pages"]) else "failed"
            if render_status == "failed":
                render_error = f"expected {len(specification['pages'])} slides; rendered {preview_count}"
        except Exception as exc:
            render_status = "failed"
            render_error = _summarize_runtime_error(exc)

    media_archetypes = [
        {
            "page_id": page["page_id"],
            "scope": page["media_layout"]["scope"],
            "kind": page["media_layout"]["kind"],
            "slot_count": page["media_layout"]["slot_count"],
        }
        for page in specification["pages"]
        if page["media_layout"]["slot_count"]
    ]
    return {
        "template_id": template_id,
        "standard_editable_pptx": entry["path"],
        "semantic_specification": entry["semantic_spec_path"],
        "slide_count": len(specification["pages"]),
        "semantic_module_count": sum(len(page["semantic_modules"]) for page in specification["pages"]),
        "child_slot_count": sum(
            len(module["child_slots"])
            for page in specification["pages"]
            for module in page["semantic_modules"]
        ),
        "media_archetypes": media_archetypes,
        "identity_signature": specification["template_identity"]["identity_signature"],
        "structure_identity": identity,
        "semantic_compile_passed": validation.passed,
        "object_qa_passed": object_qa.passed,
        "object_qa_observations": list(object_qa.observations),
        "powerpoint_visual_review": render_status,
        "powerpoint_preview_count": preview_count,
        "powerpoint_error": render_error,
        "product_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--templates",
        default=",".join(DEFAULT_TEMPLATE_IDS),
        help="Comma-separated catalog IDs. The current completed prototype batch is T01,T03.",
    )
    parser.add_argument(
        "--repackage",
        action="store_true",
        help="Rebuild complete-structure PPTX packages from their catalog source before semantic compilation.",
    )
    parser.add_argument(
        "--render-check",
        action="store_true",
        help="Also require a Windows PowerPoint render of every compiled standard template.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[1] / "references" / "compiled-template-report.json"),
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    catalog = _load_catalog(root)
    by_id = {item["id"]: item for item in catalog}
    requested = tuple(value.strip().upper() for value in args.templates.split(",") if value.strip())
    unknown = sorted(set(requested) - set(by_id))
    if unknown:
        raise SystemExit(f"unknown template IDs: {unknown}")
    prototypes = load_semantic_prototypes(root / "references" / "template-semantic-prototypes.json")
    missing_prototypes = sorted(set(requested) - set(prototypes))
    if missing_prototypes:
        raise SystemExit(f"semantic prototypes are not completed for: {missing_prototypes}")

    results = []
    failures = []
    with tempfile.TemporaryDirectory(prefix="academic-ppt-standard-template-") as temp_dir:
        for template_id in requested:
            try:
                result = compile_template(
                    root=root,
                    entry=by_id[template_id],
                    prototype=prototypes[template_id],
                    work_dir=Path(temp_dir),
                    repackage=args.repackage,
                    render_check=args.render_check,
                )
            except Exception as exc:
                failures.append({"template_id": template_id, "error": str(exc)})
                print(f"[FAIL] {template_id}: {exc}")
            else:
                results.append(result)
                print(
                    f"[PASS] {template_id}: pages={result['slide_count']} "
                    f"modules={result['semantic_module_count']} slots={result['child_slot_count']}"
                )

    remaining = sorted(set(by_id) - {result["template_id"] for result in results})
    report = {
        "schema_version": 2,
        "contract": "standard_template_semantic_compilation",
        "requested_templates": list(requested),
        "semantic_compile_passed": not failures and len(results) == len(requested),
        "render_check_requested": args.render_check,
        "render_check_passed": bool(
            args.render_check
            and results
            and all(result["powerpoint_visual_review"] == "passed" for result in results)
        ),
        "templates": results,
        "failures": failures,
        "remaining_templates": remaining,
        "all_eight_templates_complete": not remaining and not failures,
        "product_accepted": False,
        "release_note": "Semantic compilation is a prerequisite only; all eight templates and formal PowerPoint review remain mandatory.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {output.resolve()}")
    failed = bool(failures) or (args.render_check and not report["render_check_passed"])
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
