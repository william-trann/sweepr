"""Backup utilities.

Before sweepr writes any file, it preserves the original source under a backup
folder so changes can be reversed easily.
"""

from __future__ import annotations

import shutil
from pathlib import Path


BACKUP_DIR_NAME = "code_sifter_backup"


def backup_file(file_path: Path, root: Path, backup_root: Path | None = None) -> Path:
    """Copy ``file_path`` into the backup directory, preserving its relative path."""
    backup_root = backup_root or root / BACKUP_DIR_NAME
    relative_path = file_path.relative_to(root)
    destination = backup_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file_path, destination)
    return destination
