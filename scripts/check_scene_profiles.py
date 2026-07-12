"""Regression-check every bundled academic presentation scene profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_scene_plan import validate_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", default=str(Path(__file__).resolve().parents[1] / "references" / "scene-profiles.json"))
    parser.add_argument("--output")
    args = parser.parse_args()
    profiles = json.loads(Path(args.profiles).read_text(encoding="utf-8"))
    results = []
    for scene, profile in profiles["profiles"].items():
        valid_plan = {
            "scene": scene, "deck_scope": "complete", "evidence_state": profile["evidence_states"][0],
            "coverage_tags": profile["required_tags"],
            "argument_units": profile["argument_chain"],
            "section_variant": next(iter(profile["default_variants"])),
            "sections": next(iter(profile["default_variants"].values())),
            "pages": [
                {
                    "page_id": f"P{index + 1:02d}",
                    "page_role": "evidence",
                    "visual_strategy": "native_table",
                    "page_payload": {
                        "claim": f"Regression claim {index + 1}",
                        "supporting_unit_ids": [f"E{index + 1:02d}A", f"E{index + 1:02d}B"],
                        "evidence_carriers": [f"TAB_{index + 1:02d}"],
                        "interpretation": "The fixture evidence supports the scene argument unit.",
                        "density": {
                            "module_count": 3,
                            "evidence_unit_count": 2,
                            "carrier_count": 1,
                            "status": "adequate",
                        },
                    },
                }
                for index in range(profile["complete_min"])
            ],
        }
        if scene == "组会-文献精读":
            valid_plan["pages"][-1].update({
                "page_role": "transfer",
                "text_bindings": [{
                    "shape_id": 1,
                    "content": (
                        "迁移论文的问题路由和证据追溯机制；验证社区划分是否适配课题数据。"
                        "先复现最小流程，设置无社区、静态社区和分层社区三组消融实验，"
                        "比较正确率、覆盖率、可追溯性与响应延迟指标；记录数据规模、"
                        "检索参数、失败案例和人工评估边界，最后依据收益与成本决定下一步集成。"
                    ),
                }],
            })
        valid_result = validate_plan(valid_plan, profiles)
        short_plan = dict(valid_plan)
        short_plan["pages"] = [{"page_id": "P01"}]
        short_result = validate_plan(short_plan, profiles)
        passed = valid_result["passed"] and not short_result["passed"]
        results.append({
            "scene": scene, "passed": passed,
            "valid_plan": valid_result, "short_complete_rejected": not short_result["passed"],
        })
    report = {
        "profile_count": len(results), "passed_count": sum(item["passed"] for item in results),
        "results": results,
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in results:
        print(f"[{'PASS' if item['passed'] else 'FAIL'}] {item['scene']}")
    raise SystemExit(0 if report["passed_count"] == report["profile_count"] else 1)


if __name__ == "__main__":
    main()
