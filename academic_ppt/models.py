"""Shared serializable contracts for the reusable Academic PPT Skill core."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceBlock:
    block_id: str
    kind: str
    text: str = ""
    locator: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    path: str
    format: str
    role: str
    sha256: str
    blocks: list[SourceBlock]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
