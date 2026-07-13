"""Infer research method profiles from normalized source material."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import SourceDocument


PROFILE_KEYWORDS = {
    "computational_modeling": (
        "模型", "算法", "训练", "数据集", "基线", "消融", "泛化",
        "transformer", "model", "algorithm", "dataset", "baseline", "ablation", "f1", "accuracy",
    ),
    "laboratory_experiment": (
        "对照", "重复", "实验条件", "显微", "试剂",
        "control", "replicate", "microscopy", "reagent",
    ),
    "survey_empirical_analysis": (
        "问卷", "样本量", "量表", "信度", "效度", "回归",
        "survey", "questionnaire", "reliability", "validity", "regression",
    ),
    "engineering_system_validation": (
        "架构", "部署", "环境", "负载", "延迟", "吞吐量", "可靠性", "api",
        "architecture", "deployment", "latency", "throughput", "reliability",
    ),
    "literature_synthesis": (
        "文献", "综述", "检索", "引文", "系统评价",
        "literature", "review", "retrieval", "citation", "systematic review",
    ),
}


@dataclass(frozen=True)
class MethodProfileResolution:
    primary: str | None
    secondary: tuple[str, ...]
    basis: dict[str, tuple[str, ...]]
    user_overridden: bool = False


class ResearchMethodProfileResolver:
    """Classify one primary and optional secondary evidence-production profiles."""

    def infer(
        self,
        sources: Iterable[SourceDocument],
        primary_override: str | None = None,
    ) -> MethodProfileResolution:
        if primary_override is not None and primary_override not in PROFILE_KEYWORDS:
            raise ValueError(f"unsupported research method profile: {primary_override}")

        corpus = self._source_text(sources).lower()
        basis = {
            profile: tuple(keyword for keyword in keywords if keyword.lower() in corpus)
            for profile, keywords in PROFILE_KEYWORDS.items()
        }
        scores = {
            profile: sum(corpus.count(keyword.lower()) for keyword in keywords)
            for profile, keywords in PROFILE_KEYWORDS.items()
        }
        candidates = [profile for profile, score in scores.items() if score]
        ranked = sorted(candidates, key=lambda profile: (-scores[profile], profile))
        primary = primary_override or (ranked[0] if ranked else None)
        secondary = tuple(profile for profile in ranked if profile != primary)
        return MethodProfileResolution(
            primary=primary,
            secondary=secondary,
            basis={profile: values for profile, values in basis.items() if values},
            user_overridden=primary_override is not None,
        )

    @staticmethod
    def _source_text(sources: Iterable[SourceDocument]) -> str:
        fragments = []
        for source in sources:
            for block in source.blocks:
                if block.text:
                    fragments.append(block.text)
                for row in block.data.get("rows", []):
                    fragments.extend(str(value) for value in row if value is not None)
        return "\n".join(fragments)
