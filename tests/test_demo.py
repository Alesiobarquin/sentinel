from copy import deepcopy
from contextlib import redirect_stdout
from io import BytesIO
from io import StringIO
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts import demo
from sentinel.tools.metrics import READINESS_QUERY
from sentinel.tools.metrics.prometheus import parse_result


def active_metrics(value="12"):
    return parse_result({"status": "success", "data": {"resultType": "vector", "result": [
        {"metric": {}, "value": [1, value]},
    ]}}, READINESS_QUERY)


def config():
    return {
        "name": "upstream",
        "services": {name: {"image": f"example/{name}:1.2.3", "container_name": name, "ports": ["8080"], "build": {"context": "."}} for name in (*demo.PORTS, "payment")},
        "networks": {"default": {"name": "upstream"}},
        "volumes": {"data": {"name": "upstream-data"}},
    }


class DemoTests(unittest.TestCase):
    def test_render_isolates_names_publishes_loopback_and_uses_prebuilt_images(self):
        original = config()
        untouched = deepcopy(original)
        result = demo.normalize_compose(original)
        self.assertEqual(original, untouched)
        self.assertEqual(result["name"], "sentinel-demo")
        self.assertEqual(result["networks"]["default"]["name"], "sentinel-demo-default")
        self.assertEqual(result["volumes"]["data"]["name"], "sentinel-demo-data")
        for name, service in result["services"].items():
            self.assertNotIn("build", service)
            self.assertNotIn("container_name", service)
            if name in demo.PORTS:
                self.assertEqual(service["ports"][0]["host_ip"], "127.0.0.1")
                self.assertEqual(service["ports"][0]["target"], demo.PORTS[name])
            else:
                self.assertNotIn("ports", service)

    def test_render_rejects_missing_backends_and_floating_images(self):
        for image in ["example/payment:latest", "example/payment", ""]:
            with self.subTest(image=image):
                value = config()
                value["services"]["payment"]["image"] = image
                with self.assertRaises(demo.DemoError):
                    demo.normalize_compose(value)
        value = config()
        del value["services"]["prometheus"]
        with self.assertRaises(demo.DemoError):
            demo.normalize_compose(value)

    def test_archive_is_fetched_by_commit_and_installed_atomically(self):
        lock = demo.load_lock()
        archive = BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as bundle:
            for filename in (*demo.LAYERS, ".env", "src/flagd/demo.flagd.json"):
                data = b"{}"
                info = tarfile.TarInfo(f"opentelemetry-demo-{lock['commit']}/{filename}")
                info.size = len(data)
                bundle.addfile(info, BytesIO(data))
        archive.seek(0)
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            source = cache / "source"
            with patch.object(demo, "CACHE", cache), patch.object(demo, "SOURCE", source), patch.object(demo, "urlopen", return_value=archive) as transport:
                demo.fetch_demo()
                demo.fetch_demo()
            marker = json.loads((source / ".sentinel-source.json").read_text())
            self.assertEqual(marker["commit"], lock["commit"])
            self.assertIn(lock["commit"], transport.call_args.args[0])
            self.assertEqual(len(marker["download_sha256"]), 64)
            self.assertTrue((source / ".env.override").exists())
            transport.assert_called_once()

    def test_wrong_cache_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            with patch.object(demo, "SOURCE", source), self.assertRaises(demo.DemoError):
                demo.fetch_demo()

    def test_backend_probe_rejects_a_healthy_server_without_trace_data(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(demo, "ROOT", Path(directory)), patch("sentinel.tools.metrics.PrometheusProvider") as metrics, patch("sentinel.tools.http.JsonHttpClient") as client:
                metrics.return_value.query_metrics.return_value = active_metrics()
                client.return_value.get.return_value = {"data": []}
                with self.assertRaisesRegex(demo.DemoError, "has not received traces"):
                    demo.verify()
                events = [json.loads(line) for line in (Path(directory) / "var/audit/tool-calls.jsonl").read_text().splitlines()]
        self.assertFalse(events[-1]["success"])

    def test_backend_probe_uses_the_demo_jaeger_route_and_reports_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            output = StringIO()
            with patch.object(demo, "ROOT", Path(directory)), patch("sentinel.tools.metrics.PrometheusProvider") as metrics, patch("sentinel.tools.http.JsonHttpClient") as client, redirect_stdout(output):
                metrics.return_value.query_metrics.return_value = active_metrics()
                client.return_value.get.side_effect = [{"data": ["payment"]}, {"status": "yellow"}]
                demo.verify()
                metrics.return_value.query_metrics.assert_called_once_with(READINESS_QUERY)
                self.assertEqual(client.call_args_list[0].args[0], "http://127.0.0.1:8080/jaeger/ui")
        self.assertIn("Log ingestion and fault diagnosis still need separate verification", output.getvalue())

    def test_backend_probe_rejects_zero_or_missing_telemetry_values(self):
        for value in ["0", "NaN"]:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                with patch.object(demo, "ROOT", Path(directory)), patch("sentinel.tools.metrics.PrometheusProvider") as metrics:
                    metrics.return_value.query_metrics.return_value = active_metrics(value)
                    with self.assertRaisesRegex(demo.DemoError, "no active telemetry"):
                        demo.verify()

    def test_fault_reset_restores_prior_variant_and_preserves_other_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            flags_path = source / "src/flagd/demo.flagd.json"
            flags_path.parent.mkdir(parents=True)
            flags_path.write_text(json.dumps({"flags": {
                "paymentFailure": {"defaultVariant": "50%", "state": "ENABLED", "variants": {"off": 0, "50%": 0.5, "100%": 1}},
                "other": {"defaultVariant": "off"},
            }}))
            state = source / "state.json"
            with patch.object(demo, "SOURCE", source), patch.object(demo, "STATE", state), patch.object(demo, "fetch_demo"):
                demo.inject_fault("payment-failure")
                flags = json.loads(flags_path.read_text())
                self.assertEqual(flags["flags"]["paymentFailure"]["defaultVariant"], "100%")
                flags["flags"]["other"]["defaultVariant"] = "on"
                flags_path.write_text(json.dumps(flags))
                with self.assertRaises(demo.DemoError):
                    demo.inject_fault("payment-failure")
                demo.reset_fault()
                restored = json.loads(flags_path.read_text())
                self.assertEqual(restored["flags"]["paymentFailure"]["defaultVariant"], "50%")
                self.assertEqual(restored["flags"]["other"]["defaultVariant"], "on")
                self.assertFalse(state.exists())
                demo.reset_fault()
