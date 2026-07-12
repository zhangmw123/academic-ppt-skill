# Academic Presentation Generation

This context defines how source evidence, presentation arguments, template identity, and slide composition interact when producing research presentations.

## Language

**Scientific Page Contract**:
A slide-level argument containing one claim, supporting evidence, an evidence carrier, interpretation or boundary, and a transition appropriate to its scene.
_Avoid_: Content block, slide text quota

**Template Identity**:
The recognizable visual language of a template, including typography, palette, title geometry, navigation, spacing rhythm, panel treatment, and decorative motifs.
_Avoid_: Template layout, fixed sample page structure

**Native Reuse**:
Binding content directly to compatible editable components from a source template slide while preserving their geometry and relationships.
_Avoid_: Copy template

**Reconstructive Reuse**:
Rebuilding an editable composition that preserves **Template Identity** when the source slide structure cannot express the **Scientific Page Contract**.
_Avoid_: Freeform fallback

**Scientific Freeform**:
Creating a new research-specific composition when neither native nor reconstructive reuse can carry the argument, while retaining the deck's **Template Identity**.
_Avoid_: Generic page

**Reference Corpus**:
A collection of research presentation pages used to discover candidate composition patterns, with no assumption that every deck or page is a quality exemplar.
_Avoid_: Gold-standard template, target style

**Visual QA Protocol**:
The freeze, register, compare, and rework mechanism used to audit a rendered slide against its approved scientific and visual contracts.
_Avoid_: CyberPPT style

**Presentation Scene**:
The communicative situation that defines the audience decision, argument goal, time budget, and required argument units, such as a proposal defense or lab meeting.
_Avoid_: Research discipline

**Research Method Profile**:
The way a project produces and validates evidence, such as computational modeling, laboratory experimentation, survey-based empirical analysis, engineering-system validation, or literature synthesis.
_Avoid_: Academic subject, department

**Evidence Authority Policy**:
A claim-specific rule that determines how multiple sources are prioritized or reconciled using the presentation scene, the user's objective, and explicit user instructions.
_Avoid_: Latest file wins, paper always wins

**Editable Information Layer**:
The user-facing titles, body text, key numbers, scientific labels, and simple tables, charts, or diagrams that should remain directly editable in the delivered PPTX.
_Avoid_: Every visual object

**Complex Visual Asset**:
A photograph, source figure, microscopy image, map, dense scientific diagram, complex statistical graphic, equation rendering, texture, or non-text visual whose fidelity and legibility take priority over object-level editability.
_Avoid_: Flattened slide

**Evidence Conflict**:
A disagreement among supplied sources about a claim, value, unit, status, interpretation, or requirement, classified as blocking, material, or non-blocking according to its effect on the presentation.
_Avoid_: File difference

**Presentation Transform**:
An auditable change made only to present supplied evidence, such as unit conversion, sorting, percentage calculation, or chart reconstruction, without introducing a new scientific analysis.
_Avoid_: Reanalysis

**Derived Analysis**:
A new statistical test, aggregate, regression, model metric, or scientific inference computed from supplied raw data rather than explicitly reported by a source.
_Avoid_: Source result

**Risk-Driven Review**:
A review policy in which the user confirms the complete content and layout plan, while representative and high-risk slides receive detailed rendered review; page-by-page approval is reserved for explicitly requested high-fidelity work.
_Avoid_: Random sample review, mandatory review of every slide

**Guided Workflow**:
The default delivery mode in which gated content, layout, and representative-render artifacts require explicit user confirmation before formal assembly and delivery.
_Avoid_: Internal validation as user approval

**Autonomous Draft**:
A non-blocking mode that completes all internal artifacts and QA gates without conversational pauses but produces only an unapproved draft until the user confirms it.
_Avoid_: Automatically approved final deck

