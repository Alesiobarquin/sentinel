# ADR 004: read-only tools, separate developer lab

**Status:** implemented for read-only investigation. Write permissions remain
pending checkpoint 3.

## Context

Diagnostic reads, intentional fault injection, and production remediation have
different permission needs. A model must not be able to turn a diagnostic tool
into unrestricted runtime access.

## Decision

The Sentinel CLI reads Prometheus, Jaeger, OpenSearch, pinned source/current flags,
and explicitly configured namespaced pod state. Closed model contracts and
application policy select fixed tools and observed services. Kubernetes reads
use an independently restricted reader identity. No model-controlled query,
endpoint, file path, namespace, shell, or write operation exists.

Developer-only lab commands in `scripts/demo.py` support three allowlisted
scenarios and restore the prior flag value. Tracked ownership prevents one
exercise from resetting another. These helpers are not registered agent tools.
Record diagnostic calls before execution and publish local lab APIs on loopback.

## Alternatives

Giving a future model shell or unrestricted kubectl access would collapse the
permission boundary. Relying on a prompt for approval would not enforce policy.
Resetting every feature flag would erase unrelated developer work.

## Why this option

Manual fault injection can establish ground truth before an agent exists while
keeping the investigation surface read-only by default.

## Consequences

The fault helper is a local development operation, not a remediation system.
Current JSONL audit is not a transactional durable write-action ledger. Future
remediation needs application policy, read-only/separate-write Kubernetes RBAC,
human approval, audit persistence, and recovery verification. Secrets never
belong in tracked files or browser data.

External data and model decisions remain untrusted. Valid citations establish
provenance, not causal correctness or permission to execute recommendation prose.

## Future reconsideration

At checkpoint 3, review write permissions, threat model, policy enforcement, and
auditing before enabling GitHub writes or infrastructure-changing agent actions.
