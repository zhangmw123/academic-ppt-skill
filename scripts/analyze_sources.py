"""Analyze research sources without creating a presentation or project lifecycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from academic_ppt.evidence import EvidenceGraph
from academic_ppt.ingest import SourceIngestor
from academic_ppt.profiles import ResearchMethodProfileResolver


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+")
    args = parser.parse_args()
    sources = [SourceIngestor().ingest(path) for path in args.sources]
    profiles = ResearchMethodProfileResolver().infer(sources)
    graph = EvidenceGraph.from_sources(sources)
    print(json.dumps({
        "source_count": len(sources),
        "sources": [source.to_dict() for source in sources],
        "method_profiles": {
            "primary": profiles.primary,
            "secondary": list(profiles.secondary),
            "basis": {key: list(value) for key, value in profiles.basis.items()},
        },
        "evidence": [node.to_dict() for node in graph.all()],
        "conflicts": [conflict.to_dict() for conflict in graph.conflicts()],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
