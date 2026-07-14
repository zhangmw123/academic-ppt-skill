# Reusable Skill capability contract

This file defines the capabilities that belong to the portable Academic PPT Skill.
They must not be removed as "application" or "platform" code during cleanup.

## Required research workflow

- Discover and ingest PDF, Markdown, DOCX, XLSX, PPTX, and raster-image sources.
- Track claims, source locations, confidence, boundaries, figures, and tables in an
  evidence ledger.
- Compare alternative storylines, bind the selected argument to a scene contract,
  and author complete page-by-page content before rendering.
- Preserve source grounding from ingestion through slide content, speaker script,
  and acceptance reports.

## Required visual workflow

- Extract and review scientific figures and tables from supplied sources.
- Build editable native PowerPoint diagrams, charts, tables, comparisons, and
  process or architecture views when the relationship is better expressed visually.
- Render evidence-bound quantitative charts with matplotlib; never invent values.
- Route complex illustrations to an available plotting, diagram, or image-generation
  skill while rebuilding factual labels and numbers as editable PowerPoint objects.
- Search the web only for a necessary missing public visual, record provenance and
  license, and never upload private source material without explicit permission.

## Required template workflow

- Learn grammar, fonts, palette, geometry, navigation, grouped components, text
  ownership, image slots, and decorative identity from bundled or user PPTX files.
- Compile each bundled source template into a standard editable PPTX and a
  machine-readable semantic specification. The specification must encode the
  hierarchy `page -> semantic module -> child slot`, ownership groups, supported
  content types, capacity, and removal policy.
- Bind content into native components and preserve layout identity. Recoloring may
  change colors only; structure, fonts, sizes, and positions must remain identical.
- Distinguish page-level media compositions from module-level media slots. Support
  1, 2, 3, 4, and 6-image arrangements, primary-plus-supporting layouts, and one
  evidence image or chart inside each repeated card when the source supports it.
- Make region render modes exclusive: reuse the complete native component or remove
  it and fully reconstruct the region. Never retain covered, duplicated, or orphaned
  sample frames, labels, icons, captions, or connectors.
- Apply bounded typography and reflow content before shrinking below readable
  limits. Validate duplicate objects, overlaps, orphan companions, and empty slots.
- Support T01-T08 and user templates that pass package, grammar, clone/save, and
  authoritative-runtime admission checks.

## Required delivery workflow

- Keep representative samples separate from complete candidates and final products.
- Produce an editable PPTX, individual previews, contact sheet, speaker script,
  evidence and planning artifacts, and an acceptance report.
- Require real rendering and per-slide visual review before product acceptance.

## Out of scope

The Skill must not grow its own web service, desktop application, hosted platform,
job database, user account system, dashboard, or deployment control plane. Host
agents orchestrate the reusable scripts and contracts directly from an installed
Skill directory.
