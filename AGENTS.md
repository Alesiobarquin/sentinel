# Sentinel coding-agent instructions

Read this file before modifying the repository. It condenses `prd.md` sections
42–46 and the architecture, safety, cost, and human checkpoints they reference.
Consult the relevant PRD sections for full requirements, implementation order
(39, 55), and MVP/portfolio acceptance criteria (51–52).
Read `docs/progress.md` for recorded implementation and validation status.

## Mission and scope

- Canonical resume subtitle: **AI Incident Investigation Agent**. Use
  `Sentinel — AI Incident Investigation Agent` in resume-facing documentation and
  recommendations. Keep the repository and product name Sentinel.
- Current authorized sprint: reproducible real-telemetry scenarios, repeated AI
  evaluations, explicit abstention grading, and a fair context comparison. Keep
  fixed configurations and auditable raw results. AWS, Terraform, MCP, database
  persistence, and agent write permissions remain out of scope. Local developer
  fault setup/cleanup is authorized; never expose it through agent tools.

- Recruiter delivery, clarified by the developer on 2026-10-05: one public site
  with an interactive replay of a real investigation and a project/learning
  explanation page. Optimize for a reliable, free visitor experience. Execute
  authorized setup/publication through CLI; involve the developer for browser
  sign-in and required checkpoints. A separate public backend or permanent
  cloud lab is not required for this delivery. Preserve the guide's remaining
  scope and label completed versus planned capabilities honestly.

- Public presentation is a student portfolio, not a SaaS sales site. Use concise,
  factual language about what I built, how it works, tests, limitations, and
  lessons. Avoid slogans, dramatic headlines, and product pitches. A small
  project logo is allowed. Explain the purpose, ownership, and result in plain
  language first. Present the site as an engineering write-up: concrete
  experiments, failures, changes, code, tests, and unresolved questions. Avoid
  headline statistics and generic feature-card layouts. Keep measurements with
  their experiment and limitations. Be honest about AI coding assistance and
  external software; do not invent personal learning or unaided authorship.

- Build an AI production engineer that investigates distributed-system incidents
  using real telemetry, tests hypotheses, cites evidence, recommends remediation,
  and verifies recovery after approved actions.
- Prioritize engineering depth and measured reliability over resume keywords.
  Do not expand into a generic chatbot/RAG app, code autocomplete/review product,
  monitoring replacement, full observability vendor, giant multi-agent system,
  custom Kubernetes operator, or unnecessary microservice architecture.
- Use the official OpenTelemetry Demo as a pinned, reproducible external target;
  do not claim its code as original Sentinel work.

## Architecture and dependencies

- Never silently change architecture. Major changes require human involvement
  and an ADR in `docs/decisions/` covering context, decision, alternatives,
  rationale, consequences, and when to reconsider.
- Prefer simple, explicit code, standard libraries, and existing dependencies.
  Before adding technology, explain the problem, whether existing architecture
  can solve it, and its product, evaluation, or meaningful learning value.
- Default stack: Next.js/React/TypeScript; Python/FastAPI/Pydantic;
  SQLAlchemy/Alembic/PostgreSQL; Redis only where justified.
- Start with one investigation agent, direct model SDKs, and an explicit loop.
  Additional agents require demonstrated evaluation gains. Keep model providers
  and telemetry backends behind adapters; stabilize native tools before MCP.
- Reduce telemetry deterministically before LLM inference. Use typed tools,
  structured evidence, explicit hypotheses, evidence IDs, and bounded budgets.
  Keep full audit history outside the selected model context.
- Follow the phased plan: establish local telemetry tools and one real diagnosis
  before building a large UI or AWS infrastructure.

## Testing, evaluation, and observability

- Every major feature needs tests. Before declaring implementation complete,
  run relevant tests and demonstrate the behavior; report limitations honestly.
- Unit tests: tool parsing, telemetry aggregation, context construction, policy
  decisions, and evaluation graders.
