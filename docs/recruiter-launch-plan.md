# Sentinel recruiter launch

Updated October 5, 2026 after the developer clarified the goal and authorized
CLI execution. This replaces the earlier account-by-account hosting checklist.

## Deployment target

One public website with two connected experiences:

- **Demo:** an interactive replay of one real Sentinel investigation. A visitor
  can follow the original tool calls, hypotheses, evidence, diagnosis, and
  developer-controlled recovery. It is labeled as a recorded investigation.
- **Project:** a case study explaining the problem, original Sentinel work,
  architecture, technical choices, validation, tradeoffs, failures, limitations,
  lessons, and reproducible local commands. Link to the source and measured data.

The landing page should let a recruiter reach either experience immediately.
The product does not require recruiter sign-in or generate new model requests
while being browsed. Model credentials and the telemetry lab stay local.

## Hosting choice

Use GitHub Pages and GitHub Actions for the static Next.js/React/TypeScript site.
The GitHub CLI is already authenticated as `Alesiobarquin`, so this can be created
and published through the CLI without a second hosting-account sign-in. Published
repository: [Alesiobarquin/sentinel](https://github.com/Alesiobarquin/sentinel).
Pages is configured for workflow deployment. Verified public site:
[alesiobarquin.github.io/sentinel](https://alesiobarquin.github.io/sentinel/).

GitHub Pages supports public repositories on GitHub Free and public/private
repositories on GitHub Pro. The developer's Student Pack provides Pro while
eligible. Pages publishes static assets; model execution and Python services do
not run inside Pages. [Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages),
[Student Pack](https://education.github.com/pack).

Standard GitHub-hosted runners are free for public repositories; retained
artifacts and nonstandard runners have separate limits. Keep the deployment
small and costly AI evaluations outside ordinary CI.
[Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

Expected public hosting cost: **$0 within applicable quotas**. This excludes the
existing ChatGPT subscription and local development resources. No Heroku
subscription, external database, Azure VM, AWS cluster, domain purchase, or new
hosting account is required for this delivery. Student credits remain available
for later needs; optional domain registration can wait.

## CLI execution and human handoffs

The coding agent executes setup, tests, capture, publication checks, local
commits, repository creation, Pages configuration, deployment, and URL checks.
The developer handles browser sign-in and existing guide checkpoints. This does
not enable Sentinel's investigation agent to write to GitHub or infrastructure.

1. Verify locked dependencies, Docker, the real telemetry backends, and existing
   GitHub CLI authorization. These checks have been run.
2. Open Sentinel's supported ChatGPT login and let the developer complete browser
   consent. Completed on October 5; protected local credentials are configured.
3. Confirm available models and use an explicitly selected small account model
   for one real investigation. The available catalog includes `gpt-5.6-luna`;
   the previous default `gpt-6-luna` was unavailable. The corrected investigation
   succeeded within the existing budgets; no model upgrade was performed.
4. Preserve baseline, incident, run, and recovery artifacts. Review a successful
   diagnosis at [checkpoint 2](checkpoints/02-first-investigation.md) before major
   web/product implementation. The diagnosis and sampled recovery are verified;
   the developer acknowledged checkpoint 2 on October 5. A status string alone does not prove correctness.
5. Prepare source publication without local credentials, raw private run files,
   cached upstream source, local build output, or paid-service configuration.
   Repository creation, source push, and hosted deterministic CI are complete.
6. Build the focused Next.js viewer after the required review. Export sanitized
   real data with original evidence IDs, timestamps, model, usage, outcome, and
   coverage limits. Build the explanatory page from evidence-backed content.
   Completed: the real recording, interactive tool/evidence trail, recovery view,
   architecture explorer, lessons, limitations, and reproduction are implemented.
7. Configure Next.js static export, the repository base path, trailing-slash
   routes, and deployment through GitHub Actions. Test navigation, direct URLs,
   mobile layout, evidence links, empty/failed states, and asset paths locally.
   Completed: TypeScript/static export and all 22 desktop/mobile browser checks
   passed; screenshots were reviewed. The viewer intentionally publishes one
   successful case; failed investigations remain documented rather than replayed
   as successful diagnoses. Missing routes have a custom return path.
8. Configure Pages through `gh api` with workflow builds, publish the tested
   release, observe the hosted checks, and inspect the actual HTTPS pages.
   Completed: all first-deployment jobs passed, public endpoints returned HTTP
   200, and all 22 desktop/mobile browser checks passed against GitHub Pages.
9. Put the verified demo URL in the repository About field and README. Present
   completed capabilities and defensible resume wording with their limitations.
   Completed: About/README link the live site; the delivery review provides
   demo flow, measurements, tradeoffs, limitations, resume bullets, and questions.

[Pages REST API](https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site),
[Next.js static export](https://nextjs.org/docs/app/guides/static-exports).

## Original project scope and acceptance

This is the recruiter delivery target. The full operator architecture, remaining
PRD phases, and their acceptance criteria stay separately documented. Do not
claim a public inference service, FastAPI/PostgreSQL persistence, automatic
remediation, measured AI accuracy, or AWS deployment before those capabilities
are actually implemented and demonstrated.

The explanatory page must distinguish original Sentinel code from the pinned
external OpenTelemetry Demo. Separate deterministic tests, real telemetry
validation, a single model-produced diagnosis, and any later AI evaluation.
Retain failed runs and unknown usage instead of converting them into successes.

AWS/Terraform/EKS remains a later disposable demonstration under checkpoint 4
if pursuing the full PRD portfolio scope. It is not the target of this public
website deployment. Read [ADR 009](decisions/009-recruiter-demo-hosting.md),
[progress](progress.md), [case study](portfolio-case-study.md), and
[delivery review](checkpoints/05-recruiter-delivery.md).
