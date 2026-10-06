import type { Metadata } from "next";
import Link from "next/link";
import { Architecture } from "@/components/architecture";
import { ErrorComparison } from "@/components/error-comparison";
import { Icon } from "@/components/icons";
import {
  number,
  replay,
  REPO,
  seconds,
  totalTokens,
  UPSTREAM,
} from "@/lib/replay";

export const metadata: Metadata = {
  title: "Project notes",
  alternates: { canonical: "/sentinel/project/" },
};
const sections = [
  "Experiment",
  "Architecture",
  "Implementation",
  "Decisions",
  "Development",
  "Validation",
  "Limits",
  "Reproduce",
];
const decisions = [
  {
    title: "One explicit agent loop",
    why: "A single loop records each tool choice, hypothesis, and diagnosis. Its transitions can be tested directly.",
    alternative:
      "I did not add multiple agents because the current scenarios do not demonstrate a need for them.",
    link: "docs/decisions/007-bounded-investigation.md",
  },
  {
    title: "Reduce data before inference",
    why: "Log grouping, selected spans, fixed queries, and source excerpts limit model context. Evidence IDs and omissions are recorded.",
    alternative:
      "A comparison with newer native results at the same context limit used fewer tokens with reduction, but the baseline diagnosed one more payment run. The small study shows no accuracy advantage for ranked selection.",
    link: "sentinel/agent/context.py",
  },
  {
    title: "Policy outside the prompt",
    why: "Python validates decisions and restricts tools. Kubernetes RBAC limits read access. The agent cannot execute remediation.",
    alternative:
      "Prompt instructions alone cannot enforce tool permissions or validate evidence references.",
    link: "docs/decisions/004-safety-boundaries.md",
  },
  {
    title: "Local execution, public replay",
    why: "The lab and Python agent run locally; model requests go to the provider. GitHub Pages hosts the recorded demo and project notes.",
    alternative:
      "A public lab would require more resources. The static site needs no backend, but cannot run a new investigation.",
    link: "docs/decisions/009-recruiter-demo-hosting.md",
  },
];
const implementation = [
  {
    title: "Telemetry tools and reduction",
    body: "Adapters parse Prometheus, OpenSearch, and Jaeger responses. Diagnostic tools use fixed queries, group repeated logs, select relevant spans, and report missing samples and omissions.",
    source: "sentinel/agent/diagnostics.py",
    tests: "tests/test_diagnostics.py",
  },
  {
    title: "Investigation loop and policy",
    body: "Pydantic validates model decisions. The loop checks service scope, citations to earlier successful reads, duplicate requests, and run budgets. Decisions and full results are written to local files.",
    source: "sentinel/agent/runner.py",
    tests: "tests/test_agent.py",
  },
  {
    title: "Model adapter",
    body: "The direct OpenAI SDK handles requests. Sentinel's adapter validates completed tool calls, retains reported usage, and surfaces incomplete or invalid responses. Sign-in credentials remain local.",
    source: "sentinel/agent/provider.py",
    tests: "tests/test_provider.py",
  },
  {
    title: "Public recording and viewer",
    body: "The exporter checks the reviewed run and selects allowed fields for publication. Next.js displays that record. Browser tests exercise replay controls, evidence links, direct routes, and mobile layouts.",
    source: "sentinel/replay.py",
    tests: "tests/test_replay.py",
  },
];
const lessons = [
  {
    title: "Evidence omitted from context",
    body: "Repeated trials retrieved a source branch, later omitted it from the selected context, and then requested it again. The duplicate-read policy stopped those investigations. Saving the full audit did not make the omitted payload available to the model. The evaluation preserves those failures rather than counting only completed diagnoses.",
    source: "docs/validation/resume-evaluation.md",
    tests: "tests/test_benchmark.py",
  },
  {
    title: "Citations and causal claims",
    body: "Some trials named the injected fault but did not cite the evidence establishing its mechanism. A cart conclusion also added Valkey to the affected services without support. Structural citation checks and semantic claim review measure different things; valid evidence IDs do not prove an explanation is correct.",
    source: "evals/reports/resume-20261005/reviews.jsonl",
    tests: "tests/test_benchmark.py",
  },
  {
    title: "Streaming response parsing",
    body: "The first model investigation failed: the function call arrived in output_item.done, while the terminal response's output was empty. The adapter now accepts finalized stream items only after successful completion and reported usage. Regression tests reproduce that response shape and reject incomplete, oversized, or inconsistent streams.",
    source: "sentinel/agent/provider.py",
    tests: "tests/test_provider.py",
  },
  {
    title: "Tool argument schemas",
    body: "The second investigation supplied a service argument to a global configuration tool. Python rejected it, but the model-facing JSON Schema had not expressed that rule. The schema now describes global, service-scoped, timed, and untimed argument families. The next investigation completed with the same model and budgets.",
    source: "sentinel/agent/contracts.py",
    tests: "tests/test_agent.py",
  },
  {
    title: "Telemetry coverage",
    body: "An intermittent ad fault had a warning log but only one raw error-counter sample, so its increase remained unknown. A cart fault was visible in logs and metrics but missed by the bounded trace sample. The tools expose raw sample counts and omitted traces/spans. Configuration reads are labeled as current snapshots, which cannot establish historical state.",
    source: "docs/validation/read-only-agent.md",
    tests: "tests/test_diagnostics.py",
  },
  {
    title: "Checking errors against source",
    body: "The “Invalid token” message could suggest a credential issue. Source inspection showed that paymentFailure deliberately throws it. The baseline and enabled flag supported that cause. The gold loyalty attribute is assigned inside the failure branch; it does not identify a pre-existing customer group.",
    source: "docs/checkpoints/02-first-investigation.md",
    tests: null,
  },
  {
    title: "Docker memory limits",
    body: "Running the Compose lab and kind together exhausted the shared Docker VM and killed Kubernetes components. Increasing the fixture's memory limit did not resolve the VM-wide shortage. Running telemetry and Kubernetes checks separately passed. This validates a separate reader fixture; the application still runs in Compose.",
    source: "docs/validation/read-only-agent.md",
    tests: "tests/test_live_kubernetes.py",
  },
];

