"""Audit all Academic PPT Skill 1.0 release evidence without optimistic defaults."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.release import ReleaseEvidenceAuditor  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default=str(SKILL_ROOT / "references" / "release-evidence.json"),
    )
    parser.add_argument("--output")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    report = ReleaseEvidenceAuditor(SKILL_ROOT).audit(args.manifest)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["release_accepted"] and not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
