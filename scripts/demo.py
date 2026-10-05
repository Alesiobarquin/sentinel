"""Fetch and run the pinned official OpenTelemetry Demo using Compose."""

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from uuid import uuid4
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CACHE = ROOT / ".cache" / "demo"
SOURCE = CACHE / "source"
RUNTIME = CACHE / "compose.json"
PROJECT = "sentinel-demo"
LOCK = ROOT / "infra" / "docker" / "demo.lock.json"
LAYERS = ("compose.yaml", "compose.full.yaml", "compose.observability.yaml", "compose.extras.yaml")
PORTS = {"frontend-proxy": 8080, "prometheus": 9090, "jaeger": 16686, "opensearch": 9200, "otel-collector": 4318}
STATE = CACHE / "fault-state.json"


class DemoError(RuntimeError):
    pass


def load_lock() -> dict:
    lock = json.loads(LOCK.read_text())
    if not re.fullmatch(r"[0-9a-f]{40}", lock["commit"]):
        raise DemoError("Demo lock needs a full commit SHA")
    if not re.fullmatch(r"\d+\.\d+\.\d+", lock["version"]):
        raise DemoError("Demo lock needs a release version")
    return lock


def run(command: list[str], *, cwd: Path = ROOT, env: dict | None = None, stream: bool = False) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=not stream, text=True)
    if result.returncode:
        # Avoid printing resolved Compose configuration or environment variables.
        detail = (result.stderr or "").strip()[-1500:]
        raise DemoError(f"{' '.join(command[:3])} failed: {detail or 'see the command output manually'}")
    return result.stdout or ""


def doctor() -> None:
    if sys.version_info < (3, 12):
        raise DemoError("Python 3.12 or newer is required")
    if not shutil.which("docker"):
        raise DemoError("Docker is missing; install and start Docker Desktop")
    version = run(["docker", "compose", "version", "--short"]).strip()
    if not re.match(r"v?2\.", version):
        raise DemoError(f"Docker Compose v2 is required (found {version})")
    try:
        server = run(["docker", "version", "--format", "{{.Server.Version}}"])
    except DemoError as exc:
        if "permission denied" in str(exc).lower() or "operation not permitted" in str(exc).lower():
            raise DemoError("This session is denied access to Docker's socket. Allow local Docker access or run make doctor in your Mac Terminal") from exc
        raise DemoError("Docker daemon unreachable (stopped or access restricted). Check Docker Desktop and session permissions, then run make doctor") from exc
    print(f"Python {sys.version.split()[0]}; Compose {version}; Docker server {server.strip()}")


def fetch_demo() -> Path:
    lock = load_lock()
    if SOURCE.exists():
        marker = SOURCE / ".sentinel-source.json"
        if not marker.is_file() or json.loads(marker.read_text()).get("commit") != lock["commit"]:
            raise DemoError("Cached demo does not match the lock. Move .cache/demo aside before fetching again")
        for name in (*LAYERS, ".env", "src/flagd/demo.flagd.json"):
            if not (SOURCE / name).is_file():
                raise DemoError(f"Cached demo is incomplete: missing {name}")
        print(f"Using OpenTelemetry Demo {lock['version']} ({lock['commit'][:12]})")
        return SOURCE
    CACHE.mkdir(parents=True, exist_ok=True)
    url = f"https://codeload.github.com/open-telemetry/opentelemetry-demo/tar.gz/{lock['commit']}"
    print(f"Fetching official OpenTelemetry Demo {lock['version']} ({lock['commit'][:12]})", flush=True)
    with tempfile.TemporaryDirectory(prefix="fetch-", dir=CACHE) as temporary:
        archive = Path(temporary) / "demo.tar.gz"
        digest = hashlib.sha256()
        size = 0
        try:
            with urlopen(url, timeout=30) as response, archive.open("wb") as stream:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > 250_000_000:
                        raise DemoError("Upstream archive exceeds the 250 MB download limit")
                    digest.update(chunk)
                    stream.write(chunk)
        except (URLError, TimeoutError, OSError) as exc:
            raise DemoError("Cannot download the pinned demo. Check shell access to codeload.github.com") from exc
        expected_root = f"opentelemetry-demo-{lock['commit']}"
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            if any(Path(item.name).parts[0] != expected_root for item in members):
                raise DemoError("Unexpected archive root")
            if sum(item.size for item in members) > 1_000_000_000:
                raise DemoError("Unpacked archive exceeds the 1 GB limit")
            # Python's data filter rejects traversal, unsafe links, and device files.
            bundle.extractall(Path(temporary) / "extracted", filter="data")
        extracted = Path(temporary) / "extracted" / expected_root
        for name in (*LAYERS, ".env", "src/flagd/demo.flagd.json"):
            if not (extracted / name).is_file():
                raise DemoError(f"Pinned release is missing required file {name}")
        (extracted / ".sentinel-source.json").write_text(json.dumps({
            "version": lock["version"], "commit": lock["commit"],
            "archive_url": url, "download_sha256": digest.hexdigest(),
        }, indent=2) + "\n")
        # Hash records this download; it is not an independently verified checksum.
        (extracted / ".env.override").touch()
        extracted.rename(SOURCE)
    return SOURCE


