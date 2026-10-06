"""Direct Responses SDK adapter; no SDK agent runner or concealed retries."""

from dataclasses import dataclass
import json
import time
from typing import Protocol

from openai import OpenAI, OpenAIError

from sentinel.agent.contracts import Budget, InvestigationResponse, Usage

DEFAULT_MODEL = "gpt-6-luna"
# Standard API rates checked 2026-10-04. Subscription usage is not API dollars.
API_RATES = {"gpt-6-luna": (0.10, 0.01, 0.50)}


class ModelError(RuntimeError):
    """A sanitized model failure; unknown usage is recorded rather than assumed free."""

    def __init__(self, message: str, *, usage: Usage | None = None, response_id: str | None = None,
                 response: dict | None = None):
        super().__init__(message)
        self.usage, self.response_id, self.response = usage, response_id, response


@dataclass(frozen=True)
class ModelReply:
    decision: dict
    usage: Usage
    response_id: str
    model: str
    latency_ms: float
    response: dict | None = None


class ModelProvider(Protocol):
    model: str
    billing_mode: str

    def step(self, instructions: str, context: dict, budget: Budget, *, timeout: float) -> ModelReply: ...


class OpenAIProvider:
    def __init__(self, credential: str, *, model: str = DEFAULT_MODEL, billing_mode: str = "chatgpt", client=None):
        if billing_mode not in {"chatgpt", "api"}:
            raise ValueError("Unknown billing mode")
        if billing_mode == "api" and model not in API_RATES:
            raise ValueError("API model lacks verified prices for budget enforcement")
        self.model, self.billing_mode = model, billing_mode
        self.client = client or OpenAI(api_key=credential, base_url="https://api.openai.com/v1", max_retries=0, timeout=30)

    def step(self, instructions: str, context: dict, budget: Budget, *, timeout: float = 30) -> ModelReply:
        started = time.monotonic()
        parameters = {
            "model": self.model, "instructions": instructions,
            "input": [{"role": "user", "content": json.dumps(context, separators=(",", ":"), allow_nan=False)}],
            "store": False, "stream": True, "parallel_tool_calls": False,
            "tools": [{"type": "namespace", "name": "sentinel", "description": "Bounded read-only incident investigation",
                       "tools": [{"type": "function", "name": "investigation_step", "description": "Select one diagnostic read or finish with cited evidence.",
                                  "parameters": InvestigationResponse.model_json_schema(), "strict": True}]}],
            "tool_choice": "required", "timeout": max(0.1, min(timeout, 30)),
        }
        if self.billing_mode == "api":
            parameters["max_output_tokens"] = budget.max_output_tokens
        completed, output_bytes, streamed_calls = None, 0, {}
        try:
            with self.client.responses.create(**parameters) as stream:
                for event in stream:
                    if time.monotonic() - started > timeout:
                        raise ModelError("Model response exceeded the wall-time budget; usage is unknown")
                    if event.type.endswith(".delta"):
                        output_bytes += len(str(getattr(event, "delta", "")).encode())
                        if output_bytes > budget.max_response_bytes:
                            raise ModelError("Model response exceeded the local byte limit; usage is unknown")
                    if event.type in {"response.failed", "response.incomplete", "error"}:
                        raise ModelError("Model stream reported failure or incomplete output; usage is unknown")
                    if event.type == "response.output_item.done" and event.item.type == "function_call":
                        index = event.output_index
                        if type(index) is not int or not 0 <= index < 16 or index in streamed_calls:
                            raise ModelError("Model stream returned an invalid or duplicate completed tool item; usage is unknown")
                        streamed_calls[index] = event.item
                    if event.type == "response.completed":
                        completed = event.response
                        break
        except OpenAIError:
            raise ModelError("OpenAI request failed; usage may be unknown; no retry was attempted") from None
        if completed is None or completed.status != "completed":
            raise ModelError("Model stream ended without a completed response; usage is unknown")
        usage = completed.usage
        if usage is None:
            raise ModelError("Completed model response did not report usage")
        try:
            measured = Usage(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                             cached_input_tokens=usage.input_tokens_details.cached_tokens)
        except (ValueError, AttributeError) as exc:
            raise ModelError("Model usage was malformed") from exc
        terminal_calls = [item for item in completed.output if item.type == "function_call"]
        finalized_calls = [streamed_calls[index] for index in sorted(streamed_calls)]
        # The subscription endpoint sends finalized tool items during the stream
        # and can leave terminal output empty. Never use unfinished argument deltas.
        calls = terminal_calls if completed.output else finalized_calls
        response = None
        if hasattr(completed, "model_dump"):
            response = {"terminal": completed.model_dump(mode="json"),
                        "streamed_tool_calls": [item.model_dump(mode="json") for item in finalized_calls]}
        signature = lambda item: (item.name, item.namespace, item.arguments)
        if terminal_calls and finalized_calls and list(map(signature, terminal_calls)) != list(map(signature, finalized_calls)):
            raise ModelError("Completed model output conflicts with finalized stream items", usage=measured,
                             response_id=completed.id, response=response)
        if len(calls) != 1 or calls[0].name != "investigation_step" or calls[0].namespace != "sentinel":
            raise ModelError("Model did not return exactly one allowed investigation decision", usage=measured,
                             response_id=completed.id, response=response)
        if len(calls[0].arguments.encode()) > budget.max_response_bytes:
            raise ModelError("Completed model arguments exceeded their size limit", usage=measured,
                             response_id=completed.id, response=response)
        try:
            decision = InvestigationResponse.model_validate(json.loads(calls[0].arguments)).step.model_dump()
        except (ValueError, AttributeError) as exc:
            raise ModelError("Model decision was malformed", usage=measured,
                             response_id=completed.id, response=response) from exc
        return ModelReply(decision, measured, completed.id, completed.model,
                          round((time.monotonic() - started) * 1000, 3), response)

    def close(self):
        self.client.close()


def api_cost(model: str, usage: Usage) -> float:
    input_rate, cached_rate, output_rate = API_RATES[model]
    return ((usage.input_tokens - usage.cached_input_tokens) * input_rate +
            usage.cached_input_tokens * cached_rate + usage.output_tokens * output_rate) / 1_000_000
