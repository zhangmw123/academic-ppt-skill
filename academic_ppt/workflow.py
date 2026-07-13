"""Persistent gated workflow for academic presentation projects."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable


PHASES = ("brief", "evidence", "content_plan", "visual_plan", "sample", "delivery")
VALID_STATUSES = {"not_started", "draft", "awaiting_confirmation", "confirmed", "stale", "failed"}


class ApprovalKind(str, Enum):
    USER = "user"
    AUTO = "auto"


@dataclass(frozen=True)
class WorkflowConfig:
    scene: str
    interaction_mode: str = "guided"
    rigor_profile: str = "standard"
    authoritative_runtime: str = "powerpoint"

    def validate(self) -> None:
        if self.interaction_mode not in {"guided", "autonomous_draft"}:
            raise ValueError(f"unsupported interaction_mode: {self.interaction_mode}")
        if self.rigor_profile not in {"lean", "standard", "strict"}:
            raise ValueError(f"unsupported rigor_profile: {self.rigor_profile}")
        if self.authoritative_runtime not in {"powerpoint", "wps", "portable"}:
            raise ValueError(f"unsupported authoritative_runtime: {self.authoritative_runtime}")
        if not self.scene.strip():
            raise ValueError("scene is required")


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    sha256: str


@dataclass
class PhaseState:
    name: str
    status: str = "not_started"
    outputs: list[ArtifactRecord] = field(default_factory=list)
    approval_kind: str | None = None
    confirmed_at: str | None = None
    confirmation_note: str = ""

    @property
    def progress_approved(self) -> bool:
        return self.status == "confirmed" or (
            self.status == "awaiting_confirmation" and self.approval_kind == ApprovalKind.AUTO.value
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectWorkflow:
    """Small public interface around workflow validation and persistence."""

    state_relative_path = Path("audit") / "workflow_state.json"

    def __init__(self, root: Path, config: WorkflowConfig, phases: dict[str, PhaseState]):
        self.root = root.resolve()
        self.config = config
        self._phases = phases

    @classmethod
    def create(cls, root: Path | str, config: WorkflowConfig) -> "ProjectWorkflow":
        config.validate()
        project_root = Path(root).resolve()
        for directory in ("deliverables", "audit", "working"):
            (project_root / directory).mkdir(parents=True, exist_ok=True)
        state_path = project_root / cls.state_relative_path
        if state_path.exists():
            raise FileExistsError(f"workflow already exists: {state_path}")
        phases = {name: PhaseState(name=name) for name in PHASES}
        phases[PHASES[0]].status = "draft"
        workflow = cls(project_root, config, phases)
        workflow._save()
        return workflow

    @classmethod
    def open(cls, root: Path | str) -> "ProjectWorkflow":
        project_root = Path(root).resolve()
        state_path = project_root / cls.state_relative_path
        if not state_path.exists():
            raise FileNotFoundError(f"workflow state not found: {state_path}")
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        config = WorkflowConfig(**payload["config"])
        config.validate()
        phases = {}
        for name in PHASES:
            raw = payload["phases"][name]
            status = raw.get("status", "not_started")
            if status not in VALID_STATUSES:
                raise ValueError(f"invalid phase status for {name}: {status}")
            phases[name] = PhaseState(
                name=name,
                status=status,
                outputs=[ArtifactRecord(**item) for item in raw.get("outputs", [])],
                approval_kind=raw.get("approval_kind"),
                confirmed_at=raw.get("confirmed_at"),
                confirmation_note=raw.get("confirmation_note", ""),
            )
        return cls(project_root, config, phases)

    def phase(self, name: str) -> PhaseState:
        try:
            return self._phases[name]
        except KeyError as exc:
            raise ValueError(f"unknown phase: {name}") from exc

    def begin_phase(self, name: str) -> None:
        phase = self.phase(name)
        index = PHASES.index(name)
        if phase.status != "not_started":
            raise ValueError(f"phase {name} cannot begin from {phase.status}")
        if index and not self.phase(PHASES[index - 1]).progress_approved:
            raise ValueError(f"phase {name} requires approval of {PHASES[index - 1]}")
        phase.status = "draft"
        self._save()

    def complete_phase(self, name: str, outputs: Iterable[Path | str]) -> None:
        phase = self.phase(name)
        if phase.status != "draft":
            raise ValueError(f"phase {name} cannot complete from {phase.status}")
        records = []
        for value in outputs:
            path = Path(value).resolve()
            if not path.is_file():
                raise FileNotFoundError(f"phase output not found: {path}")
            try:
                relative = path.relative_to(self.root).as_posix()
            except ValueError as exc:
                raise ValueError(f"phase output must be inside project root: {path}") from exc
            records.append(ArtifactRecord(path=relative, sha256=_sha256(path)))
        if not records:
            raise ValueError(f"phase {name} requires at least one output")
        phase.outputs = records
        phase.status = "awaiting_confirmation"
        phase.approval_kind = None
        phase.confirmed_at = None
        phase.confirmation_note = ""
        self._save()

    def approve_phase(self, name: str, kind: ApprovalKind, note: str) -> None:
        phase = self.phase(name)
        if phase.status != "awaiting_confirmation":
            raise ValueError(f"phase {name} cannot be approved from {phase.status}")
        if kind == ApprovalKind.AUTO and self.config.interaction_mode != "autonomous_draft":
            raise ValueError("automatic approval is only valid in autonomous_draft mode")
        if not note.strip():
            raise ValueError("approval note is required")
        phase.approval_kind = kind.value
        phase.confirmed_at = _now()
        phase.confirmation_note = note.strip()
        if kind == ApprovalKind.USER:
            phase.status = "confirmed"
        self._save()

    def is_formally_confirmed(self) -> bool:
        return all(self.phase(name).status == "confirmed" for name in PHASES[:-1])

    def refresh_artifacts(self) -> list[str]:
        changed = []
        first_changed_index = None
        for index, name in enumerate(PHASES):
            phase = self.phase(name)
            if not phase.outputs or phase.status in {"not_started", "draft"}:
                continue
            for artifact in phase.outputs:
                path = self.root / artifact.path
                if not path.is_file() or _sha256(path) != artifact.sha256:
                    changed.append(name)
                    if first_changed_index is None:
                        first_changed_index = index
                    break
        if first_changed_index is not None:
            for name in PHASES[first_changed_index:]:
                phase = self.phase(name)
                if phase.status != "not_started":
                    phase.status = "stale"
            self._save()
        return changed

    def _save(self) -> None:
        state_path = self.root / self.state_relative_path
        payload = {
            "schema_version": 2,
            "updated_at": _now(),
            "config": asdict(self.config),
            "phases": {name: asdict(state) for name, state in self._phases.items()},
        }
        temporary = state_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(state_path)
