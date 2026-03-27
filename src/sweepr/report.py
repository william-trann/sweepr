"""Markdown report generation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

from sweepr.models import FileAnalysis


def render_markdown_report(root: Path, analyses: Iterable[FileAnalysis]) -> str:
    """Render a markdown report summarizing all findings."""
    analyses = list(analyses)
    total_files = len(analyses)
    total_findings = sum(len(a.findings) for a in analyses)
    safe_changes = sum(sum(1 for f in a.findings if f.safe_to_apply) for a in analyses)
    by_language = Counter(a.language for a in analyses)
    by_kind = Counter(f.kind for a in analyses for f in a.findings)

    lines: list[str] = []
    lines.append("# sweepr report")
    lines.append("")
    lines.append(f"Target root: `{root}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Files with findings: **{total_files}**")
    lines.append(f"- Total findings: **{total_findings}**")
    lines.append(f"- Safe auto-fix findings: **{safe_changes}**")
    lines.append("")

    if by_language:
        lines.append("## Findings by language")
        lines.append("")
        for language, count in sorted(by_language.items()):
            lines.append(f"- **{language}**: {count}")
        lines.append("")

    if by_kind:
        lines.append("## Findings by type")
        lines.append("")
        for kind, count in sorted(by_kind.items()):
            lines.append(f"- **{kind}**: {count}")
        lines.append("")

    lines.append("## Detailed findings")
    lines.append("")

    for analysis in sorted(analyses, key=lambda item: str(item.path)):
        lines.append(f"### `{analysis.path}`")
        lines.append("")
        lines.append(f"- Language: **{analysis.language}**")
        lines.append(f"- Findings: **{len(analysis.findings)}**")
        lines.append("")
        for finding in sorted(analysis.findings, key=lambda item: (item.line, item.kind, item.symbol)):
            status = "safe" if finding.safe_to_apply else "report-only"
            lines.append(
                f"- Line {finding.line}: `{finding.kind}` on `{finding.symbol}` — {finding.message} ({status})"
            )
        lines.append("")

    return "\n".join(lines)