def normalize_compose(config: dict) -> dict:
    """Isolate the lab and publish store, telemetry reads, and Sentinel OTLP ingestion on loopback."""
    config = deepcopy(config)
    config["name"] = PROJECT
    services = config.get("services", {})
    for name in PORTS:
        if name not in services:
            raise DemoError(f"Upstream Compose configuration is missing {name}")
    for name, service in services.items():
        service.pop("container_name", None)
        service.pop("ports", None)
        # This is a prebuilt-image workflow, never a compilation of upstream code.
        service.pop("build", None)
        image = service.get("image", "")
        if not image or image.endswith(":latest") or (":" not in image.rsplit("/", 1)[-1] and "@sha256:" not in image):
            raise DemoError(f"Service {name} has an unpinned image")
        if name in PORTS:
            port = PORTS[name]
            service["ports"] = [{"target": port, "published": str(port), "host_ip": "127.0.0.1", "protocol": "tcp"}]
    for name, network in config.get("networks", {}).items():
        if not network.get("external"):
            network["name"] = f"{PROJECT}-{name}"
    for name, volume in config.get("volumes", {}).items():
        if not volume.get("external"):
            volume["name"] = f"{PROJECT}-{name}"
    return config


def render_compose() -> Path:
    source = fetch_demo()
    version = load_lock()["version"]
    env = os.environ.copy()
    # Shell variables override env-files in Compose, so enforce the release here.
    env.update(DEMO_VERSION=version, IMAGE_VERSION=version, ENVOY_PORT="8080", PROMETHEUS_PORT="9090", JAEGER_UI_PORT="16686")
    command = ["docker", "compose", "--project-name", PROJECT, "--env-file", ".env", "--env-file", ".env.override"]
    for layer in LAYERS:
        command.extend(["-f", layer])
    resolved = json.loads(run(command + ["config", "--format", "json"], cwd=source, env=env))
    # Compose resolves all source mounts relative to the upstream project first.
    config = normalize_compose(resolved)
    RUNTIME.write_text(json.dumps(config, indent=2) + "\n")
    run(compose_command() + ["config", "--quiet"])
    print(f"Rendered pinned Compose configuration: {RUNTIME.relative_to(ROOT)}")
    return RUNTIME


def compose_command() -> list[str]:
    return ["docker", "compose", "--project-name", PROJECT, "--project-directory", str(SOURCE), "-f", str(RUNTIME)]


