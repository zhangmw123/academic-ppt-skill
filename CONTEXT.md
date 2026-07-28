# Academic Presentation Generation

This context defines how source evidence, presentation arguments, template identity, and slide composition interact when producing research presentations.

## Development Handoff (2026-07-17)

- The product remains an installable, self-contained Skill. It is not released and must not be described as complete.
- T01 and T03 remain formally accepted. Their standard templates render 10/10 and 11/11 pages in PowerPoint; their curated real-content candidates pass 17/17 automated gates and full-resolution human review on 10/10 and 18/18 pages.
- T02 is now a complete-structure recompile of all 9 source pages, with 26 semantic modules and 83 child slots. Standard-template semantic compilation, structure identity, object ownership, and PowerPoint review pass 9/9. The joint T01/T02/T03 standard render matrix passes 30/30 pages.
- T02 real-content regression uses `测试文件.pdf`, scene `学术会议报告`, and 8 pages. Candidate `real_product_outputs/test_file_conference_t02_v14/working/final/complete_deck.pptx` passes object QA, composition QA, structural checks, and formal PowerPoint validation with 17/17 checks and 8/8 exported pages.
- T02 v14 is not human-accepted: full-resolution review found that slide 4 displayed Figure 5 with a Figure 6 reference caption, and slide 5 displayed Figure 6 with a Figure 7 reference caption. Do not mark T02 complete or reuse v14 as the final candidate.
- The caption root cause is fixed in `scripts/extract_figures.py`: caption candidates now retain geometry and prefer the explicit label nearest the image bottom instead of the first Figure/Table reference on the page. Unit tests pass, and a real re-extraction confirms PDF pages 10/11 resolve to `FIGURE 5`/`FIGURE 6` (page 12 resolves to `FIGURE 7`). The fix has not yet been rebuilt into a new deck.
- Evidence compilation now normalizes scene-role aliases, rejects table/caption text as narrative claims, favors explicit result/contribution/limitation evidence, removes embedded section headings, preserves sentence boundaries, prevents dangling English fragments, and rejects unrelated adjacent figures for contribution/limitation pages. Process cards use complete semantic steps and their quality gate rejects single-word or dangling explanations.
- Formal bundled-template selection retains `source_fidelity` and `source_limitations` in the build audit. Blank-reconstruction object QA no longer collides with native shape IDs, and dark terminal scaffolds receive readable light text.
- The complete automated suite passes with `115 passed`; Skill validation passes; `SKILL.md` remains 500 lines. PowerPoint COM remained stable on the latest T02 run (8/8 export, 17/17 validation).
- Next work starts by rebuilding the same T02 regression as `real_product_outputs/test_file_conference_t02_v15`, confirming captions `FIGURE 5` and `FIGURE 6`, rerunning formal PowerPoint validation, and reviewing all 8 full-resolution slides. Only after that review passes may T02 move from `semantic_compilation_in_progress` to its accepted status.
- T04, T05, T06, T07, and T08 still require full semantic compilation, real-content regression, object QA, PowerPoint review, and the final release matrix. Keep `product_accepted=false`; do not rebuild the deleted V2 project or use another PPT Skill.

## Development Continuation (2026-07-26)

- Standard-template selection now prioritizes an exact semantic-module count and records every selected content module and its child-slot IDs in the dynamic composition plan. The composition gate rejects a plan when visible modules cannot map one-to-one to the selected standard-template modules.
- Point compositions no longer repeat evidence merely to make four cards. They retain three or four distinct evidence modules, allowing T02's three-innovation-pillar archetype to be selected instead of forcing a mismatched four-card page.
- The dynamic renderer now uses a semantic specification's exact `image_or_chart` and `caption` geometry for page galleries and module media only when the number of supplied assets exactly matches the recorded slots; otherwise it retains the existing adaptive grid. This preserves precise template spacing without inventing an invalid binding.
- Regression coverage now verifies T02's three-module binding and rejects semantic module mismatches. The complete suite passes with `117 passed`, and the canonical Skill directory passes the Skill structure validator.
- The real-content regression source `测试文件.pdf` is not tracked in this repository. Provide it locally before rebuilding `real_product_outputs/test_file_conference_t02_v15`; that build still requires its formal Windows PowerPoint export and full-resolution review before T02 can be accepted.

## Development Handoff (2026-07-26, End of Day)

