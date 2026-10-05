# ADR 002: Compose first, kind next

**Status:** accepted within the PRD bootstrap scope.

## Context

Normal development must avoid continuously running paid cloud infrastructure.
The first milestone needs reliable telemetry access before Kubernetes-specific
investigation or AI orchestration.

## Decision

Start with the official full Compose deployment and its observability layer.
Use prebuilt images; isolate project, network, and container identities; publish
the store and telemetry APIs on loopback ports. Preserve upstream source
configuration and render local changes to an ignored runtime file. Add kind
after the first functioning deterministic diagnostics.

## Alternatives

Starting with kind adds cluster installation and port-forwarding prerequisites.
An always-running EKS cluster adds cost and credential complexity. Minimal
Compose saves memory but omits Kafka and related fault coverage.

## Why this option

This follows PRD section 30 and the supported
[official Docker installation](https://opentelemetry.io/docs/demo/docker-deployment/).
The full target supports a broader range of later incidents without requiring
cloud resources.

## Consequences

Reserve approximately 6 GB of Docker memory and 14 GB of disk. Local ports can
conflict with other applications. Generated configuration must be re-rendered
after changing the lock. Shutdown preserves lab volumes and source; injected
flags require explicit reset. The initial stage had no Kubernetes adapter; a
separate read-only kind fixture was added after deterministic diagnostics.

The shared local Docker VM ran out of memory/swap when the full demo and kind
ran together alongside other projects. Kind workloads were OOM-killed and its
API timed out. Validate the two local targets separately on that VM. Neither
runtime requires a paid resource, and the user's unrelated projects are preserved.
Sentinel's own OTLP export adds a fifth loopback port on the existing collector.

## Future reconsideration

Add an explicit minimal mode if resource pressure prevents local development.
Move the reference target to kind when Kubernetes evidence is needed. AWS stays
ephemeral and requires the PRD's explicit cost/security checkpoint.
