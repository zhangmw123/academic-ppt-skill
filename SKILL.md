---
name: academic-ppt-skill
description: Create editable academic PPTX presentations from papers, theses, proposals, experiment reports, PDFs, DOCX, figures, and tables. Use for thesis defenses, proposal defenses, mid-term reviews, lab meetings, journal clubs, paper sharing, project applications, and requests such as 论文答辩PPT、开题PPT、组会汇报、论文分享、科研汇报. Learn visual rules from a user or bundled PPTX without forcing its sample page structure, build an evidence-grounded storyline, confirm each phase, generate dynamic navigation and scientific visuals, and verify formal 1.0 delivery through Windows PowerPoint; WPS or LibreOffice renders provide compatibility evidence only.
---

# Academic PPT

Build a real, editable `.pptx`. Treat the source as evidence, the confirmed scene
contract as the argument, and the selected template as a visual system plus a set
of layout archetypes. Bind every content page to a compatible template archetype,
then rebuild the evidence layer with editable text, shapes, charts, diagrams, and
necessary local visual assets. Preserve template identity without carrying over
sample frames whose capacity does not match the page.

Own this workflow end to end. Do not invoke another presentation-generation Skill,
create a user-managed project, or replace this Skill's contracts with another system.

## Hard rules

1. Complete at most one gated phase per assistant turn. Stop for explicit user
   confirmation after Phases 0-4 unless the user explicitly requests full
   automation.
2. Read the primary source before outlining. Never fabricate metadata, numbers,
   results, citations, figure meanings, logos, or institutional details.
3. Build an evidence ledger and compare 2-3 storylines before producing the final
   outline. Do not map paper chapters directly to slides without narrative review.
4. Use `template_hybrid_editable` by default. Learn the template's fonts, type
   scale, navigation, title geometry, grid, panel language, colors, and archetypes.
   Rebuild each page on the closest archetype with editable information objects;
   retain only identity decorations that do not contain sample content.
5. Use `template_native` only when an original slide's editable components and
   capacity exactly match the page contract. Use `template_adaptive` for a small
   documented reflow. Do not clone a large sample frame merely because it exists.
6. Derive navigation from the confirmed story sections. Three sections produce
   three equal tabs; unused template tabs are removed. Highlight the current
   section on each page. Cover and ending pages need no navigation.
7. Treat logos as image assets. If the user supplies a logo, place it consistently.
   If no logo is supplied, remove placeholders unless the template already embeds
   an approved official logo the user asked to retain.
8. Every page must state a visual strategy: source figure, native diagram, native
   chart, native table, structured comparison, or intentional text-only page.
9. Do not solve overflow by unlimited font shrinking. Shorten, restructure, split,
   or change layout when minimum readable sizes would be violated.
10. Do not deliver until package integrity, content gates, real rendering, overlap,
    overflow, template-residue, and visual inspection pass.
11. Distinguish a representative sample from a complete deck. A graduation-defense
    test must satisfy the scene page budget and cannot be declared complete after
    rendering only 3-7 representative pages.
12. Reject color-only template adaptation. The rendered deck must preserve the
    chosen template's navigation orientation, title geometry, composition family,
    panel treatment, and at least two decorative identity features.
13. Distinguish user-visible sections from required scene argument units. Users may
    rename, merge, replace, or reorder sections, but the plan must disclose any
    required argument unit that would be lost.
14. Respect explicit font and palette choices. Otherwise preserve template fonts
    and colors. Recolor editable OOXML objects without changing layout; disclose
    colored raster assets that require separate image processing.
15. Treat a supplied PNG logo as an asset for the template's recorded Logo slot or
    reserved Logo box. Do not draw an additional Logo label or cover existing content.
16. Rebuilt navigation uses one font family and one font size on every content
    page. Show the current section with the template's dark active fill and keep
    every other tab light; do not signal state by changing type size.
17. Match layout capacity to real content. A short claim must not be stretched
    across tall three-, four-, or five-column cards. Prefer a compact native page,
    resize the original panels and text slots, add grounded supporting evidence,
    or merge the page. Record the chosen adjustment in `layout_plan.json`.
