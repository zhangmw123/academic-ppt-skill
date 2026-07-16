# Academic Presentation Generation

This context defines how source evidence, presentation arguments, template identity, and slide composition interact when producing research presentations.

## Development Handoff (2026-07-16)

- The product remains an installable, self-contained Skill. It is not released and must not be described as complete.
- The standard semantic template compiler now models page -> semantic module -> child slot, including capacity, typography, media scope, ownership, complete removal, and template identity.
- T01 and T03 compile successfully: T01 has 10 pages, 31 modules, and 88 child slots; T03 has 11 pages, 32 modules, and 101 child slots.
- Dynamic reconstruction now uses semantic module geometry, excludes retained content-sized scaffold rasters, suppresses duplicate frames and conclusions, and does not overlay legacy process circles on semantic module headers.
- Rendered object-binding manifests and object-level QA cover duplicate objects, cross-module overlap, orphan components, empty media slots, template residue, font bounds, identity, provenance, and exclusive render modes.
- The complete automated suite passes with `82 passed`.
- Real-content regression candidates are retained under `real_product_outputs/test_file_lab_share_v9` and `real_product_outputs/liujinping_defense_v9`; v7 and v8 remain preserved as requested. Their curated PPTX files each pass 16/16 static, semantic, and object checks.
- Windows PowerPoint successfully exported the v9 candidates once (10 and 18 slides), and those preview directories remain available. Later in the same session, PowerPoint COM regressed and returned `0x80070570` even for the previously successful candidate and minimal image decks. Therefore formal PowerPoint acceptance remains blocked by an unstable local runtime; do not report it as continuously passing.
- The tracked compilation report intentionally records the current PowerPoint failure. T02, T04, T05, T06, T07, and T08 still require full semantic compilation and real-content regression. All eight templates remain mandatory for release.
- Next work should first re-establish a repeatable PowerPoint image-render control, rerun T01/T03 formal review, and only then continue with T02 followed by T04-T08. Do not rebuild the deleted V2 project or delegate core work to another PPT Skill.

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
Ten fixed end-to-end cases, one for each 1.0 Supported Presentation Scene, using representative evidence and method profiles to verify formal delivery.
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

**Speaker Script**:
A separate DOCX document following slide order that provides the presenter's fuller spoken narrative while the PPTX retains Concise Speaker Notes for in-slide delivery.
_Avoid_: Concise Speaker Notes, visible slide text

**1.0 Supported Language**:
Simplified Chinese, English, and mixed Chinese-English source and output content whose typography and rendering are covered by the 1.0 Release Gate.
_Avoid_: An implied quality guarantee for every language

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

**Licensed External Asset Retrieval**:
The automatic retrieval of a necessary public visual asset with a compatible recorded license when supplied material cannot provide that real-world visual, without transmitting user material to the external source.
_Avoid_: Uploading private source material, untraceable search thumbnails

**Delivery Bundle**:
A three-layer Skill output separating the user-facing editable PPTX and speaker script, durable audit artifacts, and disposable working assets so rigor does not clutter the final handoff.
_Avoid_: Flat output directory

**Rigor Profile**:
The independently selected workflow strength: Lean for low-risk short work, Standard for formal research presentations, and Strict for high-risk, high-fidelity, conflicting, sensitive, or repeatedly failing work.
_Avoid_: One maximum-rigor workflow for every task

**Authoritative Edit Baseline**:
A user-edited generated PPTX adopted as the visual source of truth for subsequent localized revisions, protecting untouched pages and manual objects from full regeneration.
_Avoid_: Rebuilding from an outdated layout plan

**Academic PPT Skill**:
The installable, user-facing Codex capability that turns research materials into scene-aware, evidence-grounded, editable academic PPTX deliverables.
_Avoid_: A separate project users must deploy or operate

**Self-Contained Skill Boundary**:
The rule that Academic PPT Skill owns the complete presentation workflow and may use low-level host tools or libraries without delegating its core work to another presentation Skill or becoming a user-managed project.
_Avoid_: Nature-paper2ppt delegation, required companion Skill, internal application presented as the product

