"""Namespaced GET-only Kubernetes adapter. No kubeconfig admin identity is used."""

from datetime import datetime, timezone
from pathlib import Path
import re
import ssl
from urllib.parse import urlsplit

import httpx

from sentinel.tools.http import TelemetryError


def dns_name(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", value):
        raise ValueError("Kubernetes namespace and service must be DNS labels")


class KubernetesClient:
    def __init__(self, server: str, token_file: Path, ca_file: Path):
        parsed = urlsplit(server)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise ValueError("Kubernetes server must be a credential-free HTTPS origin")
        if token_file.is_symlink() or token_file.stat().st_mode & 0o077:
            raise ValueError("Kubernetes token must be in an owner-only regular file")
        token = token_file.read_text().strip()
        if not token or len(token) > 30_000 or any(c.isspace() for c in token):
            raise ValueError("Invalid Kubernetes bearer token file")
        self.server, self.token = server.rstrip("/"), token
        self.tls = ssl.create_default_context(cafile=str(ca_file))

    def get(self, path: str, parameters: dict) -> dict:
        if not re.fullmatch(r"/api/v1/namespaces/[a-z0-9-]+/(pods|events)", path):
            raise ValueError("Kubernetes transport allows only namespaced pod/event reads")
        try:
            with httpx.Client(verify=self.tls, timeout=10, follow_redirects=False) as client:
                with client.stream("GET", self.server + path, params=parameters,
                                   headers={"Authorization": "Bearer " + self.token}) as response:
                    if response.status_code != 200:
                        raise TelemetryError(f"Kubernetes read returned HTTP {response.status_code}")
                    raw, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > 2_000_000:
                            raise TelemetryError("Kubernetes response exceeded its size limit")
                        raw.append(chunk)
            import json
            payload = json.loads(b"".join(raw))
            if not isinstance(payload, dict):
                raise ValueError()
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            raise TelemetryError("Kubernetes read unavailable or malformed; health is unknown") from exc


def _text(value, maximum: int = 500) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Expected a string")
    return value[:maximum]


def _list(payload: dict, kind: str) -> tuple[list, bool]:
    if payload.get("kind") != kind or not isinstance(payload.get("items"), list):
        raise TelemetryError("Kubernetes returned an unexpected resource list")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise TelemetryError("Kubernetes list metadata is malformed")
    return payload["items"], bool(metadata.get("continue"))


class KubernetesProvider:
    def __init__(self, client: KubernetesClient, namespace: str):
        dns_name(namespace)
        self.client, self.namespace = client, namespace

    def pods(self, service: str) -> dict:
        dns_name(service)
        items, more = _list(self.client.get(f"/api/v1/namespaces/{self.namespace}/pods", {
            "labelSelector": "app.kubernetes.io/name=" + service, "limit": 15,
        }), "PodList")
        if len(items) > 15:
            raise TelemetryError("Kubernetes returned more pods than the requested limit")
        summaries, event_reads = [], 0
        try:
            for item in items:
                metadata, status = item["metadata"], item.get("status", {})
                if (metadata["namespace"] != self.namespace or
                        metadata.get("labels", {}).get("app.kubernetes.io/name") != service):
                    raise ValueError("Mismatched pod identity")
                name, uid = metadata["name"], metadata["uid"]
                if not isinstance(name, str) or len(name) > 253:
                    raise ValueError("Invalid pod name")
                for label in name.split("."):
                    dns_name(label)
                if not isinstance(uid, str) or not re.fullmatch(r"[a-zA-Z0-9-]{1,128}", uid):
                    raise ValueError("Invalid pod UID")
                conditions = status.get("conditions", [])
                ready_values = [c["status"] for c in conditions if c.get("type") == "Ready"]
                if any(value not in {"True", "False", "Unknown"} for value in ready_values) or len(ready_values) > 1:
                    raise ValueError("Invalid readiness")
                ready = {"True": True, "False": False, "Unknown": None}.get(ready_values[0]) if ready_values else None
                containers = []
                for container in [*status.get("initContainerStatuses", []), *status.get("containerStatuses", [])]:
                    count = container["restartCount"]
                    if type(count) is not int or count < 0 or type(container["ready"]) is not bool:
                        raise ValueError("Invalid restart/readiness status")
                    state = container.get("state", {})
                    states = [key for key in ("running", "waiting", "terminated") if key in state]
                    if len(states) > 1:
                        raise ValueError("Conflicting container state")
                    current = state.get(states[0], {}) if states else {}
                    containers.append({"name": _text(container["name"]), "ready": container["ready"],
                                       "restart_count": count, "state": states[0] if states else "unknown",
                                       "reason": _text(current.get("reason")), "message": _text(current.get("message")),
                                       "exit_code": current.get("exitCode"),
                                       "last_termination_reason": _text(container.get("lastState", {}).get("terminated", {}).get("reason"))})
                pod = {"name": name, "uid": uid, "phase": _text(status.get("phase")), "ready": ready,
                       "containers": containers, "events": [], "events_queried": False, "events_limit_reached": False}
                if event_reads < 5:
                    events, partial = self.events(uid)
                    event_reads += 1
                    pod.update(events=events, events_queried=True, events_limit_reached=partial)
                summaries.append(pod)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise TelemetryError("Kubernetes pod status is malformed or outside the configured scope") from exc
        return {"source": "kubernetes", "namespace": self.namespace, "service": service,
                "observed_at": datetime.now(timezone.utc).isoformat(), "pods": summaries, "limit_reached": more,
                "limitation": "Current state only. Missing pod/container status is unknown; events are sampled for at most five pods."}

    def events(self, uid: str) -> tuple[list, bool]:
        if not isinstance(uid, str) or not re.fullmatch(r"[a-zA-Z0-9-]{1,128}", uid):
            raise ValueError("Invalid Kubernetes object UID")
        items, more = _list(self.client.get(f"/api/v1/namespaces/{self.namespace}/events", {
            "fieldSelector": "involvedObject.uid=" + uid, "limit": 10,
        }), "EventList")
        if len(items) > 10:
            raise TelemetryError("Kubernetes returned more events than the requested limit")
        summaries = []
        try:
            for item in items:
                obj = item["involvedObject"]
                if obj.get("namespace") != self.namespace or obj["uid"] != uid:
                    raise ValueError("Mismatched event identity")
                count = item.get("count")
                if count is not None and (type(count) is not int or count < 0):
                    raise ValueError("Invalid event count")
                summaries.append({"reason": _text(item.get("reason")), "message": _text(item.get("message")),
                                  "type": _text(item.get("type")), "count": count,
                                  "last_seen": _text(item.get("lastTimestamp") or item.get("eventTime"))})
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise TelemetryError("Kubernetes event payload is malformed or mismatched") from exc
        return summaries, more
