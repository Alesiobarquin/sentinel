# ADR 009: inexpensive public recruiter delivery

**Status: accepted, implemented, and publicly verified on October 5, 2026.**

Prepared October 5, 2026 and revised after the developer requested one public
demo plus an explanatory page, with CLI execution and browser sign-in handoffs.
The authenticated GitHub CLI makes Pages the simplest free publication path.
See the [cost comparison and execution plan](../recruiter-launch-plan.md).

## Context

The complete incident target has 28 Compose services and substantially exceeds
the resources of a small free web service. Public recruiter access should be
reliable without requiring the developer's computer to remain available or
funding continuous telemetry generation and inference. The PRD still requires
the full operator product and a disposable AWS/Terraform/EKS demonstration.
The first correct live AI investigation and sampled recovery are verified;
the developer acknowledged checkpoint 2 on October 5, 2026.

## Decision

Deliver one static Next.js/React website on GitHub Pages. Include an interactive
investigation replay and a project case study describing original work,
architecture, validation, tradeoffs, limitations, and learning. Use sanitized,
provenance-preserving exports of actual investigations. Publish through the
existing authenticated GitHub CLI and GitHub Actions. The public site requires
no backend, database account, model key, or additional hosting sign-in.

Run the full telemetry lab and model execution locally. Implement the complete
PRD operator features in their normal guide phases. Later demonstrate the
AWS/Terraform/EKS deployment temporarily, with checkpoint 4 approval and verified
cleanup. No public browsing request triggers model inference or remediation.
Recorded interactions and results are visibly identified as recordings.

## Alternatives

- Cloudflare Pages: similarly suitable for static delivery, but requires another
  hosting account/sign-in in this workspace. Retain as a hosting alternative.
- Heroku student-funded API/PostgreSQL: useful for a later public backend, but
  adds a payment card, expiring credit, and persistent resources that are not
  necessary for the clarified viewer and explanatory-page goal.
- Render Free with Neon Free PostgreSQL: useful without a payment card; cold
  starts make the static fallback important.
- Vercel Hobby: useful if the frontend requires request-time Next.js features;
  subject to personal, non-commercial use and its quotas.
- Azure student resources: useful for separate learning exercises; replacing
  EKS with AKS would change the agreed portfolio scope.
- An always-running EKS lab: retains full public infrastructure availability
  but violates the project's default cost and ephemeral-deployment constraints.

## Rationale

This solves recruiter availability with the prescribed Next.js frontend and a
selected data export, without requiring the planned FastAPI/PostgreSQL services
for static browsing. GitHub already hosts the source and provides authenticated
publication. Public evidence browsing and local investigation execution have
different resource needs. The recording shows measured engineering outcomes;
the code and reproducible local lab demonstrate the implemented pipeline.

## Consequences

The UI needs an explicit viewer mode, validated export schema, sanitization,
evidence provenance, and useful navigation failures. It must not imply recorded runs
are current incidents. Static exports do not provide request-time Next.js server
features. Repository-relative routes and asset paths need explicit verification.
The public viewer does not execute Python services or provide new inference.

This delivery does not satisfy full PRD portfolio acceptance on its own.
The implementation order, evidence requirements, agent permission review, cloud
approval, and final portfolio review remain in effect. The developer authorized
CLI execution and clarified this delivery scope on October 5. Checkpoint 2
review was completed before major web/product implementation.

The publication exporter, static frontend, and gated Actions workflow are now
implemented. Python checks passed 122 deterministic cases, and 22 desktop/mobile
browser checks passed locally and against the public Pages site. The gated
[first deployment](https://github.com/Alesiobarquin/sentinel/actions/runs/37349717998)
passed. See [site operations](../recruiter-site.md) and
[the delivery review](../checkpoints/05-recruiter-delivery.md).

## When to reconsider

Reconsider if hosting terms change, Pages cannot meet the static-site needs,
the frontend needs server rendering, or the
developer requires unsupervised live public investigations. Changes involving
cost, model credentials, write permissions, or a cloud-provider substitution
need their corresponding human review and an updated ADR.