- Integration tests: metrics/Prometheus, trace, log, Kubernetes, PostgreSQL,
  Redis, and GitHub adapters as implemented.
- End-to-end tests: inject a real incident, detect/receive it, investigate it,
  and produce the correct diagnosis.
- Evaluate every agent behavior with reproducible scenarios, ground truth,
  expected evidence, acceptable remediation, unsafe actions, setup, and cleanup.
  Start with three scenarios; reach ten for portfolio readiness; 30+ is a stretch.
- Keep AI evaluations separate from deterministic tests so model variability
  cannot destabilize ordinary CI. Run costly evaluations separately.
- Persist every tool call with arguments, timing, latency, outcome, and result
  summary. Instrument Sentinel itself with OpenTelemetry. Record model, tokens,
  approximate cost, latency, tool-call count, and investigation outcome.
- Publish only measured results. Never fabricate benchmark/evaluation numbers
  or treat PRD example values as results. Confidence scores are ranking indicators,
  not calibrated probabilities.
- Never hide failures behind endless retries. Surface tool/model failures and
  insufficient or conflicting evidence; do not force a diagnosis.

## Safety and cost

- Enforce tool permissions in application policy, outside model prompts. Treat
  model output and external data as untrusted; validate inputs and tool arguments.
- Start with read-only Kubernetes RBAC. Sentinel may perform read-only diagnosis
  automatically; non-production writes require configuration and checkpoint 3.
- Every infrastructure-changing remediation requires policy checks and human
  approval, followed by an audit record and recovery verification against baseline.
- Sentinel's tool layer must not expose arbitrary shell, unrestricted `kubectl`,
  database deletion, IAM modification, infrastructure deletion, or unrestricted
  Terraform apply. Never automatically merge PRs.
- Never commit secrets or expose them to the browser. Use environment variables
  or secure secrets; involve the human when external credentials are required.
- Keep local setup functional and reproducible. Use Docker/Compose as appropriate,
  then kind; do not require both kind and Minikube.
- Normal infrastructure development must remain free and local. Track and budget
  LLM usage. Never provision paid cloud infrastructure until explicitly requested.
  AWS comes after local functionality and evaluations; deployments must be
  ephemeral with documented cleanup, not an always-running paid EKS cluster.

## Documentation and human checkpoints

- Update documentation after major milestones. Explain each major subsystem's
  purpose, operation, alternatives, failure modes, tradeoffs, testing, and what
  a developer needs to understand before modifying it. Maintain learning material
  in `docs/learning/`, including questions the developer should be able to answer.
- Work autonomously on ordinary coding decisions within approved scope. Escalate
  material changes to scope, architecture, security, or cost. After an approved
  checkpoint, continue until the next one; see PRD section 38 for full deliverables.
- **Checkpoint 1 — Architecture:** after repository/demo setup and deterministic
  diagnostic evidence, present architecture, services, data flow, local setup,
  rationale, top five decisions, and learning questions. Wait for acknowledgment
  before major agent implementation.
- **Checkpoint 2 — First investigation:** stop after diagnosing one real injected
  incident. Explain evidence, tools, root cause, relevant code, manual reproduction,
  and five technical questions; the developer should run the scenario manually.
- **Checkpoint 3 — Write permissions:** before enabling Kubernetes rollback,
  restart/configuration changes, or GitHub writes, explain permissions, RBAC,
  threat model, approval mechanism, and auditing; require acknowledgment.
- **Checkpoint 4 — AWS:** before creating resources, present the Terraform plan,
  resources, cost drivers, destroy procedure, credentials, and security implications.
  Do not run `terraform apply` without explicit approval.
- **Checkpoint 5 — Portfolio review:** before declaring portfolio readiness,
  present architecture, demo flow, measured evaluations, cloud deployment,
  tradeoffs, limitations, defensible resume bullets, and interview questions.
