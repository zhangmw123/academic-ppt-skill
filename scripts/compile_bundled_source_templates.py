"""Repackage selected bundled source templates without replacing their structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_template_palette import transform
from academic_ppt.template_identity import compare_structure


MAPPINGS = (
    ("assets/templates/绿色-科研风格PPT模版.pptx", "assets/powerpoint_templates/T01_green_research.pptx"),
    (
        "assets/templates/蓝色-学术答辩多版式通用模板 (Academic Defense Multi-Layout Template).pptx",
        "assets/powerpoint_templates/T03_blue_defense.pptx",
    ),
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    reports = []
    for source_value, output_value in MAPPINGS:
        source = root / source_value
        output = root / output_value
        source_accent, target_accent, replacements, normalized, recolored = transform(
            source, output, None, None, 0.12
        )
        identity = compare_structure(source, output)
        report = {
            "source": str(source.resolve()),
            "output": str(output.resolve()),
            "source_accent": source_accent,
            "target_accent": target_accent,
            "editable_color_replacements": len(replacements),
            "normalized_png_count": normalized,
            "recolored_png_count": recolored,
            "structure_identity": identity,
        }
        if not identity["passed"]:
            raise RuntimeError(f"structure identity changed while compiling {source.name}")
        reports.append(report)
        print(f"Compiled complete source structure: {source.name} -> {output.name}")
    report_path = root / "references" / "compiled-template-report.json"
    report_path.write_text(json.dumps({"schema_version": 1, "templates": reports}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
