"""Tests for security alert logging."""

from __future__ import annotations

from unittest.mock import patch

from alerts import alert_added, alert_deleted, alert_modified


def test_alert_modified_logs() -> None:
    """It logs modified-file alerts at warning level."""
    with patch("logging.warning") as mocked_warning:
        alert_modified("project/config.json", "oldhash", "newhash")
        mocked_warning.assert_called_once()


def test_alert_added_logs() -> None:
    """It logs added-file alerts at warning level."""
    with patch("logging.warning") as mocked_warning:
        alert_added("project/new.bin", "abc123")
        mocked_warning.assert_called_once()


def test_alert_deleted_logs() -> None:
    """It logs deleted-file alerts at warning level."""
    with patch("logging.warning") as mocked_warning:
        alert_deleted("project/old.txt")
        mocked_warning.assert_called_once()
