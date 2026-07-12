"""Validate evidence-bound visual tasks and external image provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


KINDS = {
    "source_figure", "matplotlib_chart", "native_diagram", "web_image",
    "generated_image", "native_table", "text_only",
}
LICENSE_OK = {
    "CC0", "Public Domain", "CC BY", "CC BY-SA", "user-provided",
    "permission-granted", "institutional-approved",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks")
    parser.add_argument("--evidence")
    parser.add_argument("--asset-root", default=".")
    parser.add_argument("--require-outputs", action="store_true")
    args = parser.parse_args()
    path = Path(args.tasks)
    payload = json.loads(path.read_text(encoding="utf-8"))
    evidence_ids = None
    if args.evidence:
        ledger = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        evidence_ids = {item["id"] for item in ledger["items"]}

    errors, warnings, outputs = [], [], {}
    asset_root = Path(args.asset_root)
    for task in payload.get("tasks", []):
        task_id = task.get("task_id", "UNKNOWN")
        kind = task.get("kind")
        if kind not in KINDS:
            errors.append(f"{task_id}: unsupported kind {kind}")
        if not task.get("claim"):
            errors.append(f"{task_id}: missing claim")
        if kind not in {"text_only"} and not task.get("evidence_ids"):
            errors.append(f"{task_id}: missing evidence_ids")
        if evidence_ids is not None:
            missing = sorted(set(task.get("evidence_ids", [])) - evidence_ids)
            if missing:
                errors.append(f"{task_id}: unknown evidence IDs {missing}")
        output = task.get("output")
        if output:
            if output in outputs and not task.get("allow_reuse"):
                errors.append(f"{task_id}: output already used by {outputs[output]}")
            outputs[output] = task_id
            if args.require_outputs and not output.startswith("native:"):
                output_path = asset_root / output
                if not output_path.exists():
                    errors.append(f"{task_id}: output does not exist: {output_path}")
                elif kind in {"source_figure", "matplotlib_chart", "web_image", "generated_image"}:
                    try:
                        with Image.open(output_path) as image:
                            image.verify()
                    except Exception as exc:
                        errors.append(f"{task_id}: invalid image output {output_path}: {exc}")

        if kind == "matplotlib_chart":
            chart = task.get("chart", {})
            if not chart.get("type") or not chart.get("series"):
                errors.append(f"{task_id}: chart requires type and series")
            for series in chart.get("series", []):
                if not series.get("source_refs"):
                    errors.append(f"{task_id}: series {series.get('name')} lacks source_refs")
        elif kind == "native_diagram":
            spec = task.get("diagram", {})
            node_ids = {n.get("id") for c in spec.get("columns", []) for n in c.get("nodes", [])}
            if not node_ids:
                errors.append(f"{task_id}: diagram has no nodes")
            for edge in spec.get("edges", []):
                if edge.get("source") not in node_ids or edge.get("target") not in node_ids:
                    errors.append(f"{task_id}: edge references an unknown node")
        elif kind == "web_image":
            source = task.get("source", {})
            required = ("query", "page_url", "asset_url", "author", "license")
            for key in required:
                if not source.get(key):
                    errors.append(f"{task_id}: web image missing {key}")
            if source.get("license") not in LICENSE_OK:
                errors.append(f"{task_id}: unapproved or unknown license {source.get('license')}")
            if task.get("usage_role") not in {"subject", "context", "background"}:
                errors.append(f"{task_id}: web image needs usage_role")
            if task.get("usage_role") == "background" and not task.get("decorative_only"):
                warnings.append(f"{task_id}: background must not carry factual meaning")
        elif kind == "generated_image":
            if not task.get("generation", {}).get("prompt"):
                errors.append(f"{task_id}: generated image lacks reproducible prompt")
            if task.get("contains_factual_labels"):
                errors.append(f"{task_id}: factual labels must be rebuilt as editable PPT elements")

    result = {"tasks": len(payload.get("tasks", [])), "errors": errors, "warnings": warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