18. A single source figure or chart is not self-explanatory. Place its claim,
    reading guidance, mechanism or comparison, and caveat next to the figure using
    native text slots. Image-only pages are reserved for multi-image galleries or
    a genuinely inspectable full-canvas visual whose takeaway is explicit.
19. For paper sharing, the transfer page must state what is borrowed, what must be
    validated, the concrete replication or ablation, and the decision metrics.
    Do not end a normal research sharing deck with classroom prompts such as
    `请讨论`; close with the core judgment and next action unless the user requests
    a discussion agenda.
20. Treat information density as an evidence-and-relationship requirement, not a
    character quota. A normal content page should carry one claim, 2-4 supporting
    evidence units, 1-2 evidence carriers, an interpretation or boundary, and a
    transition, unless the page role justifies another composition.
21. In native mode, never draw over a compatible editable template component.
    In hybrid mode, rebuild the complete content region from the selected archetype
    geometry; do not mix new content with leftover sample frames or labels.
22. Treat navigation as a protected stateful component. Detect who owns each label,
    preserve one global font family and size, reset every tab state after cloning,
    and highlight exactly the current section with the template's active treatment.
23. Apply dual hard gates to every content page: the core information layer must
    remain editable, and the template's visual identity and page semantics must
    remain recognizable. Neither gate can compensate for failure of the other.
24. Generate `slide_manifest.json` from the actual PPTX. Every content page must
    record its template archetype, visible module count, density, editable text
    count, native-object count, picture count, and page-level errors.
25. Never expose internal composition labels such as `核心判断`, `证据依据`,
    `机制解释`, `边界与行动`, `读图重点`, or `证据、读图与边界`. Use a
    source-specific key-point heading followed by smaller explanatory text.
26. Treat a key point as a heading/explanation pair. A method name, dataset scale,
    metric, limitation, or contribution belongs in the heading; its mechanism,
    advantage, numerical support, or implication belongs in the explanation.
27. When several template frames are baked into one raster or group, recover their
    geometry and rebuild every semantic panel, title, body, image slot, node, and
    connector as a separately editable PowerPoint object. Retain a combined raster
    only for non-semantic decoration.
28. Bind a selected PDF figure by verified source page and caption, not merely by
    nearest-page proximity. Record the PDF page in the visible caption or asset
    manifest and reject a figure whose semantic role does not match the page claim.
29. Model every content composition as `page -> semantic module -> child slot`.
    A repeated card may own its own heading, explanation, image or chart, icon, and
    caption. Do not treat all visuals as page-level attachments.
30. Distinguish page-level multi-image evidence from module-level media. Support
    1, 2, 3, 4, and 6-image layouts plus primary-and-supporting compositions; bind
    every visual to evidence and remove or reflow any slot that has no valid asset.
31. For each semantic region, choose exactly one mode: reuse the complete native
    editable component, or remove it and fully reconstruct the region. Never hide
    old frames with masks or stack new panels over retained sample components.
32. Remove unused components by ownership group, including frames, sample text,
    icons, captions, connectors, and child placeholders. Treat duplicate, orphaned,
    overlapping, or visibly empty components as blocking QA failures.
33. Use these default typography ranges unless the confirmed template requires a
    compatible alternative: cover 28-32 pt, page title 20-24 pt, module heading
    13-16 pt, body 11-13 pt, caption 8.5-10 pt, with normal content no smaller than
    10.5 pt. Shorten, split, or reflow before shrinking below the range.
34. Treat T01-T08 as one release surface. Every template must pass parsing, semantic
    compilation, editable binding, dense and multi-image rendering, object-level QA,
    and PowerPoint visual acceptance; T01/T03-first is sequencing, not partial support.

## First response

Discover obvious workspace files before asking the user to repeat paths. Infer the
primary source, Presentation Scene, Method Profiles, a compatible bundled template,
duration, language, scene sections, palette, font policy, cover fields, logo,
speaker-note preference, and Guided Workflow mode whenever the material or request
makes a choice non-blocking.