**1.0 Release Gate**:
The public-release condition requiring every declared supported Presentation Scene to meet formal delivery quality rather than treating a single representative workflow as sufficient.
_Avoid_: MVP-only acceptance, preview release

**1.0 Release Matrix**:
The bounded verification set of one end-to-end benchmark per supported scene, regression checks for every bundled template, and selected high-risk scene-template combinations.
_Avoid_: Full scene-template Cartesian-product manual acceptance

**1.0 Supported Surface**:
The ten declared Presentation Scenes and bundled templates T01 through T08 that are covered by the 1.0 Release Gate.
_Avoid_: An implied or undocumented support promise

**Conditionally Supported Template**:
A user-supplied PPTX template that may be used for formal delivery only after grammar extraction, editable-component checks, and authoritative real-render validation succeed for that project.
_Avoid_: Guaranteed support for every uploaded PPTX

**1.0 Invocation Contract**:
The Academic PPT Skill defaults to Guided Workflow checkpoints and permits Autonomous Draft only when explicitly requested, with autonomous output remaining an unconfirmed draft.
_Avoid_: Silent automation presented as a formal deliverable

**Supported Skill Host**:
A Codex or Claude Code runtime that discovers and invokes the canonical Academic PPT Skill directory without requiring a host-specific functional fork.
_Avoid_: A separately deployed application, duplicated host implementations

**1.0 Formal Runtime**:
Windows 10 or 11 with Microsoft PowerPoint, the only runtime whose real rendering can satisfy the 1.0 Release Gate for formal delivery.
_Avoid_: Cross-platform draft generation presented as formal visual acceptance

**One-Time Skill Configuration**:
The host-specific installation and environment provisioning completed before normal Academic PPT Skill use, after which users invoke the skill without managing dependencies, virtual environments, or internal commands.
_Avoid_: First-use setup dialogue, per-invocation dependency management

**Progressive Input Discovery**:
The Skill's default interaction strategy of discovering materials and inferring non-blocking presentation choices before asking the user only to resolve material uncertainty or approve a concise task summary.
_Avoid_: An upfront internal configuration questionnaire

**Template Autoselection**:
The selection of one compatible bundled template for a request without a user-supplied template, subject to user confirmation in the inferred task summary.
_Avoid_: Mandatory template picking, silent generic-theme fallback

**Standard Template Specification**:
The machine-readable companion to a standardized editable PPTX, recording page archetypes, semantic modules, child slots, ownership groups, capacity, render modes, and removal policies.
_Avoid_: Screenshot-only template analysis, palette summary

**Semantic Module**:
A bounded argument unit inside a page, such as a contribution card, result panel, method step, or evidence group, that owns its heading, explanation, and optional visual children.
_Avoid_: Decorative box, arbitrary text chunk

**Module Child Slot**:
An owned position inside a Semantic Module for a heading, explanation, image, chart, icon, metric, or caption, including the rules for replacement, omission, and reflow.
_Avoid_: Unowned placeholder, page-wide image slot

**Page-Level Media Layout**:
A composition in which several visuals form the page's primary evidence carrier, including 1, 2, 3, 4, or 6-image galleries and primary-plus-supporting arrangements.
_Avoid_: Any picture anywhere on a slide

**Module-Level Media**:
A visual child owned by one Semantic Module, such as one figure inside each of three contribution cards.
_Avoid_: Page gallery, decorative thumbnail

**Complete Component Removal**:
Deleting an unused component together with every owned frame, label, icon, caption, connector, and placeholder so no sample residue or orphan object remains.
_Avoid_: Emptying text only, covering with a white mask

**Exclusive Region Render Mode**:
The requirement that one semantic region uses either complete native reuse or complete reconstruction, never overlapping old and new implementations.
_Avoid_: Drawing a new panel over a retained sample frame

