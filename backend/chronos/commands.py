import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import compression, storage, version_control
from .exceptions import PayloadNotFoundError, VersionNotFoundError
from .models import VersionInfo

_INITIAL_VERSION_ID = "base"


def _load_history_payload(file_path: Path) -> dict[str, Any]:
    compressed = storage.load_payload(file_path)
    payload = json.loads(compression.decompress(compressed).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Chronos payload root must be an object.")
    return payload


def get_history(params: dict[str, Any]) -> list[dict[str, str]]:
    file_path = Path(params["file_path"])
    try:
        payload = _load_history_payload(file_path)
    except PayloadNotFoundError:
        return []

    versions = [
        VersionInfo(
            id=item["id"],
            timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
            author=item.get("author", "Unknown"),
        )
        for item in payload.get("history", [])
    ]
    versions.sort(key=lambda version: version.timestamp, reverse=True)
    return [version.to_dict() for version in versions]


def get_content(params: dict[str, Any]) -> str:
    file_path = Path(params["file_path"])
    version_id = params["version_id"]
    payload = _load_history_payload(file_path)

    base_text = payload.get("base_content", "")
    history = payload.get("history", [])
    if version_id == _INITIAL_VERSION_ID:
        return base_text

    patches: list[str] = []
    for item in history:
        patches.append(item["patch"])
        if item["id"] == version_id:
            return version_control.reconstruct_version(base_text, patches)

    raise VersionNotFoundError(f"Version ID {version_id!r} not found.")


def save_version(params: dict[str, Any]) -> dict[str, str]:
    file_path = Path(params["file_path"])
    new_content = params["content"]

    try:
        payload = _load_history_payload(file_path)
        base_text = payload.get("base_content", "")
        history = payload.get("history", [])
        latest_text = version_control.reconstruct_version(
            base_text,
            [item["patch"] for item in history],
        )
    except PayloadNotFoundError:
        payload = {"base_content": "", "history": []}
        latest_text = ""

    patch_text = version_control.create_patch(latest_text, new_content)
    if not patch_text:
        last_id = payload["history"][-1]["id"] if payload["history"] else _INITIAL_VERSION_ID
        return {"new_version_id": last_id, "message": "No changes detected."}

    now = datetime.now(timezone.utc)
    version_id = f"v-{now.strftime('%Y%m%d%H%M%S%f')}"
    payload["history"].append(
        {
            "id": version_id,
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "author": "User",
            "patch": patch_text,
        }
    )

    serialized = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    storage.save_file_with_payload(file_path, new_content, compression.compress(serialized))
    return {"new_version_id": version_id, "message": "New version saved."}
