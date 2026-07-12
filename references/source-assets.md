# Source asset library

Build `source_assets.json` before page planning. It complements the evidence
ledger: the ledger records what the source proves; the asset library records what
can be shown.

## Required asset types

- `figure`: source figures, subfigures, architecture diagrams, screenshots, sample
  photographs, and result plots;
- `table`: structured rows, columns, units, bold/best-value semantics, title, and
  notes; prefer structured data over a screenshot;
- `equation`: equation number, original rendering, LaTeX/OMML only when verified,
  symbol definitions, units, and source context.

Each asset records `asset_id`, source file/page/section, caption, local path or
structured data, semantic summary, linked evidence IDs, quality, editability,
recommended uses, and caveats.

## Extraction rules

1. Preserve the complete figure and caption before considering subfigure crops.
2. Reject headers, footers, logos, decorative rules, and repeated page furniture.
3. Never detach a chart from its axis, legend, unit, or caveat.
4. Extract tables as data when reliable. Keep the original crop for audit.
5. Preserve native Word OMML equations. For PDF equations, keep a high-resolution
   or vector rendering; reconstruct LaTeX only when recognition is verified.
6. Do not place every extracted item in the deck. Scene planning selects assets
   that directly support a page claim.
7. Link every used asset to evidence. A generated explanatory diagram is a new
   visual task, not a source asset.

## Schema example

```json
{
  "asset_id": "FIG_003",
  "type": "figure",
  "source_page": 18,
  "caption": "图 3-2 系统总体架构",
  "local_path": "working/assets/FIG_003.png",
  "semantic_summary": "展示前端、服务层、模型层和知识图谱之间的关系",
  "linked_evidence_ids": ["E21", "E22"],
  "quality": "high",
  "editable": false,
  "recommended_usage": ["方法总览", "系统架构"],
  "caveat": ""
}
```
