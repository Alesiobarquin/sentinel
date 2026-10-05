# Sentinel
## AI-Native Incident Investigation and Remediation Platform

### Master PRD and Coding-Agent Execution Specification

---

## 1. Mission

Build **Sentinel**, an AI-powered incident investigation and remediation platform for distributed software systems.

Sentinel should behave like an AI production engineer / SRE.

When an application experiences an incident such as elevated latency, increased error rates, unhealthy Kubernetes pods, a failed deployment, or a downstream service failure, Sentinel should:

1. Detect or receive the incident.
2. Understand which services are affected.
3. Collect relevant logs, metrics, traces, deployment information, Kubernetes state, source-code changes, and documentation.
4. Generate competing root-cause hypotheses.
5. Select and call diagnostic tools to test those hypotheses.
6. Identify the most likely root cause.
7. Present the evidence supporting the diagnosis.
8. Recommend an appropriate remediation.
9. Optionally create artifacts such as GitHub issues or pull requests.
10. Require human approval before performing actions that modify running infrastructure.
11. Verify that the system recovered after an approved remediation.
12. Record the entire investigation for observability and evaluation.

Sentinel is **not** primarily a chatbot, source-code reviewer, generic RAG app, or monitoring dashboard.

The defining workflow is:

```text
Production symptom
      ↓
Incident
      ↓
Evidence collection
      ↓
Hypothesis generation
      ↓
Autonomous investigation
      ↓
Root-cause diagnosis
      ↓
Recommended remediation
      ↓
Human approval
      ↓
Optional action
      ↓
Recovery verification
```

The finished system should be technically substantial enough to demonstrate competency in:

- applied AI engineering
- AI agents
- model tool use
- context engineering
- AI evaluations
- distributed systems
- observability
- backend engineering
- Kubernetes
- Docker
- AWS
- Terraform
- CI/CD
- PostgreSQL
- Redis
- OpenTelemetry
- GitHub integrations
- production safety and permissions

The project is intended to become a major portfolio project for Forward Deployed Software Engineer, Applied AI Engineer, AI Engineer, backend SWE, and infrastructure-oriented SWE recruiting.

---

# 2. Primary Design Constraint

The primary developer plans to use coding agents to write most implementation code.

Therefore:

**The coding agent should perform implementation autonomously while forcing human involvement at important architectural, safety, credential, and learning checkpoints.**

Do not ask for human confirmation for ordinary coding decisions.

Do ask for human involvement when:

- architecture materially changes
- an external credential is required
- AWS resources are about to be created
- infrastructure-changing agent permissions are being enabled
- a security-sensitive decision must be made
- the project reaches one of the explicit Human Checkpoints defined below

The developer must be able to explain the resulting architecture in an interview.

Therefore, every major subsystem must have documentation explaining:

- why it exists
- how it works
- major alternatives considered
- failure modes
- important tradeoffs
- how to test it
- what a developer should understand before modifying it

---

# 3. Cost Constraint

Sentinel must be **local-first**.

Normal development must not require continuously running paid cloud infrastructure.

The primary development environment should run on a Mac using:

```text
Docker
+
kind
+
local Kubernetes
+
local observability stack
+
local PostgreSQL
+
local Redis
```

Normal local infrastructure cost:

```text
$0
```

The only expected recurring development cost is LLM API usage.

LLM usage must therefore be observable and budget-aware.

Every agent run should record:

- model
- prompt tokens
- completion tokens
- approximate cost
- latency
- number of tool calls
- investigation outcome

Cloud infrastructure comes later.

AWS must be supported through Terraform, but AWS deployments should be **ephemeral**:

```text
terraform apply
↓
deploy
↓
validate
↓
run evaluation/demo
↓
terraform destroy
```

Never architect the system around an always-running paid EKS cluster.

Do not provision expensive managed services unless there is a clear requirement.

---

# 4. Target Application

The developer does not own a production application large enough to test Sentinel against.

Use the **official OpenTelemetry Demo application** as the primary target environment.

Do not claim any OpenTelemetry Demo code as original Sentinel work.

Treat it as an external production-like system that Sentinel monitors and investigates.

The OpenTelemetry Demo should be pinned to a known upstream version or commit so tests remain reproducible.

Prefer its currently supported official installation method.

Do not vendor its entire source tree into Sentinel unless necessary.

Preferred structure:

```text
Sentinel repository
      │
      ├── Sentinel application
      │
      ├── infrastructure
      │
      ├── evaluation suite
      │
      └── bootstrap scripts
             ↓
      install/pull pinned
      OpenTelemetry Demo
```

Sentinel should eventually support arbitrary compatible environments, but the OpenTelemetry Demo is the reference implementation.

---

# 5. Product Experience

There are three primary ways users should interact with Sentinel.

## 5.1 Dashboard

Provide a web application.

Primary navigation:

```text
Dashboard
Incidents
Services
Evaluations
System
```

Dashboard should display approximately:

