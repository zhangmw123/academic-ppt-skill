# Evidence and academic storyline

## Evidence ledger

Record each fact, method statement, result, limitation, interpretation, and
recommended visual as an evidence unit. Extract for page composition rather than
only summarizing the source section:

| Field | Requirement |
|---|---|
| `id` | Stable evidence ID |
| `claim` | Atomic factual or interpretive statement |
| `type` | fact / method / parameter / experiment / result / limitation / case |
| `support` | Numbers, observations, steps, or comparisons that substantiate the claim |
| `mechanism` | Source-supported explanation of why or how |
| `interpretation` | Explicitly marked presenter interpretation, when useful |
| `boundary` | Generalization limit, caveat, conflict, or missing context |
| `value`, `unit` | Preserve original units when present |
| `source` | Exact page, section, table, figure, or paragraph |
| `confidence` | high / medium / low |
| `asset_ids` | Linked equation, figure, subfigure, table, or screenshot IDs |
| `scene_value` | Which scene argument unit this evidence can support |
| `visual_candidates` | Figure, chart, process, comparison, table, or text |

Do not silently reconcile conflicting numbers. Preserve both, explain the likely
reason, and ask the user when the choice changes the conclusion.

## Storyline alternatives

Before outlining, produce 2-3 alternatives. Useful academic variants include:

- problem -> method -> evidence: default for defenses and paper sharing;
- results-first -> mechanism: useful for short lab meetings;
- method-first -> implementation -> validation: useful for technical review;
- gap -> hypotheses -> experiments -> inference: useful for discovery papers;
- design requirement -> material/system -> performance -> mechanism: useful for
  engineering and materials papers.

Compare each option on audience fit, evidence strength, narrative clarity, visual
potential, page budget, and risk. Recommend one and wait for confirmation.

## Page architecture

Every page answers one main question and advances the argument. Compose a page
from related evidence units rather than expanding one chapter heading. Required
fields:

- claim-led title;
- evidence IDs;
- main evidence and secondary evidence;
- caveat;
- optional academic implication or page conclusion when the claim-led title is insufficient;
- transition;
- visual strategy;
- component and density plan.

For a normal content page, target one claim, 2-4 supporting evidence units, 1-2
evidence carriers, an interpretation/mechanism/comparison or boundary, and a
transition. Density is inadequate when a panel has no semantic job or a figure
has no stated implication, even if the raw character count is high. See
[evidence-density-template-contracts.md](evidence-density-template-contracts.md).

For any page with one figure, also record the figure's reading target, takeaway,
mechanism or comparison, and caveat. For multi-column pages, estimate whether each
column has enough evidence to occupy the native panel. If not, resize the original
slots, switch to a compact native archetype, merge the page, or add grounded
secondary evidence. Never keep tall empty cards merely because the template has them.

Split pages with unrelated conclusions. Merge pages that repeat evidence without
advancing the argument. Section count follows this argument, not a template.
