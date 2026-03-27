"""Java analyzer.

Java support uses the optional ``javalang`` dependency for parsing when
available. Findings remain report-only because safe automated rewrites require
more semantic certainty than this lightweight tool currently guarantees.
"""

from __future__ import annotations

from pathlib import Path
import re

import javalang

from sweepr.models import FileAnalysis, Finding

IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?(?P<name>[\w.]+);", re.MULTILINE)


def analyze_java(path: Path, content: str) -> FileAnalysis:
    """Analyze Java code conservatively."""
    analysis = FileAnalysis(path=path, language="java")

    try:
        tree = javalang.parse.parse(content)
    except Exception as exc:
        analysis.findings.append(
            Finding(
                kind="parse_warning",
                symbol=path.name,
                line=1,
                message=f"Could not parse Java file safely: {exc}",
                safe_to_apply=False,
            )
        )
        return analysis

    imported_simple_names: list[tuple[str, int]] = []
    for match in IMPORT_RE.finditer(content):
        simple = match.group("name").split(".")[-1]
        line = content[: match.start()].count("\n") + 1
        imported_simple_names.append((simple, line))

    for symbol, line in imported_simple_names:
        if len(re.findall(rf"\b{re.escape(symbol)}\b", content)) <= 1:
            analysis.findings.append(
                Finding(
                    kind="unused_import",
                    symbol=symbol,
                    line=line,
                    message=f"likely unused import: {symbol}",
                    safe_to_apply=False,
                )
            )

    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        if node.name.startswith("_") and len(re.findall(rf"\b{re.escape(node.name)}\b", content)) <= 1:
            analysis.findings.append(
                Finding(
                    kind="unused_function",
                    symbol=node.name,
                    line=node.position.line if node.position else 1,
                    message=f"potentially unused private-style method: {node.name}",
                    safe_to_apply=False,
                )
            )

    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        if node.name.startswith("_") and len(re.findall(rf"\b{re.escape(node.name)}\b", content)) <= 1:
            analysis.findings.append(
                Finding(
                    kind="unused_class",
                    symbol=node.name,
                    line=node.position.line if node.position else 1,
                    message=f"potentially unused private-style class: {node.name}",
                    safe_to_apply=False,
                )
            )

    return analysis
