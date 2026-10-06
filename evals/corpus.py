"""Real-backend capture and immutable native-tool replay for paired evaluations."""

from contextlib import AbstractContextManager
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import re
import time
from uuid import uuid4

from scripts import demo
from sentinel.agent.contracts import Incident, ToolRequest
from sentinel.agent.local import local_tools
from sentinel.tools.audit import ToolRecorder
from sentinel.tools.http import TelemetryError

CATALOG = demo.ROOT / "evals/resume-scenarios.json"
LAB_STATE = demo.CACHE / "evaluation-state.json"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def catalog() -> list[dict]:
    data = json.loads(CATALOG.read_text())
    cases = data["scenarios"]
    if data["demo_commit"] != demo.load_lock()["commit"] or len({s["id"] for s in cases}) != len(cases):
        raise ValueError("Catalog identity/version is inconsistent")
    required = {"id", "category", "service", "affected_services", "injection", "symptom", "root_cause",
                "expected_outcome", "expected_evidence", "relevant_telemetry", "acceptable_diagnosis",
                "acceptable_remediation", "noncausal_evidence", "required_tools", "limits"}
    for case in cases:
        if set(case) != required or case["expected_outcome"] not in {"diagnose", "abstain"}:
            raise ValueError("Incomplete scenario ground truth")
        Incident(service=case["service"], symptom=case["symptom"], start=1000.0, end=1180.0)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", case["id"]):
            raise ValueError("Scenario ID must be a safe directory name")
        if not all(case[field] for field in required - {"injection"}):
            raise ValueError("Empty scenario ground truth")
    return cases


def runtime() -> list[dict]:
    result = subprocess.run(["docker", "ps", "-a", "--filter", "label=com.docker.compose.project=sentinel-demo",
                             "--format", "{{.Names}}"], capture_output=True, text=True, check=True, timeout=15)
    names = result.stdout.splitlines()
    result = subprocess.run(["docker", "inspect", *names], capture_output=True, text=True, check=True, timeout=15)
    return [{"name": v["Name"].lstrip("/"), "image_id": v["Image"], "restart_count": v["RestartCount"],
             "running": v["State"]["Running"], "started_at": v["State"]["StartedAt"],
             "memory_limit": v["HostConfig"]["Memory"], "oom_killed": v["State"]["OOMKilled"]}
            for v in json.loads(result.stdout)]


def compose_service(action: str, service: str) -> None:
    if action not in {"stop", "start"} or service not in {"payment", "otel-collector"}:
        raise ValueError("Evaluation operation outside the fixed local allowlist")
    subprocess.run([*demo.compose_command(), action, service], check=True, capture_output=True, timeout=90)


def cleanup(owner: str | None = None) -> None:
    if not LAB_STATE.exists():
        return
    state = json.loads(LAB_STATE.read_text())
    if owner is not None and state["owner"] != owner:
        raise ValueError("Cannot clean another evaluation's local fault")
    path = demo.SOURCE / "src/flagd/demo.flagd.json"
    data = json.loads(path.read_text())
    for name, previous in state["previous_variants"].items():
        if data["flags"][name]["defaultVariant"] not in {previous, state["injected_variants"][name]}:
            raise ValueError("Flag changed by another operation; preserve it for review")
        data["flags"][name]["defaultVariant"] = previous
    path.write_text(json.dumps(data, indent=2) + "\n")
    for service in state["stopped_services"]:
        compose_service("start", service)
    LAB_STATE.unlink()


