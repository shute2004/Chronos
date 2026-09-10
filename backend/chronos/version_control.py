from typing import Iterable

from diff_match_patch import diff_match_patch

_dmp = diff_match_patch()


def create_patch(old_text: str, new_text: str) -> str:
    """Return a textual patch from old_text to new_text."""
    return _dmp.patch_toText(_dmp.patch_make(old_text, new_text))


def apply_patch(base_text: str, patch_text: str) -> str:
    """Apply one patch and fail if any patch hunk cannot be applied."""
    patches = _dmp.patch_fromText(patch_text)
    new_text, results = _dmp.patch_apply(patches, base_text)
    if not all(results):
        raise ValueError("Failed to apply patch completely.")
    return new_text


def reconstruct_version(base_text: str, patch_texts: Iterable[str]) -> str:
    """Reconstruct a version by applying patches in order."""
    current = base_text
    for patch_text in patch_texts:
        current = apply_patch(current, patch_text)
    return current
