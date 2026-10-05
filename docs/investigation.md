# Read-only investigation

The first agent is implemented, with deterministic contract/policy tests. Live
model transport and diagnosis quality remain unverified until the developer
completes ChatGPT sign-in and runs a real investigation. This distinction matters:
scripted test decisions establish application behavior, not model reasoning.

## Run one real investigation

From the repository on your desktop:

```bash
make setup
make demo-up
make login
make models
make first-investigation
```

Login opens the system browser; review the identity and ChatGPT plan permissions.
The default smaller model is `gpt-6-luna`. The account catalog must contain it;
otherwise select an available model explicitly:

```bash
SENTINEL_MODEL=your-selected-model make first-investigation
```

There is no automatic upgrade. The exercise checks credentials and configuration,
captures baseline, injects the payment fault, waits for a retained telemetry
window, runs one agent, resets its owned fault, and captures recovery. Reset is
a developer exercise operation, not an agent remediation. SIGTERM/Ctrl-C clean up;
SIGKILL or power loss may require `make lab-reset`. A tracked owner ID prevents
one exercise from resetting another exercise's fault.

`--preflight-only` on `scripts/first_investigation.py` makes no model call and
injects no fault. It checks authentication/model availability and local wiring,
not backend health. Baseline reads are performed before actual injection.

After the first correct live diagnosis, stop at
[checkpoint 2](checkpoints/02-first-investigation.md). An output that satisfies
the schema and citation checks can still be causally wrong; review it against
the real evidence and pinned source.

## Trust boundaries and loop

`Incident` contains a service, symptom, and bounded Unix-second window. An
explicit baseline may end earlier than the incident, allowing a settling gap.
Without one, the equally sized preceding window is used. Baseline choice is
visible; it is not a guarantee that those requests were healthy.

One model response selects one `investigation_step`: a diagnostic read, a
diagnosis, or insufficient evidence. The step includes explicit competing
hypotheses and supporting/contradicting evidence IDs. Pydantic rejects extra
fields, inconsistent actions, non-finite values, and malformed tool arguments.
Application policy restricts services to the incident service and observed
inventory. PromQL, backend endpoints, filesystem paths, namespaces, and shell
commands are never chosen by the model.

Native tools provide inventory, server-span latency ranking/status estimates,
raw counter sample coverage, grouped logs, compact traces, dependencies,
current feature defaults, pinned
source excerpts, and optional namespaced pod state. The runtime snapshot and
source are legitimate diagnostic context, not evaluation ground truth. No
scenario catalog, tracked injection state, manual runbook answer, or expected
diagnosis enters model context. Source context is explicitly allowlisted in
`infra/docker/source-context.json`, with hashes, line numbers, commit, and
omission flags. It does not prove the deployed image contains identical bytes.

Every successful or failed read receives an evidence ID. Failed evidence cannot
support a diagnosis. Final citations must exist, cover two evidence kinds, and
include a metric, trace, or log. These checks establish provenance and minimum
coverage; they do not establish that the causal interpretation is correct.

Context construction selects whole reduced results within a byte limit. It
retains a full evidence index, current hypotheses, tool history, and explicit
omission IDs. Full tool results and all prior contexts remain outside the chosen
model context. Recommendations require human review, and infrastructure-change
kinds are marked for approval. Recommendation text remains untrusted. No
remediation executor exists, so neither prose nor a misleading action label can
authorize a change.

## Authentication

The developer chose ChatGPT subscription sign-in on 2026-10-05. This supported
public-client flow uses `dynamic_agent_client` for first registration, a stable
host ID, fresh state/nonce/PKCE, and a listener bound to `127.0.0.1`. The issued
client ID is used for token exchange. RS256 signature, issuer, audience, expiry,
nonce, verified account identity, and plan-usage scopes are validated before
credentials become active. Public discovery confirmed the issuer/JWKS and RS256.

