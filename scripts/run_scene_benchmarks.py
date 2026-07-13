"""Run one or all fixed scene benchmarks through the V2 service workflow."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.benchmarks import SceneBenchmarkSuite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="case_ids", help="Run only this case ID; repeatable")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--formal", action="store_true", help="Require an authoritative runtime render")
    parser.add_argument("--runtime", choices=("powerpoint", "wps", "portable"), default="powerpoint")
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    output_dir = args.output_dir or Path.cwd() / "ppt_output" / "benchmarks" / stamp
    suite = SceneBenchmarkSuite.load(args.manifest)
    report = suite.run(
        output_dir,
        case_ids=args.case_ids,
        require_runtime=args.formal,
        runtime=args.runtime,
        keep_going=not args.fail_fast,
    )
    print(json.dumps({
        "output_dir": str(output_dir.resolve()),
        "passed": report["passed"],
        "case_count": len(report["cases"]),
        "failed_cases": [item["case_id"] for item in report["cases"] if not item["passed"]],
    }, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
