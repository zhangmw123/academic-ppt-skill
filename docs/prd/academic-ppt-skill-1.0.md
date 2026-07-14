---
title: Academic PPT Skill 1.0 Release
status: accepted
---

# Academic PPT Skill 1.0 Release PRD

## Product Contract

Academic PPT Skill is an installable Codex and Claude Code Skill, not a separately
deployed application. After host-native configuration, a user invokes it with natural
language or `$academic-ppt-skill` and supplies research materials, a Presentation
Scene, and optionally a template. The skill owns its bundled scripts and references and
returns an editable, evidence-grounded academic PPTX plus its Delivery Bundle.

The user must not need to create or understand an internal project model, invoke
individual Python modules, assemble JSON contracts, choose an internal renderer, or
manage Python dependencies after One-Time Skill Configuration. The skill may create
local working artifacts as part of Local-First Processing.

## 1.0 Supported Surface

- Presentation Scenes: 开题答辩、中期考核、毕业答辩、组会-文献精读、组会-周报进展、组会-课题进展、科研项目申报、科研项目比赛、项目中期与结题、学术会议报告.
- Bundled Templates: T01 through T08 are formally supported.
- User Templates: conditionally supported only after template grammar extraction,
  editable-component checks, and Authoritative Runtime rendering pass. Rejection is
  explicit and must not silently substitute a generic theme or uncontrolled layout.
- Research Method Profiles: computational modeling, laboratory experiment, survey
  empirical analysis, engineering-system validation, and literature synthesis,
  including supported mixed-profile decks.
- Language: Simplified Chinese, English, and mixed Chinese-English material and
  output are formally supported; output language is inferred from the request and
  materials. Other languages may be attempted without formal 1.0 quality assurance.

## Invocation Contract

- Default to Guided Workflow. Require user confirmation after material/task setup,
  evidence/storyline, page plan, visual blueprint, and representative-page review.
- Permit Autonomous Draft only when the user explicitly requests it. It may complete
  internal work, but its output is never a formal deliverable until later confirmed.
- Use Local-First Processing by default. Never send supplied or unpublished material
  to an external service without explicit authorization.
- Prefer supplied visuals and native scientific diagrams. When a necessary real-world
  visual is absent, retrieve a public asset only with a compatible recorded license
  and attribution, without transmitting user materials to the external source.
- Perform only auditable Presentation Transforms automatically, including recorded
  unit conversion, ordering, percentage calculation, and chart reconstruction. Any
  Derived Analysis requires explicit user authorization, reproducible records, and
  visible identification as system-computed rather than source-reported evidence.
- Expose one user-facing skill invocation. Task scripts remain bundled implementation
  details and are not required user knowledge.
- Ship one canonical skill directory for Codex and Claude Code. Host-specific
  discovery metadata may be added only as a thin adapter and must not fork behavior,
  resources, validation, or output contracts.
- Require Windows 10/11 with Microsoft PowerPoint for formal 1.0 delivery. WPS is a
  separately verified optional target; macOS/Linux may generate drafts but cannot
  claim formal visual acceptance without an Authoritative Runtime render.
- Treat host installation, Python/runtime provisioning, bundled resources, and formal
  runtime detection as One-Time Skill Configuration. Normal invocation is direct and
  must not require a user to run internal setup commands or interpret dependencies.
- Default to Progressive Input Discovery: discover supplied materials, infer scene,
  method profiles, template, duration, language, and other non-blocking choices, then
  ask the user to approve or correct one concise task summary. Ask additional
  questions only when a required choice is missing or materially ambiguous.
- Infer and apply a Rigor Profile from the selected scene and risk. Use Standard or
  Strict for formal, conflicting, sensitive, or complex work and Lean for low-risk
  progress reports; expose the profile only when the user requests or overrides it.
- When no template is supplied, use Template Autoselection to recommend one bundled
  T01-T08 template in that summary. Show multiple options or previews only for low
  confidence, material conflict, or an explicit comparison request.

## Required End-to-End Behavior

For every supported scene, the skill must complete this path:

1. Discover and normalize supplied sources with stable source locations and hashes.
2. Infer and present Research Method Profiles and Evidence Conflicts for confirmation.
3. Build traceable evidence, storyline options, Scientific Page Contracts, and a
   user-reviewable page plan.
