class ChronosError(Exception):
    """Base class for Chronos history-core errors."""


class PayloadNotFoundError(ChronosError):
    """Raised when a Markdown file does not contain a Chronos payload."""


class InvalidPayloadError(ChronosError):
    """Raised when an embedded Chronos payload is malformed or corrupted."""


class VersionNotFoundError(ChronosError):
    """Raised when a requested stored version does not exist."""
