# Evidence density and template component contracts

Use this reference in Phases 1-3. It converts source material into speakable page
arguments and converts a PPTX template into editable semantic components.

## 1. Evidence units

Do not extract only chapter summaries. Split the source into reusable evidence
units so several related units can support one page claim.

```json
{
  "id": "EU_021",
  "kind": "result",
  "claim": "The proposed method improves F1 by 3.2 percentage points.",
  "support": ["baseline=89.7%", "proposed=92.9%"],
  "mechanism": "The graph constraint reduces entity-linking ambiguity.",
  "interpretation": "The gain is concentrated in ambiguous plant names.",
  "boundary": "The source reports one dataset only.",
  "source_refs": [{"page": 47, "label": "Table 4-4"}],
  "asset_ids": ["TAB_04_04"],
  "scene_value": ["毕业答辩:results", "中期考核:completed_work"],
  "visual_candidates": ["native_chart", "comparison_table"],
  "confidence": "high"
}
```

Preserve distinctions among author-supported findings, presenter interpretation,
and proposed follow-up work. Never convert an inference into a source fact.

## 2. Page payload and density

A content page is a compact argument bundle, not a paragraph summary and not a
quota of characters. Default target:

- one claim-led title;
- two to four supporting evidence units;
- one or two evidence carriers: source figure, chart, table, formula, diagram,
  metric card, map, screenshot, or structured comparison;
- one interpretation, mechanism, comparison, or boundary;
- one transition that makes the next page necessary.

```json
{
  "page_id": "P08",
  "claim": "The completed experiments already support the central hypothesis.",
  "supporting_unit_ids": ["EU_021", "EU_022", "EU_024"],
  "evidence_carriers": ["FIG_08", "native_metric_cards"],
  "interpretation": "All three indicators improve in the same direction.",
  "boundary": "Generalization to another dataset remains untested.",
  "transition": "The next page locates the remaining error sources.",
  "density": {
    "module_count": 4,
    "evidence_unit_count": 3,
    "carrier_count": 2,
    "status": "adequate"
  }
}
```

Judge density by coverage and relationships, not raw word count. A page is sparse
when a native panel has no semantic job, a lone figure has no interpretation, or
the speaker cannot explain why its modules belong together. A page is overloaded
when it contains unrelated conclusions, unreadable evidence, or more modules than
the selected template page can express.

Exceptions are intentional: cover, agenda, section divider, and ending pages may
be sparse; a multi-panel evidence gallery may be image-dominant; a text-heavy
definition or limitation page may omit images. Do not force decorative pictures
onto every page.

### Composition rules learned from the reference decks

Store the rules, not the six sample PPTX files or their page content, in the skill:

- keep one visual system while varying page composition across the deck;
- combine roughly 3-5 meaningful modules on a normal evidence page when the
  source supports them, rather than repeating one generic card layout;
- use claim + mechanism/evidence + interpretation as the common reading path;
- use contribution columns, architecture-with-annotations, formula-with-steps,
  comparison tables, metric cards, multi-panel evidence, and summary connections
  according to the argument, not as decoration;
- place a bottom conclusion strip only when it states a page-specific inference;
  never label it with internal prompts such as `读图结论`;
- keep diagrams, charts, tables, formulas, screenshots, and maps large enough to
  inspect; remove a visual whose contribution cannot be stated precisely;
- let cover, divider, and ending pages breathe, but require content pages to use
  their native canvas deliberately.

## 3. Material-to-visual planning

Plan missing visuals during PRD creation, not after an empty layout is selected.
For every page, classify the visual state:

- `source_ready`: a legible source figure/table/formula directly supports the claim;
- `reconstruct`: verified data or relationships should become a native chart,
  table, or diagram;
- `external_subject`: a traceable licensed image is needed for a real object;
- `explanatory_generation`: a generated illustration can explain a confirmed
  concept but cannot supply facts or scientific labels;
- `intentional_text_only`: text is the best evidence carrier for this page.

Every selected visual must answer `what does this prove on this page?`. Reject a
visual that is merely related to the topic.

## 4. Template components

Parse every source slide into semantic components before binding content:

```json
{
  "component_id": "S05_C12",
  "shape_ids": [181, 182],
  "component_role": "image_panel",
  "text_owner": "autoshape",
  "parent_component_id": null,
  "child_component_ids": ["S05_C13"],
  "editable": true,
  "replace_policy": "replace_child_picture_or_remove_child",
  "preserve_geometry": true
}
```

Recognize these cases:

1. Separate textbox: write directly into that textbox.
2. Text inside an AutoShape: edit the AutoShape text frame; do not add a textbox
   over it.
3. Text or picture inside a group: bind the child shape while preserving the group.
4. Outer panel plus independent inner placeholder: replace or remove the inner
   child; keep the outer panel unless the page plan removes the whole component.
5. Placeholder frame baked into a raster scaffold: create and cache a clean raster
   variant for that source asset, then reuse it. Do not cover the frame with an
   arbitrary new white rectangle unless an explicit temporary mask is approved.
6. Sample icon, image, caption, or metric card: treat the related shapes as one
   component so removal does not leave orphan labels or frames.

The renderer must not create a new textbox, panel, or picture frame when a
compatible editable component already exists. `freeform` additions require both a
missing native component and a recorded `fallback_reason`.

## 5. Navigation contract

Navigation is a repeated component with state, not ordinary repeated text.

```json
{
  "orientation": "top",
  "section_order": ["基本信息", "核心方法", "实验结果", "研究启发"],
  "members": [
    {"position": 1, "backing_shape_ids": [12], "label_shape_id": 12, "text_owner": "autoshape"}
  ],
  "active_state": {"rule": "dark_fill_only"},
  "inactive_state": {"rule": "light_fill"},
  "font": {"family": "template_native", "size_pt": 9.0, "bold": false},
  "clear_protection": true
}
```

Derive `members` from geometry, repetition, z-order, and visual state. Do not infer
navigation only from repeated strings: labels may be stored directly in shapes,
separate textboxes, grouped children, or raster-backed tabs. Exclude navigation
members before classifying a slide as agenda, section, or content.

On every content page:

- bind all labels from the confirmed top-level sections;
- use one font family and one size for every member and every page;
- highlight exactly the current section using the template's active treatment;
- protect navigation shapes from `clear_unbound_text`;
- remove unused tabs as complete components, not only their labels;
- never inherit the active state of the cloned sample slide.

## 6. Binding decision

For each planned page, perform this sequence:

1. Match its `page_payload` to an archetype by semantic role, module count,
   relationship, evidence carriers, and capacity.
2. Bind every module to an existing `template_component`.
3. Resize or reflow native components only when capacity requires it.
4. Remove unused child placeholders and all orphan companion shapes.
5. Apply the `navigation_contract` after ordinary content clearing.
6. Record any new object in `additions` with `fallback_reason`.

Reject the page plan when important content remains unbound, when a native panel
has no semantic job without an approved compacting adjustment, or when an added
object overlaps a reusable template component.
