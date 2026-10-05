"""Run read-only developer diagnostics with python -m sentinel."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

from sentinel.tools.audit import ToolRecorder
from sentinel.tools.common import TimeWindow
from sentinel.tools.http import TelemetryError
from sentinel.tools.logs import LogSchema, OpenSearchProvider
from sentinel.tools.metrics import PrometheusProvider
from sentinel.tools.traces import JaegerProvider


def add_window(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start", type=float, required=True, help="Window start, Unix seconds")
    parser.add_argument("--end", type=float, required=True, help="Window end, Unix seconds (exclusive for logs)")


def load_log_schema(path: str) -> LogSchema:
    with Path(path).open(encoding="utf-8") as stream:
        raw = stream.read(64_001)
    if len(raw) > 64_000:
        raise ValueError("Log schema exceeds the 64 KB limit")
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected an object")
        return LogSchema(**data)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid log schema JSON; see docs/telemetry.md for the required fields") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sentinel deterministic telemetry tools")
    sub = parser.add_subparsers(dest="command", required=True)
    login_parser = sub.add_parser("login", help="Continue with ChatGPT using explicit browser consent")
    login_parser.add_argument("--timeout", type=int, default=300, choices=range(30, 901), metavar="30..900")
    sub.add_parser("models", help="List models available to the connected ChatGPT account")
    sub.add_parser("logout", help="Revoke the ChatGPT session and clear local tokens")
    pods = sub.add_parser("pods", help="Read current pods/events using only the restricted service-account identity")
    pods.add_argument("--service", required=True)
    pods.add_argument("--config", default=os.getenv("SENTINEL_KUBERNETES_CONFIG", ".cache/kind/reader.json"))
    semantic = sub.add_parser("diagnostic", help="Run one bounded model-facing semantic tool without a model")
    semantic.add_argument("--tool", choices=["services", "latency_ranking", "metrics", "logs", "traces", "dependencies", "runtime_configuration", "source"], required=True)
    semantic.add_argument("--service", required=True, help="Incident service; global tools use no service argument internally")
    semantic.add_argument("--period", choices=["incident", "baseline"], default="incident")
    add_window(semantic)
    investigate = sub.add_parser("investigate", help="Run the read-only agent with bounded usage and cited evidence")
    investigate.add_argument("--service", required=True)
    investigate.add_argument("--symptom", required=True)
    investigate.add_argument("--model", default=os.getenv("SENTINEL_MODEL", "gpt-6-luna"))
    investigate.add_argument("--billing-mode", choices=["chatgpt", "api"], default="chatgpt")
    investigate.add_argument("--max-model-calls", type=int, default=8)
    investigate.add_argument("--max-tool-calls", type=int, default=10)
    investigate.add_argument("--max-total-tokens", type=int, default=50000)
    investigate.add_argument("--api-cost-cap", type=float, default=1)
    investigate.add_argument("--baseline-start", type=float)
    investigate.add_argument("--baseline-end", type=float)
    add_window(investigate)
    metrics = sub.add_parser("metrics", help="Run a numeric PromQL instant or range query")
    metrics.add_argument("--query", required=True)
    metrics.add_argument("--at", type=float, help="Unix seconds for an instant query")
    metrics.add_argument("--start", type=float, help="Range start, Unix seconds")
    metrics.add_argument("--end", type=float, help="Range end, Unix seconds")
    metrics.add_argument("--step", type=float, default=15, help="Range resolution, seconds")
    sub.add_parser("metric-names", help="Discover the metric names present in Prometheus")
    sub.add_parser("services", help="Discover service names in Jaeger")
    traces = sub.add_parser("traces", help="Query compact traces, preserving IDs and parent references")
    traces.add_argument("--service", required=True)
    traces.add_argument("--limit", type=int, default=10)
    traces.add_argument("--span-limit", type=int, default=5)
    traces.add_argument("--min-duration-ms", type=float, default=0)
    add_window(traces)
    dependencies = sub.add_parser("dependencies", help="Read Jaeger's aggregated service dependency graph")
    add_window(dependencies)
    fields = sub.add_parser("log-fields", help="Inspect OpenSearch field types before configuring log queries")
    fields.add_argument("--index", required=True, help="Log index, alias, or pattern with a literal prefix")
    logs = sub.add_parser("logs", help="Query and group a bounded log sample using an explicit schema")
    logs.add_argument("--index", required=True)
    logs.add_argument("--schema", required=True, help="Path to a JSON LogSchema; no default field assumptions")
    logs.add_argument("--service", required=True)
    logs.add_argument("--limit", type=int, default=50)
    logs.add_argument("--severity")
    add_window(logs)
    args = parser.parse_args(argv)
    try:
        if args.command in {"login", "models", "logout"}:
            from sentinel.auth import AuthError, CredentialStore, available_models, login, logout
            store = CredentialStore(Path(os.getenv("SENTINEL_AUTH_DIR", str(Path.home() / ".config/sentinel"))))
            try:
                if args.command == "login":
                    login(store, timeout=args.timeout)
                elif args.command == "models":
                    print(json.dumps(available_models(store), indent=2))
                else:
                    confirmed = logout(store)
                    print("Local credentials cleared. " + ("Remote revocation confirmed." if confirmed else
                          "Remote revocation was not confirmed; disconnect Sentinel in ChatGPT Settings."))
                return 0
            except AuthError as exc:
                print(f"Sentinel: {exc}", file=sys.stderr)
                return 1
        if args.command == "investigate":
            from sentinel.agent.contracts import Budget, Incident
            from sentinel.agent.local import local_tools
            from sentinel.agent.provider import OpenAIProvider
            from sentinel.agent.runner import InvestigationRunner
            from sentinel.auth import AuthError, CredentialStore, access_token, available_models
            from pydantic import ValidationError
            try:
                incident = Incident(service=args.service, symptom=args.symptom, start=args.start, end=args.end,
                                    baseline_start=args.baseline_start, baseline_end=args.baseline_end)
                budget = Budget(max_model_calls=args.max_model_calls, max_tool_calls=args.max_tool_calls,
                                max_total_tokens=args.max_total_tokens, max_api_cost_usd=args.api_cost_cap)
                if args.billing_mode == "chatgpt":
                    store = CredentialStore(Path(os.getenv("SENTINEL_AUTH_DIR", str(Path.home() / ".config/sentinel"))))
                    models = available_models(store)
                    if args.model not in {m["slug"] for m in models}:
                        raise ValueError("Selected model is unavailable for this account. Run 'make models'; no automatic model upgrade occurs.")
                    credential = access_token(store)
                else:
                    credential = os.getenv("OPENAI_API_KEY", "")
                    if not credential:
                        raise ValueError("API-key billing was selected but OPENAI_API_KEY is not exported")
                tools = local_tools(incident)
                provider = OpenAIProvider(credential, model=args.model, billing_mode=args.billing_mode)
                try:
                    result = InvestigationRunner(provider, tools, budget=budget,
                                                 otlp_endpoint=os.getenv("SENTINEL_OTLP_TRACES_ENDPOINT")).run(incident)
                finally:
                    provider.close()
                print(json.dumps(asdict(result), indent=2, allow_nan=False))
                return 0 if result.status == "diagnosed" else 2
            except (AuthError, ValidationError) as exc:
                print(f"Sentinel: {str(exc) if isinstance(exc, AuthError) else 'Invalid incident or budget parameters'}", file=sys.stderr)
                return 1
        recorder = ToolRecorder(Path(os.getenv("SENTINEL_AUDIT_PATH", "var/audit/tool-calls.jsonl")))
        parameters = {k: v for k, v in vars(args).items() if k != "command"}
        if args.command == "pods":
            from sentinel.agent.local import kubernetes_provider
            provider = kubernetes_provider(Path(args.config))
            output = recorder.invoke("pods", {"service": args.service, "namespace": provider.namespace},
                                     lambda: provider.pods(args.service), lambda r: {"pod_count": len(r["pods"]), "limit_reached": r["limit_reached"]})
        elif args.command == "diagnostic":
            from sentinel.agent.contracts import Incident, ToolRequest
            from sentinel.agent.local import local_tools
            incident = Incident(service=args.service, symptom="Manual diagnostic read", start=args.start, end=args.end)
            tools = local_tools(incident)
            scoped = args.tool in {"metrics", "logs", "traces", "source"}
            timed = args.tool in {"latency_ranking", "metrics", "logs", "traces", "dependencies"}
            request = ToolRequest(name=args.tool, service=args.service if scoped else None, period=args.period if timed else None)
            kind, source, raw, summary = recorder.invoke(args.tool, request.model_dump(), lambda: tools.execute(request),
                                                       lambda r: {"kind": r[0], "source": r[1]})
            output = {"kind": kind, "source": source, "summary": summary}
        elif args.command == "metrics":
            provider = PrometheusProvider(os.getenv("SENTINEL_PROMETHEUS_URL", "http://127.0.0.1:9090"))
            result = recorder.invoke(
                "query_metrics", parameters, lambda: provider.query_metrics(**parameters),
                lambda r: {"series_count": len(r.series), "result_type": r.result_type},
            )
            output = asdict(result)
        elif args.command == "metric-names":
            provider = PrometheusProvider(os.getenv("SENTINEL_PROMETHEUS_URL", "http://127.0.0.1:9090"))
            names = recorder.invoke("metric_names", {}, provider.metric_names, lambda r: {"count": len(r)})
            output = {"source": "prometheus", "names": names}
        elif args.command in {"services", "traces", "dependencies"}:
            provider = JaegerProvider(os.getenv("SENTINEL_JAEGER_URL", "http://127.0.0.1:8080/jaeger/ui"))
            if args.command == "services":
                names = recorder.invoke("trace_services", {}, provider.services, lambda r: {"count": len(r)})
                output = {"source": "jaeger", "services": names}
            elif args.command == "traces":
                result = recorder.invoke(
                    "query_traces", parameters,
                    lambda: provider.query_traces(
                        args.service, TimeWindow(args.start, args.end), limit=args.limit,
                        span_limit=args.span_limit, min_duration_ms=args.min_duration_ms,
                    ),
                    lambda r: {"trace_count": len(r.traces), "limit_reached": r.limit_reached},
                )
                output = asdict(result)
            else:
                result = recorder.invoke(
                    "get_service_dependencies", parameters,
                    lambda: provider.get_service_dependencies(TimeWindow(args.start, args.end)),
                    lambda r: {"edge_count": len(r.edges)},
                )
                output = asdict(result)
        else:
            provider = OpenSearchProvider(os.getenv("SENTINEL_OPENSEARCH_URL", "http://127.0.0.1:9200"))
            if args.command == "log-fields":
                result = recorder.invoke(
                    "log_fields", parameters, lambda: provider.fields(args.index),
                    lambda r: {"index_count": len(r.indices), "field_count": len(r.fields)},
                )
            else:
                schema = load_log_schema(args.schema)
                parameters["schema"] = asdict(schema)
                result = recorder.invoke(
                    "query_logs", parameters,
                    lambda: provider.query_logs(
                        args.service, TimeWindow(args.start, args.end), index_pattern=args.index,
                        schema=schema, limit=args.limit, severity=args.severity,
                    ),
                    lambda r: {"returned_count": r.returned_count, "group_count": len(r.groups), "sample_complete": r.sample_complete},
                )
            output = asdict(result)
        print(json.dumps(output, indent=2, allow_nan=False))
        return 0
    except (TelemetryError, ValueError, OSError) as exc:
        print(f"Sentinel: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
