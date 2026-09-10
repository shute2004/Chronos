import io

import py7zr
from py7zr.io import BytesIOFactory

_INTERNAL_FILENAME = "payload"
_MAX_EXTRACT_BYTES = 100 * 1024 * 1024


def compress(data: bytes) -> bytes:
    archive_buffer = io.BytesIO()
    with py7zr.SevenZipFile(archive_buffer, "w") as archive:
        archive.writestr(data, _INTERNAL_FILENAME)
    return archive_buffer.getvalue()


def decompress(compressed_data: bytes) -> bytes:
    archive_buffer = io.BytesIO(compressed_data)
    factory = BytesIOFactory(limit=_MAX_EXTRACT_BYTES)
    with py7zr.SevenZipFile(archive_buffer, "r") as archive:
        archive.extractall(factory=factory)

    payload = factory.products.get(_INTERNAL_FILENAME)
    if payload is None:
        raise FileNotFoundError(f"{_INTERNAL_FILENAME!r} not found in archive.")
    payload.seek(0)
    return payload.read()
