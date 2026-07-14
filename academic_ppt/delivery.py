"""Build a concise user-facing delivery bundle with retained audit artifacts."""

from __future__ import annotations

import shutil
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DeliveryResult:
    visible_files: tuple[Path, ...]
    audit_files: tuple[Path, ...]
    candidate_files: tuple[Path, ...] = ()


class DeliveryBundle:
    """Separate normal-user deliverables from audit and working artifacts."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.deliverables_dir = self.root / "deliverables"
        self.audit_dir = self.root / "audit"
        self.working_dir = self.root / "working"

    @classmethod
    def create(cls, root: Path | str) -> "DeliveryBundle":
        bundle = cls(Path(root))
        for directory in (bundle.deliverables_dir, bundle.audit_dir, bundle.working_dir):
            directory.mkdir(parents=True, exist_ok=True)
        return bundle

    def publish(
        self,
        pptx_path: Path | str,
        speaker_script_path: Path | str,
        *,
        audit_artifacts: Iterable[Path | str] = (),
        quality_summary: dict | None = None,
        approved: bool = True,
    ) -> DeliveryResult:
        pptx = self._require_file(pptx_path, ".pptx")
        speaker_script = self._require_file(speaker_script_path, ".docx")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
        if "sample" in pptx.name.casefold():
            raise ValueError("representative sample PPTX cannot be published")
        target_dir = self.deliverables_dir if approved else self.working_dir / "candidate"
        target_dir.mkdir(parents=True, exist_ok=True)
        published = (
            self._copy(pptx, target_dir / f"{pptx.stem}_{stamp}.pptx"),
            self._copy(speaker_script, target_dir / f"{speaker_script.stem}_{stamp}.docx"),
        )
        visible_files = published if approved else ()
        candidate_files = () if approved else published
        audit_files = tuple(
            self._copy(self._require_file(value), self.audit_dir / Path(value).name)
            for value in audit_artifacts
        )
        if quality_summary is not None:
            summary_path = self.audit_dir / "quality_summary.json"
            summary_path.write_text(json.dumps(quality_summary, ensure_ascii=False, indent=2), encoding="utf-8")
            audit_files += (summary_path,)
        return DeliveryResult(
            visible_files=visible_files,
            audit_files=audit_files,
            candidate_files=candidate_files,
        )

    @staticmethod
    def _require_file(value: Path | str, expected_suffix: str | None = None) -> Path:
        path = Path(value).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        if expected_suffix is not None and path.suffix.lower() != expected_suffix:
            raise ValueError(f"expected {expected_suffix} file: {path}")
        return path

    @staticmethod
    def _copy(source: Path, destination: Path) -> Path:
        if source == destination.resolve():
            return source
        shutil.copy2(source, destination)
        return destination
