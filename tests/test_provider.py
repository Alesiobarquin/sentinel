from contextlib import contextmanager
from types import SimpleNamespace as NS
import json
import unittest

from sentinel.agent.contracts import Budget, InvestigationResponse, Usage
from sentinel.agent.provider import ModelError, OpenAIProvider, api_cost


class Client:
    def __init__(self, events):
        self.events, self.parameters = events, None
        self.responses = self
    @contextmanager
    def create(self, **kwargs):
        self.parameters = kwargs
        yield iter(self.events)


def read_decision():
    return {"action": "read", "reason": "Synthetic diagnostic read", "hypotheses": [{
        "name": "Fixture", "explanation": "Synthetic fixture", "confidence": 0.5,
        "supporting_evidence": [], "contradicting_evidence": [], "status": "active"}],
        "tool": {"name": "logs", "service": "payment", "period": "incident"}, "diagnosis": None}


def completed(arguments=None, **changes):
    if arguments is None:
        arguments = json.dumps({"step": read_decision()})
    call = NS(type="function_call", name="investigation_step", namespace="sentinel", arguments=arguments)
    response = NS(status="completed", id="test-response", model="gpt-6-luna", output=[call],
                  usage=NS(input_tokens=10, output_tokens=5, input_tokens_details=NS(cached_tokens=2)))
    response.__dict__.update(changes)
    return NS(type="response.completed", response=response)


class ProviderTests(unittest.TestCase):
    def test_subscription_request_is_public_streamed_and_preview_compatible(self):
        client = Client([NS(type="response.function_call_arguments.delta", delta="{}"), completed()])
        provider = OpenAIProvider("fake", client=client)
        reply = provider.step("instructions", {"incident": "fixture"}, Budget(), timeout=5)
        self.assertEqual(reply.usage.output_tokens, 5)
        self.assertEqual(reply.decision, read_decision())
        p = client.parameters
        self.assertFalse(p["store"])
        self.assertTrue(p["stream"])
        self.assertFalse(p["parallel_tool_calls"])
        self.assertNotIn("max_output_tokens", p)
        self.assertNotIn("previous_response_id", p)
        self.assertEqual(p["tools"][0]["type"], "namespace")
        schema = p["tools"][0]["tools"][0]["parameters"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        for definition in schema["$defs"].values():
            if definition.get("type") == "object":
                self.assertFalse(definition["additionalProperties"])
                self.assertEqual(set(definition["required"]), set(definition["properties"]))

    def test_interrupted_failed_incomplete_or_oversized_stream_never_succeeds(self):
        events = [[NS(type="response.function_call_arguments.delta", delta="{}")],
                  [NS(type="response.failed")], [NS(type="response.incomplete")],
                  [NS(type="response.function_call_arguments.delta", delta="x" * 13000), completed()],
                  [completed(status="incomplete")], [completed(usage=None)], [completed(output=[])],
                  [completed(arguments="not-json")]]
        for stream in events:
            with self.subTest(stream=str(stream)[:100]), self.assertRaises(ModelError):
                OpenAIProvider("fake", client=Client(stream)).step("instructions", {}, Budget(), timeout=5)

    def test_api_mode_has_output_limit_and_known_price(self):
        client = Client([completed()])
        OpenAIProvider("fake", client=client, billing_mode="api").step("instructions", {}, Budget())
        self.assertEqual(client.parameters["max_output_tokens"], 2400)
        self.assertAlmostEqual(api_cost("gpt-6-luna", Usage(input_tokens=1000000, cached_input_tokens=100000, output_tokens=1000000)), 0.591)
        with self.assertRaises(ValueError):
            OpenAIProvider("fake", model="unknown", billing_mode="api")

    def test_completed_invalid_decision_keeps_measured_usage(self):
        with self.assertRaises(ModelError) as failure:
            OpenAIProvider("fake", client=Client([completed(arguments="not-json")])).step("instructions", {}, Budget())
        self.assertEqual(failure.exception.usage.input_tokens, 10)
        self.assertEqual(failure.exception.response_id, "test-response")

    def test_subscription_accepts_finalized_tool_item_with_empty_terminal_output(self):
        call = completed().response.output[0]
        stream = [NS(type="response.output_item.done", output_index=1, item=call), completed(output=[])]
        reply = OpenAIProvider("fake", client=Client(stream)).step("instructions", {}, Budget())
        self.assertEqual(reply.decision, read_decision())
        self.assertEqual(reply.usage.output_tokens, 5)

    def test_finalized_item_without_completed_response_is_rejected(self):
        call = completed().response.output[0]
        with self.assertRaises(ModelError):
            OpenAIProvider("fake", client=Client([NS(type="response.output_item.done", output_index=1, item=call)])).step(
                "instructions", {}, Budget())

    def test_streamed_tool_items_still_enforce_identity_count_size_and_consistency(self):
        good = completed().response.output[0]
        wrong = NS(type="function_call", name="shell", namespace="other", arguments='{}')
        large = NS(type="function_call", name="investigation_step", namespace="sentinel", arguments='x' * 13000)
        done = lambda index, item: NS(type="response.output_item.done", output_index=index, item=item)
        streams = [[done(1, wrong), completed(output=[])],
                   [done(1, good), done(2, good), completed(output=[])],
                   [done(1, good), done(1, good), completed(output=[])],
                   [done(-1, good), completed(output=[])],
                   [done(1, large), completed(output=[])],
                   [done(1, good), completed(arguments='{"action":"diagnose"}')],
                   [NS(type="response.function_call_arguments.delta", delta=good.arguments), completed(output=[])]]
        for stream in streams:
            with self.subTest(events=len(stream)), self.assertRaises(ModelError):
                OpenAIProvider("fake", client=Client(stream)).step("instructions", {}, Budget())

    def test_model_contract_and_python_reject_mixed_terminal_and_read_actions(self):
        schema = InvestigationResponse.model_json_schema()
        self.assertNotIn("anyOf", schema)
        variants = [schema["$defs"][branch["$ref"].split("/")[-1]]
                    for branch in schema["properties"]["step"]["anyOf"]]
        by_action = {branch["properties"]["action"]["const"]: branch for branch in variants}
        self.assertEqual(by_action["diagnose"]["properties"]["tool"]["type"], "null")
        self.assertEqual(by_action["read"]["properties"]["diagnosis"]["type"], "null")
        for action in ["diagnose", "insufficient_evidence"]:
            invalid = {**read_decision(), "action": action}
            with self.subTest(action=action), self.assertRaises(ModelError) as failure:
                OpenAIProvider("fake", client=Client([completed(json.dumps({"step": invalid}))])).step("instructions", {}, Budget())
            self.assertEqual(failure.exception.usage.output_tokens, 5)
        for invalid in [read_decision(), {"step": read_decision(), "command": "shell"}, {"step": None}]:
            with self.subTest(envelope=invalid), self.assertRaises(ModelError):
                OpenAIProvider("fake", client=Client([completed(json.dumps(invalid))])).step("instructions", {}, Budget())


if __name__ == "__main__":
    unittest.main()