```text
SENTINEL

System Health                     96%

Active Incidents                    2
Resolved Today                      8
Diagnosis Accuracy                87%
Avg Investigation Time           9.1s
Avg Investigation Cost          $0.03
```

Below that:

```text
ACTIVE INCIDENTS

INC-1042
checkout-service
P99 latency regression
Started 7 minutes ago
Investigating...

INC-1041
payment-service
Error rate 11.8%
Root cause identified
```

Exact UI design is flexible.

The interface should look like a credible developer infrastructure product rather than a student dashboard.

---

# 6. Incident Detail Experience

An incident should have:

```text
INCIDENT #1042

Checkout Service Latency Regression

Severity
High

Started
14:03 UTC

Baseline P99
180ms

Current P99
4.2s

Status
Root cause identified
```

Then:

## Root Cause

Example:

```text
Redis connection pool exhaustion caused by deployment v1.42.

Confidence: 92%
```

## Evidence

Example:

```text
✓ request latency increased 81 seconds after deployment v1.42

✓ Redis active connections reached configured maximum

✓ 83% of degraded traces spend >2s waiting for Redis

✓ commit 9fa812 introduced per-item Redis lookups

✓ database latency remained within normal baseline
```

## Hypotheses

Example:

```text
Redis contention           92%
CPU saturation              4%
Database latency            3%
Downstream failure          1%
```

## Recommended Remediation

Example:

```text
Rollback checkout-service from v1.42 to v1.41.

Expected result:
Redis connection pressure should return to baseline.
```

Buttons:

```text
View Evidence

Ask Sentinel

Create GitHub Issue

Generate Fix

Approve Rollback
```

Only display actions that are currently implemented and safe.

---

# 7. Incident Chat

Each incident should support a conversational interface.

Example interaction:

```text
USER
Why do you think Redis caused this?

SENTINEL
83% of degraded request traces spend more than two seconds
waiting for a Redis connection.

This behavior began immediately following deployment v1.42.

Database and downstream-service latency remained within
their normal ranges during the same interval.
```

User:

```text
What changed in v1.42?
```

Sentinel should retrieve the relevant deployment and source-code diff before responding.

Later:

```text
Can you fix it?
```

Sentinel may propose:

```text
I can create a patch that batches the repeated Redis reads
and open a draft pull request.

This would not modify the running environment.

[Create Draft PR]
```

Conversation must remain scoped to the incident's evidence and system context.

---

# 8. Core Technical Architecture

Target conceptual architecture:

```text
                        ┌─────────────────┐
                        │    Next.js      │
                        │       UI        │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │     FastAPI     │
                        │      API        │
                        └────────┬────────┘
                                 │
                                 ▼
                   ┌──────────────────────────┐
                   │ Sentinel Orchestrator    │
                   │                          │
                   │ Context Builder          │
                   │ Investigation Agent      │
                   │ Hypothesis Manager       │
                   │ Policy Engine            │
                   │ Remediation Planner      │
                   └────────────┬─────────────┘
                                │
             ┌──────────────────┼───────────────────┐
             │                  │                   │
             ▼                  ▼                   ▼
         Metrics              Logs               Traces
        Prometheus       OpenSearch/Loki      Jaeger/Tempo
             │                  │                   │
             └──────────────────┼───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
                Kubernetes                GitHub
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                         Agent Tool Layer
                                │
                                ▼
                        LLM Provider Layer
```

The specific telemetry backend should match what the pinned OpenTelemetry Demo exposes.

Implement adapters rather than hard-coupling the application to one backend:

```text
MetricsProvider
TraceProvider
LogProvider
KubernetesProvider
SourceControlProvider
```

This allows changing Jaeger → Tempo or OpenSearch → Loki without rewriting the agent.

---

# 9. Required Technology Stack

Use these unless a compelling technical reason exists not to.

## Frontend

```text
Next.js
React
TypeScript
```

Use a professional component library if helpful, but do not turn frontend styling into the main project.

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

Prefer Python 3.12+ or current stable equivalent.

## Persistent State

```text
PostgreSQL
```

Use PostgreSQL for:

- incidents
- hypotheses
- evidence
- tool calls
- agent runs
- remediation proposals
- evaluations
- audit events

## Ephemeral State / Cache

```text
Redis
```

Use Redis where justified for:

- caching telemetry queries
- temporary investigation state
- rate limiting
- job coordination
- streaming progress if appropriate

Do not use Redis merely to claim Redis experience.

## AI

Support a provider abstraction.

Initial implementation may use one high-quality model provider.

The architecture should make model switching possible without rewriting business logic.

Avoid deep dependency on LangChain or similar orchestration frameworks initially.

Prefer direct model SDKs plus explicit application-controlled agent logic.

We want to understand:

```text
messages
tools
context
state
policies
termination
evaluation
```

rather than hiding these behind a large framework.

---

# 10. Agent Architecture

Start with **one investigation agent**.

