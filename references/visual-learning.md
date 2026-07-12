# Learning from PPT templates

## Default: native template editing

A selected template is both an editable page library and a source of visual rules:

- background and surface colors;
- primary, secondary, muted, and line colors;
- Chinese and Latin font families;
- title/body/caption/navigation type scale;
- safe margins, columns, gaps, and vertical rhythm;
- navigation treatment and active-state language;
- panel borders, fills, corner radius, and shadow policy;
- chart colors, annotations, legends, and table treatment;
- footer, page number, source note, and logo placement.

Do not force content into an incompatible sample page. Inventory all source pages,
select the page whose component count and relationship match the content, clone
that complete page, and edit its original objects.

## Template grammar

Run `extract_template_grammar.py` for every bundled or user-uploaded template.
Treat schema v3 output as both a design grammar and an editable slot map:

- `identity.navigation`: top, sidebar, or minimal;
- `identity.composition`: the persistent page skeleton;
- `identity.panel_mode`: native shapes or image-based scaffold;
- `geometry`: title, content, cover, and ending regions;
- `archetypes`: source-slide roles, layout signatures, columns, text slots,
  picture slots, Logo candidates, capacities, and decorative assets;
- `signature_features`: features that must remain recognizable after rendering.
- `components`: textboxes, text-bearing AutoShapes, groups, panels, nested image
  placeholders, sample cards, captions, and their parent-child relationships;
- `navigation_contract`: ordered members, label ownership, active/inactive state,
  font policy, and shapes protected from content clearing.

Clone the complete source page. Replace sample text through existing shape IDs,
replace or remove sample pictures in their original z-order, and preserve native
decorations and groups. Never preserve sample figures or text as evidence.

Do not add a textbox over a text-bearing AutoShape. Do not add a second frame over
an existing picture slot. Bind grouped children directly. When an outer white
panel contains an independent light-colored placeholder, replace or remove the
inner child and retain the outer component. When the placeholder is baked into a
raster scaffold, use a cleaned cached copy of that raster asset; do not treat an
overlay mask as the default permanent repair.

### Identity gate

Render the same 3-5 page smoke content with two templates. Run
`validate_rendered_identity.py`. If the decks differ only in colors or the identity
distance is below the configured threshold, template learning has failed. Revise
navigation, title geometry, scaffolds, or composition before continuing.

Templates that intentionally belong to one family, such as color variants of the
same university template, may share geometry. Their family relationship must be
recorded rather than misrepresented as independent layouts.

## Navigation

Build tabs from confirmed story sections:

- 1 section: omit navigation;
- 2-6 sections: use equal or content-proportional tabs;
- more than 6: show top-level sections only or use a section label rather than
  unreadably narrow tabs;
- highlight exactly one current section on content pages;
- cover and ending may omit navigation;
- never label all pages as the first section.

Navigation labels may be separate textboxes, text inside tab AutoShapes, grouped
children, or text over raster tabs. Detect and record the actual text owner. Apply
one template-derived font family and one size across all tabs and pages. Protect
all navigation members from generic text clearing, then reset every active and
inactive state after cloning so the source slide cannot leak its original state.
Remove unused tabs as complete backing-and-label components.

Exclude navigation text and shapes before slide-role classification. A content
page with a large side navigation must not be misclassified as an agenda or
section divider merely because navigation labels are large or repeated.

## Logo policy

- User logo supplied: place the same asset consistently and preserve aspect ratio.
- Approved official logo already embedded: retain only when requested.
- No logo: remove placeholder artwork and placeholder text.
- Never generate or infer a university/company logo.

## Layout admission

Select a native source page by content components. It is compatible when:

- same semantic role;
- same number of major components;
- compatible text/image proportions;
- enough readable capacity at the minimum font size;
- no unused sample block remains.

If only capacity differs, use `template_adaptive` and record movement, resize,
reflow, or hidden original slots. Use `freeform` only when no source page can
express the required relationship, and record `fallback_reason`.

## Capacity and overlap

- Use fixed role-based type sizes before estimating capacity.
- If content exceeds capacity: shorten, restructure, split, or choose another
  archetype.
- Do not shrink body text below the academic minimum merely to fit.
- Render every changed page and check text box intersections, container bounds,
  captions, and image legibility.

## Visual strategy admission

Each page declares one primary strategy:

- `source_figure`;
- `native_diagram`;
- `native_chart`;
- `native_table`;
- `structured_comparison`;
- `intentional_text_only`.

Method, architecture, workflow, experiment-design, and causal pages should usually
have a diagram. Result pages should usually show the source chart or reconstruct a
chart from verified data. Text-only is a reasoned choice, not a renderer fallback.

Choose the strategy during page PRD creation. A visual is admitted only when it
supports the page claim and has a planned interpretation. Drawing, source-figure
reuse, chart reconstruction, and licensed image search are normal evidence-carrier
options; they are not late repairs for visibly empty pages.
