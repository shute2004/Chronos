import io
import json
from pathlib import Path

import pytest

from chronos import cli, commands
from chronos.exceptions import VersionNotFoundError


def test_save_history_and_reconstruct_versions(tmp_path: Path) -> None:
    target = tmp_path / "note.md"

    first = commands.save_version({"file_path": str(target), "content": "Line 1"})
    second = commands.save_version({"file_path": str(target), "content": "Line 1\nLine 2"})
    third = commands.save_version({"file_path": str(target), "content": "Line 1\nLine 2\nLine 3"})

    history = commands.get_history({"file_path": str(target)})
    assert [entry["id"] for entry in history] == [
        third["new_version_id"],
        second["new_version_id"],
        first["new_version_id"],
    ]
    assert all(entry["timestamp"].endswith("Z") for entry in history)

    assert commands.get_content({"file_path": str(target), "version_id": first["new_version_id"]}) == "Line 1"
    assert commands.get_content({"file_path": str(target), "version_id": second["new_version_id"]}) == "Line 1\nLine 2"
    assert commands.get_content({"file_path": str(target), "version_id": third["new_version_id"]}) == "Line 1\nLine 2\nLine 3"
    assert commands.get_content({"file_path": str(target), "version_id": "base"}) == ""


def test_identical_save_does_not_add_version(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    first = commands.save_version({"file_path": str(target), "content": "same"})
    second = commands.save_version({"file_path": str(target), "content": "same"})

    assert second["new_version_id"] == first["new_version_id"]
    assert second["message"] == "No changes detected."
    assert len(commands.get_history({"file_path": str(target)})) == 1


def test_history_for_missing_file_is_empty(tmp_path: Path) -> None:
    assert commands.get_history({"file_path": str(tmp_path / "missing.md")}) == []


def test_invalid_version_raises_specific_error(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    commands.save_version({"file_path": str(target), "content": "v1"})
    with pytest.raises(VersionNotFoundError, match="not found"):
        commands.get_content({"file_path": str(target), "version_id": "missing"})


def test_json_line_cli_success_and_error(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    requests = io.StringIO(
        json.dumps({"command": "save_version", "params": {"file_path": str(target), "content": "hello"}})
        + "\n"
        + json.dumps({"command": "unknown", "params": {}})
        + "\n"
    )
    responses = io.StringIO()

    cli.run(requests, responses)

    decoded = [json.loads(line) for line in responses.getvalue().splitlines()]
    assert decoded[0]["status"] == "success"
    assert decoded[1]["status"] == "error"
    assert "Unknown command" in decoded[1]["error"]["message"]
