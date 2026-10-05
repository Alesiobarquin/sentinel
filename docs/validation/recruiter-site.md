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

## Student-portfolio copy revision

On October 5, the developer requested plain, concise project descriptions instead
of promotional language. The revision removes the branding icon, replaces slogans
across pages and metadata, simplifies headings, shortens project notes, removes
repeated closing banners, and updates the sharing image/favicon. Recorded
decisions, evidence, measurements, and source excerpts were not edited.

TypeScript and production static export passed. All 22 existing desktop/mobile
browser checks passed locally in 8.4 seconds, with retries disabled. Six page
screenshots were generated; landing on desktop/mobile, desktop project notes,
and mobile diagnosis were inspected, along with the regenerated sharing image.
All six screenshot routes had zero branding SVGs and document widths equal to
their 1440/390 viewport widths.

The first test startup failed because a separate generic HTTP server already
occupied port 4173 and did not serve `/sentinel/`. That server was left intact.
Checks used a separate owned preview on 4175. Logs and screenshots are retained
in `var/site-tests-portfolio-copy-port-conflict.log`,
`var/site-tests-portfolio-copy.log`, and `var/site-qa-portfolio-copy/`.

## Recruiter readability polish

The developer subsequently permitted the original logo and requested polish for
technical and nontechnical recruiters. The latest version restores the logo,
uses a plain-language introduction, defines logs/metrics/traces, adds an ownership
and result summary, and opens demo entry links at the diagnosis. The original
model explanation remains available through a disclosure rather than being
rewritten. Configuration evidence is selected initially at the diagnosis; every
original citation and replay step remains accessible.

TypeScript and static export passed. All 22 desktop/mobile browser cases passed
after the final layout adjustment in 11.7 seconds, with retries disabled. Existing
cases now verify result-first entry and exact preservation of the original model
explanation against the downloadable JSON. Six routes were captured with one
logo each and matching document/viewport widths of 1440/390. Desktop/mobile
landing, desktop overview, mobile result, and the sharing image were inspected.
Final compact chart labels fit on one line in both viewports.

Logs/screenshots are under `var/site-tests-recruiter-polish-final.log` and
`var/site-qa-recruiter-polish/`. The source recording, measured results, and
read-only agent permissions were not changed.