Do not build a multi-agent system unless evaluation data later demonstrates a concrete improvement.

Initial agent:

```text
Incident
   ↓
Context Builder
   ↓
Investigation Agent
   ↓
Diagnostic Tools
   ↓
Evidence
   ↓
Hypotheses
   ↓
More Tools if needed
   ↓
Diagnosis
   ↓
Remediation Plan
```

Avoid:

```text
Manager Agent
Planning Agent
Logs Agent
Metrics Agent
GitHub Agent
Critic Agent
Security Agent
etc.
```

unless these are later justified empirically.

Complexity must be earned through evaluation results.

---

# 11. Investigation Loop

Implement an explicit agent loop.

Conceptually:

```text
receive incident

identify:
    service
    symptom
    relevant time window

gather baseline context

generate hypotheses

while confidence insufficient
      AND useful investigation actions remain
      AND tool-call budget not exceeded:

    choose highest-information diagnostic action

    call tool

    normalize evidence

    update hypotheses

produce:
    root cause
    confidence
    evidence
    competing hypotheses
    remediation recommendation
```

The agent should reason using **structured evidence**, not giant blobs of raw logs.

---

# 12. Deterministic Analysis Before LLM Reasoning

Do not send all available telemetry directly to the LLM.

Bad architecture:

```text
10MB logs
+
all traces
+
all metrics
↓
LLM
↓
answer
```

Preferred:

```text
Raw telemetry
     ↓
deterministic filtering
     ↓
aggregation
     ↓
anomaly / correlation extraction
     ↓
structured evidence
     ↓
LLM reasoning
```

Examples:

Instead of thousands of traces:

```text
checkout-service

baseline P99: 182ms
incident P99: 4117ms

slow trace commonality:
Redis span >2s in 83% of degraded traces
```

Instead of thousands of duplicate logs:

```text
ERROR GROUP

RedisConnectionTimeout
count: 427
first seen: 14:04:21
baseline count: 0
```

The application should perform as much cheap deterministic reduction as practical before model inference.

---

# 13. Diagnostic Tools

Create strongly typed tool interfaces.

Initial tools should include:

```text
query_metrics
query_logs
query_traces

get_service_dependencies

get_kubernetes_pods
get_kubernetes_events
get_resource_usage
get_deployment_history

get_recent_commits
get_commit_diff
search_repository

get_runbook
```

Tool responses must return structured objects.

Example conceptual tool call:

```json
{
  "tool": "query_metrics",
  "arguments": {
    "service": "checkout-service",
    "metric": "request_latency",
    "start_time": "...",
    "end_time": "..."
  }
}
```

Tool result:

```json
{
  "service": "checkout-service",
  "metric": "request_latency",
  "baseline_p99_ms": 182,
  "incident_p99_ms": 4117,
  "change_percent": 2162
}
```

Agent tools should not return giant unprocessed payloads unless requested.

---

# 14. MCP

Sentinel should eventually expose or consume diagnostic capabilities through **Model Context Protocol** where appropriate.

Do not make MCP a prerequisite for MVP investigation logic.

Recommended sequence:

```text
Python native tool interface
↓
stable tool contracts
↓
MCP transport/adapters
```

Potential logical MCP groups:

```text
sentinel-observability
sentinel-kubernetes
sentinel-github
```

A single MCP server is acceptable initially.

The important part is demonstrating real tool interoperability, not maximizing the number of MCP servers.

---

# 15. Incident Detection

MVP should support manual incident creation.

Example:

```text
POST /incidents

service=checkout-service
symptom=p99 latency > 2 seconds
time window=last 10 minutes
```

Next phase:

Integrate Prometheus Alertmanager or an equivalent alert source.

Flow:

```text
Prometheus detects threshold
↓
Alertmanager
↓
Sentinel webhook
↓
Incident created
↓
Investigation starts
```

Do not spend significant effort creating a custom monitoring system.

Sentinel consumes monitoring data. It does not replace Prometheus.

---

# 16. Incident State Model

Every incident should have approximately:

```text
id

service

title

severity

status

created_at

detected_at

resolved_at

symptom

trigger_source

time_window

current_diagnosis

diagnosis_confidence

recommended_remediation
```

Potential statuses:

```text
detected
investigating
diagnosed
awaiting_approval
remediating
verifying
resolved
failed
```

---

# 17. Evidence Model

Evidence must be first-class data.

Examples:

```text
metric
log
trace
deployment
kubernetes
source_code
runbook
```

Each evidence object should include:

```text
id
incident_id
type
source
timestamp
summary
structured_payload
relevance_score
```

Sentinel's diagnosis should reference specific evidence IDs.

This gives the UI traceability.

---

# 18. Hypothesis Model

Represent hypotheses explicitly.

Example:

```json
{
  "name": "Redis connection pool exhaustion",
  "probability": 0.74,
  "supporting_evidence": ["ev_32", "ev_41"],
  "contradicting_evidence": ["ev_55"],
  "status": "active"
}
```

