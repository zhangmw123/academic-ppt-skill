"""Build traceable evidence nodes from normalized research sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import re
from typing import Iterable

from .models import SourceBlock, SourceDocument


@dataclass(frozen=True)
class EvidenceNode:
    evidence_id: str
    evidence_type: str
    text: str
    source_id: str
    source_block_id: str
    locator: dict
    data: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceConflict:
    conflict_id: str
    severity: str
    metric: str
    values: tuple[float, ...]
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ClaimNode:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PageNode:
    page_id: str
    claim_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class VisualTaskNode:
    task_id: str
    page_id: str
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


class EvidenceGraph:
    """A source-indexed evidence graph, ready for later claim and page links."""

    def __init__(self, evidence: Iterable[EvidenceNode]):
        self._evidence = tuple(evidence)
        self._by_source: dict[str, tuple[EvidenceNode, ...]] = {}
        self._by_id = {node.evidence_id: node for node in self._evidence}
        self._claims: dict[str, ClaimNode] = {}
        self._pages: dict[str, PageNode] = {}
        self._visual_tasks: dict[str, VisualTaskNode] = {}
        for node in self._evidence:
            self._by_source[node.source_id] = self._by_source.get(node.source_id, ()) + (node,)

    @classmethod
    def from_sources(cls, sources: Iterable[SourceDocument]) -> "EvidenceGraph":
        evidence = []
        for source in sources:
            for block in source.blocks:
                if not cls._is_evidence_block(block):
                    continue
                evidence.append(EvidenceNode(
                    evidence_id=f"EVD_{source.source_id.removeprefix('SRC_')}_{block.block_id}",
                    evidence_type=cls._classify(block),
                    text=block.text,
                    source_id=source.source_id,
                    source_block_id=block.block_id,
                    locator=dict(block.locator),
                    data=dict(block.data),
                ))
        return cls(evidence)

    def for_source(self, source_id: str) -> tuple[EvidenceNode, ...]:
        return self._by_source.get(source_id, ())

    def all(self) -> tuple[EvidenceNode, ...]:
        return self._evidence

    def conflicts(self) -> tuple[EvidenceConflict, ...]:
        measurements: dict[str, list[tuple[float, str, bool]]] = {}
        for node in self._evidence:
            measurement = self._measurement(node)
            if measurement is not None:
                metric, value, is_derived = measurement
                measurements.setdefault(metric, []).append((value, node.evidence_id, is_derived))
        conflicts = []
        for metric, entries in measurements.items():
            values = tuple(sorted({value for value, _, _ in entries}))
            if len(values) < 2:
                continue
            evidence_ids = tuple(evidence_id for _, evidence_id, _ in entries)
            conflicts.append(EvidenceConflict(
                conflict_id=f"CONFLICT_{metric.upper()}_{'_'.join(evidence_ids)}",
                severity="blocking" if any(is_derived for _, _, is_derived in entries) else "material",
                metric=metric,
                values=values,
                evidence_ids=evidence_ids,
            ))
        return tuple(conflicts)

    def add_claim(self, text: str, evidence_ids: Iterable[str]) -> ClaimNode:
        resolved_ids = tuple(evidence_ids)
        if not text.strip():
            raise ValueError("claim text is required")
        if not resolved_ids:
            raise ValueError("claim requires at least one evidence ID")
        unknown = [evidence_id for evidence_id in resolved_ids if evidence_id not in self._by_id]
        if unknown:
            raise ValueError(f"unknown evidence: {', '.join(unknown)}")
        payload = f"{text.strip()}\n{'|'.join(resolved_ids)}".encode("utf-8")
        claim = ClaimNode(
            claim_id=f"CLM_{hashlib.sha256(payload).hexdigest()[:12].upper()}",
            text=text.strip(),
            evidence_ids=resolved_ids,
        )
        self._claims[claim.claim_id] = claim
        return claim

    def trace_claim(self, claim_id: str) -> tuple[EvidenceNode, ...]:
        try:
            claim = self._claims[claim_id]
        except KeyError as exc:
            raise ValueError(f"unknown claim: {claim_id}") from exc
        return tuple(self._by_id[evidence_id] for evidence_id in claim.evidence_ids)

    def claim(self, claim_id: str) -> ClaimNode:
        try:
            return self._claims[claim_id]
        except KeyError as exc:
            raise ValueError(f"unknown claim: {claim_id}") from exc

    def add_page(self, page_id: str, claim_ids: Iterable[str]) -> PageNode:
        resolved_id = page_id.strip()
        resolved_claim_ids = tuple(claim_ids)
        if not resolved_id:
            raise ValueError("page ID is required")
        if resolved_id in self._pages:
            raise ValueError(f"page already exists: {resolved_id}")
        if not resolved_claim_ids:
            raise ValueError("page requires at least one claim")
        unknown = [claim_id for claim_id in resolved_claim_ids if claim_id not in self._claims]
        if unknown:
            raise ValueError(f"unknown claim: {', '.join(unknown)}")
        page = PageNode(page_id=resolved_id, claim_ids=resolved_claim_ids)
        self._pages[page.page_id] = page
        return page

    def trace_page(self, page_id: str) -> tuple[ClaimNode, ...]:
        try:
            page = self._pages[page_id]
        except KeyError as exc:
            raise ValueError(f"unknown page: {page_id}") from exc
        return tuple(self._claims[claim_id] for claim_id in page.claim_ids)

    def add_visual_task(
        self,
        task_id: str,
        page_id: str,
        evidence_ids: Iterable[str],
    ) -> VisualTaskNode:
        resolved_task_id = task_id.strip()
        resolved_evidence_ids = tuple(evidence_ids)
        if not resolved_task_id:
            raise ValueError("visual task ID is required")
        if resolved_task_id in self._visual_tasks:
            raise ValueError(f"visual task already exists: {resolved_task_id}")
        if not resolved_evidence_ids:
            raise ValueError("visual task requires at least one evidence ID")
        page_claim_evidence = {
            evidence_id
            for claim in self.trace_page(page_id)
            for evidence_id in claim.evidence_ids
        }
        unbound = [evidence_id for evidence_id in resolved_evidence_ids if evidence_id not in page_claim_evidence]
        if unbound:
            raise ValueError(f"visual evidence is not bound to page claims: {', '.join(unbound)}")
        visual_task = VisualTaskNode(
            task_id=resolved_task_id,
            page_id=page_id,
            evidence_ids=resolved_evidence_ids,
        )
        self._visual_tasks[visual_task.task_id] = visual_task
        return visual_task

    def trace_visual(self, task_id: str) -> tuple[EvidenceNode, ...]:
        try:
            visual_task = self._visual_tasks[task_id]
        except KeyError as exc:
            raise ValueError(f"unknown visual task: {task_id}") from exc
        return tuple(self._by_id[evidence_id] for evidence_id in visual_task.evidence_ids)

    def add_derived_evidence(
        self,
        text: str,
        input_evidence_ids: Iterable[str],
        *,
        metric: str,
        value: float,
        authorization_note: str,
    ) -> EvidenceNode:
        resolved_input_ids = tuple(input_evidence_ids)
        normalized_metric = metric.strip().lower()
        if not text.strip():
            raise ValueError("derived evidence text is required")
        if not normalized_metric:
            raise ValueError("derived evidence metric is required")
        if not resolved_input_ids:
            raise ValueError("derived evidence requires input evidence")
        if not authorization_note.strip():
            raise ValueError("derived analysis requires authorization")
        unknown = [evidence_id for evidence_id in resolved_input_ids if evidence_id not in self._by_id]
        if unknown:
            raise ValueError(f"unknown evidence: {', '.join(unknown)}")
        payload = (
            f"{text.strip()}\n{normalized_metric}\n{value}\n"
            f"{'|'.join(resolved_input_ids)}"
        ).encode("utf-8")
        node = EvidenceNode(
            evidence_id=f"EVD_DERIVED_{hashlib.sha256(payload).hexdigest()[:12].upper()}",
            evidence_type="derived_analysis",
            text=text.strip(),
            source_id="SYSTEM_DERIVED",
            source_block_id="DERIVED",
            locator={"derived": True},
            data={
                "metric": normalized_metric,
                "value": value,
                "input_evidence_ids": list(resolved_input_ids),
                "authorization_note": authorization_note.strip(),
            },
        )
        self._evidence += (node,)
        self._by_id[node.evidence_id] = node
        self._by_source[node.source_id] = self._by_source.get(node.source_id, ()) + (node,)
        return node

    @staticmethod
    def _is_evidence_block(block: SourceBlock) -> bool:
        return bool(block.text or block.data)

    @staticmethod
    def _classify(block: SourceBlock) -> str:
        if block.kind == "heading":
            return "context"
        if block.kind in {"picture", "chart"}:
            return "asset"
        if block.kind == "table":
            return "result"
        text = block.text.lower()
        if any(token in text for token in ("边界", "限制", "局限", "仅", "不足", "limitation", "boundary")):
            return "limitation"
        if any(token in text for token in ("f1", "accuracy", "提升", "结果", "显著", "result")):
            return "result"
        if any(token in text for token in ("模型", "算法", "方法", "架构", "流程", "model", "method", "architecture")):
            return "method"
        return "fact"

    @staticmethod
    def _measurement(node: EvidenceNode) -> tuple[str, float, bool] | None:
        if node.evidence_type == "derived_analysis":
            return node.data["metric"], float(node.data["value"]), True
        if node.evidence_type != "result":
            return None
        text = node.text.lower()
        metric = next((name for name in ("f1", "accuracy", "precision", "recall") if name in text), None)
        value = re.search(r"(?<![\w.])(\d+(?:\.\d+)?)\s*%?", text)
        if metric is None or value is None:
            return None
        return metric, float(value.group(1)), False
