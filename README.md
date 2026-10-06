# Sentinel

**AI Incident Investigation Agent**

A student project for investigating failures in a local distributed-system lab.
Sentinel's Python agent reads metrics, logs, traces, source, and configuration,
compares hypotheses, and records a diagnosis with evidence references. The site
contains a recorded investigation and notes on the implementation and lessons.

**Current stage: a read-only local agent and a recorded investigation viewer.**
One real payment investigation identified the injected flag-controlled failure
using logs, traces, metrics, source, and configuration. The developer-owned
exercise reset the fault and measured sampled recovery. Sentinel recommended
remediation without executing it. This
single controlled case does not establish general diagnosis quality. Two earlier
model investigations failed in transport and tool validation; their history,
fixes, and regression tests are documented. Development used AI coding assistance.

The Next.js/React/TypeScript site includes an interactive replay of that actual
run and project notes explaining the architecture, original work, decisions,
failures, and lessons. Visitors need no sign-in or model credits. The selected
public recording is validated and filtered; credentials and full private audit
files stay local. Published on GitHub Pages:
[the site](https://alesiobarquin.github.io/sentinel/),
[demo](https://alesiobarquin.github.io/sentinel/demo/#step-8), and
[project page](https://alesiobarquin.github.io/sentinel/project/).

The bounded agent, typed telemetry tools, policy, ChatGPT authentication, local
audit, and self-instrumentation are implemented. Metrics/logs/traces and restricted
Kubernetes reads passed real integration checks. Three deterministic fault
scenarios are reproducible; broader AI evaluations, FastAPI/PostgreSQL persistence,
incident chat, controlled remediation, MCP, and disposable AWS deployment remain
later guide work. Checkpoints 1 and 2 are acknowledged. See
[the delivery review](docs/checkpoints/05-recruiter-delivery.md),
[the full PRD](prd.md), and [repository constraints](AGENTS.md).

## Website development

```bash
cd apps/web
npm ci
npx playwright install chromium
npm run typecheck
npm run build
npm test
npm run preview
```

Open `http://127.0.0.1:4173/sentinel/`. The static site works independently of
Docker, Python services, and model credentials. Python is used by the local
preview server and publication validator. Read
[site operation and maintenance](docs/recruiter-site.md) for the export boundary,
development commands, deployment, failure modes, and cleanup.

## Local setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker Desktop running, Docker Compose v2, internet
access to GitHub and container registries, approximately 6 GB available to Docker,
and at least 14 GB of free disk space. These resource estimates come from the
[official demo installation guide](https://opentelemetry.io/docs/demo/docker-deployment/).
Run `make setup` to install the locked Python dependencies. Deterministic tools
need no LLM credentials or cloud account. A kind fixture uses additional Docker
resources; stop it after testing when sharing Docker with other projects.

```bash
make setup
make doctor
make demo-up
```

The bootstrap downloads the official OpenTelemetry Demo **3.1.0**, pinned to
commit `dedc0178918e260823323b8d95005a8cb924b007`, into `.cache/demo/source`.
It renders the official Compose layers, uses release images without building
upstream application code, and isolates the lab under the `sentinel-demo` project.
The upstream application remains external to Sentinel and is not original
Sentinel work. See the [release](https://github.com/open-telemetry/opentelemetry-demo/releases/tag/3.1.0)
and [lock file](infra/docker/demo.lock.json).

| Endpoint | Local URL |
| --- | --- |
| Demo web store | <http://127.0.0.1:8080> |
| Demo feature flags | <http://127.0.0.1:8080/feature> |
| Demo Grafana | <http://127.0.0.1:8080/grafana/> |
| Prometheus API | <http://127.0.0.1:9090> |
| Jaeger UI/API through the proxy | <http://127.0.0.1:8080/jaeger/ui/> |
| OpenSearch API | <http://127.0.0.1:9200> |
| Sentinel OTLP trace ingestion | <http://127.0.0.1:4318/v1/traces> |

Five host ports are published on loopback. Allow synthetic traffic
to warm up, then check the backends. Jaeger's direct query port 16686 is also
published; its base path follows the pinned Jaeger configuration.

```bash
make demo-status
make demo-verify
make metrics
make metric-names
make services
```

`demo-verify` requires a positive count of active Prometheus series, Jaeger service names, and a healthy
OpenSearch cluster. It does not establish that logs are ingested correctly or
that Sentinel can diagnose a fault. Empty or unavailable telemetry is reported
explicitly. A failed startup does not tear down automatically; inspect it with
`demo-status`, then stop it when finished.

## Deterministic telemetry tools

```bash
uv run python -m sentinel metrics --query 'count({__name__!=""})'
uv run python -m sentinel metric-names
uv run python -m sentinel metrics --query 'traces_span_metrics_calls_total{service_name="payment",span_kind="SPAN_KIND_SERVER"}' \
  --start 1791144000 --end 1791144300 --step 15
uv run python -m sentinel services
uv run python -m sentinel traces --service payment --start 1791144000 --end 1791144300
uv run python -m sentinel dependencies --start 1791144000 --end 1791144300
```

The timestamps above illustrate Unix seconds; substitute the time window
you want to inspect. Metrics results contain the query, provider, labels, timestamped
numeric samples, and backend warnings. `null` denotes a non-finite sample; an
empty result means no matching data, not a healthy application. This deployment
pushes metrics over OTLP; `up` is absent and is not a suitable readiness query.
Numeric float
samples are supported; string results and native histogram payloads fail clearly.

Trace queries return compact summaries with trace/span IDs, services, parent
references, durations in milliseconds, explicit error tags, and warnings. They
retain up to five relevant spans per trace by default, reporting how many were
omitted. A full result limit remains visible. Dependency graphs may be empty
when Jaeger's aggregation is unavailable or delayed.

Log queries require an explicit schema. The running Demo 3.1.0 mappings and
documents were verified against [the checked-in schema](infra/docker/log-schema.json).
Follow [the telemetry guide](docs/telemetry.md) when changing the target:

```bash
uv run python -m sentinel log-fields --index 'otel-logs*'
uv run python -m sentinel logs --index 'otel-logs*' --schema infra/docker/log-schema.json \
  --service payment --start 1791144000 --end 1791144300 --limit 50
```

Logs are grouped by identical full message and severity. Counts describe the
returned sample; the total matching count and whether it is a lower bound are
reported separately. Incomplete searches fail explicitly. No default log field
mapping is assumed.

Export `SENTINEL_PROMETHEUS_URL`, `SENTINEL_JAEGER_URL`, or
`SENTINEL_OPENSEARCH_URL` to change a backend. Export
`SENTINEL_AUDIT_PATH` to change the append-only audit file (default:
`var/audit/tool-calls.jsonl`). `.env.example` documents these settings; it is not
automatically loaded. Calls record their arguments, timing, success/failure, and
a compact result summary. Raw telemetry is not duplicated into audit records.

## First lab scenario

```bash
uv run python scripts/capture.py baseline --seconds 120
make lab-inject SCENARIO=payment-failure
# Allow traffic to run, then capture a window entirely inside the fault period.
# See the runbook for precise start timestamps and recovery collection.
uv run python scripts/capture.py incident --seconds 120
make lab-reset
# Allow new transactions and telemetry export before capturing recovery.
uv run python scripts/capture.py recovery --seconds 120
```

This changes the demo's `paymentFailure` flag to its `100%` variant. Reset
restores the previous value and preserves changes to other flags. The helper
operates on the downloaded lab configuration; it is not an investigation-agent
capability. The capture helper reads the pinned localhost backends, keeps bounded
evidence in `var/live-validation/`, records failed signals explicitly, and refuses
to overwrite an existing capture. See the
[manual investigation runbook](docs/runbooks/payment-failure.md) and
[measured validation](docs/validation/payment-failure.md).

Stop the lab with `make demo-down`. This stops only the Sentinel Compose project
and retains its volumes and downloaded source. Reset an injected fault before
stopping if you want the next run to start with the previous flag value.

## Read-only agent

Connect your account from a desktop terminal, then list its available models:

```bash
make login
make models
SENTINEL_MODEL=gpt-5.6-luna make first-investigation
```

The last command runs one bounded AI investigation against a real payment fault,
resets the developer lab even when diagnosis fails, and captures recovery. It
checks sign-in and model availability before injection. The example selects the
small model available to the validated account. The default is
`gpt-6-luna`; if it is unavailable, select an available smaller model explicitly
with `SENTINEL_MODEL`. No automatic upgrade occurs. The exercise takes several
minutes and stops at checkpoint 2 for review. Login requires your browser consent.

Subscription mode uses the supported public Responses endpoint with OAuth,
streaming, and `store=false`. API-key billing is separate. See the
[authentication and budget guide](docs/investigation.md) for eligibility, credential
storage, preview restrictions, and cap limitations. Defaults: eight model calls,
ten diagnostic reads, 50,000 reported tokens, 32 KB selected context, 12 KB response,
and a 300-second investigation budget. Per-request timeouts are bounded. The
subscription preview cannot enforce a server-side output token or exact credit
cap; a response can cross the local token limit before Sentinel stops further work.

For an existing incident, pass explicit Unix seconds and optional baseline:

```bash
uv run python -m sentinel investigate --service payment \
  --symptom 'Payment charge requests are failing' \
  --start 1791144000 --end 1791144300 \
  --baseline-start 1791143600 --baseline-end 1791143900
```

Substitute a window containing real retained telemetry. Each run saves its input,
bounded contexts, full tool results, reduced evidence, hypotheses, model decisions,
token accounting, tool audit, and OTel spans under `var/investigations/<run-id>/`.
Failures, insufficient evidence, and exhausted budgets are explicit outcomes.
Recommendations are text only; the agent has no remediation execution capability.

## Kubernetes and scenario validation

```bash
make demo-down
make kind-up
make pods
make kind-verify
SENTINEL_K8_LIVE_TESTS=1 uv run python -m unittest discover -s tests -p test_live_kubernetes.py
make kind-down
make demo-up
make scenario-validate
```

Run kind and the full demo separately on a constrained shared Docker VM; the
commands above stop only Sentinel's demo and restore it afterwards. The pinned
kind fixture is separate from the Compose target. Its service account
can read pods/events in `sentinel-fixture`; it cannot write, read secrets, or inspect
other namespaces. The script preserves your global kubeconfig. Credentials expire
after one hour; `make kind-credentials` renews them. Never give the agent the admin
kubeconfig. See [Kubernetes notes](docs/kubernetes.md).

`scenario-validate` runs payment, EmptyCart, and intermittent ad faults without
model calls. It records baseline/incident/recovery and resets each owned fault.
Results are adapter and fault validation, not AI accuracy. The
[scenario catalog](evals/scenarios.json) holds ground truth outside model context.
See [measured validation](docs/validation/read-only-agent.md).

## Measured validation

```bash
make check
make check-live-telemetry
```

The latest local suite passed **122 deterministic tests**, with eight opt-in
live tests skipped, plus Python compilation. The website passed **22 Chromium
browser checks** across desktop and mobile, TypeScript checks, and static export.
Six real telemetry checks and two isolated kind integration checks passed
separately. These counts describe different validation layers, not AI accuracy.

GitHub Actions checks Python 3.12/3.14, validates the public recording, builds the
site, and runs browser checks before deploying main to Pages.
[The first website deployment](https://github.com/Alesiobarquin/sentinel/actions/runs/37349717998)
passed every job; all 22 browser checks also passed against the actual public
HTTPS site. Live/costly AI runs remain outside ordinary CI. See
[the site validation record](docs/validation/recruiter-site.md).

The [first diagnosis review](docs/checkpoints/02-first-investigation.md) records
actual evidence, usage, recovery, and limitations. Exact subscription credit
consumption is unknown; the recorded run's OTLP export timed out, while its local
audit and 25 self-trace spans remained. Two earlier failed AI investigations are
retained and are not counted as successes. Full PRD portfolio acceptance is
still future work. See [the delivery review](docs/checkpoints/05-recruiter-delivery.md).

Read [the architecture](docs/architecture.md), [telemetry guide](docs/telemetry.md),
[decisions](docs/decisions/README.md), [learning questions](docs/learning/bootstrap.md),
and [recorded progress](docs/progress.md).