The agent should update hypotheses as evidence arrives.

Do not present numerical probabilities as scientifically calibrated probabilities.

Treat them as model confidence/ranking indicators.

---

# 19. Tool Call Auditability

Every agent tool call should be persisted.

Record:

```text
agent_run_id
tool
arguments
start_time
end_time
latency
success/failure
result_summary
```

The UI should eventually support a timeline such as:

```text
14:04:20 query_metrics
14:04:21 query_logs
14:04:22 query_traces
14:04:24 get_deployment_history
14:04:25 get_commit_diff
14:04:27 diagnosis produced
```

This is essential for debugging agents.

---

# 20. Sentinel Must Observe Itself

Instrument Sentinel using OpenTelemetry.

Trace:

```text
incident investigation

├── context build
├── model call
├── query metrics
├── query logs
├── query traces
├── model call
├── GitHub lookup
└── diagnosis
```

Track:

```text
investigation latency
tool latency
LLM latency
token usage
LLM cost
tool-call count
diagnosis success
```

This makes the AI application itself observable.

---

# 21. Remediation Safety Model

Sentinel should have explicit capability tiers.

### Read-only

Allowed automatically:

```text
logs
metrics
traces
Kubernetes status
deployment history
source code
GitHub diffs
runbooks
```

### Non-production write actions

May be automatically allowed after configuration:

```text
create GitHub issue
create draft pull request
write investigation report
```

### Infrastructure-changing actions

Require human approval:

```text
rollback deployment
restart service
scale deployment
modify runtime configuration
apply patch
```

### Forbidden

Do not provide unrestricted capabilities such as:

```text
arbitrary shell
kubectl *
database deletion
IAM modification
infrastructure deletion
arbitrary Terraform apply
```

Implement a policy layer instead of relying solely on prompts.

---

# 22. Remediation Approval Flow

Example:

```text
Sentinel recommendation:

Rollback checkout-service:
v1.42 → v1.41

Reason:
Current deployment introduced repeated Redis queries.

Expected impact:
Restore connection pool utilization to baseline.

Risk:
Temporary pod restart.

[Approve]
[Reject]
```

An approved action should:

```text
execute
↓
persist audit record
↓
observe recovery
↓
compare metrics to baseline
↓
report success/failure
```

---

# 23. GitHub Integration

Integrate GitHub later in the project.

Required capabilities:

```text
retrieve recent commits
retrieve commit diffs
search code
identify deployment commit
create issue
create draft PR
```

Do not automatically merge pull requests.

A useful workflow:

```text
Incident
↓
Sentinel finds offending commit
↓
Sentinel proposes code modification
↓
user approves "Generate Fix"
↓
coding agent/LLM generates patch
↓
tests run
↓
draft PR created
```

GitHub repository credentials must come from environment variables or secure secrets.

Never commit tokens.

---

# 24. Evaluation System

The evaluation harness is a major part of Sentinel.

It is not optional.

Create reproducible incident scenarios.

Start with approximately:

```text
3 scenarios
↓
10 scenarios
↓
30+ scenarios
```

Each scenario should define:

```text
scenario ID

system state

fault

visible symptoms

ground-truth root cause

expected supporting evidence

acceptable diagnosis

acceptable remediation

unsafe actions

setup command

cleanup command
```

Example:

```json
{
  "id": "redis_pool_exhaustion",
  "service": "checkout-service",
  "root_cause": "redis_connection_pool_exhaustion",
  "expected_evidence": [
    "redis_connections_at_limit",
    "request_trace_waiting_on_redis"
  ],
  "acceptable_remediations": [
    "rollback_offending_deployment",
    "remove_excess_redis_calls"
  ],
  "unsafe_actions": [
    "delete_database",
    "restart_entire_cluster"
  ]
}
```

---

# 25. Evaluation Metrics

Track at minimum:

```text
Root Cause Accuracy

Evidence Coverage

Correct Tool Selection

Unsafe Action Rate

Average Tool Calls

Investigation Latency

LLM Cost

Remediation Correctness
```

Eventually present results like:

```text
Sentinel Evaluation Suite

Scenarios                         30

Root Cause Accuracy              87%

Evidence Coverage                91%

Unsafe Action Rate                0%

Avg Tool Calls                   6.4

Avg Investigation Time           8.7 sec

Avg Model Cost                 $0.021
```

Do not fabricate metrics.

Only publish measured numbers.

---

# 26. Configuration Experiments

The evaluation system should allow comparing different approaches.

Examples:

```text
baseline prompt

vs

structured evidence

vs

retrieval-enhanced context

vs

hypothesis-driven investigation

vs

hypothesis + verifier
```

Potential result:

```text
Baseline                     61%
Structured evidence          74%
Hypothesis-driven            83%
Verifier-enhanced            88%
```

Again, use real measurements.

This experimentation is an important AI-engineering component.

---

# 27. Fault Injection

Use existing OpenTelemetry Demo fault scenarios where possible.