Present one concise task summary of the inferred choices and request confirmation or
correction. Ask a direct follow-up only when a required source, scene, template,
formal-cover detail, delivery choice, or user decision remains missing or materially
ambiguous. Do not present an upfront internal configuration questionnaire.

Infer output language from the request and materials. Formally support Simplified
Chinese, English, and mixed Chinese-English decks; disclose that other languages are
best-effort unless their typography and render coverage has been added.

When no user template is supplied, select one compatible bundled template from T01
to T08 and state its ID and short name in the summary. Show alternatives or previews
only when confidence is low, the request materially conflicts with the selection, or
the user asks to compare styles.

When the user names one of the cataloged source templates under `assets/templates`,
resolve it to the matching repaired catalog copy and disclose the source path,
catalog ID, and package-recompile reason in the task summary. T01 and T03 retain the
complete 10/11-slide source structure, geometry, fonts, sizes, positions, and layout
archetypes; their media packages are normalized for compatibility. Do not replace
either with a merely color-similar five-page template. Admit any other user PPTX only after
editable-component, grammar-extraction, clone/save, and Authoritative Runtime checks pass.

## Portable Skill scripts

Invoke scripts through this Skill's absolute installed path. Do not ask the user to
create an internal project, run phase commands, hand-author JSON, or change into the
Skill repository.

For an explicitly requested autonomous candidate, use the single task entry point:

```powershell
python "<skill-root>/scripts/build_complete_deck.py" "<source.pdf>" --scene "毕业答辩" --template "<template.pptx>" --output "<output-dir>"
```

The script self-locates bundled modules and assets from any working directory. Its
default output is an unconfirmed candidate under `working/candidate`. Pass
`--confirmed` only after explicit user approval of the complete plan and sample;
formal publication additionally requires a PowerPoint render and per-slide visual
review report.

## Phase protocol

Use these labels exactly:

- `PHASE 0/5 素材与任务确认`
- `PHASE 1/5 证据底稿与故事线确认`
- `PHASE 2/5 大纲与内容锁定确认`
- `PHASE 3/5 视觉系统与逐页蓝图确认`
- `PHASE 4/5 样稿与单页验收`
- `PHASE 5/5 完整渲染与质检`

At the end of Phases 0-4, report what was inspected, key decisions and risks, exact
artifact paths, and one concrete confirmation request. Record confirmation with
`confirmed`, `confirmed_at`, and `confirmation_note`.

## Phase 0: brief

Write `ppt_output/config.json`. Do not analyze the full paper or render the deck
before the user confirms the source, scene, template, duration, and language.
Template preview images are allowed to support selection.

Resolve the scene and subtype through [scene-profiles.json](references/scene-profiles.json).
Do not treat opening, mid-term, graduation, station-entry, project-application,
lab-meeting, and paper-sharing decks as one generic academic outline. Record
`scene`, `section_variant`, user-visible `sections`, `deck_scope`,
`evidence_state`, required `coverage_tags`, and required `argument_units` in the plan.
If the user says only “组会”, ask or infer whether it is 文献精读、周报进展 or
课题/论文进展; these are different scene contracts.

## Phase 1: evidence and storyline

Read [content-and-storyline.md](references/content-and-storyline.md) and the chosen
scene in [scene-templates.md](references/scene-templates.md).

Read [evidence-density-template-contracts.md](references/evidence-density-template-contracts.md).
Create:

- `ppt_output/evidence_ledger.json`: one evidence unit per fact, result, method
  claim, mechanism, limitation, caveat, and figure/table; include support,
  interpretation, boundary, exact source location, scene value, confidence,
  linked assets, and visual candidates;
- `ppt_output/storyline_options.json`: 2-3 alternatives such as
  problem-method-evidence, results-first, or method-first; compare audience fit,
  evidence strength, visual potential, and risk.
- `ppt_output/source_assets.json`: a reviewed library of equations, figures,
  subfigures, and structured tables with captions, source locations, quality,
  editability, semantic summaries, and linked evidence IDs. Read
  [source-assets.md](references/source-assets.md). Do not treat extracted page
  furniture as a scientific asset.

