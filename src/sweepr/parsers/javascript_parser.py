"""JavaScript and TypeScript analyzer.

This analyzer intentionally stays conservative and report-only. It uses regular
expressions to identify likely unused imports and private-style declarations.
Because JavaScript and TypeScript often rely on framework magic, decorators,
and build-time transforms, the analyzer does not rewrite files automatically.
"""

from __future__ import annotations

from pathlib import Path
import re

from sweepr.models import FileAnalysis, Finding

IMPORT_RE = re.compile(
    r"^\s*import\s+(?P<what>.+?)\s+from\s+[\"\'](?P<source>.+?)[\"\']\s*;?\s*$",
    re.MULTILINE,
)
FUNCTION_RE = re.compile(r"^\s*function\s+(_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
CLASS_RE = re.compile(r"^\s*class\s+(_[A-Za-z0-9_]+)\b", re.MULTILINE)
CONST_FN_RE = re.compile(r"^\s*(?:const|let|var)\s+(_[A-Za-z0-9_]+)\s*=\s*(?:async\s+)?\(?", re.MULTILINE)


def _count_token_uses(content: str, symbol: str) -> int:
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    return len(pattern.findall(content))


def analyze_javascript(path: Path, content: str) -> FileAnalysis:
    """Analyze JavaScript or TypeScript content conservatively."""
    analysis = FileAnalysis(path=path, language="typescript" if path.suffix in {".ts", ".tsx"} else "javascript")

    for match in IMPORT_RE.finditer(content):
        raw = match.group("what")
        line = content[: match.start()].count("\n") + 1
        candidates = [part.strip().strip("{}*") for part in raw.split(",")]
        names = [c.split(" as ")[-1].strip() for c in candidates if c and c != "type"]
        names = [name for name in names if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", name)]
        if names and all(_count_token_uses(content, name) <= 1 for name in names):
            analysis.findings.append(
                Finding(
                    kind="unused_import",
                    symbol=", ".join(names),
                    line=line,
                    message=f"likely unused import: {', '.join(names)}",
                    safe_to_apply=False,
                )
            )

    for regex, kind in [(FUNCTION_RE, "unused_function"), (CLASS_RE, "unused_class"), (CONST_FN_RE, "unused_function")]:
        for match in regex.finditer(content):
            symbol = match.group(1)
            line = content[: match.start()].count("\n") + 1
            if _count_token_uses(content, symbol) <= 1:
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
