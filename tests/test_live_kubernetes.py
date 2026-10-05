import os
from pathlib import Path
import subprocess
import unittest

from sentinel.agent.local import kubernetes_provider


@unittest.skipUnless(os.getenv("SENTINEL_K8_LIVE_TESTS") == "1", "requires kind-up and SENTINEL_K8_LIVE_TESTS=1")
class LiveKubernetesTests(unittest.TestCase):
    def test_fixture_state_is_read_with_service_account_credentials(self):
        result = kubernetes_provider(Path(".cache/kind/reader.json")).pods("fixture")
        self.assertEqual(len(result["pods"]), 1)
        self.assertTrue(result["pods"][0]["ready"])
        self.assertEqual(result["namespace"], "sentinel-fixture")

    def test_reader_is_denied_writes_secrets_and_other_namespaces(self):
        for verb, resource, namespace in [("patch", "pods", "sentinel-fixture"),
                                          ("get", "secrets", "sentinel-fixture"),
                                          ("list", "pods", "default")]:
            response = subprocess.run(["kubectl", "--kubeconfig", ".cache/kind/reader.conf", "-n", namespace,
                                       "auth", "can-i", verb, resource], capture_output=True, text=True, timeout=15)
            self.assertEqual(response.returncode, 1)
            self.assertEqual(response.stdout.strip(), "no")
