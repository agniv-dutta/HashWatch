"""Tests for hashing utilities."""

from __future__ import annotations

import hashlib

from hasher import compute_file_hash, hash_directory


def test_compute_file_hash_known_value(tmp_path) -> None:
    """It hashes known file content correctly."""
    sample = tmp_path / "sample.txt"
    sample.write_text("hello world", encoding="utf-8")

    expected = hashlib.sha256(b"hello world").hexdigest()
    assert compute_file_hash(sample) == expected


def test_hash_directory_returns_dict(tmp_path, monkeypatch) -> None:
    """It returns a string-to-string hash mapping for directories."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("alpha", encoding="utf-8")
    (folder / "b.txt").write_text("beta", encoding="utf-8")

    result = hash_directory(folder)

    assert isinstance(result, dict)
    assert result
    assert all(isinstance(key, str) for key in result.keys())
    assert all(isinstance(value, str) for value in result.values())


def test_missing_file_returns_none() -> None:
    """It returns None when hashing a missing file."""
    assert compute_file_hash("this-file-should-not-exist.txt") is None
