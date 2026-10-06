"""Developer-owned traffic for a real international shipping fault, never an agent tool."""

from contextlib import AbstractContextManager, nullcontext
import json
from pathlib import Path
import threading
import time
import urllib.request
from uuid import uuid4

from scripts import demo
from evals.corpus import digest, write_json


class InternationalCheckoutWorkload(AbstractContextManager):
    def __init__(self, output: Path):
        self.output = output
        self.stop = threading.Event()
        self.thread = None
        self.failure = None

    def __enter__(self):
        people = json.loads((demo.SOURCE / "src/load-generator/people.json").read_text())
        self.person = next(p for p in people if p["address"]["country"] == "Canada")
        write_json(self.output / "workload-method.json", {
            "driver_sha256": digest(Path(__file__).read_bytes()),
            "method": "Real frontend add-to-cart and checkout with the upstream Canadian fixture; identical closed-loop driver during baseline and incident; local URL only. The five-second gap follows each response, so delay changes arrival rate.",
            "routes": ["/api/cart", "/api/checkout"],
            "gap_seconds": 5,
            "request_timeout_seconds": 25,
            "scope": "Developer test traffic outside the agent tool layer. No request bodies, credentials, or card fields in the audit.",
        })
        self.thread = threading.Thread(target=self._run, name="shipping-test-traffic", daemon=True)
        self.thread.start()
        return self

    def _request(self, route: str, body: dict):
        started = time.monotonic()
        status, error = None, None
        try:
            req = urllib.request.Request("http://127.0.0.1:8080" + route,
                data=json.dumps(body).encode(), method="POST",
                headers={"Content-Type": "application/json", "baggage": "synthetic_request=true"})
            with urllib.request.urlopen(req, timeout=25) as response:
                status = response.status
                if len(response.read(1_000_001)) > 1_000_000:
                    raise ValueError("Workload response too large")
        except (OSError, ValueError) as exc:
            error = type(exc).__name__
        with (self.output / "workload.jsonl").open("a") as stream:
            stream.write(json.dumps({"at": time.time(), "route": route, "country": "Canada",
                "status": status, "error_type": error,
                "latency_ms": (time.monotonic() - started) * 1000}) + "\n")

    def _run(self):
        try:
            while not self.stop.is_set():
                user = str(uuid4())
                self._request("/api/cart", {"userId": user, "item": {"productId": "OLJCESPC7Z", "quantity": 1}})
                if not self.stop.is_set():
                    self._request("/api/checkout", {**self.person, "userId": user})
                self.stop.wait(5)
        except Exception as exc:
            self.failure = type(exc).__name__

    def __exit__(self, exc_type, exc, traceback):
        self.stop.set()
        self.thread.join(timeout=30)
        if self.thread.is_alive():
            raise ValueError("Shipping workload did not stop; do not begin another case")
        if self.failure:
            raise ValueError(f"Shipping workload failed: {self.failure}")


def case_workload(case: dict, output: Path):
    return InternationalCheckoutWorkload(output) if case["id"] == "shipping-slowdown" else nullcontext()