- Both real regression PDFs are now present at the repository root: `测试文件.pdf` and `基于知识图谱的云南植物知识问答系统的研究与构建_刘金平.pdf`. They are local test inputs and remain untracked.
- T02 v15 was generated at `real_product_outputs/test_file_conference_t02_v15`. It contains an 8-page PPTX, speaker script, full fallback preview, and audit bundle. Figure 5, Figure 6, and Figure 7 are bound to PDF pages 10, 11, and 12 respectively; composition QA and object QA pass. Keep `product_accepted=false`: user confirmation, visual-task acceptance, authoritative Windows PowerPoint rendering, and formal full-resolution human review are still outstanding. Linux fallback previews do not have the required Chinese fonts and cannot satisfy the formal visual gate.
- Delivery copying now uses byte-only `shutil.copyfile` instead of `copy2`, because WSL/Windows-mounted paths can reject timestamp and metadata updates even when file content can be written. Delivery regression coverage is included in `tests/test_delivery.py`.
- Agent-authored content can now reset the draft text-component contract to any supported count from 2 through 6. `apply_authored_content` validates the bounded count and writes it back to `component_requirements["text"]`; it still rejects empty components, incomplete page coverage, and counts outside that range. New tests cover a draft contract of 2 expanding to 6 and rejection of 1 or 7 components. The focused authored-content and composition suite passes with `23 passed`.
- The second real regression was successfully generated as an 18-page T03 graduation-defense candidate at `real_product_outputs/liujinping_defense_t03_current`. Its complete scene budget, scene contract, structural QA, scientific-semantic QA, template manifest, composition QA, and object QA pass. It uses six source figures on P006, P007, P009, P012, P015, and P016. The candidate PPTX is `real_product_outputs/liujinping_defense_t03_current/working/final/complete_deck.pptx`; the contact sheet is `real_product_outputs/liujinping_defense_t03_current/deliverables/preview/contact-sheet.jpg`.
- Do not accept the current T03 regression. `product_accepted=false` is correct because visual tasks remain `bound_to_slide`, not accepted; no authoritative Windows PowerPoint render or human review has occurred. The fallback contact sheet also exposed a remaining visible-content defect: `_text_figure` in `academic_ppt/composition.py` still adds `page.next_link` as an evidence bullet. P007 visibly repeats “模型输出将进入...” and P016 repeats “据此归纳...”. The same method can split the hybrid term `BERT-ADV-BiLSTM-GlobalPointer` mid-word into `GlobalPointe` plus `r ...` because `_headline_detail` clips an unseparated claim by raw length.
- Next work must begin by fixing `_text_figure` so visible bullets come only from authored evidence, claim, and interpretation, never `next_link` or `question_answered`. Preserve at least three substantive bullets or fail the composition contract instead of padding with production metadata. Make `_headline_detail` word-boundary-safe for Latin or hybrid scientific terms, and add regression tests analogous to `test_points_never_render_transition_or_question_as_evidence_cards`.
- After that fix, run the focused composition/authored-content tests, then the complete test suite and the official Skill validator. Delete and rebuild only `real_product_outputs/liujinping_defense_t03_current`, inspect P007, P013, P016 and the full contact sheet, and keep both T02 and T03 candidates unaccepted until Windows PowerPoint and explicit full-resolution review are available.
- The working tree is intentionally uncommitted. Current source/test changes include `academic_ppt/authored_content.py`, `academic_ppt/composition.py`, `academic_ppt/delivery.py`, `scripts/render_dynamic.py`, `tests/test_authored_content.py`, `tests/test_composition.py`, `tests/test_delivery.py`, `CONTEXT.md`, and the new `benchmarks/real_products/test_file_conference_t02.content.json`. Do not revert any of them. Use `/tmp/academic-ppt-skill-venv` for tests and builds; the `D:` mount may reject chmod, utime, or Git metadata operations.

## Development Continuation (2026-07-27)

