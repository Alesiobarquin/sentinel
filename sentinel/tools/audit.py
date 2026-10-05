"""Append-only local tool audit until agent-run persistence is introduced."""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Callable, TypeVar
from uuid import uuid4

T = TypeVar("T")


class ToolRecorder:
    def __init__(self, path: Path):
        self.path = path

    def _write(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, allow_nan=False) + "\n")

    def invoke(self, name: str, arguments: dict, action: Callable[[], T], summary: Callable[[T], dict]) -> T:
        call_id = str(uuid4())
        started = time.perf_counter()
        self._write({
            "event": "tool_started", "call_id": call_id, "tool": name,
            "arguments": arguments, "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            result = action()
            result_summary = summary(result)
        except Exception as exc:
            self._write({
                "event": "tool_finished", "call_id": call_id, "tool": name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "success": False, "error_type": type(exc).__name__,
            })
            raise
        self._write({
            "event": "tool_finished", "call_id": call_id, "tool": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "success": True, "result_summary": result_summary,
        })
        return result
