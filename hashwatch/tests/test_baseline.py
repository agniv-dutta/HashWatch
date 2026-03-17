"""Tests for baseline operations."""

from __future__ import annotations

from baseline import create_baseline, diff_against_baseline, load_baseline
from hasher import hash_directory


def test_create_and_load_baseline(tmp_path, monkeypatch) -> None:
    """It creates and loads a baseline with metadata."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "app.py").write_text("print('ok')\n", encoding="utf-8")

    create_baseline([str(folder)])
    loaded = load_baseline()

    assert loaded is not None
    assert "_meta" in loaded
    assert loaded["_meta"]["total_files"] > 0


def test_diff_detects_modification(tmp_path, monkeypatch) -> None:
    """It flags modified files against baseline."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "project"
    folder.mkdir()
    target = folder / "config.json"
    target.write_text('{"safe": true}', encoding="utf-8")

    baseline = create_baseline([str(folder)])
    target.write_text('{"safe": false}', encoding="utf-8")

    current = hash_directory(folder)
    diff = diff_against_baseline(current, baseline)
    assert diff["modified"]


def test_diff_detects_added_file(tmp_path, monkeypatch) -> None:
    """It flags files added after baseline creation."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "project"
    folder.mkdir()
    (folder / "a.txt").write_text("a", encoding="utf-8")

    baseline = create_baseline([str(folder)])
    (folder / "b.txt").write_text("b", encoding="utf-8")

    current = hash_directory(folder)
    diff = diff_against_baseline(current, baseline)
    assert diff["added"]


def test_diff_detects_deleted_file(tmp_path, monkeypatch) -> None:
    """It flags files deleted after baseline creation."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "project"
    folder.mkdir()
    target = folder / "keep.txt"
    target.write_text("watch", encoding="utf-8")

    baseline = create_baseline([str(folder)])
    target.unlink()

    current = hash_directory(folder)
    diff = diff_against_baseline(current, baseline)
    assert diff["deleted"]