def verify() -> None:
    # scripts/demo.py runs as a standalone script: import the repository package.
    sys.path.insert(0, str(ROOT))
    from sentinel.tools.http import JsonHttpClient, TelemetryError
    from sentinel.tools.metrics import PrometheusProvider, READINESS_QUERY
    from sentinel.tools.audit import ToolRecorder

    recorder = ToolRecorder(ROOT / "var/audit/tool-calls.jsonl")
    def probes() -> dict:
        metrics = PrometheusProvider().query_metrics(READINESS_QUERY)
        if len(metrics.series) != 1 or len(metrics.series[0].samples) != 1:
            raise DemoError("Prometheus responds but has no active telemetry series yet")
        active_series = metrics.series[0].samples[0].value
        if active_series is None or active_series <= 0:
            raise DemoError("Prometheus responds but has no active telemetry series yet")
        # Use the published UI route so the demo's Jaeger base path is respected.
        traces = JsonHttpClient("http://127.0.0.1:8080/jaeger/ui").get("/api/services")
        if not isinstance(traces.get("data"), list) or not traces["data"]:
            raise DemoError("Jaeger responds but has not received traces yet")
        search = JsonHttpClient("http://127.0.0.1:9200").get("/_cluster/health")
        if search.get("status") not in {"green", "yellow"}:
            raise DemoError("OpenSearch is not healthy")
        return {"prometheus_active_series": int(active_series), "jaeger_services": traces["data"], "opensearch_status": search["status"]}
    try:
        result = recorder.invoke("demo_telemetry_verify", {}, probes, lambda r: r)
    except TelemetryError as exc:
        raise DemoError(f"Telemetry is not ready: {exc}. Check make demo-status and retry make demo-verify after warmup") from exc
    print(json.dumps(result, indent=2))
    print("Backend smoke checks passed. Log ingestion and fault diagnosis still need separate verification.")


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def inject_fault(scenario: str, *, owner_id: str | None = None) -> None:
    from scripts.lab_scenarios import SCENARIOS
    if scenario not in SCENARIOS:
        raise DemoError("Unknown pinned local lab scenario")
    fault = SCENARIOS[scenario]
    if STATE.exists():
        raise DemoError("A lab fault is already tracked; run make lab-reset first")
    fetch_demo()
    flags_path = SOURCE / "src/flagd/demo.flagd.json"
    flags = json.loads(flags_path.read_text())
    flag = flags["flags"][fault.flag]
    actual_value = flag.get("variants", {}).get(fault.variant)
    if flag.get("state") != "ENABLED" or type(actual_value) is not type(fault.value) or actual_value != fault.value:
        raise DemoError("Pinned feature flag does not match the expected scenario")
    # Persist the old value before modifying the watched file, allowing recovery.
    state = {"scenario": scenario, "flag": fault.flag, "previous_variant": flag["defaultVariant"],
             "owner_id": owner_id or str(uuid4())}
    try:
        with STATE.open("x") as stream:
            json.dump(state, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise DemoError("A lab fault is already tracked; run make lab-reset first") from exc
    flag["defaultVariant"] = fault.variant
    # Preserve the inode: flagd/flagd-ui watch this mounted configuration file.
    flags_path.write_text(json.dumps(flags, indent=2) + "\n")
    print(f"Enabled {fault.flag}={fault.variant}. Keep traffic running; collect evidence, then run make lab-reset.")


def reset_fault(*, owner_id: str | None = None) -> None:
    if not STATE.exists():
        if owner_id is None:
            print("No Sentinel lab fault to reset")
        return
    state = json.loads(STATE.read_text())
    if owner_id is not None and state.get("owner_id") != owner_id:
        return  # Preserve another exercise's fault; manual reset remains explicit.
    flags_path = SOURCE / "src/flagd/demo.flagd.json"
    flags = json.loads(flags_path.read_text())
    flags["flags"][state["flag"]]["defaultVariant"] = state["previous_variant"]
    flags_path.write_text(json.dumps(flags, indent=2) + "\n")
    STATE.unlink()
    print(f"Restored the previous {state['flag']} variant; other feature flags are unchanged")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pinned OpenTelemetry Demo lab (local development only)")
    parser.add_argument("command", choices=("doctor", "fetch", "config", "up", "down", "status", "verify", "inject", "reset"))
    parser.add_argument("--scenario", default="payment-failure")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            doctor()
        elif args.command == "fetch":
            fetch_demo()
        elif args.command == "config":
            render_compose()
        elif args.command == "up":
            doctor()
            render_compose()
            run(compose_command() + ["up", "--detach", "--no-build", "--wait", "--wait-timeout", "180"], stream=True)
            print("Demo started. Allow traffic to warm up, then run make demo-verify.")
            print("Web store: http://127.0.0.1:8080; feature flags: http://127.0.0.1:8080/feature")
        elif args.command in {"down", "status"}:
            if not RUNTIME.is_file():
                raise DemoError("No rendered demo configuration; run make demo-up first")
            options = ["down", "--remove-orphans"] if args.command == "down" else ["ps", "--all"]
            print(run(compose_command() + options))
        elif args.command == "verify":
            verify()
        elif args.command == "inject":
            inject_fault(args.scenario)
        elif args.command == "reset":
            reset_fault()
    except (DemoError, OSError, ValueError, KeyError, tarfile.TarError) as exc:
        print(f"Demo: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