Later create Sentinel-specific reproducible scenarios.

Potential categories:

```text
downstream latency

service unavailable

bad deployment

CPU saturation

memory pressure

misconfiguration

dependency timeout

increased error rate

broken feature flag

network degradation

cache failure
```

Avoid introducing a large chaos-engineering framework unless necessary.

Simple reproducible failure injection is preferable.

---

# 28. Developer CLI

Create a useful CLI or Make targets.

Examples:

```bash
make dev-up

make dev-down

make demo-up

make demo-down

make sentinel-up

make test

make eval

make eval SCENARIO=redis-timeout
```

Potential CLI:

```bash
sentinel incident create ...

sentinel investigate INC-1042

sentinel eval run

sentinel lab inject <scenario>

sentinel lab reset
```

The exact command system is flexible.

Developer experience should be simple.

---

# 29. Local Kubernetes

Use:

```text
kind
```

Normal local environment:

```text
Mac

Docker

kind Kubernetes cluster

OpenTelemetry Demo

Sentinel API

Sentinel Web

Prometheus

trace backend

log backend

PostgreSQL

Redis
```

Do not require Minikube and kind simultaneously.

Pick one.

Use kind.

---

# 30. Docker

Every Sentinel service should have a production-quality Dockerfile.

Prefer multi-stage builds where applicable.

Local development may use Docker Compose for Sentinel dependencies before full Kubernetes integration.

Do not force Kubernetes into the first working prototype.

Recommended progression:

```text
Docker Compose
↓
working Sentinel
↓
kind
↓
Kubernetes manifests / Helm
```

---

# 31. Kubernetes

Sentinel should eventually support:

```text
Deployments
Services
ConfigMaps
Secrets
Ingress where appropriate
resource requests / limits
health checks
readiness probes
```

Do not create unnecessary custom Kubernetes operators.

Use standard Kubernetes primitives.

Create minimal RBAC.

Sentinel's service account should initially be read-only.

A separate controlled permission path should exist for approved remediation actions.

---

# 32. AWS Deployment

Only implement after local functionality and evaluation work.

Use:

```text
AWS
Terraform
EKS
```

Cloud deployment should be disposable.

Desired workflow:

```bash
cd infra/terraform/aws

terraform init

terraform plan

terraform apply
```

Deploy application.

Run smoke test.

Run sample incident.

Then:

```bash
terraform destroy
```

Do not leave infrastructure running by default.

---

# 33. Terraform

Terraform should provision only infrastructure Sentinel genuinely needs.

Likely:

```text
VPC

subnets

security groups

EKS

IAM roles

container registry where necessary
```

Potential additional services can be evaluated later.

Do not introduce expensive managed databases simply because they exist.

For portfolio deployment, PostgreSQL/Redis may run inside Kubernetes if appropriate.

For a hypothetical production architecture, documentation may explain how RDS and ElastiCache would replace them.

Distinguish:

```text
actual project deployment
```

from:

```text
recommended enterprise architecture
```

---

# 34. GitHub Actions

CI should include:

```text
frontend lint

backend lint

unit tests

integration tests

type checking

Docker build validation

Terraform formatting/validation

security scanning if practical
```

Do not run expensive LLM evaluations on every commit.

Use separate manually-triggered or scheduled evaluation workflows.

---

# 35. Repository Structure

Target approximately:

```text
sentinel/
│
├── apps/
│   └── web/
│
├── services/
│   └── api/
│
├── sentinel/
│   ├── agent/
│   │   ├── runtime/
│   │   ├── context/
│   │   ├── hypotheses/
│   │   ├── policies/
│   │   └── remediation/
│   │
│   ├── tools/
│   │   ├── metrics/
│   │   ├── logs/
│   │   ├── traces/
│   │   ├── kubernetes/
│   │   └── github/
│   │
│   ├── providers/
│   │   └── llm/
│   │
│   └── models/
│
├── mcp/
│
├── evals/
│   ├── scenarios/
│   ├── graders/
│   ├── runners/
│   └── results/
│
├── infra/
│   ├── docker/
│   ├── kind/
│   ├── kubernetes/
│   └── terraform/
│       └── aws/
│
├── scripts/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/
│   ├── architecture.md
│   ├── decisions/
│   ├── learning/
│   ├── runbooks/
│   └── diagrams/
│
├── .github/
│   └── workflows/
│
├── AGENTS.md
├── README.md
├── Makefile
└── .env.example
```

Modify where justified.

Do not preserve structure merely for aesthetics.

---

# 36. Architecture Decision Records

Any important architecture choice requires an ADR.

Examples:

```text
001-open-telemetry-demo.md

002-local-first-development.md

003-agent-tool-contracts.md

004-direct-model-sdk.md

005-context-selection-strategy.md

006-evaluation-methodology.md

007-kubernetes-permissions.md

008-aws-eks-deployment.md
```

ADR structure:

```text
Context

Decision

Alternatives

Why this option

Consequences

Future reconsideration
```