**Core Benchmark Suite**:
Eight fixed end-to-end cases covering computational defense, laboratory mid-term review, survey proposal, engineering project application, literature-reading lab meeting, mixed-method engineering work, weekly lab update, and research-progress lab meeting.
_Avoid_: Every scene-template combination

**Evidence Provenance**:
The internal trace from source location through evidence, claim, page, and visual that demonstrates why presentation content is supportable without requiring a visible citation on every slide.
_Avoid_: Mandatory per-slide bibliography

**Deck Rationale**:
The page-external audit explaining why each slide exists, which evidence supports it, why its visual and layout were selected, and whether its scientific and visual QA gates passed.
_Avoid_: On-slide process explanation

**Concise Speaker Notes**:
The default page notes containing speaking order, the central interpretation, an important boundary, a transition, and suggested timing without duplicating the slide or becoming a verbatim script.
_Avoid_: Slide transcript

**Authoritative Runtime**:
The presentation application whose real render determines formal visual acceptance; Windows PowerPoint is the default, WPS becomes authoritative when selected in Phase 0, and portable mode is an explicit conservative target.
_Avoid_: Package validation as visual acceptance

**Deck Visual System**:
The locked, deck-wide system of typography, palette, title and navigation geometry, spacing rhythm, panel treatment, chart and table language, icon style, footer, and decorative identity that remains consistent across varied page compositions.
_Avoid_: Repeating one layout

**Scientific Color Semantics**:
A color mapping whose meaning is part of the evidence, such as a heat-map scale, category legend, microscopy channel, remote-sensing class, or medical-image encoding.
_Avoid_: Decorative palette choice

**Local-First Processing**:
The privacy policy that keeps supplied documents, raw data, extraction, template analysis, rendering, and QA local by default; sending original or unpublished content to an external service requires explicit user authorization.
_Avoid_: Silent external upload

**Delivery Bundle**:
A three-layer project output separating concise user-facing deliverables, durable audit artifacts, and disposable working assets so rigor does not clutter the final handoff.
_Avoid_: Flat output directory

**Rigor Profile**:
The independently selected workflow strength: Lean for low-risk short work, Standard for formal research presentations, and Strict for high-risk, high-fidelity, conflicting, sensitive, or repeatedly failing work.
_Avoid_: One maximum-rigor workflow for every task

**Authoritative Edit Baseline**:
A user-edited generated PPTX adopted as the visual source of truth for subsequent localized revisions, protecting untouched pages and manual objects from full regeneration.
_Avoid_: Rebuilding from an outdated layout plan

**V2 Core**:
The unified internal workflow, schema, and module architecture for evidence, templates, layout, visuals, QA, and delivery, exposed to existing users through legacy command and artifact adapters.
_Avoid_: Unbounded patching of v1 JSON contracts

## Relationships

