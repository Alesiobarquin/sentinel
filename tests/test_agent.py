from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from sentinel.agent.context import build_context, encoded_size
from sentinel.agent.contracts import Budget, Evidence, Incident, InvestigationStep, ToolRequest, Usage
from sentinel.agent.provider import ModelError, ModelReply
from sentinel.agent.runner import InvestigationRunner
from sentinel.tools.http import TelemetryError


def hypothesis():
    return {"name": "Test hypothesis", "explanation": "Synthetic fixture only", "confidence": 0.5,
            "supporting_evidence": [], "contradicting_evidence": [], "status": "active"}


def read(name, service="payment", period="incident"):
    return {"action": "read", "reason": "Gather evidence", "hypotheses": [hypothesis()],
            "tool": {"name": name, "service": service, "period": period}, "diagnosis": None}


def diagnosis(ids=None):
    return {"action": "diagnose", "reason": "Synthetic fixture conclusion", "hypotheses": [hypothesis()], "tool": None,
            "diagnosis": {"root_cause": "Synthetic test cause", "confidence": 0.7, "evidence_ids": ids or ["ev_002", "ev_003"],
                          "affected_services": ["payment"], "recommended_remediation": "Request configuration review",
                          "remediation_kind": "request_config_revert", "limitations": ["Synthetic fixture; not an AI evaluation."]}}


class FixtureProvider:
    model = "fixture-model"
    billing_mode = "chatgpt"

    def __init__(self, decisions):
        self.decisions, self.contexts = list(decisions), []

    def step(self, instructions, context, budget, *, timeout):
        self.contexts.append(context)
        item = self.decisions.pop(0)
        if isinstance(item, Exception):
            raise item
        return ModelReply(item, Usage(input_tokens=100, output_tokens=50), "fixture-response", self.model, 1)