---

# 37. Learning Documentation

The project is intentionally being used to learn several technologies.

Maintain:

```text
docs/learning/
```

Suggested documents:

```text
kubernetes.md

terraform.md

opentelemetry.md

distributed-tracing.md

prometheus.md

agent-tool-calling.md

context-engineering.md

agent-evals.md

mcp.md

aws-eks.md
```

Coding agents may produce first drafts.

However, after each Human Checkpoint, generate a section:

```text
Questions the developer should be able to answer
```

Examples:

```text
Why are traces different from logs?

Why use OpenTelemetry?

What does the Collector do?

What does Kubernetes give us that Docker Compose does not?

Why do we use Redis here?

What happens if the agent selects the wrong tool?

Why not send every log line to the LLM?

Why does remediation require a policy layer?
```

---

# 38. Human Checkpoints

## Checkpoint 1: Architecture

After basic repository setup and OpenTelemetry Demo integration, stop and provide:

```text
architecture diagram

service descriptions

data flow

local setup

technology rationale

top five architecture decisions

questions developer should understand
```

Wait for human acknowledgment before major agent implementation.

---

## Checkpoint 2: First Successful Investigation

After Sentinel can correctly diagnose one real injected incident, stop.

Provide:

```text
incident

symptom

agent investigation

tool calls

root cause

why diagnosis was correct

relevant code

how to reproduce manually

five technical questions
```

The human should manually run the scenario.

---

## Checkpoint 3: Write Permissions

Before enabling:

```text
Kubernetes rollback

restart

configuration modification

GitHub write operations
```

stop and explain:

```text
permissions

RBAC

threat model

approval mechanism

audit design
```

Require acknowledgment.

---

## Checkpoint 4: AWS

Before running any Terraform that creates AWS resources:

Stop.

Produce:

```text
terraform plan summary

resources created

estimated cost drivers

destroy procedure

credentials required

security implications
```

Do not run `terraform apply` without explicit approval.

---

## Checkpoint 5: Final Portfolio Review

Before declaring project portfolio-ready:

Present:

```text
architecture

demo flow

evaluation metrics

cloud deployment

major engineering tradeoffs

known limitations

resume bullets

likely interview questions
```

---

# 39. Implementation Phases

## Phase 0 — Bootstrap

Goal:

Run the OpenTelemetry Demo locally and understand the telemetry environment.

Deliver:

```text
reproducible setup

pinned upstream version

bootstrap script

README setup instructions

basic architecture documentation
```

No AI required.

---

## Phase 1 — Observability Tool Layer

Implement tools capable of:

```text
querying metrics

querying logs

querying traces

mapping service dependencies

reading Kubernetes state
```

Acceptance criteria:

A Python script can answer:

```text
What services exist?

Which service currently has the highest request latency?

Show recent errors for service X.

Show a slow trace for service X.

Show current pods for service X.
```

No agent required yet.

---

## Phase 2 — First AI Investigation

Implement one agent.

Input:

```text
service

symptom

time window
```

Agent may call diagnostic tools.

Output:

```text
likely root cause

confidence

evidence

recommended remediation
```

Get one incident working end-to-end.

This is the most important early milestone.

---

## Phase 3 — Persistence and API

Add:

```text
FastAPI

PostgreSQL

Redis

incident models

agent-run models

evidence models

tool-call models
```

Expose clean APIs.

---

## Phase 4 — Web Product

Create Next.js dashboard.

Pages:

```text
/dashboard

/incidents

/incidents/[id]

/services

/evals
```

Support live investigation updates.

SSE is acceptable and likely preferable to unnecessary WebSocket complexity.

---

## Phase 5 — Evaluation Harness

Implement scenario definition format.

Implement automatic:

```text
setup

incident trigger

Sentinel run

grading

cleanup
```

Start with three incidents.

Expand to ten.

Target 30+ eventually.

---

## Phase 6 — GitHub Context

Add:

```text
deployment commit mapping

recent commits

diff inspection

source search
```

Allow code changes to become evidence.

---

## Phase 7 — Remediation

Add:

```text
recommended actions

approval workflow

audit trail

controlled Kubernetes actions

post-remediation verification
```

Do not add unrestricted shell access.

---

## Phase 8 — MCP

Expose stable Sentinel tool contracts through MCP.

Verify another compatible client can invoke a subset of Sentinel tools.

---

## Phase 9 — AWS / Terraform

Add ephemeral EKS deployment.

Verify:

```text
terraform apply

deployment succeeds

Sentinel functions

sample incident resolves

terraform destroy
```

---

## Phase 10 — Portfolio Quality

Produce:

```text
excellent README

architecture diagram

animated GIF/video demo

evaluation results

benchmark tables

screenshots

one-command local setup

clean GitHub history

clear documentation
```

---

# 40. README Requirements

README should immediately communicate:

```text
What Sentinel is

Why it exists

Demo

Architecture

How investigation works

Example incident

Evaluation results

Local setup

AWS deployment

Safety model

Technology stack
```

An engineer should understand why the project is interesting within approximately 30 seconds.

A deeper reader should find enough documentation to inspect architectural decisions.

---

# 41. Example README Demo Story

Use one strong incident.

Example:

```text
1. checkout-service p99 increases from 180ms → 4.2s.

2. Prometheus fires an alert.

3. Sentinel starts an investigation.

4. Sentinel identifies 83% of degraded traces waiting on Redis.

5. Sentinel finds Redis connection saturation.

6. Sentinel observes that the issue began immediately following v1.42.

7. Sentinel retrieves the deployment's Git diff.

8. Sentinel identifies repeated Redis calls introduced in the release.

9. Sentinel recommends rollback.

10. User approves.

11. Sentinel performs controlled rollback.

12. P99 returns to 190ms.

13. Sentinel verifies recovery and closes the incident.
```

This should eventually be reproducible.

---

# 42. Explicit Non-Goals

Do not turn Sentinel into:

```text
generic chatbot

ChatGPT clone

generic RAG app

source code autocomplete

CodeRabbit clone

Datadog replacement

Prometheus replacement

full observability vendor

giant multi-agent system

custom Kubernetes operator

huge microservice architecture
```

The core product is:

> An AI engineer that investigates production incidents using real system evidence.

Stay focused.

---

# 43. Anti-Overengineering Rules

Before adding a technology, answer:

```text
What specific problem does this solve?

Could the existing architecture solve it?

Does this improve the actual product?

Does this improve an evaluation result?

Does this create meaningful learning value?
```

If not, do not add it.

Do not add technologies only to expand the resume stack.

The project already provides enough technical breadth.

Depth matters more.

---

# 44. Coding-Agent Rules

All coding agents working on this repository must follow these rules.

### Rule 1

Do not silently alter architecture.

Major architecture changes require an ADR.

### Rule 2

Do not introduce frameworks when standard libraries or existing dependencies are adequate.

### Rule 3

Every major feature needs tests.

### Rule 4

Every agent behavior eventually requires an evaluation.

### Rule 5

Every tool call must be observable.

### Rule 6

Every infrastructure-changing action must pass through the policy layer.

### Rule 7

Never hide failures behind endless retry logic.

### Rule 8

Do not fabricate benchmark or evaluation results.

### Rule 9

Never commit secrets.

### Rule 10

Prefer simple explicit implementation over magical abstractions.

### Rule 11

Do not prematurely build multi-agent orchestration.

### Rule 12

Do not provision paid cloud infrastructure until requested.

### Rule 13

Keep local setup functional throughout development.

### Rule 14

After each major milestone, update documentation.

### Rule 15

Before marking a task complete, run the relevant tests and demonstrate the behavior.

---

# 45. AGENTS.md

Create an `AGENTS.md` file containing the most important engineering rules from this PRD.

Coding agents should read it before making modifications.

Include at minimum:

```text
project mission

architecture principles

testing requirements

evaluation requirements

safety policy

cost constraints

dependency policy

documentation policy

human checkpoints
```

---

# 46. Testing Requirements

Use multiple levels.

### Unit

Test:

```text
tool parsing

telemetry aggregation

context construction

policy decisions

evaluation graders
```

### Integration

Test:

```text
Prometheus adapter

trace adapter

log adapter

Kubernetes adapter

PostgreSQL

Redis

GitHub adapter
```

### End-to-End

Test:

```text
inject incident
↓
detect incident
↓
investigate
↓
produce correct diagnosis
```

### AI Evaluation

Separate from deterministic tests.

LLM variability should not make ordinary CI unreliable.

---

# 47. Failure Handling

Sentinel must handle cases such as:

```text
telemetry unavailable

LLM timeout

tool timeout

malformed model output

missing Kubernetes permissions

GitHub unavailable

insufficient evidence

conflicting evidence
```

If evidence is insufficient, Sentinel should say:

```text
Unable to determine root cause with sufficient confidence.
```

Do not force a diagnosis.

---

# 48. Context Engineering

Design context intentionally.

Do not continually stuff the entire investigation history into every request.

Prefer:

```text
incident summary

current hypotheses

high-value evidence

recent tool results

relevant service metadata
```

Persist the full audit history separately.

Experiment with context strategies through evaluations.

---

# 49. Model Independence

Business logic should not depend directly on a single provider.

Conceptual interface:

```text
LLMProvider

generate_structured(...)

tool_call(...)

stream(...)
```

Provider-specific code should live behind adapters.

Initial development may target one provider.

Do not build complicated automatic model routing until justified.

---

# 50. Security

At minimum:

```text
validate external inputs

never expose secrets to browser

limit Kubernetes permissions

sanitize GitHub data

audit write actions

validate model tool arguments

enforce tool permissions outside model prompts
```

Treat model output as untrusted input.

The LLM must not be the final authority for security-sensitive operations.

