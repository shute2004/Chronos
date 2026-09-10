from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class VersionInfo:
    id: str
    timestamp: datetime
    author: str

    def to_dict(self) -> dict[str, str]:
        timestamp = self.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        timestamp = timestamp.astimezone(timezone.utc)
        return {
            "id": self.id,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "author": self.author,
        }