- Fixed visible evidence generation for figure pages: `_text_figure` now uses only authored evidence, claim, and interpretation. It never promotes `next_link` or `question_answered` into an evidence bullet, and pages without three substantive modules fail the composition contract instead of receiving production-metadata padding.
- Made `_headline_detail` token-boundary-safe for Latin and hybrid scientific identifiers on ordinary text, colon-separated metric items, and comma-separated items. `BERT-ADV-BiLSTM-GlobalPointer` and `BERT-BiLSTM-GlobalPointer` now remain intact rather than being truncated to `GlobalPointe` plus a stray `r`.
- The focused composition/authored-content suite passes with `25 passed`; the full suite and Skill validator must be rerun after this continuation's final edits before release work resumes.
- Rebuilt the ignored local regression at `real_product_outputs/liujinping_defense_t03_current` using the real thesis PDF and `benchmarks/real_products/liujinping_defense.content.json`. It produces 18 pages; composition, manifest, and object QA pass for all 18 pages. P007, P013, and P016 content was checked directly and the stale transition text is absent.
- The fallback renderer now finds Microsoft YaHei through the WSL-mounted Windows font directory, so its Chinese preview supports content and geometric inspection. P013 was reflowed from five cards to the exact four-module T03 archetype: the GlobalPointer and final-model metrics form one complete comparison module, preserving all five source model results without shrinking type or exceeding semantic ownership bounds.
- Keep T03 unaccepted: the non-authoritative fallback preview cannot replace Windows PowerPoint. Windows PowerPoint authoritative rendering and an explicit full-resolution visual review remain required. The regenerated acceptance record correctly reports `product_accepted=false`.

## Development Continuation (2026-07-28)

- Template selection is now user-first and auditable. A user-provided `.pptx` is admitted as `conditional_user`, copied byte-for-byte into the working bundle, and is never replaced by a bundled style. Omitting `--template` makes `scripts/build_complete_deck.py` choose a bundled recommendation; its `template` audit record carries `selection_mode` as `user_supplied`, `bundled_requested`, or `bundled_recommended`.
- Automatic bundled selection uses only templates with both a semantic specification and `semantic_compiled_powerpoint_review_passed`: currently T01 and T03. A compatible reviewed scene template is preferred; a custom or unsupported scene falls back to a nearest reviewed template or the first neutral reviewed template, with the substitution reason recorded. Explicit requests for T02 or T04-T08 remain possible, but the audit classifies them as `bundled_development` rather than formal templates.
- Scene classification accepts a canonical scene name, known alias, or natural-language audience/goal description. It records requested text, match type, confidence, signals, nearby scenes, inferred audience, and decision goal. Requests without enough support resolve to `自定义场景` and `custom_unverified`, preserving a bounded generic contract without claiming formal supported-scene acceptance.
- `build_complete_deck.py` now carries scene resolution through task summary, content compilation, page plan, and acceptance. The scene-plan validator accepts custom contracts with an explicit warning instead of failing as an unknown scene. The content compiler can receive an already resolved scene profile, so a custom-scene build does not silently re-resolve or lose the original request.
- Regression coverage includes natural-language and custom-scene classification, automatic template recommendation, nearest-template disclosure, user-template precedence, development-template status, and automatic source-figure content. Full suite: `130 passed`; official Skill validator: `Skill is valid!`.
- A real entrypoint smoke build now passes without `--template`: `测试文件.pdf` plus `--scene "面向学术同行的会议报告"` resolves to `学术会议报告`, automatically selects T01, and generates an 8-page candidate under `/tmp/academic-ppt-template-auto-smoke-v2`. The automatic source-figure payload now supplies evidence, a source-grounded figure reading, and interpretation so it meets the three-bullet composition gate. This candidate remains unaccepted because it has no authoritative PowerPoint render or human visual review.
- No new real deck or authoritative Windows PowerPoint visual review was produced in this continuation. Keep T02 and T03 real-content candidates unaccepted until their existing Windows PowerPoint and full-resolution human-review gates are complete.

## Release Validation Continuation (2026-07-28)

- Current-head T02 real regression was rebuilt from `测试文件.pdf` with `benchmarks/real_products/test_file_conference_t02.content.json` into the ignored working bundle `/tmp/academic-ppt-t02-v16`. The 8-page candidate passes composition QA, object QA, and all 7 structural checks. Its source-figure captions resolve to `FIGURE 1`, `FIGURE 4`, `FIGURE 5`, `FIGURE 6`, and `FIGURE 7`; this confirms the earlier Figure 5/6 caption shift is absent in the current build.
- The full fallback contact sheet was inspected for geometry and content association. No obvious overflow, overlap, or caption/image mismatch was found. This is non-authoritative fallback evidence only: the WSL runtime reports `find_powerpoint() == False`, so it cannot run the required Windows PowerPoint export or satisfy the formal visual gate.
- Keep T02 `semantic_compilation_in_progress` and `product_accepted=false`. Its remaining gates are an authoritative Windows PowerPoint render, explicit full-resolution visual-review decisions for all 8 pages, and user confirmation. Apply the same distinction to the existing T03 real regression.

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
