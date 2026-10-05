# Architecture decisions

These decisions implement the PRD's initial architecture; material departures
require human involvement before implementation.

| ADR | Decision |
| --- | --- |
| [001](001-reference-environment.md) | Pinned external OpenTelemetry Demo |
| [002](002-local-first.md) | Local Compose bootstrap, then kind |
| [003](003-tool-contracts.md) | Explicit native diagnostic contracts |
| [004](004-safety-boundaries.md) | Read-only tools and separate lab operations |
| [005](005-validation.md) | Separate deterministic, live, and AI validation |
| [006](006-telemetry-compatibility.md) | Isolated Jaeger compatibility and explicit log schema |
| [007](007-bounded-investigation.md) | One bounded native investigation loop |
| [008](008-chatgpt-authentication.md) | Supported ChatGPT sign-in and explicit usage limits |
| [009](009-recruiter-demo-hosting.md) | One free GitHub Pages site with a real investigation replay and project case study |
