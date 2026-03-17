"""Hashing utilities for files and directories."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from config import CHUNK_SIZE, HASH_ALGO


def normalize_path(path: str | Path) -> str:
    """Normalize paths for stable storage and comparisons.

    Args:
        path: Input file or directory path.

    Returns:
        A POSIX-style relative path when possible, otherwise an absolute path.
    """
    candidate = Path(path).resolve(strict=False)
    cwd = Path.cwd().resolve()
    try:
        normalized = candidate.relative_to(cwd)
    except ValueError:
        normalized = candidate
    return normalized.as_posix()


def compute_file_hash(filepath: str | Path) -> str | None:
    """Compute the SHA-256 hash for a file.

    Args:
        filepath: Path to the file to hash.

    Returns:
        Lowercase hexadecimal hash string, or None when file access fails.
    """
    logger = logging.getLogger("hashwatch")
    file_path = Path(filepath)

    try:
        hasher = hashlib.new(HASH_ALGO)
        with file_path.open("rb") as handle:
            while True:
                chunk = handle.read(CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except PermissionError:
        logger.warning("Permission denied while hashing: %s", file_path)
        return None
    except FileNotFoundError:
        logger.warning("File not found while hashing: %s", file_path)
        return None


def hash_directory(dirpath: str | Path) -> dict[str, str]:
    """Recursively hash all files in a directory.

    Args:
        dirpath: Root directory path to hash.

    Returns:
        Mapping of normalized relative file paths to SHA-256 hashes.
    """
    hashes: dict[str, str] = {}
    directory = Path(dirpath)

    for root, _, files in os.walk(directory):
        for filename in files:
            full_path = Path(root) / filename
            if full_path.is_symlink():
                continue
            display_path = normalize_path(full_path)
            print(f"Hashing: {display_path}")
            digest = compute_file_hash(full_path)
            if digest is not None:
                hashes[display_path] = digest

    return hashes
