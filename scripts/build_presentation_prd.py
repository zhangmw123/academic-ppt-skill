"""Build the user-facing, page-by-page presentation PRD from a planned deck."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_optional(path: str | None) -> dict:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def as_text(value, fallback="-") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, list):
        return "；".join(str(item) for item in value) or fallback
    if isinstance(value, dict):
        return "；".join(f"{key}: {val}" for key, val in value.items()) or fallback
    return str(value).replace("\n", "<br>")


def evidence_index(payload: dict) -> dict:
    items = payload.get("items", payload.get("evidence", []))
    return {str(item.get("id")): item for item in items if item.get("id")}


def asset_index(payload: dict) -> dict:
    items = payload.get("items", payload.get("assets", []))
    return {str(item.get("asset_id", item.get("id"))): item for item in items if item.get("asset_id", item.get("id"))}


def validate(plan: dict) -> list[str]:
    errors = []
    for field in ("scene", "duration_minutes", "sections", "pages"):
        if not plan.get(field):
            errors.append(f"missing top-level field: {field}")
    for page in plan.get("pages", []):
        page_id = page.get("page_id", "UNKNOWN")
        page_role = page.get("page_role", page.get("layout"))
        for field in ("title", "page_role", "question_answered", "time_seconds"):
            if not page.get(field):
                errors.append(f"{page_id}: missing {field}")
        if page_role not in {"cover", "agenda", "ending", "section"}:
            if not page.get("content_units"):
                errors.append(f"{page_id}: missing content_units")
            if not page.get("visual_strategy"):
                errors.append(f"{page_id}: missing visual_strategy")
            if not page.get("template_layout_need"):
                errors.append(f"{page_id}: missing template_layout_need")
            payload = page.get("page_payload", {})
            if not payload.get("claim"):
                errors.append(f"{page_id}: missing page_payload.claim")
            if not payload.get("supporting_unit_ids"):
                errors.append(f"{page_id}: missing page_payload.supporting_unit_ids")
            if not (payload.get("interpretation") or payload.get("boundary")):
                errors.append(f"{page_id}: page_payload requires interpretation or boundary")
    return errors


def build(plan: dict, evidence: dict, assets: dict, grammar: dict) -> str:
    evidence_by_id = evidence_index(evidence)
    assets_by_id = asset_index(assets)
    pages = plan.get("pages", [])
    total_seconds = sum(int(page.get("time_seconds", 0) or 0) for page in pages)
    lines = [
        "# PPT 逐页规划预览（Presentation PRD）",
        "",
        "> 本文件用于用户裁决内容、顺序、页数、模板布局和素材使用。确认前不得生成完整 PPT。",
        "",
        "## 任务摘要",
        "",
        f"- 场景：{as_text(plan.get('scene'))}",
        f"- 汇报目标：{as_text(plan.get('objective'))}",
        f"- 听众：{as_text(plan.get('audience'))}",
        f"- 汇报时间：{as_text(plan.get('duration_minutes'))} 分钟",
        f"- 计划页数：{len(pages)} 页",
        f"- 逐页讲述预算：{total_seconds // 60} 分 {total_seconds % 60} 秒",
        f"- 证据状态：{as_text(plan.get('evidence_state'))}",
        f"- 模板：{as_text(plan.get('template_path', grammar.get('template_name')))}",
        f"- 模板策略：{as_text(plan.get('template_mode', 'template_native'))}",
        f"- 配色：{as_text(plan.get('palette', '沿用模板'))}",
        f"- 字体：{as_text(plan.get('font_policy', '沿用模板'))}",
        f"- Logo：{as_text(plan.get('logo_path', '未提供，保留模板留白或移除样例 Logo'))}",
        "",
        "## 用户确认的分块",
        "",
    ]
    for index, section in enumerate(plan.get("sections", []), 1):
        lines.append(f"{index}. {section}")

    lines.extend([
        "",
        "## 讲述逻辑",
        "",
        as_text(plan.get("storyline", plan.get("argument_chain"))),
        "",
        "## 逐页预览",
        "",
        "| 页码 | 板块 | 本页结论与支撑 | 解释/边界 | 证据载体 | 视觉与模板布局 | 时间 | 承接 |",
        "|---:|---|---|---|---|---|---:|---|",
    ])

    for index, page in enumerate(pages, 1):
        evidence_labels = []
        for evidence_id in page.get("evidence_ids", []):
            item = evidence_by_id.get(str(evidence_id), {})
            label = item.get("claim", item.get("summary", ""))
            evidence_labels.append(f"{evidence_id}{': ' + label if label else ''}")
        asset_labels = []
        for asset_id in page.get("asset_ids", []):
            item = assets_by_id.get(str(asset_id), {})
            label = item.get("caption", item.get("semantic_summary", ""))
            asset_labels.append(f"{asset_id}{': ' + label if label else ''}")
        source_material = evidence_labels + asset_labels
        payload = page.get("page_payload", {})
        support = payload.get("supporting_unit_ids", page.get("evidence_ids", []))
        claim_and_support = f"{payload.get('claim', page.get('title', '-'))}<br>支撑：{as_text(support)}"
        interpretation = payload.get("interpretation") or payload.get("boundary") or "-"
        carriers = payload.get("evidence_carriers", source_material)
        layout = page.get("template_layout_need", {})
        source_slide = page.get("source_slide_index", "待匹配")
        visual = f"{page.get('visual_strategy', '-')}；需求={as_text(layout)}；模板页={source_slide}"
        lines.append(
            "| {index} | {section} | {claim} | {interpretation} | {carriers} | {visual} | {seconds}s | {transition} |".format(
                index=index,
                section=as_text(page.get("section")),
                claim=as_text(claim_and_support),
                interpretation=as_text(interpretation),
                carriers=as_text(carriers),
                visual=visual,
                seconds=int(page.get("time_seconds", 0) or 0),
                transition=as_text(page.get("next_link")),
            )
        )

    missing = plan.get("missing_information", [])
    visual_tasks = plan.get("supplemental_visuals", [])
    risks = plan.get("risks", [])
    lines.extend([
        "",
        "## 素材与补充绘图",
        "",
        f"- 已登记证据：{len(evidence_by_id)} 条",
        f"- 已登记公式、图、表素材：{len(assets_by_id)} 项",
        f"- 计划补充绘图：{as_text(visual_tasks)}",
        "- 补充绘图只能解释已确认关系，不得补造实验数据、结果或科学事实。",
        "",
        "## 缺失信息与风险",
        "",
        f"- 缺失信息：{as_text(missing)}",
        f"- 风险：{as_text(risks)}",
        "",
        "## 模板复用约束",
        "",
        "- 默认复制并编辑模板原页；文本框、图形自身文字和组合子对象均直接绑定，禁止另画同用途文本框覆盖。",
        "- 样例图片可以删除或替换；外框与独立内层占位框按父子组件处理，避免留下粘连框或孤立标签。",
        "- 烘焙在位图中的占位框使用清洁缓存版本；临时遮罩必须单独批准并说明原因。",
        "- 导航栏统一字体和字号，只将当前板块设为模板原有的深色激活状态。",
        "- 用户提供 PNG Logo 时，替换模板 Logo 槽位或写入已登记的 Logo 留白区域。",
        "- 自由绘制页面必须在逐页计划中写明 fallback_reason。",
        "",
        "## 裁决",
        "",
        f"- 当前状态：{'已确认' if plan.get('confirmed') else '等待用户确认'}",
        f"- 确认时间：{as_text(plan.get('confirmed_at'))}",
        f"- 确认说明：{as_text(plan.get('confirmation_note'))}",
        "",
        "用户可直接提出删页、换序、合并、拆分、改标题、替换板块或调整模板页。",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--evidence")
    parser.add_argument("--assets")
    parser.add_argument("--grammar")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    errors = validate(plan)
    if errors:
        raise SystemExit("\n".join(errors))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build(plan, load_optional(args.evidence), load_optional(args.assets), load_optional(args.grammar)),
        encoding="utf-8",
    )
    print(f"Presentation PRD: {output}")


if __name__ == "__main__":
    main()