**Typography Capacity Policy**:
The bounded type scale and reflow rule that protects readability by shortening, splitting, or changing composition before shrinking content below its accepted range.
_Avoid_: Fit by unlimited font shrinking

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
- A **Speaker Script** is the default separate normal-user deliverable in DOCX format and complements, rather than replaces, **Concise Speaker Notes**.
- The **1.0 Supported Language** is inferred from the request and materials; other languages may be attempted but do not satisfy the formal 1.0 quality guarantee without added coverage.
- Formal visual QA requires a real render from the **Authoritative Runtime**; secondary runtimes provide compatibility evidence rather than replacing the authoritative result.
- Every slide, including reconstructed and scientific-freeform slides, follows the same **Deck Visual System** unless a recorded scientific-semantic exception requires otherwise.
- The **Deck Visual System** governs reconstructed charts and surrounding presentation elements, but **Scientific Color Semantics** must be preserved when recoloring would alter or obscure the evidence.
- **Local-First Processing** permits public-information lookup and abstract non-sensitive generation prompts, while external handling of user source material is separately disclosed and approved.
- **Licensed External Asset Retrieval** is permitted when a necessary real-world visual is missing, provided its license and attribution are recorded and no user-supplied or unpublished material is transmitted externally.
- A **Delivery Bundle** exposes the editable PPTX and separate speaker script by default; rendered previews, Deck Rationale, quality summaries, audit, and working artifacts remain available without becoming normal-user handoff clutter.
- The **Rigor Profile** controls which gates and audit artifacts are materialized, while interaction remains independently selectable as **Guided Workflow** or **Autonomous Draft**.
- An **Authoritative Edit Baseline** is revised only on explicitly targeted pages; detected manual edits are protected, and any required rebuild discloses what would be replaced before proceeding.
- The **1.0 Release Gate** requires the Core Benchmark Suite, template regressions, and formal delivery quality gates to pass for the declared supported surface.
- The **1.0 Release Matrix** verifies every supported scene and template without requiring every possible scene-template pair to receive complete manual review.
- The **1.0 Supported Surface** consists of 开题答辩、中期考核、毕业答辩、组会-文献精读、组会-周报进展、组会-课题进展、科研项目申报、科研项目比赛、项目中期与结题、学术会议报告, plus T01 through T08.
- T01 through T08 are unconditionally supported within the **1.0 Supported Surface**; a **Conditionally Supported Template** is rejected early when its required validation does not pass and must never silently fall back to a generic theme.
- The **1.0 Invocation Contract** uses Guided Workflow by default; an **Autonomous Draft** cannot satisfy the **1.0 Release Gate** for a formal deliverable without later user confirmation.
- The canonical **Academic PPT Skill** directory is shared by both **Supported Skill Hosts**; optional host metadata may improve discovery but cannot change the workflow or output contract.
- The **Self-Contained Skill Boundary** makes the Academic PPT Skill the sole owner of source analysis, storyline, template interpretation, composition, rendering, and acceptance; another presentation Skill cannot replace any stage.
- The **1.0 Formal Runtime** is required for formal delivery; WPS is an optional separately verified target, while macOS and Linux output remains an unaccepted draft unless an Authoritative Runtime render is available.
- **One-Time Skill Configuration** prepares the supported host and local runtime once; a normal skill invocation performs only lightweight checks and never exposes internal dependency management to the user.
- **Progressive Input Discovery** makes an inferred task summary the default initial interaction; explicit questions are reserved for missing or materially ambiguous scene, source, template, formal-cover, or delivery choices.
- **Template Autoselection** chooses one T01-T08 candidate by default; alternatives and previews are shown only for low confidence, material conflict, or an explicit user comparison request.
- A **Standard Template Specification** describes each page as **Semantic Modules** with owned **Module Child Slots** and is compiled alongside the standard editable PPTX.
- T01 through T08 must each receive a **Standard Template Specification** and pass the complete release gates; implementation order does not create a partially supported release.
- **Page-Level Media Layout** and **Module-Level Media** are separate composition choices; both require evidence binding and must remove unavailable slots rather than leave empty frames.
- **Exclusive Region Render Mode** requires **Complete Component Removal** before reconstruction and forbids masks or stacked native and rebuilt components.
- The **Typography Capacity Policy** governs every Semantic Module and triggers shortening, splitting, or reflow before unreadable shrinking.

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