class FixtureTools:
    def __init__(self, failed=None):
        self.requests, self.failed = [], failed

    def validate(self, request):
        if request.service not in {None, "payment"}:
            raise ValueError("Out-of-scope service")

    def execute(self, request):
        self.requests.append(request)
        if request.name == self.failed:
            raise TelemetryError("Unavailable")
        kind = {"services": "inventory", "logs": "log", "traces": "trace", "metrics": "metric"}[request.name]
        return kind, "fixture", {"fixture": True}, {"sample_complete": False, "fixture": True}


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.incident = Incident(service="payment", symptom="Errors observed", start=1000.0, end=1300.0)

    def run_fixture(self, decisions, *, budget=None, failed=None):
        provider, tools = FixtureProvider(decisions), FixtureTools(failed)
        with tempfile.TemporaryDirectory() as directory:
            runner = InvestigationRunner(provider, tools, output_root=Path(directory), budget=budget)
            result = runner.run(self.incident)
            artifacts = {p.name: p.read_text() for p in runner.directory.iterdir()}
        return result, artifacts, provider, tools

    def test_loop_persists_evidence_usage_hypotheses_and_spans(self):
        result, artifacts, provider, tools = self.run_fixture([read("logs"), read("traces"), diagnosis()])
        self.assertEqual(result.status, "diagnosed")
        self.assertEqual((result.model_calls, result.tool_calls), (3, 3))
        self.assertEqual((result.input_tokens, result.output_tokens), (300, 150))
        self.assertIsNone(result.approximate_api_cost_usd)
        self.assertFalse(result.usage_unknown)
        self.assertTrue(result.diagnosis["requires_human_approval"])
        self.assertFalse(result.diagnosis["remediation_executed"])
        self.assertIn("ev_003.json", artifacts)
        self.assertIn("decision-03.json", artifacts)
        tool_events = [json.loads(line) for line in artifacts["tools.jsonl"].splitlines()]
        self.assertEqual(len(tool_events), 6)
        self.assertTrue(all(e["arguments"]["run_id"] == result.run_id for e in tool_events if "arguments" in e))
        spans = [json.loads(line) for line in artifacts["spans.jsonl"].splitlines()]
        names = {s["name"] for s in spans}
        self.assertTrue({"sentinel.investigation", "sentinel.tool", "sentinel.model", "sentinel.context"} <= names)
        self.assertEqual(len({s["context"]["trace_id"] for s in spans}), 1)
        self.assertEqual(len(provider.contexts[-1]["evidence_index"]), 3)

    def test_completed_provider_failure_retains_response_outside_model_context(self):
        failure = ModelError("Fixture transport failure", usage=Usage(input_tokens=100, output_tokens=50),
                             response_id="fixture-response", response={"terminal": {"output": []}})
        result, artifacts, provider, _ = self.run_fixture([failure])
        self.assertEqual(result.status, "failed")
        self.assertFalse(result.usage_unknown)
        self.assertEqual(json.loads(artifacts["response-01.json"]), {"terminal": {"output": []}})
        self.assertNotIn("terminal", provider.contexts[0])

    def test_model_schema_exposes_tool_scope_and_period_constraints(self):
        schema = InvestigationStep.model_json_schema()["$defs"]["ToolRequest"]
        families = {name: branch for branch in schema["anyOf"]
                    for name in branch["properties"]["name"]["enum"]}
        self.assertEqual(set(families), {"services", "runtime_configuration", "latency_ranking",
                                         "dependencies", "metrics", "logs", "traces", "source", "pods"})
        global_config = families["runtime_configuration"]["properties"]
        self.assertEqual(global_config["service"], {"type": "null"})
        self.assertEqual(global_config["period"], {"type": "null"})
        self.assertEqual(families["metrics"]["properties"]["service"], {"type": "string"})
        self.assertEqual(families["source"]["properties"]["period"], {"type": "null"})
        with self.assertRaises(ValidationError):
            ToolRequest(name="runtime_configuration", service="payment", period=None)
        self.assertIsNone(ToolRequest(name="runtime_configuration", service=None, period=None).service)

    def test_unknown_or_failed_citations_cannot_be_diagnosed(self):
        for ids, failed in [(["ev_999", "ev_003"], None), (["ev_002", "ev_003"], "logs")]:
            with self.subTest(ids=ids, failed=failed):
                result, artifacts, _, _ = self.run_fixture([read("logs"), read("traces"), diagnosis(ids)], failed=failed)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.diagnosis)
                self.assertIn("DecisionError", result.reason)
                if failed:
                    self.assertIn("tool_failure", artifacts["events.jsonl"])
                    self.assertIn('"success": false', artifacts["tools.jsonl"])

    def test_one_kind_or_inventory_only_is_insufficient_for_diagnosis(self):
        for requests, ids in [([read("logs"), read("logs", period="baseline")], ["ev_002", "ev_003"]),
                              ([read("logs")], ["ev_001", "ev_001"])]:
            result, _, _, _ = self.run_fixture([*requests, diagnosis(ids)])
            self.assertEqual(result.status, "failed")

    def test_model_cannot_expose_shell_writes_or_extra_arguments(self):
        for mutation in [read("shell"), {**read("logs"), "command": "delete everything"}, read("logs", service="unknown")]:
            result, _, _, tools = self.run_fixture([mutation])
            self.assertEqual(result.status, "failed")
            self.assertEqual(len(tools.requests), 1)  # Inventory only; requested action never executed.

    def test_duplicate_read_is_stopped_without_retry(self):
        result, _, _, tools = self.run_fixture([read("logs"), read("logs")])
        self.assertEqual(result.status, "failed")
        self.assertEqual(len(tools.requests), 2)

    def test_call_and_reported_token_limits_stop_execution(self):
        for budget, expected_reads in [(Budget(max_model_calls=1), 2), (Budget(max_tool_calls=1), 1),
                                       (Budget(max_total_tokens=1000), 7)]:
            decisions = [read("logs", period="incident"), read("logs", period="baseline"), read("traces"),
                         read("traces", period="baseline"), read("metrics"), read("metrics", period="baseline")]
            # The first two budgets stop before a third response. The token
            # limit gets a measured large response rather than repeating tools.
            provider = FixtureProvider(decisions)
            if budget.max_total_tokens == 1000:
                def large_reply(*args, **kwargs):
                    return ModelReply(read("logs"), Usage(input_tokens=900, output_tokens=200), "large", "fixture", 1)
                provider.step = large_reply
                expected_reads = 1
            with tempfile.TemporaryDirectory() as directory:
                tools = FixtureTools()
                result = InvestigationRunner(provider, tools, output_root=Path(directory), budget=budget).run(self.incident)
            self.assertEqual(result.status, "budget_exhausted")
            self.assertEqual(len(tools.requests), expected_reads)

    def test_model_failure_has_unknown_usage_and_no_retries(self):
        result, artifacts, provider, _ = self.run_fixture([ModelError("Stream interrupted")])
        self.assertEqual(result.status, "failed")
        self.assertTrue(result.usage_unknown)
        self.assertEqual(result.model_calls, 1)
        self.assertIn('"usage_unknown": true', artifacts["events.jsonl"])

    def test_failed_request_records_latency_and_safe_quota_metadata_without_retry(self):
        failure = ModelError("Safe failure", provider_error_type="RateLimitError", http_status=429,
                             provider_error_code="subscription_sharing_usage_limit_exceeded",
                             failure_category="subscription_usage_limit")
        result, artifacts, provider, _ = self.run_fixture([failure])
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.model_calls, 1)
        self.assertEqual(len(provider.contexts), 1)
        self.assertTrue(result.usage_unknown)
        self.assertIsNone(result.approximate_api_cost_usd)
        self.assertIn("usage limit reached", result.reason)
        events = [json.loads(line) for line in artifacts["events.jsonl"].splitlines()]
        finished = next(e for e in events if e["event"] == "model_finished")
        self.assertGreaterEqual(finished["latency_ms"], 0)
        self.assertEqual(finished["http_status"], 429)
        self.assertEqual(finished["failure_category"], "subscription_usage_limit")
        self.assertIsNone(finished["usage"])

    def test_invalid_completed_model_output_retains_measured_usage(self):
        failure = ModelError("Invalid completed output", usage=Usage(input_tokens=100, output_tokens=50), response_id="completed-invalid")
        result, artifacts, _, _ = self.run_fixture([failure])
        self.assertEqual(result.status, "failed")
        self.assertEqual((result.input_tokens, result.output_tokens), (100, 50))
        self.assertFalse(result.usage_unknown)
        self.assertIn("completed-invalid", artifacts["events.jsonl"])

    def test_insufficient_evidence_is_an_explicit_terminal_result(self):
        decision = {"action": "insufficient_evidence", "reason": "Cannot distinguish causes", "hypotheses": [hypothesis()],
                    "tool": None, "diagnosis": None}
        result, _, _, _ = self.run_fixture([decision])
        self.assertEqual(result.status, "insufficient_evidence")
        self.assertIsNone(result.diagnosis)

    def test_context_bound_preserves_index_and_discloses_omissions(self):
        evidence = [Evidence(id=f"ev_{i}", run_id="run", kind="log", source="fixture", observed_at=float(i),
                             tool=ToolRequest(name="logs", service="payment", period="incident"), success=True,
                             summary={"body": "x" * 5000, "sample_complete": False}, payload_file=f"ev_{i}.json") for i in range(3)]
        context = build_context(self.incident, evidence, [], max_bytes=4000, remaining={})
        self.assertLessEqual(encoded_size(context), 4000)
        self.assertEqual(len(context["evidence_index"]), 3)
        self.assertEqual(len(context["omitted_evidence_ids"]), 3)
        self.assertEqual(context["selected_evidence"], [])

    def test_closed_contract_rejects_inconsistent_action_and_window(self):
        for values in ({"start": float("nan")}, {"end": 1000.0}, {"service": 'payment"} shell'}):
            with self.assertRaises(ValidationError):
                Incident.model_validate({**self.incident.model_dump(), **values})
        with self.assertRaises(ValidationError):
            InvestigationStep.model_validate({**read("logs"), "action": "diagnose"})

    def test_explicit_baseline_avoids_contamination_from_fault_settling_time(self):
        incident = Incident(service="payment", symptom="Errors", start=1500.0, end=1800.0,
                            baseline_start=900.0, baseline_end=1200.0)
        self.assertEqual(incident.window("baseline").end, 1200.0)
        context = build_context(incident, [], [], max_bytes=4000, remaining={})
        self.assertEqual(context["baseline"], {"start": 900.0, "end": 1200.0})
        for changes in ({"baseline_end": None}, {"baseline_end": 1700.0}):
            with self.assertRaises(ValidationError):
                Incident.model_validate({**incident.model_dump(), **changes})

    def test_api_reservation_stops_before_any_billable_model_request(self):
        provider = FixtureProvider([read("logs")])
        provider.model, provider.billing_mode = "gpt-6-luna", "api"
        with tempfile.TemporaryDirectory() as directory:
            result = InvestigationRunner(provider, FixtureTools(), output_root=Path(directory),
                                         budget=Budget(max_api_cost_usd=0.000001)).run(self.incident)
        self.assertEqual(result.status, "budget_exhausted")
        self.assertEqual(result.model_calls, 0)
        self.assertEqual(provider.contexts, [])
        self.assertEqual(result.approximate_api_cost_usd, 0)

    def test_wall_budget_is_enforced_after_a_completed_response(self):
        now = [0.0]
        provider = FixtureProvider([])
        def late_reply(*args, **kwargs):
            now[0] = 11.0
            decision = {"action": "insufficient_evidence", "reason": "Late response", "hypotheses": [hypothesis()],
                        "tool": None, "diagnosis": None}
            return ModelReply(decision, Usage(input_tokens=100, output_tokens=50), "late", "fixture", 11000)
        provider.step = late_reply
        with tempfile.TemporaryDirectory() as directory:
            result = InvestigationRunner(provider, FixtureTools(), output_root=Path(directory),
                                         budget=Budget(max_seconds=10), clock=lambda: now[0]).run(self.incident)
        self.assertEqual(result.status, "budget_exhausted")
        self.assertEqual(result.tool_calls, 1)
        self.assertEqual(result.input_tokens, 100)


if __name__ == "__main__":
    unittest.main()
