"""Forward-test all bundled templates with real sources across research scenes."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]

MATRIX = (
    ("T01", "组会-文献精读", "paper", 8),
    ("T02", "学术会议报告", "paper", 8),
    ("T03", "毕业答辩", "thesis", 18),
    ("T04", "科研项目申报", "thesis", 12),
    ("T05", "开题答辩", "thesis", 12),
    ("T06", "中期考核", "thesis", 12),
    ("T07", "组会-课题进展", "thesis", 7),
    ("T08", "项目中期与结题", "thesis", 10),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-source", required=True)
    parser.add_argument("--thesis-source", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"output root must be empty or absent: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    sources = {
        "paper": Path(args.paper_source).resolve(),
        "thesis": Path(args.thesis_source).resolve(),
    }
    cases = []
    for template_id, scene, source_kind, pages in MATRIX:
        destination = output_root / f"{template_id}_{source_kind}"
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "build_complete_deck.py"),
            str(sources[source_kind]),
            "--scene", scene,
            "--template", template_id,
            "--output", str(destination),
            "--pages", str(pages),
        ]
        completed = subprocess.run(
            command,
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        case = {
            "template_id": template_id,
            "scene": scene,
            "source_kind": source_kind,
            "pages": pages,
            "returncode": completed.returncode,
            "passed": False,
        }
        if completed.returncode == 0:
            result = json.loads((destination / "audit" / "complete_build_result.json").read_text(encoding="utf-8"))
            render = json.loads((destination / "audit" / "delivery_qa" / "render_report.json").read_text(encoding="utf-8"))
            preview_count = len(list((destination / "deliverables" / "preview").glob("slide-*.png")))
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
        cases.append(case)
        print(f"{template_id} {scene}: {'PASS' if case['passed'] else 'FAIL'}")

    report = {
        "schema_version": 1,
        "matrix_passed": all(case["passed"] for case in cases),
        "product_acceptance_claimed": False,
        "cases": cases,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["matrix_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