export default function Project() {
  return (
    <main id="main" className="container project-shell">
      <header className="project-heading">
        <p className="eyebrow">Sentinel · student project</p>
        <h1>Project notes</h1>
        <p>
          The experiment, implementation, and failures behind the recorded
          payment investigation. Code and tests are linked alongside the changes
          they cover.
        </p>
        <div className="intro-links">
          <Link href="/demo/#step-8">View demo</Link>
          <a href={REPO}>Source on GitHub</a>
        </div>
      </header>
      <div className="project-layout">
        <aside className="project-index">
          <span className="eyebrow">On this page</span>
          <nav aria-label="Project sections">
            {sections.map((name) => (
              <a
                key={name}
                href={`#${name.toLowerCase().replaceAll(" ", "-")}`}
              >
                {name}
              </a>
            ))}
          </nav>
          <div className="index-note">
            <strong>Current scope</strong>
            <p>A local investigation CLI and a recorded browser demo.</p>
          </div>
        </aside>
        <div className="project-content">
          <section id="experiment" className="project-section">
            <h2>The experiment</h2>
            <p>
              The question was whether a model could work from a running
              application&apos;s telemetry to identify a service failure. The
              local test used OpenTelemetry Demo&apos;s deliberate payment
              fault. The model received the symptom, service, and time window.
              The scenario&apos;s expected cause was kept outside its input.
            </p>
            <dl className="project-summary" aria-label="Project summary">
              <div>
                <dt>Setup</dt>
                <dd>
                  Capture a healthy baseline, enable <code>paymentFailure</code>
                  , wait for telemetry, then start one investigation.
                </dd>
              </div>
              <div>
                <dt>Observation</dt>
                <dd>
                  Logs and traces carried an invalid-token error. The source
                  contained the matching flag-controlled branch, and the current
                  configuration selected <code>100%</code>.
                </dd>
              </div>
              <div>
                <dt>Result</dt>
                <dd>
                  The agent identified the payment failure setting. A separate
                  test helper reset it, and recovery samples showed no errors.
                </dd>
              </div>
              <div>
                <dt>What this establishes</dt>
                <dd>
                  One correct diagnosis of a controlled fault, with readable
                  source and an available configuration snapshot. The cause is
                  more direct than many production incidents.
                </dd>
              </div>
            </dl>
          </section>
          <section id="architecture" className="project-section">
            <h2>Architecture</h2>
            <Architecture />
            <p>
              The model receives selected data, called its context, with a size
              limit. Full results remain in local audit files. Typed adapters
              separate data parsing and model requests from the investigation
              loop.
            </p>
            <p>
              Python runs the tools and loop, Pydantic validates their
              contracts, and the OpenAI SDK connects the model. OpenTelemetry
              instruments Sentinel itself. Next.js, React, and TypeScript render
              the public recording on GitHub Pages.
            </p>
          </section>
          <section id="implementation" className="project-section">
            <h2>Implementation</h2>
            <p>
              Sentinel&apos;s code covers the investigation tooling and viewer.
              The official <a href={UPSTREAM}>OpenTelemetry Demo 3.1.0</a>{" "}
              supplies the application services and fault mechanisms; its
              version is pinned. Prometheus, OpenSearch, Jaeger, and the SDKs
              are existing dependencies. I used AI coding assistance for
              implementation and debugging.
            </p>
            <div className="implementation-list">
              {implementation.map((part) => (
                <article key={part.title}>
                  <h3>{part.title}</h3>
                  <p>{part.body}</p>
                  <div className="inline-links">
                    <a href={`${REPO}/blob/main/${part.source}`}>
                      {part.source.split("/").at(-1)}
                    </a>
                    <a href={`${REPO}/blob/main/${part.tests}`}>
                      {part.tests.split("/").at(-1)}
                    </a>
                  </div>
                </article>
              ))}
            </div>
          </section>
          <section id="decisions" className="project-section">
            <h2>Design choices</h2>
            <div className="decision-list">
              {decisions.map((d) => (
                <article key={d.title}>
                  <h3>{d.title}</h3>
                  <p>{d.why}</p>
                  <p className="tradeoff">{d.alternative}</p>
                  <a href={`${REPO}/blob/main/${d.link}`} className="text-link">
                    Related code or decision record{" "}
                    <Icon name="external" size={13} />
                  </a>
                </article>
              ))}
            </div>
            <div className="callout">
              <strong>Authentication and cost</strong>
              <p>
                The recorded run used ChatGPT sign-in and{" "}
                <code>{replay.model}</code>. Credentials stay outside the
                repository. API-key mode is billed separately.
              </p>
              <p>
                The loop limits calls, bytes, elapsed time, and reported tokens.
                Subscription mode cannot enforce an exact credit or per-response
                output-token cap; usage is checked after each response.
              </p>
            </div>
          </section>
          <section id="development" className="project-section">
            <h2>What broke during development</h2>
            <div className="lesson-list">
              {lessons.map((l) => (
                <article key={l.title}>
                  <div>
                    <h3>{l.title}</h3>
                    <p>{l.body}</p>
                    <div className="inline-links">
                      <a href={`${REPO}/blob/main/${l.source}`}>
                        {l.source.split("/").at(-1)}
                      </a>
                      {l.tests && (
                        <a href={`${REPO}/blob/main/${l.tests}`}>
                          {l.tests.split("/").at(-1)}
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
            <p className="fine-print">
              The repository documents the failure history and contains the
              fixes and tests. Full run records and provider captures remain
              local; the site publishes selected evidence from the reviewed
              successful run.
            </p>
            <a
              href={`${REPO}/blob/main/docs/learning/investigation.md`}
              className="text-link"
            >
              Learning notes <Icon name="external" size={14} />
            </a>
          </section>
          <section id="validation" className="project-section">
            <h2>What was tested</h2>
            <p>
              Ordinary tests use fixtures to check implementation behavior. Live
              checks exercise the local backends separately. Neither is a
              measure of model diagnosis accuracy.
            </p>
            <div className="table-scroll">
              <table className="validation-table">
                <caption>Validation recorded on October 5–6, 2026</caption>
                <thead>
                  <tr>
                    <th>Check</th>
                    <th>Observed result and scope</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <a href={`${REPO}/tree/main/tests`}>
                        Deterministic Python tests
                      </a>
                    </td>
                    <td>
                      153 passed; eight opt-in live tests skipped. Covers
                      parsing, context, contracts, policy, auth, transport,
                      audit, evaluation grading, and export behavior with fixtures.
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <a
                        href={`${REPO}/blob/main/docs/validation/read-only-agent.md`}
                      >
                        Live integrations
                      </a>
                    </td>
                    <td>
                      Six telemetry checks and two isolated Kubernetes checks
                      passed. The Kubernetes reader fixture was tested
                      separately from the Compose application.
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <a href={`${REPO}/blob/main/evals/resume-scenarios.json`}>
                        Fault exercises
                      </a>
                    </td>
                    <td>
                      12 real-telemetry cases: nine faults and three controls.
                      Each has one accepted capture; repeated model trials share
                      that capture. Developer helpers restore their owned faults.
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <a
                        href={`${REPO}/blob/main/docs/validation/resume-evaluation.md`}
                      >
                        Repeated AI evaluations
                      </a>
                    </td>
                    <td>
                      63 attempts: 45 primary and 18 context-baseline runs.
                      Correct causes in 9/27 primary fault trials; grounded claims
                      in 9/12 emitted primary diagnoses. Appropriate explicit
                      abstention in 1/18 primary control trials; the others used
                      a different terminal action or ended in budget/provider failures.
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <a href={`${REPO}/blob/main/apps/web/tests/site.spec.ts`}>
                        Browser checks
                      </a>
                    </td>
                    <td>
                      22 passed across desktop and mobile Chromium. Checks
                      navigation, evidence selection, playback, downloads, and
                      layout; it does not certify every browser.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              The original cohort has three model runs per case; a separate
              15-attempt control cohort reuses the same captured observations.
              Failures stay in the accuracy denominator;
              grounding applies only to emitted diagnoses. The comparison did
              not show an accuracy benefit from ranked context. All attempts are
              executed and reviewed. Reviews are Codex-assisted, without independent
              human adjudication.
            </p>
            <div className="inline-links">
              <a href={`${REPO}/blob/main/docs/validation/resume-evaluation.md`}>
                Method and measured results <Icon name="external" size={13} />
              </a>
              <a href={`${REPO}/tree/main/evals/reports/resume-20261005`}>
                Per-run data and reviews <Icon name="external" size={13} />
              </a>
            </div>
            <p>
              These are the payment test&apos;s before/failure/after-reset
              observations. Recovery followed the helper&apos;s reset, not an
              agent action. The chart uses sampled telemetry estimates.
            </p>
            <ErrorComparison />
            <details className="run-measurements">
              <summary>Recorded model usage and timing</summary>
              <div className="table-scroll">
                <table>
                  <caption>Recorded investigation · {replay.run_id}</caption>
                  <thead>
                    <tr>
                      <th>Measurement</th>
                      <th>Recorded result</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Model calls / read-only tools</td>
                      <td>
                        {replay.model_calls} / {replay.tool_calls}
                      </td>
                    </tr>
                    <tr>
                      <td>Reported input / output tokens</td>
                      <td>
                        {number(replay.input_tokens)} /{" "}
                        {number(replay.output_tokens)}
                      </td>
                    </tr>
                    <tr>
                      <td>Total tokens / budget</td>
                      <td>
                        {number(totalTokens)} /{" "}
                        {number(replay.budget.max_total_tokens)}
                      </td>
                    </tr>
                    <tr>
                      <td>Investigation latency</td>
                      <td>{seconds(replay.latency_ms)}</td>
                    </tr>
                    <tr>
                      <td>Baseline / recovery reads</td>
                      <td>5/5 succeeded in each phase</td>
                    </tr>
                    <tr>
                      <td>Recovery error signals</td>
                      <td>
                        Zero estimated server errors, selected payment error
                        spans, and sampled warning/error logs
                      </td>
                    </tr>
                    <tr>
                      <td>Remediation execution</td>
                      <td>
                        Developer exercise reset; agent recommendation only
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
            <p>
              The public record includes selected evidence, reported usage, and
              source-record hashes. Full private artifacts remain local.
            </p>
            <div className="inline-links">
              <a
                href={`${REPO}/blob/main/docs/checkpoints/02-first-investigation.md`}
              >
                Investigation review <Icon name="external" size={13} />
              </a>
              <a href={`${REPO}/blob/main/docs/validation/read-only-agent.md`}>
                Integration record <Icon name="external" size={13} />
              </a>
              <a href={`${REPO}/actions/workflows/ci.yml`}>
                CI checks <Icon name="external" size={13} />
              </a>
            </div>
          </section>
          <section id="limits" className="project-section">
            <h2>Current limitations</h2>
            <ul className="limits-list">
              <li>
                <strong>Controlled evaluation.</strong> The cases use known demo
                fault mechanisms and one capture each. Source and configuration
                reads can reveal the injected cause. The results do not establish
                performance on unfamiliar production incidents.
              </li>
              <li>
                <strong>Incomplete telemetry.</strong> Samples can miss faults.
                Late exports and insufficient counter samples can leave metrics
                unknown. Current configuration cannot prove historical state.
              </li>
              <li>
                <strong>Failed investigations.</strong> Invalid decisions,
                unavailable evidence, repeated requests, or exhausted budgets
                stop the run.
              </li>
              <li>
                <strong>Trace export.</strong> OTLP export timed out during the
                recorded run. Twenty-five local spans remained; complete
                delivery to Jaeger is unverified.
              </li>
              <li>
                <strong>Local persistence.</strong> Runs are saved as files.
                Database-backed incident management is not implemented.
              </li>
              <li>
                <strong>Recorded demo.</strong> This site displays a saved run.
                It does not start the Python agent or request new model
                responses.
              </li>
            </ul>
            <h3 className="next-experiment">Next experiment</h3>
            <p>
              Test whether retaining compact causal evidence and reserving a
              final model call improves
              completion. That needs a separate measured comparison with fresh
              captures and independent review. The current{" "}
              <a href={`${REPO}/blob/main/docs/validation/resume-evaluation.md`}>
                results and limitations
              </a>
              .
            </p>
          </section>
          <section id="reproduce" className="project-section">
            <h2>Run locally</h2>
            <p>
              Clone the repository, install its locked Python environment, start
              Docker Desktop, and bootstrap the pinned target. The full local
              lab needs about 6 GB available to Docker and 14 GB of free disk
              space. Run kind separately on resource-constrained machines.
            </p>
            <pre className="terminal">
              <code>{`git clone ${REPO}.git\ncd sentinel\nmake setup\nmake demo-up\nmake demo-verify\nmake check\n\n# Browser consent; credentials stay local.\nmake login\nmake models\nSENTINEL_MODEL=gpt-5.6-luna make first-investigation\n\n# Stop only the Sentinel demo when finished.\nmake demo-down`}</code>
            </pre>
            <p>
              Choose a model available to your account. The test captures a
              baseline, injects a fault, investigates, resets the flag even on
              failure, and checks recovery. Results can differ between runs.
            </p>
            <div className="inline-links">
              <a href={`${REPO}/blob/main/README.md`}>
                Full setup <Icon name="external" size={13} />
              </a>
              <a href={`${REPO}/blob/main/docs/investigation.md`}>
                Agent & auth guide <Icon name="external" size={13} />
              </a>
              <a href={`${REPO}/blob/main/docs/runbooks/payment-failure.md`}>
                Manual incident runbook <Icon name="external" size={13} />
              </a>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
