"""Developer-only local lab bootstrap. Never registered as an agent tool."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/kind"
VERSION = "v0.33.0"
NODE = "kindest/node:v1.34.11@sha256:44e222ee2132dab25ff87301682f89eb82c7880ea3a1bf543bfe9708fd08d67d"
CLUSTER = "sentinel-lab"


class LabError(RuntimeError):
    pass


def run(arguments: list[str], *, timeout=180) -> str:
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # kubectl failures can include credential material. Do not echo bodies.
        raise LabError(f"{Path(arguments[0]).name} failed with exit status {result.returncode}")
    return result.stdout


def binary() -> Path:
    system = {"Darwin": "darwin", "Linux": "linux"}.get(platform.system())
    architecture = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
    if not system or not architecture:
        raise LabError("This local lab supports macOS/Linux on ARM64 or AMD64")
    name = f"kind-{system}-{architecture}"
    url = f"https://github.com/kubernetes-sigs/kind/releases/download/{VERSION}/{name}"
    with urlopen(url + ".sha256sum", timeout=15) as response:
        checksum = response.read(1024).decode().split()[0]
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise LabError("Invalid official kind checksum")
    target = ROOT / ".cache/bin" / f"kind-{VERSION}-{system}-{architecture}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == checksum:
        return target
    fd, temporary = tempfile.mkstemp(dir=target.parent)
    try:
        digest, total = hashlib.sha256(), 0
        with os.fdopen(fd, "wb") as stream, urlopen(url, timeout=30) as response:
            while chunk := response.read(64_000):
                total += len(chunk)
                if total > 64_000_000:
                    raise LabError("kind binary exceeds its size limit")
                digest.update(chunk)
                stream.write(chunk)
        if digest.hexdigest() != checksum:
            raise LabError("kind binary checksum did not match the official release")
        os.chmod(temporary, 0o755)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(f"Verified kind {VERSION} download against SHA-256 {checksum}", flush=True)
    return target


def kubectl(*arguments) -> list[str]:
    return ["kubectl", "--kubeconfig", str(CACHE / "admin.conf"), *arguments]


def write_private(path: Path, body: str) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(body)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def credentials() -> None:
    config = json.loads(run(kubectl("config", "view", "--raw", "-o", "json")))
    current = config["current-context"]
    context = next(c["context"] for c in config["contexts"] if c["name"] == current)
    cluster = next(c["cluster"] for c in config["clusters"] if c["name"] == context["cluster"])
    ca = base64.b64decode(cluster["certificate-authority-data"], validate=True)
    write_private(CACHE / "ca.crt", ca.decode())
    token = run(kubectl("-n", "sentinel-fixture", "create", "token", "sentinel-reader", "--duration=1h")).strip()
    write_private(CACHE / "token", token)
    reader = {"server": cluster["server"], "namespace": "sentinel-fixture",
              "ca_file": str(CACHE / "ca.crt"), "token_file": str(CACHE / "token")}
    write_private(CACHE / "reader.json", json.dumps(reader))
    reader_kubeconfig = {"apiVersion": "v1", "kind": "Config", "current-context": "sentinel-reader",
        "clusters": [{"name": CLUSTER, "cluster": {"server": reader["server"], "certificate-authority": reader["ca_file"]}}],
        "users": [{"name": "sentinel-reader", "user": {"tokenFile": reader["token_file"]}}],
        "contexts": [{"name": "sentinel-reader", "context": {"cluster": CLUSTER, "user": "sentinel-reader", "namespace": reader["namespace"]}}]}
    write_private(CACHE / "reader.conf", json.dumps(reader_kubeconfig))
    print("Created a one-hour reader credential; no tokens were printed.", flush=True)


def verify_permissions() -> dict:
    checks = [("get", "pods", "sentinel-fixture", True), ("list", "events", "sentinel-fixture", True),
              ("patch", "pods", "sentinel-fixture", False), ("create", "pods", "sentinel-fixture", False),
              ("get", "secrets", "sentinel-fixture", False), ("list", "pods", "default", False)]
    results = []
    for verb, resource, namespace, expected in checks:
        command = ["kubectl", "--kubeconfig", str(CACHE / "reader.conf"), "-n", namespace, "auth", "can-i", verb, resource]
        response = subprocess.run(command, capture_output=True, text=True, timeout=15)
        answer = response.stdout.strip()
        if answer not in {"yes", "no"} or (answer == "yes") != expected or response.returncode not in {0, 1}:
            raise LabError(f"Unexpected RBAC result for {verb} {resource} in {namespace}")
        results.append({"verb": verb, "resource": resource, "namespace": namespace, "allowed": answer == "yes"})
    return {"cluster": CLUSTER, "identity": "system:serviceaccount:sentinel-fixture:sentinel-reader", "checks": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Isolated kind read-only integration fixture")
    parser.add_argument("command", choices=["up", "credentials", "verify", "down"])
    args = parser.parse_args(argv)
    CACHE.mkdir(parents=True, exist_ok=True, mode=0o700)
    CACHE.chmod(0o700)
    try:
        if args.command == "up":
            kind = str(binary())
            clusters = run([kind, "get", "clusters"]).splitlines()
            if CLUSTER not in clusters:
                print("Creating the isolated sentinel-lab cluster.", flush=True)
                run([kind, "create", "cluster", "--name", CLUSTER, "--image", NODE,
                     "--config", str(ROOT / "infra/kubernetes/kind.json"), "--kubeconfig", str(CACHE / "admin.conf"), "--wait", "120s"], timeout=600)
            else:
                run([kind, "export", "kubeconfig", "--name", CLUSTER, "--kubeconfig", str(CACHE / "admin.conf")])
            (CACHE / "admin.conf").chmod(0o600)
            print(run(kubectl("apply", "-f", str(ROOT / "infra/kubernetes/fixture.json"))), end="", flush=True)
            run(kubectl("-n", "sentinel-fixture", "wait", "--for=condition=Ready", "pod/fixture", "--timeout=60s"), timeout=75)
            credentials()
            print(json.dumps(verify_permissions(), indent=2))
        elif args.command == "credentials":
            credentials()
        elif args.command == "verify":
            print(json.dumps(verify_permissions(), indent=2))
        else:
            run([str(binary()), "delete", "cluster", "--name", CLUSTER])
            for name in ("admin.conf", "reader.conf", "reader.json", "token", "ca.crt"):
                (CACHE / name).unlink(missing_ok=True)
            print("Deleted only the sentinel-lab cluster and its local credentials.")
        return 0
    except (LabError, OSError, ValueError, KeyError, StopIteration, subprocess.TimeoutExpired) as exc:
        print(f"Kind lab: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
