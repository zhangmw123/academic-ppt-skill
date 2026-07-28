"""Load and validate the supported presentation scene contracts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


def _normalize_scene_text(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


_SCENE_SIGNALS: Mapping[str, tuple[str, ...]] = {
    "开题答辩": ("开题", "研究计划", "proposal"),
    "中期考核": ("中期", "midterm", "阶段考核"),
    "毕业答辩": ("毕业答辩", "毕业", "学位答辩", "dissertation"),
    "组会-文献精读": ("文献精读", "论文分享", "journalclub", "paperreview"),
    "组会-周报进展": ("周报", "本周", "weekly", "周进展"),
    "组会-课题进展": ("课题进展", "论文进展", "研究进展", "labmeeting"),
    "科研项目申报": ("项目申报", "基金申报", "立项", "grant"),
    "科研项目比赛": ("项目比赛", "竞赛", "路演", "competition"),
    "项目中期与结题": ("项目验收", "结题", "任务书", "项目中期"),
    "学术会议报告": ("学术会议", "会议报告", "conference", "学术报告"),
}


def _infer_audience(normalized: str) -> str | None:
    for signal, audience in (
        ("答辩委员会", "评审或答辩委员"), ("评委", "评审或答辩委员"),
        ("导师", "导师或课题组"), ("同行", "学术同行"),
        ("客户", "客户或合作方"), ("管理层", "管理决策者"), ("领导", "管理决策者"),
        ("公众", "非专业公众"),
    ):
        if signal in normalized:
            return audience
    return None


def _infer_decision_goal(normalized: str) -> str | None:
    for signal, goal in (
        ("决策", "支持决策"), ("复盘", "复盘结果并确定改进行动"),
        ("答辩", "证明论证或成果可信"), ("汇报", "说明当前状态与下一步"),
        ("培训", "解释知识并支持理解"), ("路演", "说服听众认可方案价值"),
    ):
        if signal in normalized:
            return goal
    return "解释证据、形成判断并明确下一步行动"


def _custom_profile() -> "SceneProfile":
    return SceneProfile(
        name="自定义场景",
        family="custom",
        objective="基于请求中的听众、目标、证据和约束，形成可审计的判断与下一步行动。",
        complete_min=6,
        complete_max=20,
        evidence_states=("planned", "preliminary", "interim", "mixed", "final", "published"),
        required_tags=(
            "research_background", "research_problem", "objectives", "methods",
            "results", "limitations", "future_work",
        ),
        argument_chain=("context", "decision", "approach", "evidence", "boundary", "action"),
        default_variants={
            "custom_5": ("背景与目标", "核心问题与约束", "方案与路径", "证据与判断", "结论与行动"),
        },
        forbidden=("把推测写成事实", "省略证据边界", "用通用场景名称替代用户目标"),
    )


@dataclass(frozen=True)
class SceneProfile:
    name: str
    family: str
    objective: str
    complete_min: int
    complete_max: int
    evidence_states: tuple[str, ...]
    required_tags: tuple[str, ...]
    argument_chain: tuple[str, ...]
    default_variants: Mapping[str, tuple[str, ...]]
    forbidden: tuple[str, ...]


@dataclass(frozen=True)
class SceneResolution:
    """Explain whether a request matched the verified catalog or a custom contract."""

    requested_scene: str
    profile: SceneProfile
    match_type: str
    support_level: str
    confidence: float
    matched_signals: tuple[str, ...] = ()
    nearest_scenes: tuple[str, ...] = ()
    audience: str | None = None
    decision_goal: str | None = None

    def to_dict(self) -> dict:
        return {
            "requested_scene": self.requested_scene,
            "resolved_scene": self.profile.name,
            "match_type": self.match_type,
            "support_level": self.support_level,
            "confidence": self.confidence,
            "matched_signals": list(self.matched_signals),
            "nearest_scenes": list(self.nearest_scenes),
            "audience": self.audience,
            "decision_goal": self.decision_goal,
        }


@dataclass(frozen=True)
class ScenePlanContract:
    deck_scope: str
    evidence_state: str
    coverage_tags: tuple[str, ...] = ()
    argument_units: tuple[str, ...] = ()
    section_variant: str | None = None
    duration_minutes: float | None = None

    @classmethod
    def sample(cls, evidence_state: str) -> "ScenePlanContract":
        return cls(deck_scope="sample", evidence_state=evidence_state)


@dataclass(frozen=True)
class SceneValidationResult:
    scene: str
    deck_scope: str
    page_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors

    def require_passed(self) -> None:
        if self.errors:
            raise ValueError("scene contract failed: " + "; ".join(self.errors))


class SceneCatalog:
    """Resolve aliases and validate plans against the shared scene profile data."""

    def __init__(self, aliases: Mapping[str, str], profiles: Mapping[str, SceneProfile]):
        self.aliases = dict(aliases)
        self.profiles = dict(profiles)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SceneCatalog":
        source = Path(path) if path else Path(__file__).resolve().parents[1] / "references" / "scene-profiles.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        return cls.from_payload(payload)

    @classmethod
    def from_payload(cls, payload: Mapping) -> "SceneCatalog":
        profiles = {
            name: SceneProfile(
                name=name,
                family=item["family"],
                objective=item["objective"],
                complete_min=int(item["complete_min"]),
                complete_max=int(item["complete_max"]),
                evidence_states=tuple(item["evidence_states"]),
                required_tags=tuple(item["required_tags"]),
                argument_chain=tuple(item.get("argument_chain", ())),
                default_variants={
                    variant: tuple(sections)
                    for variant, sections in item.get("default_variants", {}).items()
                },
                forbidden=tuple(item.get("forbidden", ())),
            )
            for name, item in payload["profiles"].items()
        }
        return cls(payload.get("aliases", {}), profiles)

    def resolve(self, scene: str) -> SceneProfile:
        raw = scene.strip()
        canonical = self.aliases.get(raw, raw)
        try:
            return self.profiles[canonical]
        except KeyError as exc:
            raise ValueError(f"unknown scene profile: {scene}") from exc

    def classify(self, scene: str) -> SceneResolution:
        """Resolve a supported scene or create a bounded custom-scene contract.

        The ten catalog scenes are the formally verified release surface, not a
        vocabulary gate. A request outside that vocabulary still receives a
        traceable argument contract and is marked as an unverified extension.
        """

        requested = scene.strip()
        if not requested:
            raise ValueError("scene is required")
        try:
            profile = self.resolve(requested)
        except ValueError:
            profile = None
        if profile is not None:
            return SceneResolution(
                requested_scene=requested,
                profile=profile,
                match_type="exact_supported",
                support_level="verified_supported",
                confidence=1.0,
            )

        normalized = _normalize_scene_text(requested)
        direct_matches = [
            (len(_normalize_scene_text(label)), canonical, label)
            for label, canonical in {**self.aliases, **{name: name for name in self.profiles}}.items()
            if len(_normalize_scene_text(label)) >= 2 and _normalize_scene_text(label) in normalized
        ]
        if direct_matches:
            _, canonical, label = max(direct_matches)
            return SceneResolution(
                requested_scene=requested,
                profile=self.profiles[canonical],
                match_type="inferred_supported",
                support_level="verified_supported",
                confidence=0.92,
                matched_signals=(label,),
                audience=_infer_audience(normalized),
                decision_goal=_infer_decision_goal(normalized),
            )

        scored = self._score_profiles(normalized)
        ranked = tuple(name for _, name, _ in scored[:3])
        if scored and scored[0][0] >= 2:
            score, name, signals = scored[0]
            return SceneResolution(
                requested_scene=requested,
                profile=self.profiles[name],
                match_type="inferred_supported",
                support_level="verified_supported",
                confidence=min(0.88, 0.58 + score * 0.1),
                matched_signals=signals,
                nearest_scenes=ranked[1:],
                audience=_infer_audience(normalized),
                decision_goal=_infer_decision_goal(normalized),
            )

        return SceneResolution(
            requested_scene=requested,
            profile=_custom_profile(),
            match_type="custom_scene",
            support_level="custom_unverified",
            confidence=0.45 if ranked else 0.2,
            nearest_scenes=ranked,
            audience=_infer_audience(normalized),
            decision_goal=_infer_decision_goal(normalized),
        )

    def _score_profiles(self, normalized: str) -> list[tuple[int, str, tuple[str, ...]]]:
        scored = []
        for name, signals in _SCENE_SIGNALS.items():
            matched = tuple(signal for signal in signals if signal in normalized)
            if matched:
                scored.append((len(matched), name, matched))
        return sorted(scored, key=lambda item: (-item[0], item[1]))

    def validate_plan(
        self,
        scene: str,
        contract: ScenePlanContract,
        *,
        sections: Sequence[str],
        page_count: int,
        total_seconds: int,
    ) -> SceneValidationResult:
        resolution = self.classify(scene)
        profile = resolution.profile
        errors: list[str] = []
        warnings: list[str] = []
        if contract.deck_scope not in {"complete", "sample", "short_version"}:
            errors.append(f"unsupported deck_scope={contract.deck_scope}")
        if contract.deck_scope == "complete" and not profile.complete_min <= page_count <= profile.complete_max:
            errors.append(
                f"{profile.name} complete deck requires {profile.complete_min}-{profile.complete_max} pages; "
                f"got {page_count}"
            )
        if contract.deck_scope == "sample" and page_count > 7:
            warnings.append(f"sample deck has {page_count} pages; use short_version or complete")
        if contract.evidence_state not in profile.evidence_states:
            errors.append(
                f"{profile.name} does not allow evidence_state={contract.evidence_state}; "
                f"expected {list(profile.evidence_states)}"
            )
        if contract.deck_scope == "complete":
            missing_tags = sorted(set(profile.required_tags) - set(contract.coverage_tags))
            if missing_tags:
                errors.append(f"{profile.name} missing coverage tags: {missing_tags}")
            missing_arguments = sorted(set(profile.argument_chain) - set(contract.argument_units))
            if missing_arguments:
                errors.append(f"{profile.name} missing argument units: {missing_arguments}")
        if not sections:
            errors.append(f"{profile.name} requires user-visible sections")
        variant = contract.section_variant
        if variant and variant != "custom" and variant not in profile.default_variants:
            errors.append(
                f"{profile.name} unknown section_variant={variant}; "
                f"expected one of {sorted(profile.default_variants)} or custom"
            )
        elif variant in profile.default_variants and tuple(sections) != profile.default_variants[variant]:
            errors.append(f"{profile.name} sections differ from variant {variant}")
        if contract.duration_minutes is not None:
            expected = int(contract.duration_minutes * 60)
            if total_seconds == 0:
                errors.append(f"{profile.name} pages require time_seconds for a {contract.duration_minutes:g}-minute talk")
            elif abs(total_seconds - expected) > max(60, expected * 0.12):
                warnings.append(f"planned speaking time is {total_seconds}s, expected about {expected}s")
        return SceneValidationResult(
            scene=profile.name,
            deck_scope=contract.deck_scope,
            page_count=page_count,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
