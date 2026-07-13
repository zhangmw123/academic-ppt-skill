"""Run the Academic PPT V2 CLI from any working directory."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from academic_ppt.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