Recommend one storyline, but stop for user confirmation. Mark missing evidence as
`未提供`, `无法推导`, or `需要外部验证`; do not fill gaps with common sense.

## Phase 2: page-by-page PRD, outline, and content lock

Convert the confirmed storyline into a section hierarchy and page plan. Section
count comes from the argument, not from template navigation.

Each page must contain:

- claim-led title;
- page role and section;
- evidence IDs and source references;
- detailed argument and caveat;
- an optional unlabeled `page_conclusion` only when the
  title and body do not already make the implication clear;
- transition to the next page;
- information-density target and component list;
- visual strategy and drawing task;
- speaker-note intent.
- `question_answered`, `page_role`, `argument_units`, `content_units`,
  `previous_link`, `next_link`, and `time_seconds`;
- `template_layout_need`, including component count, relationship, image count,
  and preferred source-page signatures.
- `page_payload`, including one claim, 2-4 supporting evidence units, 1-2 evidence
  carriers, interpretation or boundary, transition, and a density status. Record
  a page-role exception instead of padding an intentional sparse or image-dominant
  page.

Include a dedicated research-inspiration page when the scene calls for it. Separate
author-supported findings, presenter interpretation, transferable mechanisms, and
future research opportunities. Create `ppt_output/outline.json`, then generate
`ppt_output/presentation_prd.md` as the user-facing preview of every planned page:

```powershell
python scripts/build_presentation_prd.py --plan ppt_output/outline.json --evidence ppt_output/evidence_ledger.json --assets ppt_output/source_assets.json --grammar ppt_output/template_grammar.json --output ppt_output/presentation_prd.md
```

Show the PRD summary in the conversation and provide the full artifact. Stop for
section replacement, reorder, merge, split, page-title, page-content, time, visual,
and template-layout confirmation. Only then create `slide_content_lock.json`.

```powershell
python scripts/build_content_lock.py --plan ppt_output/dynamic_plan.json --evidence ppt_output/evidence_ledger.json --output ppt_output/slide_content_lock.json
```

Validate scene completeness before visual planning:

```powershell
python scripts/validate_scene_plan.py ppt_output/dynamic_plan.json
```

## Phase 3: learn style and build blueprint

Read [template-catalog.md](references/template-catalog.md),
[academic-standards.md](references/academic-standards.md), and
[visual-learning.md](references/visual-learning.md).

Run:

```powershell
python scripts/parse_template.py "<template.pptx>" -o ppt_output/template_analysis.json
python scripts/export_preview.py "<template.pptx>" --output-dir ppt_output/template_preview
python scripts/extract_visual_system.py "<template.pptx>" --preview-dir ppt_output/template_preview --output ppt_output/visual_system.json
python scripts/extract_template_grammar.py "<template.pptx>" --output ppt_output/template_grammar.json --asset-dir ppt_output/template_assets
python scripts/extract_figures.py "<source.pdf>" --output-dir ppt_output/working/figures
```

Inspect actual previews. The learned visual system records colors, Chinese and
Latin fonts, type scale, margins, navigation behavior, panel language, and chart
style. It does not copy the template's sample content structure.

The template grammar records navigation, title and content geometry, layout
signatures, two/three/four/five-column structures, editable text slots, picture
slots, Logo candidates, capacity, z-order, groups, identity features, semantic
components, text ownership, parent-child placeholder relationships, and a
`navigation_contract`. Exclude navigation members before classifying slide roles.
Select source slides by semantic role, component count, relationship, capacity,
and image ratio. A user-uploaded template must pass grammar extraction before
layout planning; falling back to a generic theme without disclosure is forbidden.

If the user requests a palette variant, create a recolored template copy before
binding pages, then inspect it:

```powershell
python scripts/apply_template_palette.py "<template.pptx>" ppt_output/template_variant.pptx --palette academic_purple --report ppt_output/palette_report.json
```

