# ADR 001: pinned external reference environment

**Status:** accepted within the PRD bootstrap scope.

## Context

Sentinel needs a distributed application with telemetry and reproducible faults.
The developer does not have a suitable production application to investigate.

## Decision

Use official OpenTelemetry Demo 3.1.0 at commit
`dedc0178918e260823323b8d95005a8cb924b007`, recorded in
`infra/docker/demo.lock.json`. Download its commit archive into an ignored cache
and run official release images. Attribute the upstream application explicitly.

## Alternatives

Following upstream HEAD would let schemas and scenarios drift. Vendoring the
whole application would blur ownership and add maintenance. Building a custom
storefront would delay incident investigation work.

## Why this option

The [official release](https://github.com/open-telemetry/opentelemetry-demo/releases/tag/3.1.0)
provides a known target, telemetry backends, and configurable faults. Pinning the
source commit preserves configuration independently of moving branch names.

## Consequences

Bootstrap needs internet access and available release images. The archive's local
SHA-256 records provenance without independently attesting upstream contents.
Container images are version-tagged, not digest-locked yet; stricter artifact
reproducibility requires capturing their platform-specific digests. Live
verification passed on the local ARM Docker runtime on 2026-10-04. Future upgrades
still require fresh integration checks; image tags remain mutable.

## Future reconsideration

Upgrade deliberately when a required fault or supported platform needs it, then
rerun live adapter tests and scenarios. Add other applications after the reference
investigations work reliably.
