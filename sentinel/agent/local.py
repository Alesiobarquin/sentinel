"""Explicit local wiring. Runtime, provider, and telemetry remain independent."""

import json
import os
from pathlib import Path

from sentinel.agent.contracts import Incident
from sentinel.agent.diagnostics import DiagnosticTools
from sentinel.tools.kubernetes import KubernetesClient, KubernetesProvider
from sentinel.tools.logs import LogSchema, OpenSearchProvider
from sentinel.tools.metrics import PrometheusProvider
from sentinel.tools.traces import JaegerProvider

ROOT = Path(__file__).resolve().parents[2]


def json_file(path: Path, limit=64_000) -> dict:
    with path.open() as stream:
        raw = stream.read(limit + 1)
    payload = json.loads(raw)
    if len(raw.encode()) > limit or not isinstance(payload, dict):
        raise ValueError("Configuration must be a bounded JSON object")
    return payload


def kubernetes_provider(path: Path) -> KubernetesProvider:
    settings = json_file(path)
    if set(settings) != {"server", "namespace", "ca_file", "token_file"}:
        raise ValueError("Kubernetes configuration needs server, namespace, ca_file, and token_file only")
    client = KubernetesClient(settings["server"], Path(settings["token_file"]), Path(settings["ca_file"]))
    return KubernetesProvider(client, settings["namespace"])


def local_tools(incident: Incident) -> DiagnosticTools:
    schema_path = Path(os.getenv("SENTINEL_LOG_SCHEMA", str(ROOT / "infra/docker/log-schema.json")))
    schema = LogSchema(**json_file(schema_path))
    source_root = ROOT / ".cache/demo/source"
    commit, source_files = None, {}
    if source_root.exists():
        lock = json_file(ROOT / "infra/docker/demo.lock.json")
        provenance = json_file(source_root / ".sentinel-source.json")
        if provenance.get("commit") != lock["commit"]:
            raise ValueError("Local source context does not match the pinned Demo commit")
        commit, source_files = lock["commit"], json_file(ROOT / "infra/docker/source-context.json")
    else:
        source_root = None
    kube_path = os.getenv("SENTINEL_KUBERNETES_CONFIG")
    kube = kubernetes_provider(Path(kube_path)) if kube_path else None
    return DiagnosticTools(
        incident, metrics=PrometheusProvider(os.getenv("SENTINEL_PROMETHEUS_URL", "http://127.0.0.1:9090")),
        traces=JaegerProvider(os.getenv("SENTINEL_JAEGER_URL", "http://127.0.0.1:8080/jaeger/ui")),
        logs=OpenSearchProvider(os.getenv("SENTINEL_OPENSEARCH_URL", "http://127.0.0.1:9200")),
        log_schema=schema, log_index=os.getenv("SENTINEL_LOG_INDEX", "otel-logs*"),
        source_root=source_root, source_files=source_files, source_commit=commit, kubernetes=kube,
    )
