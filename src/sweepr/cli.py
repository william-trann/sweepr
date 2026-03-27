"""Command-line interface for sweepr."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sweepr.backup import BACKUP_DIR_NAME, backup_file
from sweepr.logging_utils import configure_logging
from sweepr.report import render_markdown_report
from sweepr.scanner import analyze_path


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="sweepr",
        description="Conservative multi-language dead-code and unused import analyzer.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Root directory to scan.")
    parser.add_argument("--dry-run", action="store_true", help="Print safe changes without modifying files.")
    parser.add_argument("--apply", action="store_true", help="Apply safe changes and create backups first.")
    parser.add_argument("--report", action="store_true", help="Generate a markdown report.")
    parser.add_argument(
        "--report-file",
        default="sweepr-report.md",
        help="Markdown report output path when --report is used.",
    )
    parser.add_argument(
        "--log-file",
        default="sweepr.log",
        help="Path for the execution log file.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose console output.")
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if not any([args.dry_run, args.apply, args.report]):
        args.dry_run = True

    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Path does not exist or is not a directory: {root}")

    logger = configure_logging(verbose=args.verbose, log_file=Path(args.log_file))
    analyses = analyze_path(root)

    if not analyses:
        logger.info("No findings.")
        return 0

    logger.info(f"Scanned root: {root}")
    logger.info(f"Files with findings: {len(analyses)}")

    for analysis in analyses:
        mode = "APPLY" if args.apply and analysis.has_safe_changes else "DRY-RUN"
        logger.info(f"[{mode}] {analysis.path.relative_to(root)}")
        for finding in sorted(analysis.findings, key=lambda item: (item.line, item.kind, item.symbol)):
            prefix = "safe" if finding.safe_to_apply else "note"
            logger.info(f"  - [{prefix}] {finding.message} (line {finding.line})")

        if args.apply and analysis.has_safe_changes:
            backup_path = backup_file(analysis.path, root, root / BACKUP_DIR_NAME)
            analysis.path.write_text(analysis.updated_content or "", encoding="utf-8")
            logger.info(f"  - backup created: {backup_path.relative_to(root)}")
            logger.info("  - file updated")

    if args.report:
        report_path = Path(args.report_file).resolve()
        report_text = render_markdown_report(root, analyses)
        report_path.write_text(report_text, encoding="utf-8")
        logger.info(f"Markdown report written to {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
