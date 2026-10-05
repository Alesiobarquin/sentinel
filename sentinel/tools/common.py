"""Shared bounds for service-scoped diagnostic reads."""

from dataclasses import dataclass
from datetime import datetime, timezone
import math


@dataclass(frozen=True)
class TimeWindow:
    start: float
    end: float

    def __post_init__(self):
        for value in (self.start, self.end):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Time-window boundaries must be finite Unix seconds")
        if self.start < 0 or self.end <= self.start or self.end - self.start > 21600:
            raise ValueError("Time window must be nonnegative, increasing, and at most six hours")
        try:
            self.iso_start
            self.iso_end
        except (OverflowError, OSError, ValueError) as exc:
            raise ValueError("Time window is outside the supported date range") from exc

    @property
    def iso_start(self) -> str:
        return datetime.fromtimestamp(self.start, timezone.utc).isoformat()

    @property
    def iso_end(self) -> str:
        return datetime.fromtimestamp(self.end, timezone.utc).isoformat()


def validate_service(value: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 128 or any(ord(c) < 32 for c in value):
        raise ValueError("Service must be a nonempty name of at most 128 characters, without control characters")


def validate_limit(value: int, maximum: int = 100) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"Limit must be an integer between 1 and {maximum}")
