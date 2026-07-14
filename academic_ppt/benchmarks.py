"""Validate the fixed ten-scene Skill release matrix without fake product acceptance."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .profiles import PROFILE_KEYWORDS
from .scenes import SceneCatalog


@dataclass(frozen=True)
class SceneBenchmarkCase:
    case_id: str
    scene: str
    method_profile: str
    evidence_state: str
    section_variant: str
    target_pages: int
    duration_minutes: float
    template_id: str
    source_claims: tuple[str, ...]
    required_tags: tuple[str, ...]
    argument_units: tuple[str, ...]


class SceneBenchmarkSuite:
    """Keep synthetic fixtures contract-only; product runs require real sources."""

    def __init__(self, cases: Iterable[SceneBenchmarkCase]):
        self.cases = tuple(cases)
        self._validate_manifest()

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SceneBenchmarkSuite":
        source = Path(path) if path else Path(__file__).resolve().parents[1] / "references" / "scene-benchmarks.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError(f"unsupported scene benchmark schema: {payload.get('schema_version')}")
        return cls(SceneBenchmarkCase(
            case_id=item["case_id"], scene=item["scene"], method_profile=item["method_profile"],
            evidence_state=item["evidence_state"], section_variant=item["section_variant"],
            target_pages=int(item["target_pages"]), duration_minutes=float(item["duration_minutes"]),
            template_id=item["template_id"], source_claims=tuple(item["source_claims"]),
            required_tags=tuple(item["required_tags"]), argument_units=tuple(item["argument_units"]),
        ) for item in payload["cases"])

    def case(self, case_id: str) -> SceneBenchmarkCase:
        try:
            return next(case for case in self.cases if case.case_id == case_id)
        except StopIteration as exc:
            raise ValueError(f"unknown scene benchmark: {case_id}") from exc

    def run_case(
        self,
        case: SceneBenchmarkCase,
        output_root: Path | str,
        *,
        require_runtime: bool = False,
        runtime: str = "powerpoint",
        template_selection: Path | str | None = None,
        source_paths: Iterable[Path | str] | None = None,
    ) -> dict:
        root = Path(output_root).resolve()
        root.mkdir(parents=True, exist_ok=True)
        sources = [Path(value).resolve() for value in (source_paths or ())]
        if not sources:
            result = {
                "case_id": case.case_id,
                "scene": case.scene,
                "benchmark_class": "synthetic_scene_contract",
                "contract_passed": True,
                "pipeline_completed": False,
                "product_accepted": False,
                "passed": False,
                "reason": "No real representative source is configured; synthetic claims cannot satisfy product acceptance.",
            }
            (root / "benchmark_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

        skill_root = Path(__file__).resolve().parents[1]
        command = [
            sys.executable, str(skill_root / "scripts" / "build_complete_deck.py"),
            *(str(path) for path in sources),
            "--scene", case.scene,
            "--template", str(template_selection or case.template_id),
            "--output", str(root / "product"),
            "--pages", str(case.target_pages),
            "--runtime", runtime,
        ]
        if require_runtime:
            command.append("--formal")
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
        build_result_path = root / "product" / "audit" / "complete_build_result.json"
        build_result = json.loads(build_result_path.read_text(encoding="utf-8")) if build_result_path.is_file() else {}
        result = {
            "case_id": case.case_id,
            "scene": case.scene,
            "benchmark_class": "real_source_product_candidate",
            "contract_passed": True,
            "pipeline_completed": completed.returncode == 0,
            "product_accepted": bool(build_result.get("product_accepted")),
            "passed": bool(build_result.get("product_accepted")),
            "error": None if completed.returncode == 0 else (completed.stderr or completed.stdout).strip(),
        }
        (root / "benchmark_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def run(
        self,
        output_dir: Path | str,
        *,
        case_ids: Iterable[str] | None = None,
        keep_going: bool = True,
        **kwargs,
    ) -> dict:
        output = Path(output_dir).resolve()
        output.mkdir(parents=True, exist_ok=True)
        selected = [self.case(case_id) for case_id in case_ids] if case_ids else list(self.cases)
        results = []
        for case in selected:
            try:
                results.append(self.run_case(case, output / case.case_id, **kwargs))
            except Exception as exc:
                if not keep_going:
                    raise
                results.append({
                    "case_id": case.case_id,
                    "scene": case.scene,
                    "benchmark_class": "benchmark_execution_error",
                    "contract_passed": False,
                    "pipeline_completed": False,
                    "product_accepted": False,
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
        report = {
            "schema_version": 2,
            "contract_matrix_passed": bool(results) and all(item["contract_passed"] for item in results),
            "product_suite_passed": bool(results) and all(item["product_accepted"] for item in results),
            "passed": bool(results) and all(item["passed"] for item in results),
            "cases": results,
        }
        (output / "suite_result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def _validate_manifest(self) -> None:
        catalog = SceneCatalog.load()
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("scene benchmark case IDs must be unique")
        if {case.scene for case in self.cases} != set(catalog.profiles):
            raise ValueError("scene benchmark coverage must match the supported scene catalog")
        if len({case.scene for case in self.cases}) != len(self.cases):
            raise ValueError("each scene must have exactly one benchmark contract")
        for case in self.cases:
            profile = catalog.resolve(case.scene)
            if case.method_profile not in PROFILE_KEYWORDS:
                raise ValueError(f"unsupported method profile: {case.method_profile}")
            if not profile.complete_min <= case.target_pages <= profile.complete_max:
                raise ValueError(f"{case.case_id}: page budget is not complete")
            if case.section_variant not in profile.default_variants:
                raise ValueError(f"{case.case_id}: unknown section variant")
            if case.required_tags != profile.required_tags or case.argument_units != profile.argument_chain:
                raise ValueError(f"{case.case_id}: scene contract drift")
