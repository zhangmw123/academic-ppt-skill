"""Propose evidence-grounded academic storyline alternatives."""

from __future__ import annotations

from dataclasses import dataclass

from .evidence import EvidenceGraph


@dataclass(frozen=True)
class StorylineOption:
    option_id: str
    label: str
    stages: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    audience_fit: str
    evidence_strength: str
    narrative_clarity: str
    visual_potential: str
    risk: str

    def to_dict(self) -> dict:
        return {
            "option_id": self.option_id,
            "label": self.label,
            "stages": list(self.stages),
            "evidence_ids": list(self.evidence_ids),
            "audience_fit": self.audience_fit,
            "evidence_strength": self.evidence_strength,
            "narrative_clarity": self.narrative_clarity,
            "visual_potential": self.visual_potential,
            "risk": self.risk,
        }


class StorylinePlanner:
    """Offer alternatives for confirmation without inventing unsupported content."""

    def propose(self, scene: str, graph: EvidenceGraph) -> tuple[tuple[StorylineOption, ...], StorylineOption]:
        if not scene.strip():
            raise ValueError("scene is required")
        evidence_ids = tuple(node.evidence_id for node in graph.all())
        if not evidence_ids:
            raise ValueError("storyline requires evidence")
        evidence_types = {node.evidence_type for node in graph.all()}
        evidence_strength = "strong" if "result" in evidence_types else "limited"
        options = (
            StorylineOption(
                option_id="problem_method_evidence",
                label="Problem -> method -> evidence",
                stages=("problem", "gap", "method", "evidence", "boundary"),
                evidence_ids=evidence_ids,
                audience_fit="defense and paper sharing",
                evidence_strength=evidence_strength,
                narrative_clarity="high",
                visual_potential="high",
                risk="needs a clear evidence boundary",
            ),
            StorylineOption(
                option_id="results_first_mechanism",
                label="Results-first -> mechanism",
                stages=("key result", "comparison", "method", "mechanism", "boundary"),
                evidence_ids=evidence_ids,
                audience_fit="short progress review",
                evidence_strength=evidence_strength,
                narrative_clarity="medium",
                visual_potential="high",
                risk="weak when result evidence is preliminary",
            ),
            StorylineOption(
                option_id="method_first_validation",
                label="Method-first -> validation",
                stages=("requirement", "method", "implementation", "validation", "next step"),
                evidence_ids=evidence_ids,
                audience_fit="technical review",
                evidence_strength=evidence_strength,
                narrative_clarity="medium",
                visual_potential="medium",
                risk="can delay the main conclusion",
            ),
        )
        recommended = self._recommend(scene, options)
        return options, recommended

    @staticmethod
    def _recommend(scene: str, options: tuple[StorylineOption, ...]) -> StorylineOption:
        normalized = scene.lower()
        if any(token in normalized for token in ("weekly", "progress", "周报", "组会")):
            return options[1]
        if any(token in normalized for token in ("technical", "工程", "项目")):
            return options[2]
        return options[0]
