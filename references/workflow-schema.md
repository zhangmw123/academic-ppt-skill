# Workflow artifact schemas

Use UTF-8 JSON. Every gated artifact contains `confirmed`, `confirmed_at`, and
`confirmation_note`. A renderer must reject missing or false confirmation unless
the current operation is an explicitly requested sample render.

The default workflow additionally creates `evidence_ledger.json`,
`source_assets.json`, `storyline_options.json`, `presentation_prd.md`,
`slide_content_lock.json`, `visual_system.json`, `template_grammar.json`, and
`layout_plan.json`. Explicit source-slide and shape binding is the default when a
template is selected.

## presentation_prd.md input page

Before rendering, every planned page must provide:

```json
{
  "page_id": "P07",
  "section": "阶段性成果",
  "page_role": "evidence",
  "title": "已完成三项核心实验，主要指标达到中期目标",
  "question_answered": "当前研究是否形成了足以支撑继续推进的证据？",
  "argument_units": ["what_evidence_exists"],
  "content_units": ["实验一结果", "实验二结果", "与中期指标对照"],
  "evidence_ids": ["E21", "E22"],
  "asset_ids": ["TAB_03", "FIG_08"],
  "page_payload": {
    "claim": "三项核心实验均达到中期目标",
    "supporting_unit_ids": ["EU_021", "EU_022", "EU_024"],
    "evidence_carriers": ["TAB_03", "FIG_08"],
    "interpretation": "指标方向一致，研究路径可继续推进",
    "boundary": "跨数据集稳定性仍待验证",
    "transition": "下一页解释当前误差来源",
    "density": {"module_count": 4, "evidence_unit_count": 3, "carrier_count": 2, "status": "adequate"}
  },
  "visual_strategy": "native_chart_plus_table",
  "template_layout_need": {"component_count": 3, "relationship": "comparison", "preferred_signatures": ["three_columns"]},
  "time_seconds": 55,
  "previous_link": "上一页说明已完成任务，本页验证这些任务产生了什么结果。",
  "next_link": "结果仍暴露两个误差来源，下一页解释问题与调整。"
}
```

Generate `presentation_prd.md` and show it for section, page, content, time,
visual, and template-layout decisions. Confirmation of page titles alone is
insufficient.

## dynamic_plan.json page

```json
{
  "page_id": "P09",
  "layout": "text_figure",
  "section": "实验验证",
  "title": "移除社区摘要使准确率下降 12.2 个百分点",
  "lead": "社区摘要是最关键的性能组件",
  "bullets": ["完整模型 Accuracy 89.4%", "移除摘要后降至 77.2%"],
  "image": "ppt_output/working/figures/figure_06.png",
  "caption": "Figure 6 | Ablation results",
  "page_conclusion": "社区摘要是关键知识索引，而非装饰模块。",
  "evidence_ids": ["E10", "E11"],
  "page_payload": {
    "claim": "社区摘要是最关键的性能组件",
    "supporting_unit_ids": ["E10", "E11"],
    "evidence_carriers": ["FIG_06"],
    "interpretation": "移除该组件导致所有消融设置中最大的性能下降",
    "boundary": "结论限于论文报告的数据集与消融设置",
    "transition": "下一页进一步分析下降来自哪些错误类型",
    "density": {"module_count": 3, "evidence_unit_count": 2, "carrier_count": 1, "status": "adequate"}
  },
  "visual_strategy": "source_chart",
  "speaker_notes": "先给完整模型，再比较移除组件后的下降。"
}
```

`page_conclusion` is optional and has no fixed on-slide label. Omit it when the
claim-led title already states the implication. Do not add `SO WHAT` mechanically
to every page.

## visual_tasks.json

Create one task for each required visual. Keep semantic extraction separate from
rendering so that relationships and numbers can be checked before drawing.

```json
{
  "schema_version": 1,
  "tasks": [
    {
      "task_id": "V01",
      "slide_id": "P08",
      "kind": "matplotlib_chart",
      "claim": "改进模型的准确率、召回率和 F1 均高于基线",
      "evidence_ids": ["E21", "E22"],
      "backend": "matplotlib",
      "output": "working/visuals/V01_metrics.png",
      "chart": {
        "type": "grouped_bar",
        "categories": ["准确率", "召回率", "F1"],
        "y_label": "百分比 (%)",
        "series": [
          {"name": "基线", "values": [92.1, 91.4, 91.7], "source_refs": ["表4-4"]},
          {"name": "本文模型", "values": [93.36, 91.96, 92.93], "source_refs": ["表4-4"]}
        ]
      },
      "fallback": "native_table"
    }
  ]
}
```

For a native diagram, replace `chart` with `diagram.columns` and
`diagram.edges`. Every node needs a stable ID; every edge references node IDs.
Store exact terminology from the source and mark presenter-created grouping as
`visual_inference`.

For a web image, include:

```json
{
  "kind": "web_image",
  "usage_role": "subject",
  "decorative_only": false,
  "source": {
    "query": "Yunnan native plant Wikimedia Commons",
    "page_url": "https://commons.wikimedia.org/wiki/File:...",
    "asset_url": "https://upload.wikimedia.org/...",
    "author": "...",
    "license": "CC BY-SA",
    "accessed_at": "2026-07-11"
  },
  "output": "working/external/plant.jpg"
}
```

Never accept an unknown license. Never let a decorative web or generated image
stand in for experimental evidence.

