"""Alerting and logging utilities for HashWatch."""

from __future__ import annotations

import logging
import sys
from typing import Final

from config import LOG_FILE

try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init(autoreset=True)
    RED: Final[str] = Fore.RED
    RESET: Final[str] = Style.RESET_ALL
except ImportError:
    RED = ""
    RESET = ""

LOGGER_NAME: Final[str] = "hashwatch"
LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)


def _colorize(message: str) -> str:
    """Wrap alert text with red color when colorama is available.

    Args:
        message: Message to style.

    Returns:
        Styled or plain message text.
    """
    if not RED:
        return message
    return f"{RED}{message}{RESET}"


def alert_modified(filepath: str, old_hash: str, new_hash: str) -> None:
    """Raise an integrity alert for modified files.

    Args:
        filepath: Path of modified file.
        old_hash: Expected baseline hash.
        new_hash: Newly computed hash.
    """
    message = (
        f"[ALERT] MODIFIED: {filepath}\n"
        f"  Expected : {old_hash}\n"
        f"  Found    : {new_hash}"
    )
    logging.warning(_colorize(message))


def alert_added(filepath: str, new_hash: str) -> None:
    """Raise an alert for newly detected files.

    Args:
        filepath: Path of new file.
        new_hash: Hash for the new file.
    """
    message = f"[ALERT] NEW FILE DETECTED: {filepath}\n  Hash     : {new_hash}"
    logging.warning(_colorize(message))


def alert_deleted(filepath: str) -> None:
    """Raise an alert for deleted files.

    Args:
        filepath: Path of deleted file.
    """
    message = f"[ALERT] FILE DELETED: {filepath}"
    logging.warning(_colorize(message))


def alert_integrity_ok() -> None:
    """Log and print clean scan status."""
    logging.info("[OK] All files match the baseline. No threats detected.")


def log_scan_start(paths: list[str]) -> None:
    """Record that a scan has started.

    Args:
        paths: Monitored input paths.
    """
    logging.info("Scan started for: %s", paths)