- A **Scientific Page Contract** selects one of **Native Reuse**, **Reconstructive Reuse**, or **Scientific Freeform**.
- **Native Reuse**, **Reconstructive Reuse**, and **Scientific Freeform** must all preserve **Template Identity**.
- When template fidelity conflicts with scientific argument quality or legibility, the **Scientific Page Contract** takes priority.
- A **Reference Corpus** supplies candidate patterns that require page-level review before becoming reusable rules.
- A **Visual QA Protocol** may borrow verification mechanisms from other presentation systems without inheriting their target style or scene assumptions.
- A deck has one **Presentation Scene** and one or more **Research Method Profiles**.
- The **Presentation Scene** determines what the presentation must prove; each **Research Method Profile** determines what counts as evidence and how that evidence should be visualized and reviewed.
- **Research Method Profiles** are inferred from the supplied material, may be combined within one deck, and require user confirmation before content planning.
- An **Evidence Authority Policy** applies per claim or evidence family; unresolved source conflicts remain visible for user adjudication.
- The **Editable Information Layer** remains editable in the final PPTX; a **Complex Visual Asset** may be embedded as a high-quality bitmap or SVG when full reconstruction would reduce fidelity or stability.
- A **Complex Visual Asset** must not flatten or replace the entire **Editable Information Layer**.
- A blocking **Evidence Conflict** requires user adjudication; material conflicts are batched for the Phase 1 confirmation; non-blocking differences follow the **Evidence Authority Policy** and remain recorded.
- A **Presentation Transform** is allowed by default when its formula and source values are recorded.
- A **Derived Analysis** requires explicit user authorization, reproducible computation, and labeling as system-computed; disagreement with a reported result creates a blocking **Evidence Conflict**.
- **Risk-Driven Review** is the default interaction policy. High-risk status is driven by scientific importance, source uncertainty, layout reconstruction, visual complexity, and automated QA confidence.
- A **Guided Workflow** may produce a formal deliverable after the required user confirmations.
- An **Autonomous Draft** records internal continuation as `auto_approved`, never as user `confirmed`, and requires later user confirmation before formal delivery.
- The **Core Benchmark Suite** is the release baseline; focused structural tests run on every change, while broader scene-template stress combinations run for relevant changes and releases.
- **Evidence Provenance** is mandatory internally, but visible slide citations are added only when required by licensing, direct external reuse, the presentation scene, an institutional rule, or an explicit user request.
- The **Deck Rationale** is a default quality artifact and must not add internal production language or QA narration to visible slide content.
- **Concise Speaker Notes** are generated by default; a verbatim script and anticipated-question document are optional scene-dependent deliverables.
- Formal visual QA requires a real render from the **Authoritative Runtime**; secondary runtimes provide compatibility evidence rather than replacing the authoritative result.
- Every slide, including reconstructed and scientific-freeform slides, follows the same **Deck Visual System** unless a recorded scientific-semantic exception requires otherwise.
- The **Deck Visual System** governs reconstructed charts and surrounding presentation elements, but **Scientific Color Semantics** must be preserved when recoloring would alter or obscure the evidence.
- **Local-First Processing** permits public-information lookup and abstract non-sensitive generation prompts, while external handling of user source material is separately disclosed and approved.
- A **Delivery Bundle** exposes the PPTX, previews, rationale, and quality summary by default; audit and working artifacts remain available without becoming visible slide content or handoff clutter.
- The **Rigor Profile** controls which gates and audit artifacts are materialized, while interaction remains independently selectable as **Guided Workflow** or **Autonomous Draft**.
- An **Authoritative Edit Baseline** is revised only on explicitly targeted pages; detected manual edits are protected, and any required rebuild discloses what would be replaced before proceeding.
- The **V2 Core** is the source of truth for new projects; legacy commands and supported v1 artifacts are translated through compatibility adapters and remain covered by regression tests.

## Example dialogue

> **Designer:** "This template has a three-column page, but the evidence is one causal chain plus a result chart. Should we force it into three cards?"
> **Researcher:** "No. Preserve the template identity, then use reconstructive reuse so the causal relationship and evidence remain legible."

## Flagged ambiguities

- "Template reuse" previously meant both cloning source-slide geometry and learning its visual language. These are now **Native Reuse** and **Reconstructive Reuse**.
- "Flexible adjustment" previously had no boundary. It now means changing composition only when required by the **Scientific Page Contract**, while preserving **Template Identity**.
- The six root-level PPTX decks are a **Reference Corpus**, not a mandatory style target or uniform quality standard.
- CyberPPT is a source of **Visual QA Protocol** mechanisms, not the visual or narrative target for academic presentations.
- "Research type" means **Research Method Profile**, not classification by discipline. Engineering projects may combine multiple profiles in one deck.
- Source precedence is not global. The **Evidence Authority Policy** changes with the **Presentation Scene**, user requirements, and the role of each supplied source.
- "Editable PPTX" does not mean every complex scientific visual is editable. It means the **Editable Information Layer** is editable while approved **Complex Visual Assets** may remain rendered assets.