Create `ppt_output/layout_plan.json` by selecting an actual compatible source
archetype for each page. Record `render_mode`, `source_slide_index`,
`layout_signature`, editable component inventory, complex visual assets, density
target, template identity tokens, and any documented adjustments. Native pages
also record explicit shape bindings and complete component removals.
Three-, four-, and five-component content must prefer corresponding native template
pages when they exist.

Only pages explicitly approved for `freeform` use a content-driven archetype:

- cover / ending;
- text + figure;
- full figure with interpretation;
- two- or three-way comparison;
- process / architecture;
- 2x2 evidence or metric points;
- native chart / native table;
- custom scientific diagram.

Create `ppt_output/visual_tasks.json` before rendering visuals. Bind every task to
the page claim, evidence IDs, source locations, backend, editability requirement,
output path, and fallback. Validate it with:

```powershell
python scripts/validate_visual_tasks.py ppt_output/visual_tasks.json --evidence ppt_output/evidence_ledger.json
```

For every proposed source image, verify caption, source page, resolution, and
necessity. Reject page furniture, update banners, repeated headers, and logos.

### Drawing and image policy

Prefer in order:

1. a legible source figure that directly proves the page claim;
2. a native editable PowerPoint diagram for processes, architectures, comparisons,
   timelines, taxonomies, and causal chains;
3. a native or matplotlib chart reconstructed from source data;
4. a traceable web image for a missing real-world subject or restrained background;
5. a bundled or host-provided low-level image-generation tool for an explanatory visual,
   with all factual text and numbers rebuilt as editable PowerPoint elements.

Route quantitative axes to `matplotlib`; route boxes-and-arrows structures to an
editable native PowerPoint diagram, using Graphviz only as an optional coordinate
solver; use a low-level plotting or image-generation tool for complex conceptual
illustrations. Use generated imagery only as a visual base, never as the source
of scientific numbers, labels, or relationships.

For web images, use the environment's image or web search tool. Record query,
landing-page URL, direct asset URL, author, license, access date, local path, and
usage role. Accept only public-domain, CC0, CC BY, CC BY-SA, user-provided, or
explicitly approved assets. Do not use a search-result thumbnail as the source.
Prefer transparent subject images for plants and organisms; use background imagery
only when it does not compete with evidence. Add attribution in notes or an asset
manifest when required by the license.

Use external retrieval only for a necessary missing public visual. Do not transmit
user-supplied documents, raw data, screenshots, or unpublished material to the
external source without explicit authorization.

Normalize every downloaded or generated bitmap before insertion to remove EXIF,
alpha-channel, color-profile, and codec incompatibilities:

```powershell
python scripts/normalize_image_asset.py "downloaded.jpg" "working/external/asset_clean.jpg"
```

Render evidence-bound charts with:

```powershell
python scripts/render_scientific_visuals.py --tasks ppt_output/visual_tasks.json --visual-system ppt_output/visual_system.json --output-dir ppt_output
python scripts/validate_visual_tasks.py ppt_output/visual_tasks.json --evidence ppt_output/evidence_ledger.json --asset-root ppt_output --require-outputs
```

Never invent chart values. A page that needs a diagram must not silently degrade
to five bullets because drawing is inconvenient.

Apply only auditable Presentation Transforms by default. Request explicit user
authorization before any Derived Analysis such as a new statistical test, regression,
model evaluation, or scientific inference; record and label authorized results as
system-computed rather than source-reported evidence.

Stop after showing the blueprint, navigation hierarchy, drawing task list, and
representative layouts.

## Phase 4: sample and page review

Render 3-5 representative pages first: cover, method/diagram, results/chart,
dense text page, and ending when relevant.

Default template-guided editable renderer:

```powershell
python scripts/build_complete_deck.py "<source>" --scene "<scene>" --template "<template>" --content-plan ppt_output/authored_content.json --output ppt_output/candidate
python scripts/validate_pptx.py ppt_output/candidate/working/sample.pptx --layout-plan ppt_output/candidate/audit/sample_layout_plan.json --render-check required --output ppt_output/candidate/audit/sample_report.json
```

