"""Forward-test all bundled templates with real sources across research scenes."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from export_preview import list_slide_images


SKILL_ROOT = Path(__file__).resolve().parents[1]

MATRIX = (
    ("T01", "组会-文献精读", "paper", 10),
    ("T02", "学术会议报告", "paper", 8),
    ("T03", "毕业答辩", "thesis", 18),
    ("T04", "科研项目申报", "thesis", 12),
    ("T05", "开题答辩", "thesis", 12),
    ("T06", "中期考核", "thesis", 12),
    ("T07", "组会-课题进展", "thesis", 8),
    ("T08", "项目中期与结题", "thesis", 10),
)


def write_report(report_path: Path, cases: list[dict]) -> dict:
    report = {
        "schema_version": 2,
        "matrix_passed": len(cases) == len(MATRIX) and all(case["passed"] for case in cases),
        "product_acceptance_claimed": False,
        "completed_case_count": len(cases),
        "expected_case_count": len(MATRIX),
        "cases": cases,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_suffix(f"{report_path.suffix}.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-source", required=True)
    parser.add_argument("--thesis-source", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--resume", action="store_true", help="Continue from a partial report.")
    parser.add_argument("--runtime", default="portable", choices=("portable", "powerpoint", "wps"))
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    report_path = Path(args.report).resolve()
    if output_root.exists() and any(output_root.iterdir()) and not args.resume:
        raise SystemExit(f"output root must be empty or absent: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    sources = {
        "paper": Path(args.paper_source).resolve(),
        "thesis": Path(args.thesis_source).resolve(),
    }
    previous = {}
    if args.resume and report_path.is_file():
        try:
            previous = {
                case["template_id"]: case
                for case in json.loads(report_path.read_text(encoding="utf-8")).get("cases", ())
                if case.get("passed")
            }
        except (OSError, json.JSONDecodeError):
            print(f"Ignoring unreadable partial report: {report_path}", file=sys.stderr)
    cases = []
    for template_id, scene, source_kind, pages in MATRIX:
        if template_id in previous:
            cases.append(previous[template_id])
            print(f"{template_id} {scene}: REUSED PASS")
            continue
        destination = output_root / f"{template_id}_{source_kind}"
        if args.resume and destination.exists():
            shutil.rmtree(destination)
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "build_complete_deck.py"),
            str(sources[source_kind]),
            "--scene", scene,
            "--template", template_id,
            "--output", str(destination),
            "--pages", str(pages),
            "--runtime", args.runtime,
        ]
        case = {
            "template_id": template_id,
            "scene": scene,
            "source_kind": source_kind,
            "pages": pages,
            "returncode": None,
            "passed": False,
        }
        try:
            completed = subprocess.run(
                command,
                cwd=SKILL_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            case["returncode"] = completed.returncode
            if completed.returncode == 0:
                result = json.loads((destination / "audit" / "complete_build_result.json").read_text(encoding="utf-8"))
                render = json.loads((destination / "audit" / "delivery_qa" / "render_report.json").read_text(encoding="utf-8"))
                preview_count = len(list_slide_images(destination / "deliverables" / "preview"))
                case.update({
                    "selected_template_id": result["template"]["id"],
                    "render_failed_error": render["failed_error"],
                    "preview_count": preview_count,
                    "product_accepted": result["product_accepted"],
                })
                case["passed"] = (
                    result["template"]["id"] == template_id
                    and result["page_count"] == pages
                    and render["failed_error"] == 0
                    and preview_count == pages
                    and result["product_accepted"] is False
                )
            else:
                case["failure"] = (completed.stderr or completed.stdout)[-4000:]
        except Exception as exc:
            case["failure"] = f"matrix runner exception: {exc}"
        cases.append(case)
        print(f"{template_id} {scene}: {'PASS' if case['passed'] else 'FAIL'}")
        write_report(report_path, cases)

    report = write_report(report_path, cases)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["matrix_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
