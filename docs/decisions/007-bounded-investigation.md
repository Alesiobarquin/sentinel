# ADR 007: one bounded native investigation loop

## Context

Checkpoint 1 was acknowledged. Real telemetry and a manually reproduced payment
fault are available. The next guide milestone is one real AI diagnosis; a large
web product or orchestration framework would not establish that capability.

## Decision

Use one explicit Python loop, Pydantic closed contracts, and a direct OpenAI SDK
adapter. A namespaced `investigation_step` carries hypotheses and one read or
terminal decision. Application policy executes an allowlisted native diagnostic
tool, assigns evidence IDs, and validates citations. Tool arguments are service
and fixed period only; queries/endpoints/paths/namespace are application settings.

Keep full history in ignored run files, select whole reduced evidence within a
context limit, and instrument the loop using the OTel SDK. Expose loopback OTLP
ingestion in the existing collector so Sentinel's own traces reach Jaeger.
Use the separate kind read-only fixture to prove Kubernetes integration without
migrating or duplicating the full target before a working investigation.

## Alternatives

An agent framework would conceal some state/retry behavior and add another
dependency. Multiple agents need demonstrated evaluation gains. Flat function
tools are less compatible with the chosen subscription route. A transcript-only
loop would repeatedly send full history. A second complete Kubernetes demo would
consume resources before establishing diagnosis value.

## Rationale

Explicit code makes bounds, policy, evidence selection, failures, and replayable
artifacts reviewable. Pydantic validates untrusted output; the direct SDK handles
transport; existing telemetry providers retain their contracts. OTel observes
the product's own behavior. These follow the approved architecture and phases.

## Consequences

One step envelope needs cross-field validation. Provenance checks cannot certify
causal correctness. Source/config snapshots are current/pinned context with
explicit limits. Local files lack database transactions and distributed worker
coordination. Kind state does not describe the Compose target. Agent writes,
GitHub, persistent APIs, UI, and cloud remain later gated work.

## Reconsider when

Real evaluations expose loop/context weaknesses; concurrent incident jobs need
database-backed persistence; migration to kind is due; or a framework/additional
agent demonstrates measured value. Do not change these boundaries silently.
