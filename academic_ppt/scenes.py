"""Load and validate the supported presentation scene contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


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

    def validate_plan(
        self,
        scene: str,
        contract: ScenePlanContract,
        *,
        sections: Sequence[str],
        page_count: int,
        total_seconds: int,
    ) -> SceneValidationResult:
        profile = self.resolve(scene)
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
