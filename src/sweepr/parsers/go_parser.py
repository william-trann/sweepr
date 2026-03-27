"""Go analyzer.

Go tooling already catches several unused-code cases at compile time. This
module focuses on report-only hints so sweepr can still provide cross-language
repository audits.
"""

from __future__ import annotations

from pathlib import Path
import re

from sweepr.models import FileAnalysis, Finding

IMPORT_BLOCK_RE = re.compile(r"import\s*\((?P<body>.*?)\)", re.DOTALL)
SINGLE_IMPORT_RE = re.compile(r'^\s*import\s+"(?P<name>.+?)"', re.MULTILINE)
FUNC_RE = re.compile(r"^\s*func\s+([a-z][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
TYPE_RE = re.compile(r"^\s*type\s+([a-z][A-Za-z0-9_]*)\s+struct\b", re.MULTILINE)


def _uses(content: str, symbol: str) -> int:
    return len(re.findall(rf"\b{re.escape(symbol)}\b", content))


def analyze_go(path: Path, content: str) -> FileAnalysis:
    """Analyze Go source conservatively."""
    analysis = FileAnalysis(path=path, language="go")

    for block in IMPORT_BLOCK_RE.finditer(content):
        body = block.group("body")
        start_line = content[: block.start()].count("\n") + 1
        for offset, line_text in enumerate(body.splitlines(), start=1):
            candidate = line_text.strip().strip('"')
            if not candidate or candidate.startswith("//"):
                continue
            alias = candidate.split()[-1].strip('"').split("/")[-1]
            if _uses(content, alias) <= 1:
                analysis.findings.append(
                    Finding(
                        kind="unused_import",
                        symbol=alias,
                        line=start_line + offset,
                        message=f"likely unused import: {alias}",
                        safe_to_apply=False,
                    )
                )

    for match in SINGLE_IMPORT_RE.finditer(content):
        value = match.group("name").split("/")[-1]
        line = content[: match.start()].count("\n") + 1
        if _uses(content, value) <= 1:
            analysis.findings.append(
                Finding(
                    kind="unused_import",
                    symbol=value,
                    line=line,
                    message=f"likely unused import: {value}",
                    safe_to_apply=False,
                )
            )

    for regex, kind in [(FUNC_RE, "unused_function"), (TYPE_RE, "unused_class")]:
        for match in regex.finditer(content):
            symbol = match.group(1)
            line = content[: match.start()].count("\n") + 1
            if _uses(content, symbol) <= 1:
                analysis.findings.append(
                    Finding(
                        kind=kind,
                        symbol=symbol,
                        line=line,
                        message=f"potentially unused private symbol: {symbol}",
                        safe_to_apply=False,
                    )
                )

    return analysis