Credential storage defaults to `~/.config/sentinel/`: directory `0700`, files
`0600`, atomic replacement, and serialized rotating refresh. Tokens never enter
model context, audit records, access logs, or browser storage. Authorization URLs
omit the optional retained ID-token hint. One account is supported per directory;
separate directories select separate accounts. Login has only been tested with
local signed fixtures; a real consent/token exchange has not run yet.

`make models` uses that account's public model catalog. `uv run python -m sentinel
logout` attempts remote revocation and clears local tokens. When remote
revocation cannot be confirmed, disconnect Sentinel in ChatGPT Settings.

Eligible subscriptions can authorize plan use; possession of a subscription is
not an API-key balance. See the official
[sign-in guide](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
[inference contract](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
and [preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations).
No private ChatGPT endpoint or existing Codex credential is used.

## Budgets and failures

Defaults: eight model requests, ten semantic tool invocations including initial
inventory, 50,000 reported input/output tokens, 32,000 selected-context bytes,
12,000 response bytes, and 300 seconds between admitted operations. SDK retries
are disabled, model requests are bounded to 30 seconds, and backend reads have
their own finite timeouts/response limits. A semantic tool can perform multiple
fixed backend requests; the tool count is not an HTTP-request count. An in-flight
backend read can finish after the overall wall-time limit; no subsequent action
is admitted. Exact duplicate diagnostic reads terminate instead of retrying.

Subscription mode requires `store=false`, streaming, input arrays, and namespaced
functions. The preview rejects `max_output_tokens`; Sentinel omits it. It stops
oversized streams, counts completed usage, and admits no more work after the
reported-token limit. An individual response can cross that limit or consume
usage before a stream is canceled. Hidden reasoning and interrupted responses
prevent an exact client-side credit cap. No API-dollar estimate is applied to
subscription credits. Use the account's usage controls as well.

Explicit API-key mode (`--billing-mode api`) is billed separately and only
supports a model with verified prices in the adapter. It sends a server output
limit (2,400 tokens) and reserves conservative input/output cost before a request,
with a default maximum of $1 per run. The price table records standard
`gpt-6-luna` rates checked 2026-10-04; refresh it before enabling a different model
or pricing mode. See [official model pricing](https://developers.openai.com/api/docs/models/gpt-6-luna).
Approximate cost covers measured calls, not unknown interrupted usage or an
account-wide spend limit.

Malformed decisions, forbidden service reads, bad citations, tool failures,
refusals/incomplete streams, interrupted responses, and exhausted budgets remain
visible. A completed invalid model output retains its measured usage; an
interrupted response marks usage unknown. Partial deltas never become diagnoses.

## Persistence, observability, and changes

Subscription streaming can deliver completed function items in
`response.output_item.done` while the final response's output list is empty.
The adapter uses finalized items, never unfinished argument deltas, and still
requires successful response completion, reported usage, the exact namespaced
tool, a single decision, size limits, and consistent terminal/stream output.
Native response metadata and finalized function calls are retained in
`response-NN.json` beside the selected context and decision files, including
completed provider failures. They do not enter subsequent model context.
This behavior was discovered in a real failed run; the captured stream was
replayed offline and regression-tested before another incident exercise.
[Official function-stream events](https://developers.openai.com/api/docs/guides/function-calling).

`var/investigations/<run-id>/` contains input/budget, full tool payloads,
append-only events and tool timing, selected contexts, decisions, final result,
and local OTel spans. OTLP export is optional for the general CLI and enabled
against `127.0.0.1:4318/v1/traces` by the first exercise. Spans cover investigation,
context construction, model requests, and tools. Token counts, model IDs,
latency, outcomes, and evidence IDs connect the records. Local files are a
single-process development store, not transactional database persistence.

Before modifying the loop, understand `contracts.py`, `diagnostics.py`,
`context.py`, `provider.py`, and `runner.py`. Policy enforcement must stay outside
prompts. Keep auth tokens outside instrumentation. Run `make check`; test real
backends separately; run model evaluations only with deliberate usage budgets.
See [ADR 007](decisions/007-bounded-investigation.md),
[ADR 008](decisions/008-chatgpt-authentication.md), and
[learning questions](learning/investigation.md).
