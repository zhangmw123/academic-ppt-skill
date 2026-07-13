"""Evidence-bound visual task state machine."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VisualTask:
    task_id: str
    page_id: str
    evidence_ids: tuple[str, ...]
    task_type: str
    status: str = "planned"
    output_path: str | None = None

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        page_id: str,
        evidence_ids: Iterable[str],
        task_type: str,
    ) -> "VisualTask":
        resolved_evidence_ids = tuple(evidence_ids)
        if not task_id.strip():
            raise ValueError("visual task ID is required")
        if not page_id.strip():
            raise ValueError("visual task page ID is required")
        if not resolved_evidence_ids:
            raise ValueError("visual task requires evidence")
        if not task_type.strip():
            raise ValueError("visual task type is required")
        return cls(
            task_id=task_id.strip(),
            page_id=page_id.strip(),
            evidence_ids=resolved_evidence_ids,
            task_type=task_type.strip(),
        )

    def lock_semantics(self) -> "VisualTask":
        return self._transition("planned", "semantics_locked")

    def mark_rendered(self, output_path: Path | str) -> "VisualTask":
        path = Path(output_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return replace(self._transition("semantics_locked", "rendered"), output_path=str(path))

    def bind_to_slide(self) -> "VisualTask":
        return self._transition("rendered", "bound_to_slide")

    def mark_render_inspected(self) -> "VisualTask":
        return self._transition("bound_to_slide", "render_inspected")

    def accept(self) -> "VisualTask":
        return self._transition("render_inspected", "accepted")

    def _transition(self, expected: str, next_status: str) -> "VisualTask":
        if self.status != expected:
            raise ValueError(f"cannot {next_status} visual task from {self.status}")
        return replace(self, status=next_status)
