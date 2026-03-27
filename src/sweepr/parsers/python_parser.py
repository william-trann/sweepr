"""Python analyzer.

This module uses the built-in ``ast`` module to conservatively detect:
- unused imports
- obviously unused local variables from simple assignments
- potentially unused private top-level functions/classes within the same file

Only unused imports and simple local variable assignments are auto-fixable.
Private functions and classes are reported but not removed automatically.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from sweepr.models import FileAnalysis, Finding


@dataclass(slots=True)
class _ImportRecord:
    names: list[str]
    line: int
    source_line: str


class _UsageCollector(ast.NodeVisitor):
    """Collect names and top-level definitions from a module."""

    def __init__(self) -> None:
        self.loaded_names: set[str] = set()
        self.top_level_defs: dict[str, tuple[str, int]] = {}
        self.function_locals: list[tuple[str, int]] = []
        self.current_function_depth = 0

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.loaded_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.current_function_depth == 0:
            self.top_level_defs[node.name] = ("unused_function", node.lineno)
        self.current_function_depth += 1
        self._collect_simple_assignments(node)
        self.generic_visit(node)
        self.current_function_depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if self.current_function_depth == 0:
            self.top_level_defs[node.name] = ("unused_function", node.lineno)
        self.current_function_depth += 1
        self._collect_simple_assignments(node)
        self.generic_visit(node)
        self.current_function_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.current_function_depth == 0:
            self.top_level_defs[node.name] = ("unused_class", node.lineno)
        self.generic_visit(node)

    def _collect_simple_assignments(self, node: ast.AST) -> None:
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if len(child.targets) != 1:
                    continue
                target = child.targets[0]
                if isinstance(target, ast.Name):
                    self.function_locals.append((target.id, child.lineno))
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    self.function_locals.append((child.target.id, child.lineno))


def _collect_import_records(tree: ast.AST, lines: list[str]) -> list[_ImportRecord]:
    records: list[_ImportRecord] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names = [alias.asname or alias.name.split(".")[0] for alias in node.names]
            records.append(
                _ImportRecord(
                    names=imported_names,
                    line=node.lineno,
                    source_line=lines[node.lineno - 1],
                )
            )
        elif isinstance(node, ast.ImportFrom):
            imported_names = [alias.asname or alias.name for alias in node.names]
            records.append(
                _ImportRecord(
                    names=imported_names,
                    line=node.lineno,
                    source_line=lines[node.lineno - 1],
                )
            )
    return records


def _build_updated_content(
    content: str,
    import_records: list[_ImportRecord],
    loaded_names: set[str],
    unused_locals: list[tuple[str, int]],
) -> str | None:
    lines = content.splitlines()
    modified = False

    for record in import_records:
        if all(name not in loaded_names for name in record.names):
            index = record.line - 1
            if 0 <= index < len(lines):
                lines[index] = ""
                modified = True

    unused_local_lines = {line for _, line in unused_locals}
    for line in unused_local_lines:
        index = line - 1
        if 0 <= index < len(lines):
            original = lines[index]
            if re.match(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*[:=].*$", original):
                indent = re.match(r"^(\s*)", original).group(1)
                lines[index] = f"{indent}pass  # sweepr removed unused variable assignment"
                modified = True

    if not modified:
        return None

    return "\n".join(lines) + ("\n" if content.endswith("\n") else "")


def analyze_python(path: Path, content: str) -> FileAnalysis:
    """Analyze a Python file and return conservative findings."""
    analysis = FileAnalysis(path=path, language="python")
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        analysis.findings.append(
            Finding(
                kind="parse_warning",
                symbol=path.name,
                line=max(exc.lineno or 1, 1),
                message=f"Could not parse file safely: {exc.msg}",
                safe_to_apply=False,
            )
        )
        return analysis

    lines = content.splitlines()
    collector = _UsageCollector()
    collector.visit(tree)

    import_records = _collect_import_records(tree, lines)
    for record in import_records:
        if all(name not in collector.loaded_names for name in record.names):
            symbol = ", ".join(record.names)
            analysis.findings.append(
                Finding(
                    kind="unused_import",
                    symbol=symbol,
                    line=record.line,
                    message=f"remove unused import: {symbol}",
                    safe_to_apply=True,
                )
            )

    unused_locals: list[tuple[str, int]] = []
    for name, line in collector.function_locals:
        if name == "_":
            continue
        if name not in collector.loaded_names:
            unused_locals.append((name, line))
            analysis.findings.append(
                Finding(
                    kind="unused_variable",
                    symbol=name,
                    line=line,
                    message=f"remove unused variable assignment: {name}",
                    safe_to_apply=True,
                )
            )

    for name, (kind, line) in collector.top_level_defs.items():
        if not name.startswith("_") or name in {"__all__", "__version__"}:
            continue
        if name not in collector.loaded_names:
            analysis.findings.append(
                Finding(
                    kind=kind,
                    symbol=name,
                    line=line,
                    message=f"potentially unused private symbol: {name}",
                    safe_to_apply=False,
                )
            )

    analysis.updated_content = _build_updated_content(
        content=content,
        import_records=import_records,
        loaded_names=collector.loaded_names,
        unused_locals=unused_locals,
    )
    return analysis