---

# 51. Definition of MVP

Sentinel MVP is complete when:

```text
OpenTelemetry Demo runs locally.

Sentinel can query metrics, logs, and traces.

A real failure can be injected.

Sentinel receives an incident.

The agent autonomously chooses diagnostic tools.

Sentinel identifies the correct root cause.

The UI shows diagnosis and evidence.

The incident is persisted.

Agent cost, latency, and tool calls are recorded.

At least three scenarios run through an automated evaluation harness.
```

Nothing involving AWS is required for MVP.

---

# 52. Definition of Portfolio-Ready

Portfolio-ready requires:

```text
10+ reproducible incident scenarios

measured root-cause accuracy

measured latency and cost

GitHub code/deployment context

professional dashboard

incident chat

controlled remediation flow

human approval

Kubernetes integration

MCP integration

AWS Terraform deployment

CI/CD

strong documentation

architecture diagrams

recorded demo

clean README
```

30+ evaluation scenarios is the eventual stretch goal.

---

# 53. Desired Resume Outcome

Do not optimize implementation around specific wording, but the final project should justify approximately:

> **Sentinel | AI Incident Response Platform**  
> Python, MCP, OpenTelemetry, Kubernetes, AWS, Terraform
>
> Built an agentic incident-response platform that correlates distributed traces, logs, metrics, Kubernetes state, deployments, and source changes to autonomously diagnose failures across a production-like microservice environment.
>
> Developed a reproducible incident-evaluation harness measuring root-cause accuracy, tool selection, remediation safety, latency, and model cost across N failure scenarios, improving diagnosis accuracy from X% to Y%.

The actual numbers must be produced by the system.

Never engineer fake measurements to make these bullets possible.

---

# 54. Desired Interview Outcome

The developer should eventually be capable of explaining:

```text
Why OpenTelemetry exists.

Difference between logs, metrics, and traces.

How distributed tracing works.

How Kubernetes networking and deployments work.

How Terraform state works.

How EKS differs from local Kubernetes.

Why deterministic telemetry reduction happens before LLM inference.

How Sentinel decides which tool to call.

How context is constructed.

How AI agent evaluations are designed.

How root-cause accuracy is graded.

How model cost is measured.

Why multi-agent was not used initially.

How human approval protects dangerous operations.

How Kubernetes RBAC limits Sentinel.

How the system recovers from failed tools or models.

How Sentinel distinguishes correlation from causation.

Where the architecture would fail at enterprise scale.
```

If the developer cannot explain these, generate learning material before moving forward.

---

# 55. First Execution Instructions

Begin implementation with the following order.

### Step 1

Create repository structure and `AGENTS.md`.

### Step 2

Research the current official OpenTelemetry Demo installation process and pin a stable version.

Do not use unofficial tutorials where official documentation exists.

### Step 3

Create a reproducible local bootstrap process.

Goal:

```bash
make demo-up
```

should produce a working target environment.

### Step 4

Document:

```text
services

telemetry architecture

how metrics are queried

how logs are queried

how traces are queried
```

### Step 5

Implement the first deterministic Python telemetry tool.

Start with:

```text
query_metrics
```

Then:

```text
query_traces
query_logs
```

### Step 6

Identify one reproducible failure in the demo environment.

### Step 7

Demonstrate that the deterministic tools expose enough evidence to identify the root cause manually.

### Step 8

Stop at **Human Checkpoint 1**.

Do not begin building a large UI or AWS infrastructure before these steps work.

---

# 56. Coding-Agent Autonomy

Once a Human Checkpoint has been approved, continue implementation autonomously until the next checkpoint.

Do not repeatedly ask questions such as:

```text
Should I use SQLAlchemy?

Should I create this directory?

Should I add this test?

Should I refactor this class?
```

Make competent engineering decisions.

When ambiguity exists:

1. choose the simplest architecture consistent with this PRD
2. document the decision
3. continue

Escalate only when the choice materially changes product scope, security, cost, or architecture.

---

# 57. Progress Reporting

After each meaningful milestone, report:

```text
Completed

Files changed

How it works

Tests executed

Current architecture impact

Known limitations

Next milestone
```

Do not produce verbose reports after trivial edits.

---

# 58. Quality Bar

This project should not merely work in one canned demo.

The standard is:

```text
reproducible

observable

tested

measurable

safe

documented

understandable

technically defensible
```

Prioritize engineering substance over feature count.

A smaller Sentinel that reliably diagnoses ten difficult incidents is preferable to a massive platform that only succeeds during a scripted demo.

---

# 59. Final Product Principle

At every design decision, preserve this mental model:

> **Sentinel is an AI production engineer investigating a live distributed system.**

It should gather evidence the way an engineer would.

It should use real tools.

It should distinguish evidence from speculation.

It should know when it does not have enough information.

It should measure whether its reasoning actually works.

It should request approval before making dangerous changes.

It should verify whether its remediation solved the problem.

That is the product.
