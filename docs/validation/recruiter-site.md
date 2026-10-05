# Public recruiter site validation

Validated October 5, 2026. This verifies the clarified recruiter delivery;
it does not establish general AI diagnosis accuracy or full PRD completion.

## Release and hosted checks

Initial site source: `dd3fcc1df2da81ff8b22509e5fbed8024b1f008c`.
[Actions run 37349717998](https://github.com/Alesiobarquin/sentinel/actions/runs/37349717998)
completed successfully:

- Python 3.12 and Python 3.14: 122 deterministic cases passed per environment,
  eight opt-in live skips, and compilation.
- Public recording validation, locked Node dependencies, TypeScript check,
  Next.js production static export, and all 22 browser checks.
- Static artifact upload and scoped GitHub Pages deployment.

The local recording validator also accepted the actual reviewed run
`b4e5c4bc-ad01-4fde-b147-6446762705e2` with eight evidence records.
All 129 local Markdown links checked at publication resolved. A staged scan of
42 initial-release paths found no credential-pattern or private-artifact paths.
The export uses a field allowlist and review; pattern screening alone does not
prove that arbitrary future recordings are safe to publish.

## Actual public checks

| HTTPS path under `https://alesiobarquin.github.io/sentinel/` | Observed status | Content |
| --- | --- | --- |
| `/` | 200 | Landing HTML |
| `demo/` | 200 | Investigation viewer HTML |
| `project/` | 200 | Explanatory case-study HTML |
| `investigation.json` | 200 | Reviewed public recording JSON |
| `social.png` | 200 | Sharing preview PNG |

After deployment, the same Playwright suite ran against the actual Pages host:

```bash
cd apps/web
SITE_TEST_URL=https://alesiobarquin.github.io npm test
```

All **22 checks passed in 17.1 seconds**, with retries disabled: eleven cases
each on desktop 1440×1000 and mobile 390×844 Chromium. These exercise navigation,
original tool steps, playback/reset, diagnosis citations, global-tool arguments,
deep trace links and coverage, attributed source, helper recovery, architecture
details, limitations, JSON download, overflow, browser errors, same-host resource
requests, and the custom Pages 404 return path. Requests to external model or
telemetry services were not required.

A real public landing screenshot was inspected. Its title was
`Sentinel — Evidence-driven incident investigation`; viewport and document
width were both 1440. Earlier six local screenshots covered landing, diagnosis,
and project on desktop/mobile. Logs/screenshots remain in gitignored
`var/site-tests-public.log` and `var/site-qa/`.

The repository is public and its About homepage is the verified site URL.
Pages is configured for workflow builds with HTTPS enforced. No hosting account,
payment card, database, public model credentials, or AWS resources were created.
Source excerpts remain attributed to the pinned external OpenTelemetry Demo;
third-party notices and license copies are included in the export.

## Preserved failures and limits

The first local browser run passed 17 cases and failed five. Mobile grid minimum
width created horizontal overflow and wrong tap hit-testing; an indexed desktop
contents link also had the wrong accessible name. Source fixes passed all 22
checks without force-clicks or retries. The original log is retained at
`var/site-tests.log`, and the corrected one at `var/site-tests-fixed.log`.

Chromium checks and screenshot review do not certify all browsers or a complete
accessibility audit. The site displays one real retained investigation, not a
live operator service. Recovery was performed by the developer exercise rather
than the investigation agent. The two earlier failed AI investigations, sample
coverage limits, unknown subscription credit cost, and failed OTLP export remain
documented in [checkpoint 2](../checkpoints/02-first-investigation.md).

See [delivery review](../checkpoints/05-recruiter-delivery.md),
[operation and cleanup](../recruiter-site.md), and
[hosting ADR](../decisions/009-recruiter-demo-hosting.md).