class LabCase(AbstractContextManager):
    """Developer-only fault mutation, persisted before changing local state."""

    def __init__(self, scenario: dict):
        self.scenario, self.owner = scenario, str(uuid4())

    def __enter__(self):
        if demo.STATE.exists() or LAB_STATE.exists():
            raise ValueError("Existing local fault must be reviewed/reset before evaluation")
        path = demo.SOURCE / "src/flagd/demo.flagd.json"
        data = json.loads(path.read_text())
        if any(f["defaultVariant"] != "off" for f in data["flags"].values()):
            raise ValueError("Preserve existing flags: evaluation requires an all-off baseline")
        injection = self.scenario["injection"]
        variants = injection["flags"]
        for name, variant in variants.items():
            if data["flags"][name]["state"] != "ENABLED" or variant not in data["flags"][name]["variants"]:
                raise ValueError("Scenario does not match the pinned flags")
        stopped = injection["stop_services"]
        if not set(stopped) <= {"payment", "otel-collector"} or not set(variants) <= {
            "paymentFailure", "cartFailure", "adFailure", "intlShippingSlowdown",
            "productCatalogLockContention", "adHighCpu", "paymentUnreachable"}:
            raise ValueError("Scenario mutation is outside the reviewed local fault allowlist")
        current = runtime()
        for service in stopped:
            if not any(v["name"] == f"sentinel-demo-{service}-1" and v["running"] for v in current):
                raise ValueError("Preserve a service that was already stopped")
        state = {"owner": self.owner, "scenario": self.scenario["id"], "previous_variants":
                 {name: data["flags"][name]["defaultVariant"] for name in variants},
                 "injected_variants": variants, "stopped_services": stopped}
        with LAB_STATE.open("x") as stream:
            json.dump(state, stream)
            stream.flush()
            import os
            os.fsync(stream.fileno())
        try:
            for name, variant in variants.items():
                data["flags"][name]["defaultVariant"] = variant
            path.write_text(json.dumps(data, indent=2) + "\n")
            for service in stopped:
                compose_service("stop", service)
        except BaseException:
            cleanup(self.owner)
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        cleanup(self.owner)


def request_key(request: ToolRequest) -> str:
    return json.dumps(request.model_dump(), sort_keys=True, separators=(",", ":"))


def capture_corpus(incident: Incident, output: Path, *, source_access: bool = True) -> dict:
    tools = local_tools(incident)
    if not source_access:
        # Model access excludes local source/configuration for the ambiguous
        # case. All telemetry still comes from the actual configured backends.
        tools.source_root = None
    records, recorder = {}, ToolRecorder(output / "capture-audit.jsonl")

    def read(request):
        started = time.monotonic()
        try:
            kind, source, raw, summary = recorder.invoke(request.name, request.model_dump(),
                lambda: tools.execute(request), lambda r: {"kind": r[0], "source": r[1]})
            record = {"success": True, "kind": kind, "source": source, "raw": raw, "summary": summary}
        except (TelemetryError, ValueError, OSError) as exc:
            record = {"success": False, "error_type": type(exc).__name__,
                      "message": str(exc)[:500] if isinstance(exc, TelemetryError) else "Read unavailable"}
        record.update(request=request.model_dump(), capture_latency_ms=round((time.monotonic() - started) * 1000, 3))
        records[request_key(request)] = record
        return record

    inventory = read(ToolRequest(name="services", service=None, period=None))
    if not inventory["success"]:
        raise ValueError("Cannot capture a reproducible corpus without real service inventory")
    services = set(inventory["raw"]["services"]) | {incident.service}
    for name in ["runtime_configuration"]:
        read(ToolRequest(name=name, service=None, period=None))
    for period in ["baseline", "incident"]:
        for name in ["latency_ranking", "dependencies"]:
            read(ToolRequest(name=name, service=None, period=period))
        for service in sorted(services):
            for name in ["metrics", "logs", "traces"]:
                read(ToolRequest(name=name, service=service, period=period))
    for service in sorted(services):
        read(ToolRequest(name="source", service=service, period=None))
        read(ToolRequest(name="pods", service=service, period=None))
    corpus = {"schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(),
              "incident": incident.model_dump(), "records": records,
              "interpretation": "Frozen native reads from real telemetry; no scenario ground truth is provided to the model."}
    write_json(output / "corpus.json", corpus)
    return corpus


class CorpusTools:
    def __init__(self, path: Path, expected_sha256: str):
        body = path.read_bytes()
        if digest(body) != expected_sha256:
            raise ValueError("Captured telemetry changed after preparation")
        corpus = json.loads(body)
        self.records = corpus["records"]
        inventory = self.records[request_key(ToolRequest(name="services", service=None, period=None))]
        self.allowed_services = set(inventory["raw"]["services"]) | {corpus["incident"]["service"]}

    def validate(self, request):
        if request.service is not None and request.service not in self.allowed_services:
            raise ValueError("Service outside the observed inventory")

    def execute(self, request):
        self.validate(request)
        record = self.records.get(request_key(request))
        if record is None:
            raise ValueError("Request was not captured; no synthetic answer was supplied")
        if not record["success"]:
            raise TelemetryError(record["message"])
        # Replay latency is not the original backend latency. Both are retained.
        return record["kind"], record["source"], record["raw"], record["summary"]