For high-risk or highly designed decks, render and approve one page at a time.
Inspect actual PNGs, not only JSON. Check navigation hierarchy, fonts, wrapping,
figure legibility, labels, alignment, density, and whether the visual proves the
claim. Stop for user corrections.

## Phase 5: full render and QA

Require confirmed config, evidence ledger, storyline, outline/content lock, visual
system, and dynamic plan. Render the full deck, then run real PowerPoint or
LibreOffice export.

Deliver only when all ERROR checks pass and rendered previews have been visually
reviewed. Provide:

- timestamped editable PPTX;
- separate DOCX speaker script and Concise Speaker Notes in the PPTX;
- full contact sheet, individual slide PNGs, `render_report.json`, evidence ledger,
  selected storyline, content lock, and dynamic plan as retained supporting artifacts,
  not normal-user visible deliverables by default.

## Rendering modes

- `template_hybrid_editable` (default): bind the page to a template archetype and
  rebuild its information layer with editable objects while retaining template
  fonts, navigation, title geometry, grid, panel language, and identity details.
- `template_native`: clone a source page only when its complete editable component
  structure and capacity exactly fit the content.
- `template_adaptive`: same as native, with recorded movement, resize, reflow, or
  hidden original slots.
- `freeform` (exception): use content-driven geometry with a disclosed reason only
  when no template archetype can express the page. It is not a shortcut around
  template analysis or identity checks.

## Portability

Install `requirements.txt`. PowerPoint on Windows is the preferred render check;
LibreOffice plus `pdftoppm` is the cross-platform fallback. If neither is
available, do not claim visual QA passed.

When templates change, run:

```powershell
python scripts/check_templates.py --grammar-check
python scripts/check_templates.py --render-check --style-learning-check --grammar-check
```

For release or scene-contract changes, validate the fixed ten-scene contract
matrix. Synthetic cases never satisfy product acceptance; a product benchmark must
bind real representative sources and pass the complete Skill entry point:

```powershell
python "<skill-root>/scripts/run_scene_benchmarks.py"
python "<skill-root>/scripts/run_scene_benchmarks.py" --formal --runtime powerpoint
```

Do not fork per-scene application logic. Update
[scene-benchmarks.json](references/scene-benchmarks.json) when a fixed case changes,
and keep its expected coverage synchronized with the canonical scene profiles.

For cross-template regression, render the same content with two templates and run:

```powershell
python scripts/validate_template_identity.py first_grammar.json second_grammar.json
python scripts/validate_rendered_identity.py first_sample.pptx second_sample.pptx
```

For a complete deck, verify that multiple compatible source archetypes were
actually used:

```powershell
python scripts/validate_template_usage.py ppt_output/dynamic_plan.json ppt_output/template_grammar.json
```

## Resources

- Portable capability boundary: [capability-contract.md](references/capability-contract.md)
- Evidence/storyline: [content-and-storyline.md](references/content-and-storyline.md)
- Evidence density and template contracts: [evidence-density-template-contracts.md](references/evidence-density-template-contracts.md)
- Workflow and visual task schemas: [workflow-schema.md](references/workflow-schema.md)
- Scenes: [scene-templates.md](references/scene-templates.md)
- Machine-checkable scene profiles: [scene-profiles.json](references/scene-profiles.json)
- Fixed ten-scene release benchmarks: [scene-benchmarks.json](references/scene-benchmarks.json)
- Template choices: [template-catalog.md](references/template-catalog.md)
- Visual learning/navigation/layout: [visual-learning.md](references/visual-learning.md)
- Academic typography/density: [academic-standards.md](references/academic-standards.md)
- Scientific drawing/chart guidance: [drawing-prompts.md](references/drawing-prompts.md)
- Formula, figure, and table asset library: [source-assets.md](references/source-assets.md)
- PPT implementation notes: [python-pptx-guide.md](references/python-pptx-guide.md)

The evidence-first, alternative-storyline, visual-system, blueprint, and strict-gate
ideas are adapted to academic presentation needs from CyberPPT:
`https://github.com/crazyykhllc-bit/CyberPPT`.
