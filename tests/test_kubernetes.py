from copy import deepcopy
import unittest
from unittest.mock import Mock

from sentinel.tools.http import TelemetryError
from sentinel.tools.kubernetes import KubernetesProvider


def pod():
    return {"metadata": {"name": "fixture", "namespace": "sentinel-fixture", "uid": "fixture-uid",
                         "labels": {"app.kubernetes.io/name": "fixture"}},
            "spec": {"containers": [{"env": [{"name": "SECRET", "value": "never-expose"}]}]},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "False"}],
                       "containerStatuses": [{"name": "fixture", "ready": False, "restartCount": 2,
                                              "state": {"waiting": {"reason": "CrashLoopBackOff"}},
                                              "lastState": {"terminated": {"reason": "OOMKilled"}}}]}}


class KubernetesTests(unittest.TestCase):
    def client(self, pods=None, events=None):
        client = Mock()
        client.get.side_effect = [{"kind": "PodList", "items": pods if pods is not None else [pod()], "metadata": {}},
                                  {"kind": "EventList", "items": events or [], "metadata": {}}]
        return client

    def test_namespaced_read_preserves_failures_and_omits_environment_secrets(self):
        event = {"involvedObject": {"namespace": "sentinel-fixture", "uid": "fixture-uid"},
                 "reason": "BackOff", "type": "Warning", "count": 4, "message": "Restart delayed"}
        client = self.client(events=[event])
        result = KubernetesProvider(client, "sentinel-fixture").pods("fixture")
        actual = result["pods"][0]
        self.assertFalse(actual["ready"])
        self.assertEqual(actual["containers"][0]["restart_count"], 2)
        self.assertEqual(actual["containers"][0]["last_termination_reason"], "OOMKilled")
        self.assertEqual(actual["events"][0]["reason"], "BackOff")
        self.assertNotIn("never-expose", str(result))
        client.get.assert_any_call("/api/v1/namespaces/sentinel-fixture/pods", {"labelSelector": "app.kubernetes.io/name=fixture", "limit": 15})
        client.get.assert_any_call("/api/v1/namespaces/sentinel-fixture/events", {"fieldSelector": "involvedObject.uid=fixture-uid", "limit": 10})

    def test_missing_status_is_unknown_and_empty_is_not_healthy(self):
        item = pod()
        item.pop("status")
        result = KubernetesProvider(self.client([item]), "sentinel-fixture").pods("fixture")
        self.assertIsNone(result["pods"][0]["ready"])
        self.assertEqual(result["pods"][0]["containers"], [])
        self.assertEqual(KubernetesProvider(self.client([]), "sentinel-fixture").pods("fixture")["pods"], [])

    def test_scope_and_malformed_status_are_rejected(self):
        for mutate in [lambda p: p["metadata"].update(namespace="default"),
                       lambda p: p["metadata"]["labels"].update({"app.kubernetes.io/name": "other"}),
                       lambda p: p["status"]["containerStatuses"][0].update(restartCount=-1)]:
            item = pod()
            mutate(item)
            with self.assertRaises(TelemetryError):
                KubernetesProvider(self.client([item]), "sentinel-fixture").pods("fixture")
        client = self.client()
        with self.assertRaises(ValueError):
            KubernetesProvider(client, "sentinel-fixture").pods("fixture,all=true")
        client.get.assert_not_called()

    def test_event_identity_and_list_pagination_are_explicit(self):
        bad = {"involvedObject": {"namespace": "default", "uid": "fixture-uid"}}
        with self.assertRaises(TelemetryError):
            KubernetesProvider(self.client(events=[bad]), "sentinel-fixture").pods("fixture")
        client = Mock()
        client.get.return_value = {"kind": "PodList", "items": [], "metadata": {"continue": "next"}}
        self.assertTrue(KubernetesProvider(client, "sentinel-fixture").pods("fixture")["limit_reached"])


if __name__ == "__main__":
    unittest.main()
