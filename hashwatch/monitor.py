"""Real-time file integrity monitoring via watchdog."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler, FileSystemMovedEvent
from watchdog.observers import Observer

from alerts import alert_added, alert_deleted, alert_modified
from hasher import compute_file_hash, normalize_path


class HashWatchHandler(FileSystemEventHandler):
    """Watchdog event handler that checks file integrity changes."""

    def __init__(self, baseline: dict[str, object], watched_paths: list[str]) -> None:
        """Initialize the handler with baseline data.

        Args:
            baseline: Baseline object loaded from JSON.
            watched_paths: Paths currently being monitored.
        """
        super().__init__()
        self.logger = logging.getLogger("hashwatch")
        self.watched_paths = [normalize_path(path) for path in watched_paths]
        self.baseline_hashes: dict[str, str] = {
            path: value
            for path, value in baseline.items()
            if path != "_meta" and isinstance(value, str)
        }

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        key = normalize_path(event.src_path)
        new_hash = compute_file_hash(event.src_path)
        if new_hash is None:
            return

        old_hash = self.baseline_hashes.get(key)
        if old_hash is None:
            self.logger.info("Change on untracked file ignored: %s", key)
            return

        if new_hash != old_hash:
            alert_modified(key, old_hash, new_hash)
        else:
            self.logger.info("No integrity change detected for %s", key)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        key = normalize_path(event.src_path)
        new_hash = compute_file_hash(event.src_path)
        if new_hash is None:
            return

        alert_added(key, new_hash)
        self.baseline_hashes[key] = new_hash

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if event.is_directory:
            return

        key = normalize_path(event.src_path)
        alert_deleted(key)
        self.baseline_hashes.pop(key, None)

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        """Handle file move/rename events as delete+add."""
        if event.is_directory:
            return

        old_key = normalize_path(event.src_path)
        new_key = normalize_path(event.dest_path)

        alert_deleted(old_key)
        self.baseline_hashes.pop(old_key, None)

        new_hash = compute_file_hash(event.dest_path)
        if new_hash is None:
            return

        alert_added(new_key, new_hash)
        self.baseline_hashes[new_key] = new_hash


def start_monitoring(paths: list[str], baseline: dict[str, object]) -> None:
    """Start real-time monitoring for the given paths.

    Args:
        paths: Files or directories to observe.
        baseline: Loaded baseline data used for integrity comparisons.
    """
    observer = Observer()
    handler = HashWatchHandler(baseline, paths)

    for raw_path in paths:
        path_obj = Path(raw_path)
        if not path_obj.exists():
            print(f"Path does not exist and will be skipped: {raw_path}", file=sys.stderr)
            continue
        observer.schedule(handler, str(path_obj), recursive=True)

    observer.start()
    print("HashWatch is monitoring. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("Monitoring stopped.")
