import base64
import json
from pathlib import Path

import pytest

from chronos import storage
from chronos.exceptions import InvalidPayloadError, PayloadNotFoundError


def test_save_and_load_payload_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    visible = "# Hello\n\nVisible Markdown."
    payload = b"compressed-payload"

    storage.save_file_with_payload(target, visible, payload)

    saved = target.read_text("utf-8")
    assert visible in saved
    assert "chronos-locator" in saved
    assert "chronos-chunk-" in saved
    assert storage.load_payload(target) == payload


def test_resave_removes_old_chronos_comments(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    storage.save_file_with_payload(target, "v1", b"payload-v1")
    first = target.read_text("utf-8")
    locator_b64 = storage._find_tag_in_content(first, "chronos-locator")
    assert locator_b64 is not None
    old_chunk = json.loads(base64.b64decode(locator_b64))["chunk_id"]

    storage.save_file_with_payload(target, first, b"payload-v2")
    second = target.read_text("utf-8")

    assert f"chronos-chunk-{old_chunk}" not in second
    assert storage.load_payload(target) == b"payload-v2"
    assert storage._remove_chronos_comments(second) == "v1"


@pytest.mark.parametrize(
    "visible",
    [
        "",
        "  leading whitespace",
        "trailing whitespace  ",
        "\n\nleading blank lines\nbody",
        "body\n",
        "body\n\n\n",
        "  \nbody\n  \n\n",
        "\tindented\r\nbody\r\n\r\n",
    ],
)
def test_metadata_round_trip_preserves_visible_content_exactly(tmp_path: Path, visible: str) -> None:
    target = tmp_path / "note.md"
    storage.save_file_with_payload(target, visible, b"payload-v1")

    # Read without universal-newline translation so this also covers CRLF.
    with target.open("r", encoding="utf-8", newline="") as handle:
        first_text = handle.read()
    assert storage._remove_chronos_comments(first_text) == visible

    storage.save_file_with_payload(target, first_text, b"payload-v2")
    with target.open("r", encoding="utf-8", newline="") as handle:
        second_text = handle.read()
    assert storage._remove_chronos_comments(second_text) == visible
    assert storage.load_payload(target) == b"payload-v2"


def test_user_authored_inline_chronos_like_comment_is_not_removed(tmp_path: Path) -> None:
    visible = "before <!-- chronos-custom: keep-me --> after\n"
    target = tmp_path / "note.md"
    storage.save_file_with_payload(target, visible, b"payload")
    with target.open("r", encoding="utf-8", newline="") as handle:
        saved = handle.read()
    assert storage._remove_chronos_comments(saved) == visible


def test_missing_file_has_no_payload(tmp_path: Path) -> None:
    with pytest.raises(PayloadNotFoundError, match="File not found"):
        storage.load_payload(tmp_path / "missing.md")


def test_plain_markdown_has_no_payload(tmp_path: Path) -> None:
    target = tmp_path / "plain.md"
    target.write_text("# Plain", "utf-8")
    with pytest.raises(PayloadNotFoundError, match="No Chronos payload found"):
        storage.load_payload(target)


def test_missing_chunk_is_invalid(tmp_path: Path) -> None:
    target = tmp_path / "bad.md"
    locator = base64.b64encode(json.dumps({"chunk_id": "missing", "format": "v1"}).encode()).decode()
    target.write_text(f"<!-- chronos-locator: {locator} -->\n", "utf-8")
    with pytest.raises(InvalidPayloadError, match="Payload chunk not found"):
        storage.load_payload(target)


def test_invalid_base64_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "bad.md"
    target.write_text("<!-- chronos-locator: not_base64! -->\n", "utf-8")
    with pytest.raises(InvalidPayloadError, match="invalid base64"):
        storage.load_payload(target)


def test_parent_directory_is_created(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "note.md"
    storage.save_file_with_payload(target, "hello", b"payload")
    assert target.exists()