Top-level `sections` drives navigation. It may contain 2, 3, 4, 5, or 6 sections;
it does not need to match the source template. `logo_path` is optional and must be
an actual user or institutional asset.

Top-level `template_grammar` points to schema v3 grammar JSON. A native page sets
`source_slide_index`, `layout_signature`, and explicit shape bindings. The source
page must match component count and relationship; its original slots and layers
are part of the output contract.

## config.json

```json
{
  "schema_version": 2,
  "source_path": "paper.pdf",
  "scene": "毕业答辩",
  "template_path": "assets/templates/example.pptx",
  "language": "zh-CN",
  "duration_minutes": 20,
  "target_slides": 24,
  "sections": ["研究背景", "方法设计", "实验结果", "总结与展望"],
  "cover": {
    "presenter": "",
    "supervisor": "",
    "institution": "",
    "program": "",
    "date": ""
  },
  "speaker_notes": "concise",
  "interaction_mode": "gated",
  "confirmed": false,
  "confirmed_at": null,
  "confirmation_note": ""
}
```

## outline.json page

```json
{
  "page_id": "P07",
  "section": "实验结果",
  "type": "content",
  "title": "Community summaries contribute the largest accuracy gain",
  "purpose": "Use ablation evidence to identify the critical component.",
  "evidence": ["Accuracy falls from 89.4% to 77.2%."],
  "source_refs": [{"page": 10, "section": "3.2", "kind": "table", "label": "Table 3"}],
  "candidate_figures": ["Figure 6", "Table 3"],
  "speaker_notes_hint": "Explain the full model first, then compare removals."
}
```

## template_map.json archetype

```json
{
  "archetype": "text_figure_right",
  "source_slide_index": 12,
  "title_shape_id": 41,
  "body_shape_ids": [45],
  "image_box": {"left": 6.4, "top": 1.45, "width": 6.2, "height": 5.3, "unit": "inch"},
  "preserve_shape_ids": [2, 3, 7, 9],
  "clear_shape_ids": [45, 46],
  "notes": "Keep logo, top rule, side navigation, and footer."
}
```

## layout_plan.json

Top-level fields:

```json
{
  "schema_version": 3,
  "template_path": "template.pptx",
  "template_grammar": "ppt_output/template_grammar.json",
  "confirmed": false,
  "confirmed_at": null,
  "confirmation_note": "",
  "global_text_replacements": {
    "研究背景及现状": "论文概览",
    "Research Background": "Overview"
  },
  "navigation_contract": {
    "orientation": "top",
    "section_order": ["研究背景", "方法设计", "实验结果", "总结与展望"],
    "active_state": {"rule": "dark_fill_only"},
    "inactive_state": {"rule": "light_fill"},
    "font": {"family": "template_native", "size_pt": 9.0, "bold": false},
    "clear_protection": true
  },
  "pages": []
}
```

Use `global_text_replacements` for repeated template navigation labels that must
change consistently across all cloned slides. Matching is exact after trimming;
replacement preserves the source text style and is protected from
`clear_unbound_text`.

Page fields:

```json
{
  "page_id": "P07",
  "type": "content",
  "section": "实验结果",
  "title": "Community summaries contribute the largest accuracy gain",
  "source_slide_index": 18,
  "clear_unbound_text": true,
  "remove_shape_ids": [31],
  "remove_component_ids": ["S18_C07"],
  "preserve_shape_ids": [2, 3, 4, 8],
  "component_bindings": [
    {"component_id": "S18_C03", "role": "main_evidence", "content_ids": ["EU_021", "FIG_08"]}
  ],
  "text_bindings": [
    {"shape_id": 21, "content": "Community summaries contribute the largest accuracy gain"},
    {"shape_id": 26, "content": "Removing summaries: 89.4% -> 77.2%\nLargest drop among all ablations"}
  ],
  "image_bindings": [
    {
      "path": "ppt_output/working/figures/figure_06.png",
      "replace_shape_id": 30,
      "fit": "contain"
    }
  ],
  "source_refs": [{"page": 10, "label": "Table 3"}],
  "speaker_notes": "The full model reaches 89.4% accuracy. Removing community summaries causes the largest decline."
}
```

`shape_id` is the PowerPoint non-visual shape ID reported by
`parse_template.py`. It is stable within a source slide and must not be confused
with placeholder index or iteration order.

Use `remove_shape_ids` for template pictures, old logos, sample charts, or other
non-text shapes that do not belong in the generated page. Every ID must exist on
the selected source slide.

Prefer `remove_component_ids` when a sample card consists of a frame, icon,
caption, and picture. Component removal prevents orphan shapes. A nested inner
placeholder can be removed while preserving its outer panel. Add new objects only
through `additions`, and require `fallback_reason` for each addition when the
template has no compatible editable component. Each addition also records a
`binding_ref`, such as `image_bindings:0`, so validation can distinguish a
deliberate fallback from an accidental overlay.

## State rules

- Phase 1 requires confirmed `config.json`.
- Phase 2 requires confirmed `outline.json` before template mapping is finalized.
- Phase 3 requires confirmed `template_map.json`.
- A sample render may use an unconfirmed `layout_plan.json` only with `--allow-unconfirmed`.
- A full render requires confirmed `layout_plan.json`.
- Record revisions by updating the existing artifact; do not create ambiguous
  files such as `outline_final_v2_revised.json`.
