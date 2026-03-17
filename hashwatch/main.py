"""CLI entry point for HashWatch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from alerts import (
    alert_added,
    alert_deleted,
    alert_integrity_ok,
    alert_modified,
    log_scan_start,
)
from baseline import (
    create_baseline,
    diff_against_baseline,
    load_baseline,
    update_baseline,
)
from config import BASELINE_FILE, LOG_FILE
from hasher import compute_file_hash, hash_directory, normalize_path
from monitor import start_monitoring

BANNER = (
    "╔══════════════════════════════╗\n"
    "║   HashWatch v1.0.0           ║\n"
    "║   File Integrity Monitor     ║\n"
    "╚══════════════════════════════╝"
)


def _collect_current_hashes(paths: list[str | Path]) -> dict[str, str]:
    """Collect hashes for all provided file and directory paths.

    Args:
        paths: List of input paths.

    Returns:
        Mapping from normalized file path to hash digest.
    """
    hashes: dict[str, str] = {}

    for raw_path in paths:
        path_obj = Path(raw_path)
        if not path_obj.exists():
            print(f"Path does not exist and will be skipped: {raw_path}", file=sys.stderr)
            continue

        if path_obj.is_file():
            digest = compute_file_hash(path_obj)
            if digest is not None:
                hashes[normalize_path(path_obj)] = digest
            continue

        if path_obj.is_dir():
            hashes.update(hash_directory(path_obj))

    return hashes


def _print_scan_report(diff: dict[str, list[str]]) -> None:
    """Print grouped scan summary for baseline comparison.

    Args:
        diff: Diff result with modified, added, and deleted lists.
    """
    print("\nSCAN COMPLETE")
    print("─────────────────")
    print(f"Modified : {len(diff['modified'])}")
    print(f"Added    : {len(diff['added'])}")
    print(f"Deleted  : {len(diff['deleted'])}")
    print("─────────────────")


def _cmd_check(paths: list[str]) -> int:
    """Run a one-time integrity check.

    Args:
        paths: Paths to hash and compare.

    Returns:
        Exit code. 0 for clean, 1 for violations or missing baseline.
    """
    baseline = load_baseline()
    if baseline is None:
        return 1

    log_scan_start(paths)
    current = _collect_current_hashes(paths)
    diff = diff_against_baseline(current, baseline)

    baseline_hashes = {
        path: value
        for path, value in baseline.items()
        if path != "_meta" and isinstance(value, str)
    }

    for filepath in diff["modified"]:
        alert_modified(filepath, baseline_hashes[filepath], current[filepath])

    for filepath in diff["added"]:
        alert_added(filepath, current[filepath])

    for filepath in diff["deleted"]:
        alert_deleted(filepath)

    violations = any(diff[key] for key in ("modified", "added", "deleted"))
    if not violations:
        alert_integrity_ok()

    _print_scan_report(diff)
    return 1 if violations else 0


def _cmd_add_path(path: str) -> int:
    """Add a path to monitoring metadata and rebuild baseline.

    Args:
        path: New file or directory path to monitor.

    Returns:
        Exit code. 0 on success, 1 on failure.
    """
    baseline = load_baseline()
    if baseline is None:
        return 1

    meta = baseline.get("_meta", {})
    if not isinstance(meta, dict):
        print("Baseline metadata is malformed.", file=sys.stderr)
        return 1

    existing_paths = list(meta.get("paths_monitored", []))
    if not isinstance(existing_paths, list):
        print("Baseline metadata 'paths_monitored' is malformed.", file=sys.stderr)
        return 1

    normalized_new = normalize_path(path)
    if normalized_new not in existing_paths:
        existing_paths.append(normalized_new)

    create_baseline(existing_paths)
    print(f"Path added to baseline: {normalized_new}")
    return 0


def _cmd_remove_path(path: str) -> int:
    """Remove a path and related entries from baseline.

    Args:
        path: File or directory path to remove.

    Returns:
        Exit code. 0 on success, 1 on failure.
    """
    baseline = load_baseline()
    if baseline is None:
        return 1

    target = normalize_path(path)
    removed = 0

    keys_to_remove = [
        key
        for key in baseline.keys()
        if key != "_meta" and (key == target or key.startswith(f"{target}/"))
    ]

    for key in keys_to_remove:
        baseline.pop(key, None)
        removed += 1

    meta = baseline.get("_meta", {})
    if not isinstance(meta, dict):
        print("Baseline metadata is malformed.", file=sys.stderr)
        return 1

    paths_monitored = meta.get("paths_monitored", [])
    if isinstance(paths_monitored, list):
        meta["paths_monitored"] = [item for item in paths_monitored if item != target]
    meta["total_files"] = len([key for key in baseline.keys() if key != "_meta"])

    try:
        with Path(BASELINE_FILE).open("w", encoding="utf-8") as handle:
            json.dump(baseline, handle, indent=2)
    except OSError as exc:
        print(f"Error writing baseline file: {exc}", file=sys.stderr)
        return 1

    print(f"Removed {removed} entries for path: {target}")
    return 0


def _cmd_list() -> int:
    """Print baseline metadata and monitored paths.

    Returns:
        Exit code. 0 on success, 1 on failure.
    """
    baseline = load_baseline()
    if baseline is None:
        return 1

    meta = baseline.get("_meta", {})
    if not isinstance(meta, dict):
        print("Baseline metadata is malformed.", file=sys.stderr)
        return 1

    created_at = meta.get("created_at", "unknown")
    total_files = meta.get("total_files", 0)
    paths_monitored = meta.get("paths_monitored", [])

    print("Baseline Metadata")
    print("─────────────────")
    print(f"Created at : {created_at}")
    print(f"Total files: {total_files}")
    print("Monitored paths:")

    if isinstance(paths_monitored, list) and paths_monitored:
        for monitored_path in paths_monitored:
            print(f"  - {monitored_path}")
    else:
        print("  (none)")

    return 0


def _cmd_show_log(lines: int) -> int:
    """Print the last N lines of the HashWatch log file.

    Args:
        lines: Number of trailing lines to show.

    Returns:
        Exit code. 0 on success, 1 on failure.
    """
    log_path = Path(LOG_FILE)
    if not log_path.exists():
        print("Log file does not exist yet.", file=sys.stderr)
        return 1

    try:
        with log_path.open("r", encoding="utf-8") as handle:
            content = handle.readlines()
    except OSError as exc:
        print(f"Error reading log file: {exc}", file=sys.stderr)
        return 1

    tail = content[-lines:]
    for line in tail:
        sys.stdout.write(line)

    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for HashWatch.

    Returns:
        Configured argparse parser.
    """
    parser = argparse.ArgumentParser(prog="hashwatch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_create = subparsers.add_parser("create-baseline")
    parser_create.add_argument("--path", nargs="+", required=True)

    parser_update = subparsers.add_parser("update-baseline")
    parser_update.add_argument("--path", nargs="+", required=True)

    parser_check = subparsers.add_parser("check")
    parser_check.add_argument("--path", nargs="+", required=True)

    parser_monitor = subparsers.add_parser("monitor")
    parser_monitor.add_argument("--path", nargs="+", required=True)

    parser_add = subparsers.add_parser("add-path")
    parser_add.add_argument("--path", required=True)

    parser_remove = subparsers.add_parser("remove-path")
    parser_remove.add_argument("--path", required=True)

    subparsers.add_parser("list")

    parser_show_log = subparsers.add_parser("show-log")
    parser_show_log.add_argument("--lines", type=int, default=50)

    return parser


def main() -> int:
    """Run the HashWatch CLI command dispatcher.

    Returns:
        Process exit code.
    """
    print(BANNER)
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "create-baseline":
        create_baseline(args.path)
        return 0

    if args.command == "update-baseline":
        update_baseline(args.path)
        return 0

    if args.command == "check":
        return _cmd_check(args.path)

    if args.command == "monitor":
        baseline = load_baseline()
        if baseline is None:
            print("Cannot monitor without a baseline.", file=sys.stderr)
            return 1
        log_scan_start(args.path)
        start_monitoring(args.path, baseline)
        return 0

    if args.command == "add-path":
        return _cmd_add_path(args.path)

    if args.command == "remove-path":
        return _cmd_remove_path(args.path)

    if args.command == "list":
        return _cmd_list()

    if args.command == "show-log":
        return _cmd_show_log(args.lines)

    print("Unknown command.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
