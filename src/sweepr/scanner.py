"""Repository scanning and parser dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from sweepr.models import FileAnalysis
from sweepr.parsers.go_parser import analyze_go
from sweepr.parsers.java_parser import analyze_java
from sweepr.parsers.javascript_parser import analyze_javascript
from sweepr.parsers.python_parser import analyze_python

SUPPORTED_EXTENSIONS = {
    ".py": ("python", analyze_python),
    ".js": ("javascript", analyze_javascript),
    ".jsx": ("javascript", analyze_javascript),
    ".ts": ("typescript", analyze_javascript),
    ".tsx": ("typescript", analyze_javascript),
    ".go": ("go", analyze_go),
    ".java": ("java", analyze_java),
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    "__pycache__",
    "code_sifter_backup",
}


def iter_source_files(root: Path) -> Iterable[Path]:
    """Yield supported source files under ``root`` recursively."""
    for path in root.rglob("*"):
        if path.is_dir() and path.name in IGNORED_DIRS:
            continue
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def analyze_path(root: Path) -> list[FileAnalysis]:
    """Analyze all supported files under ``root``."""
    analyses: list[FileAnalysis] = []
    for file_path in iter_source_files(root):
        language, parser = SUPPORTED_EXTENSIONS[file_path.suffix.lower()]
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        analysis = parser(file_path, content)
        if analysis.findings:
            analyses.append(analysis)
    return analyses
