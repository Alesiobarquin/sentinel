# Recruiter site: operation and maintenance

The accepted delivery is one static Next.js/React/TypeScript site with a real
investigation replay and explanatory project page. It uses the prescribed
frontend stack. Playwright is a development dependency for testing navigation,
recorded interactions, direct routes, resource requests, and responsive layouts.
No UI framework, chart library, public backend, or hosting account was added.

## Purpose and data flow

`apps/web/src/lib/replay.ts` imports the reviewed public recording. Server
components generate landing/project HTML at build time. Client components
control playback, evidence selection, and architecture details in the browser.
The static export includes original decision reasons and concise hypotheses;
private model reasoning/SDK envelopes are not published. It makes no inference
or telemetry requests when browsed. Model credentials remain local.

The Python exporter reads completed run/audit/evidence files and the associated
exercise report. It requires an accepted causal review with the acknowledged
checkpoint, binds the review to source-record hashes, revalidates decisions and
prior successful citations, verifies recorded usage/counts, and projects a field
allowlist. Nested attributes, private endpoints, filesystem paths, SDK responses,
and arbitrary extra fields are excluded. Selected text is screened for common
credential patterns, and rendered as text rather than HTML.

This export is intentionally scoped to the reviewed payment example. New kinds
of evidence or source paths need explicit publication schemas and review.
Pattern screening does not replace privacy review of a new recording. This
sample contains synthetic demo traffic; source excerpts are attributed to the
external OpenTelemetry application. Full private artifacts stay in `var/`.

## Local development and checks

From the repository root:

```bash
make setup
make check
uv run python scripts/export_replay.py --check apps/web/public/investigation.json
cd apps/web
npm ci
npx playwright install chromium
npm run typecheck
npm run build
npm test
npm run preview
```

Preview: `http://127.0.0.1:4173/sentinel/`. The standard-library preview server
serves only the export, with the actual repository prefix and useful 404 page.
Tests also start it automatically. Browser tests run on desktop 1440×1000 and
mobile 390×844 Chromium. They do not establish support in every browser.
Local screenshots under `var/site-qa/` were inspected separately.

For development, `npm run dev` starts Next.js on loopback; visit
`http://127.0.0.1:3000/sentinel/`. Static export has no request-time server APIs,
server actions, or dynamic telemetry connection. Do not add such assumptions to
the public viewer. The route base and plain asset/download URLs include `/sentinel`.

The sharing preview is code-native SVG rendered to PNG. After modifying
`public/social.svg`, run `npm run social:build` with the installed Chromium.

## Publishing another reviewed recording

Do not convert a failed or inconclusive run into a showcase. Inspect causality,
coverage, cleanup, privacy, and the raw audit before preparing a review. The
current review is `docs/validation/payment-replay-review.json`; its hash mapping
binds it to the retained records. Export to a new path so existing data cannot be
silently overwritten:

```bash
uv run python scripts/export_replay.py \
  --run var/investigations/ACTUAL_RUN_ID \
  --exercise var/first-investigation/ACTUAL_EXERCISE_DIRECTORY \
  --review docs/validation/REVIEW.json \
  --output var/REVIEWED_PUBLIC_RECORD.json
```

Compare the new record with the source artifacts and review its public diff.
Update `public/investigation.json`, the case study, curated labels, measured
validation, and the sharing preview together. The current viewer deliberately
describes one known payment case rather than pretending to support all incidents.

## CI and deployment

The [workflow](../.github/workflows/ci.yml) runs Python checks on 3.12/3.14 and
validates, type-checks, builds, and browser-tests the public site. Only successful
main-branch runs deploy. Pull requests have no deployment job. Checkout does not
retain Git credentials; only the deploy job gets Pages write/OIDC permissions.
These are developer publication permissions, not investigation-agent tools.

Pages is configured for workflow builds. The deploy artifact contains only
`apps/web/out`, never repository-wide private files. `output: export`,
`basePath: /sentinel`, and trailing-slash routes are fixed in Next.js config.
Standard public-repository Actions runners and Pages provide the free hosting
path within their quotas; no model credits are used by visits.

To remove public hosting, disable/delete Pages through repository settings or
`gh api --method DELETE repos/Alesiobarquin/sentinel/pages`. To restore an earlier
release, revert its source commit through normal Git review and let CI redeploy.
No cloud lab, database account, payment card, or paid cluster needs cleanup.

## Failure modes and modification questions

A malformed/unreviewed recording fails export; unselected public fields or
inconsistent usage/citations fail validation. Build/type/browser failures block
deployment. Incorrect base paths can break direct links, downloads, or Next.js
assets even when local development looks correct; test the exported site.
Context reduction can omit evidence, and a successful read does not prove full
health. Recorded data is immutable historical evidence, not a current incident.

Before modifying the viewer, explain:

1. Why is the public replay different from full local audit history?
2. Which fields reach browser JavaScript, and how are publication decisions made?
3. Why do hypotheses cite only evidence available before their decision?
4. Why can a static Next.js export work without Python running on Pages?
5. Which tests protect direct routes, mobile interaction, and the real data story?

See [ADR 009](decisions/009-recruiter-demo-hosting.md),
[the causal review](checkpoints/02-first-investigation.md), and
[the original architecture](architecture.md).
