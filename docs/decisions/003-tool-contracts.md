# ADR 003: explicit native diagnostic contracts

**Status:** implemented for native telemetry, semantic diagnostics, and read-only
Kubernetes; live AI behavior remains unverified.

## Context

The agent should use normalized system evidence without coupling business logic
to a telemetry backend, model provider, or orchestration framework.

## Decision

Use Python `MetricsProvider`, `TraceProvider`, and `LogProvider` protocols,
frozen result dataclasses, and Prometheus, Jaeger, and OpenSearch adapters.
Use standard-library JSON/HTTP for the small read-only surface and preserve
identifiers, times, units, missing data, warnings, and query coverage limits.
Validate requests, bound time windows/resolution/payloads, and propagate failures.
Generic PromQL belongs to the developer CLI. After real telemetry discovery,
semantic tools construct fixed queries and Pydantic validates agent inputs and
decisions. Backend redirects fail instead of changing the configured read target.

## Alternatives

A large orchestration framework would hide tool/state behavior before it is
understood. MCP-first transport would add a protocol before contracts stabilize.
Sending raw response blobs to a model would increase cost and obscure provenance.

## Why this option

The first tool can be understood and tested without third-party installation,
LLM credentials, or a running API. Replacing the provider does not require changing
the CLI's normalized result contract.

## Consequences

Float sample queries are supported; native histogram and string result formats
fail explicitly. NaN/infinity become missing values rather than zero. Domain
aggregation now exposes fixed server-span estimates and raw counter sample
coverage. Incident evidence IDs and bounded context selection connect native
results to citations. Trace span selection and exact log-message grouping reduce
evidence deterministically. The separate Kubernetes adapter uses a protected
reader identity; it does not change the Compose application's runtime.

## Future reconsideration

Add richer typed contracts as concrete incidents demand them. OAuth and
Kubernetes use the SDK's existing httpx dependency for bounded authenticated
requests. Reconsider the standard-library telemetry transport if pooling or
async execution adds measured value.
Expose stable contracts over MCP after local investigation works.
