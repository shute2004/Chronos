import base64
import binascii
import json
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from .exceptions import ChronosError, InvalidPayloadError, PayloadNotFoundError

_LOCATOR_TAG = "chronos-locator"
_CHUNK_TAG_PREFIX = "chronos-chunk-"
_COMMENT_RE = re.compile(r"<!--\s*(?P<tag>[\w-]+)\s*:\s*(?P<content>\S+)\s*-->")


def _find_tag_in_content(content: str, tag_to_find: str) -> Optional[str]:
    for line in content.splitlines():
        match = _COMMENT_RE.search(line)
        if match and match.group("tag") == tag_to_find:
            return match.group("content")
    return None


def _remove_chronos_comments(content: str) -> str:
    cleaned: list[str] = []
    for line in content.splitlines():
        match = _COMMENT_RE.search(line)
        if match and match.group("tag").startswith("chronos-"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _decode_base64(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise InvalidPayloadError("Payload is corrupted or invalid: invalid base64") from error


def load_payload(file_path: Path) -> bytes:
    if not file_path.exists():
        raise PayloadNotFoundError(f"File not found: {file_path}")

    try:
        content = file_path.read_text("utf-8")
        locator_b64 = _find_tag_in_content(content, _LOCATOR_TAG)
        if not locator_b64:
            raise PayloadNotFoundError(f"No Chronos payload found in {file_path.name}")

        locator_json = _decode_base64(locator_b64).decode("utf-8")
        locator = json.loads(locator_json)
        chunk_id = locator.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise InvalidPayloadError("Locator is invalid or corrupted.")

        chunk_b64 = _find_tag_in_content(content, f"{_CHUNK_TAG_PREFIX}{chunk_id}")
        if not chunk_b64:
            raise InvalidPayloadError("Payload chunk not found for the given locator.")
        return _decode_base64(chunk_b64)
    except ChronosError:
        raise
    except (OSError, UnicodeDecodeError) as error:
        raise ChronosError(f"Failed to read file: {error}") from error
    except Exception as error:
        raise InvalidPayloadError(f"Payload is corrupted or invalid: {error}") from error


def save_file_with_payload(target_path: Path, markdown_content: str, payload_data: bytes) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)

    chunk_id = str(uuid.uuid4())
    chunk_tag = f"{_CHUNK_TAG_PREFIX}{chunk_id}"
    chunk_b64 = base64.b64encode(payload_data).decode("ascii")

    locator = {"chunk_id": chunk_id, "format": "v1"}
    locator_b64 = base64.b64encode(json.dumps(locator, separators=(",", ":")).encode("utf-8")).decode("ascii")

    cleaned_content = _remove_chronos_comments(markdown_content).strip()
    final_content = (
        f"{cleaned_content}\n\n"
        f"<!-- {chunk_tag}: {chunk_b64} -->\n"
        f"<!-- {_LOCATOR_TAG}: {locator_b64} -->\n"
    )

    temp_dir = Path(tempfile.mkdtemp(dir=target_path.parent))
    temp_file = temp_dir / target_path.name
    try:
        temp_file.write_text(final_content, "utf-8")
        os.replace(temp_file, target_path)
    except Exception as error:
        raise OSError(f"Failed to save file securely: {error}") from error
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