4. Select a compatible template path, preserve Template Identity, and bind or
   reconstruct layouts without sacrificing argument quality or minimum readability.
5. Produce or bind required visuals, retain Evidence Provenance, and render an
   editable PPTX with Concise Speaker Notes by default, plus a separate DOCX Speaker
   Script for normal-user delivery. Anticipated-question documents are optional
   explicit requests.
6. Run structural, scientific-semantic, visual-composition, and user-review gates.
7. Deliver the editable PPTX and separate speaker script as the visible Delivery
   Bundle. Retain rendered previews, Deck Rationale, quality summary, and durable
   audit artifacts for inspection without presenting them as normal-user output.
8. Accept a user-edited generated PPTX as an Authoritative Edit Baseline for explicit
   page-level revisions, protecting untargeted pages and detected manual objects and
   disclosing any replacement before rebuilding. Complex two-way semantic sync and
   three-way object merges are outside 1.0.

## Template Standardization And Dense Composition

- Compile every bundled template into both a standard editable PPTX and a
  machine-readable semantic specification. Standardize T01 and T03 first, then
  T02 and T04-T08, without collapsing their distinct visual identities.
- Model composition as `page -> semantic module -> child slot`. A module may own a
  heading, explanation, image, chart, icon, caption, or metric; a three-card page
  may therefore contain one evidence visual inside each card rather than only one
  page-level picture area.
- Distinguish page-level media layouts from module-level media. Support 1, 2, 3, 4,
  and 6-image pages, primary-plus-supporting compositions, and verified multi-panel
  source figures. Every used visual requires a semantic role, source binding, and
  caption where needed; an unavailable visual removes or reflows its slot.
- Use mutually exclusive render modes for each semantic region: reuse its complete
  native editable component, or remove that component and fully reconstruct the
  region. Never cover old frames with new panels, masks, or overlapping objects.
- Delete an unused component as a complete ownership group, including its frame,
  sample text, icon, caption, connector, and child placeholder. Orphan or duplicate
  objects are release-blocking defects.
- Use bounded typography instead of arbitrary shrinking. Default ranges are cover
  28-32 pt, page title 20-24 pt, module heading 13-16 pt, body 11-13 pt, and caption
  8.5-10 pt; normal content text should not fall below 10.5 pt. Split, shorten, or
  reflow content when a module cannot fit within those bounds.
- For literature sharing, plan a source-grounded bibliographic context module that
  may include field, journal, publication identity, and verified current indexing
  or quartile information. Time-sensitive metadata must come from a reliable current
  source and must never be inferred from the paper text alone.
- Extend formal QA with object-level duplicate, overlap, orphan, and empty-slot
  checks, plus template-identity comparison and Windows PowerPoint rendering.

## Release Matrix

- Complete one formal-delivery benchmark for each of the ten Presentation Scenes.
- Run grammar, clone/save, dynamic-render, Template Identity, and relevant visual
  regression checks for each bundled template T01-T08.
- Run selected high-risk scene-template combinations. Do not require exhaustive
  manual review of the 10 x 8 Cartesian product.
- Verify a complete deck through the selected Authoritative Runtime for every scene
  benchmark. Package-only validation is insufficient.

## Hard Release Gates

- No fabricated facts, unsupported page claims, or unresolved blocking Evidence
  Conflicts.
- No missing required argument units for a selected scene or method profile.
- No overflow, obvious overlap, unreadable required visual, sample residue,
  unhandled visual task, or missing internal asset in the delivered deck.
- No violation of Scientific Color Semantics or unexplained loss of Template Identity.
- No formal delivery from an unconfirmed Autonomous Draft.
- No release without a passing Authoritative Runtime render for every scene benchmark.
- No macOS/Linux or unverified-WPS output is labeled as a formally accepted delivery.

## Completion Criteria

1. The skill validates with the Codex skill validator and can be configured from the
   public repository in a clean Codex and Claude Code environment.
2. Each Supported Skill Host invokes the same canonical skill copy from an unrelated
   user workspace without relying on the repository checkout as the current directory.
3. All ten scene benchmarks and eight bundled-template regressions pass the Release
   Matrix and Hard Release Gates.
4. The canonical Skill exposes the complete workflow without a separately deployed
   application, server, or user-managed project lifecycle.
5. Tests, representative rendered artifacts, and release documentation identify the
   supported surface and all conditional limitations precisely.
