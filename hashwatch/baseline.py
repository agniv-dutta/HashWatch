"""Baseline creation, loading, and comparison helpers."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import BASELINE_FILE
from hasher import compute_file_hash, hash_directory, normalize_path


def _save_baseline(data: dict[str, object]) -> None:
    """Persist baseline data to disk.

    Args:
        data: Baseline data dictionary to serialize.
    """
    with Path(BASELINE_FILE).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def create_baseline(paths: list[str | Path]) -> dict[str, object]:
    """Create and persist a new baseline from paths.

    Args:
        paths: List of file and/or directory paths.

    Returns:
        Full baseline object with metadata and hash entries.
    """
    logger = logging.getLogger("hashwatch")
    file_hashes: dict[str, str] = {}
    monitored_paths: list[str] = []

    for raw_path in paths:
        input_path = Path(raw_path)
        normalized_input = normalize_path(input_path)
        monitored_paths.append(normalized_input)

        if not input_path.exists():
            logger.warning("Path does not exist and will be skipped: %s", raw_path)
            continue

        if input_path.is_file():
            digest = compute_file_hash(input_path)
            if digest is not None:
                file_hashes[normalize_path(input_path)] = digest
            continue

        if input_path.is_dir():
            file_hashes.update(hash_directory(input_path))

    baseline: dict[str, object] = {
        "_meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(file_hashes),
            "paths_monitored": monitored_paths,
        }
    }
    baseline.update(file_hashes)

    try:
        _save_baseline(baseline)
    except OSError as exc:
        print(f"Error writing baseline file: {exc}", file=sys.stderr)
        return baseline

    print(f"Baseline created: {len(file_hashes)} files indexed.")
    return baseline


def load_baseline() -> dict[str, object] | None:
    """Load the baseline JSON from disk.

    Returns:
        Baseline dictionary if available and valid, otherwise None.
    """
    baseline_path = Path(BASELINE_FILE)
    if not baseline_path.exists():
        print(
            f"No baseline found. Create one first with '{BASELINE_FILE}'.",
            file=sys.stderr,
        )
        return None

    try:
        with baseline_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"Baseline file is invalid JSON: {exc}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"Error reading baseline file: {exc}", file=sys.stderr)
        return None

    if not isinstance(data, dict):
        print("Baseline file content is malformed.", file=sys.stderr)
        return None

    return data


def update_baseline(paths: list[str | Path]) -> None:
    """Overwrite the existing baseline using provided paths.

    Args:
        paths: List of file and/or directory paths.
    """
    create_baseline(paths)
    print("Baseline updated.")


def diff_against_baseline(
    current: dict[str, str], baseline: dict[str, object]
) -> dict[str, list[str]]:
    """Compare current hashes against baseline hashes.

    Args:
        current: Current hash mapping.
        baseline: Loaded baseline object including metadata.

    Returns:
        Dict with modified, added, and deleted file path lists.
    """
    baseline_hashes = {
        path: value
        for path, value in baseline.items()
        if path != "_meta" and isinstance(value, str)
    }

    modified = sorted(
        [
            path
            for path in current
            if path in baseline_hashes and current[path] != baseline_hashes[path]
        ]
    )
    added = sorted([path for path in current if path not in baseline_hashes])
    deleted = sorted([path for path in baseline_hashes if path not in current])

    return {"modified": modified, "added": added, "deleted": deleted}
