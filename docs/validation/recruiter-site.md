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

## Engineering presentation review

The developer asked for a review by the standard of an experienced peer: a
concrete experiment and implementation history rather than product marketing.
The landing dashboard preview, statistic strip, technology badges, and generic
feature cards were removed. Its text explains the controlled payment experiment
and links to actual recorded log/source/configuration reads. Project notes link
the implementation and tests alongside parser/schema fixes, coverage limits,
and the Docker resource failure. Development used AI coding assistance; the
external target's authorship is explicit.

Review also corrected two factual presentation problems: full private failure
captures are retained locally rather than published in the repository, and the
model is accessed through its provider rather than running locally. Fixture
tests, real backend reads, deterministic fault captures, and the one successful
model investigation have separate scopes in a normal table. Model usage/timing
and confidence remain inspectable without being headline claims. The recorded
JSON, decisions, measurements, and permissions were not edited.

TypeScript and production export passed. The final local browser suite passed
all 22 cases in 10.6 seconds without retries. The landing navigation case now
also verifies the source-branch deep link. Six page routes returned 200, retained
one logo, and matched their 1440/390 viewport widths. Twenty-four repository
source/test/document targets and every project contents anchor resolved. Usage
disclosure exposed the original recorded values. Desktop/mobile landing,
development, mobile implementation/validation/result, and the sharing image were
inspected. The final mobile validation text uses 12 px rather than 10 px.

Artifacts remain under `var/site-qa-peer-review/`,
`var/site-build-peer-review-final.log`, and `var/site-tests-peer-review-final.log`.
The earlier passing suite and screenshots are retained separately from the final
readability adjustment. This review does not add another AI evaluation or
establish production reliability.

## Evaluation study presentation

On October 6, the site was updated to explain the executed 48-attempt evaluation,
with its 12 real-telemetry cases, fault-accuracy denominator, citation-grounding
scope, provider failures, and incomplete control follow-up. Links lead to the
methodology and per-run public records. No headline statistics or new dashboard
were added. The original payment recording remains unchanged; the confidence
score's calibration caveat is now visible without opening a disclosure.

Local replay validation, TypeScript checks, and production static export passed.
All **22 desktop/mobile Chromium checks passed in 7.4 seconds**, with retries
disabled. Six screenshots covered landing, evaluation notes, and the diagnosis
at widths 1440 and 390. All six were inspected and had document widths equal to
their viewport widths. The diagnosis shows the original tool sequence, selected
configuration evidence, citations, competing hypotheses, confidence caveat, and
recommendation that the agent cannot execute.

The final Python suite passed **151 deterministic tests**, eight opt-in live
skips, and compilation. Six live telemetry checks passed separately after the
stock shipping and collector-coverage captures; the two Kubernetes live tests
were skipped and retain their historical isolated-kind validation. The offline
report verifier reproduced all 48 packet-bound reviews and summary metrics.
These checks are separate from AI investigation attempts.

Artifacts remain in `var/resume-evaluation-site-browser.log`,
`var/resume-evaluation-site-build.log`, `var/resume-evaluation-site-qa/`,
`var/resume-evaluation-final-python.log`, and
`var/resume-evaluation-final-live-telemetry.log`. The owned preview used port
4187; the unrelated server on 4173 was left intact. The developer's Compose lab
was reset and stopped using its scoped `make demo-down` command, preserving its
volumes and leaving other projects untouched. Subscription quota prevents the
remaining 12 control trials; this publication does not declare the evaluation
sprint complete.

Release source: `0e6807dad1d63ac395dc7d9937e403fa8bd63ec5`.
[Actions run 37412976918](https://github.com/Alesiobarquin/sentinel/actions/runs/37412976918)
passed Python 3.12/3.14 (151 deterministic passes and eight live skips each),
offline verification of 48 published investigations, replay validation,
TypeScript/static export, 22 CI browser executions, and Pages deployment.

All five HTTPS paths in the initial release table returned 200 again. The home
metadata uses `Sentinel — AI Incident Investigation Agent`, and the project page
links the evaluation report. The fetched recording still matches the original
byte-for-byte (SHA-256
`e61ef20d37ac18a17cc29d84c3e7932c450f5e06e498b891a1954b2d4369767c`).
The published report, summary JSON, and resume entries were also fetched from
the release commit and matched the local files.

The public HTTPS Playwright suite passed **22 executions in 14.9 seconds**,
with retries disabled. These are eleven cases in two viewports, not 22 distinct
test definitions. Actual public desktop landing and mobile diagnosis screenshots
were inspected; widths remained 1440/390, and the confidence caveat was visible.
The first screenshot helper used an unsupported `?step=8` query and timed out
waiting for a diagnosis. It was corrected to use the viewer's actual **View
result** button; this was an operator navigation mistake, not a failing browser
test or product change. Its record remains under the screenshot directory.

Public evidence is retained in `var/resume-evaluation-publication-ci.json`,
`var/resume-evaluation-publication-ci-full.log`,
`var/resume-evaluation-public-https.json`,
`var/resume-evaluation-published-source.json`,
`var/resume-evaluation-public-browser-final.log`, and
`var/resume-evaluation-site-qa/public-observations.json`.
The owned preview on 4187 has been stopped.

## Completed control study — October 6

The completed study contains 63 reviewed attempts: the original 48 plus fifteen
additional control trials. The site and resume documents now report all trials
as executed, with failures retained. The original payment recording still has
SHA-256 `e61ef20d37ac18a17cc29d84c3e7932c450f5e06e498b891a1954b2d4369767c`.
The site describes 9/27 primary fault accuracy, grounding in 9/12 emitted primary
diagnoses, and appropriate explicit abstention in 1/18 primary control trials.
Measurements remain inside the experiment write-up, with method and raw-data links.

Fresh TypeScript checks, production static export, and replay validation passed.
All **22 local browser executions passed in 9.2 seconds** without retries. Six
desktop/mobile screenshots and two additional mobile table/diagnosis captures
were inspected. Both document widths match their 1440/390-pixel viewports, and
the added results remain readable without horizontal overflow.

The Python suite passed **153 deterministic tests**, eight opt-in live skips,
and compilation. Both cohort verifiers and the study verifier reproduce all 63
bound reviews. They check hashes/completeness, reject repeated run IDs, preserve
inference identity, and keep additional controls out of fault accuracy. Screening
of 48 public report files found no credential/home-path pattern matches; public
fields and the continuation helper were also reviewed. These offline checks do
not independently validate the semantic grading.

Local artifacts: `var/resume-evaluation-completed-python.log`,
`var/resume-evaluation-completed-site-typecheck.log`,
`var/resume-evaluation-completed-site-build.log`,
`var/resume-evaluation-completed-site-browser.log`, and
`var/resume-evaluation-completed-site-qa/`. The owned preview uses port 4189;
the unrelated process on 4173 is untouched. The Docker lab remains stopped;
the resumed evaluations used the existing native captures.
