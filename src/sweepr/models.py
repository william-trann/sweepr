"""Shared dataclasses used across analyzers and the CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(slots=True)
class Finding:
    """Represents a single potential cleanup or warning.

    Attributes:
        kind: The type of issue, such as ``unused_import`` or ``unused_variable``.
        symbol: The identifier involved in the finding.
        line: 1-based line number.
        message: Human-readable description.
        safe_to_apply: Whether sweepr can rewrite the code automatically.
        replacement: Optional replacement text for the affected line.
    """

    kind: str
    symbol: str
    line: int
    message: str
    safe_to_apply: bool = False
    replacement: Optional[str] = None


@dataclass(slots=True)
class FileAnalysis:
    """Stores all findings for one file and any rewritten content."""

    path: Path
    language: str
    findings: List[Finding] = field(default_factory=list)
    updated_content: Optional[str] = None

    @property
    def has_safe_changes(self) -> bool:
        """Return True when the file contains at least one safe auto-fix."""
        return any(f.safe_to_apply for f in self.findings) and self.updated_content is not None

    @property
    def change_count(self) -> int:
        """Return total findings count for the file."""
        return len(self.findings)
