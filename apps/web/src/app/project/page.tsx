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
  "Problem",
  "Architecture",
  "Original work",
  "Decisions",
  "Lessons",
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
      "Sending all raw data would use more context. Selecting data can miss evidence, so the result includes coverage limits.",
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
    why: "The 28-service lab and model run locally. GitHub Pages hosts the recorded demo and project notes.",
    alternative:
      "A public lab would require more resources. The static site needs no backend, but cannot run a new investigation.",
    link: "docs/decisions/009-recruiter-demo-hosting.md",
  },
];
const lessons = [
  {
    number: "01",
    title: "Streaming response parsing",
    body: "The first run failed because the function call arrived in output_item.done while the terminal response's output was empty. I updated the adapter to assemble finalized stream items after successful completion and usage reporting. The captured response became an offline regression fixture.",
  },
  {
    number: "02",
    title: "Tool argument schemas",
    body: "The second run supplied a service argument to a global configuration tool. Python rejected it, but the model-facing JSON Schema had not expressed that rule. I added argument families for global, service-scoped, timed, and untimed reads. The next run completed with the same model and budgets.",
  },
  {
    number: "03",
    title: "Telemetry coverage",
    body: "An absent metric is not a zero, and a trace sample can miss intermittent failures. I added raw counter sample counts and explicit trace/span omissions. Configuration reads are labeled as current snapshots because they cannot establish the historical state.",
  },
  {
    number: "04",
    title: "Checking errors against source",
    body: "The “Invalid token” message initially suggested a credential issue. Source inspection showed that paymentFailure deliberately throws it. The baseline and enabled flag supported that cause. The gold attribute is assigned inside the failure branch; it does not identify a pre-existing customer group.",
  },
  {
    number: "05",
    title: "Docker memory limits",
    body: "Running the Compose lab and kind together exhausted the shared Docker VM and killed Kubernetes components. Increasing the fixture's memory limit did not fix the VM-wide shortage. I ran telemetry and Kubernetes checks separately and retained the failed results.",
  },
];

export default function Project() {
  return (
    <main id="main" className="container project-shell">
      <header className="project-heading">
        <p className="eyebrow">Sentinel · student project</p>
        <h1>Project notes</h1>
        <p>
          I built a read-only incident investigation agent and tested it against
          the OpenTelemetry Demo. These notes cover my implementation, design
          choices, test results, and lessons from the project.
        </p>
        <div className="hero-actions">
          <Link href="/demo/" className="button primary">
            View demo <Icon name="arrow" />
          </Link>
          <a href={REPO} className="button secondary">
            Source & documentation <Icon name="external" size={15} />
          </a>
        </div>
      </header>
      <div className="project-layout">
        <aside className="project-index">
          <span className="eyebrow">On this page</span>
          <nav aria-label="Project sections">
            {sections.map((name, index) => (
              <a
                key={name}
                href={`#${name.toLowerCase().replaceAll(" ", "-")}`}
              >
                <span className="mono" aria-hidden="true">
                  0{index + 1}
                </span>
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
          <section id="problem" className="project-section">
            <p className="eyebrow">01 / Problem</p>
            <h2>Project goal</h2>
            <p>
              The goal was to diagnose an injected service failure using
              telemetry, without giving the agent the expected answer. It
              receives a service, symptom, and time window, chooses diagnostic
              reads, and returns a cause with evidence references and
              limitations.
            </p>
          </section>
          <section id="architecture" className="project-section">
            <p className="eyebrow">02 / Architecture</p>
            <h2>Architecture</h2>
            <Architecture />
            <p>
              The model sees a bounded evidence selection. Full audit history
              stays outside that context. Typed provider adapters separate
              backend parsing and model transport from the investigation loop.
            </p>
            <div className="architecture-stack">
              <span>Python + Pydantic</span>
              <span>Direct OpenAI SDK</span>
              <span>OpenTelemetry SDK</span>
              <span>Next.js + React + TypeScript</span>
            </div>
          </section>
          <section id="original-work" className="project-section">
            <p className="eyebrow">03 / Original work</p>
            <h2>What I implemented</h2>
            <div className="contribution-grid">
              <article>
                <span className="eyebrow">Project code</span>
                <ul>
                  <li>Typed telemetry adapters and fixed diagnostic tools.</li>
                  <li>
                    Deterministic reduction, structured evidence, and explicit
                    omissions.
                  </li>
                  <li>
                    Hypothesis loop, decision validation, citation policy, and
                    bounded budgets.
                  </li>
                  <li>
                    Protected OAuth sign-in, account catalog, and direct model
                    transport.
                  </li>
                  <li>
                    Full local audit, usage records, and self-instrumentation.
                  </li>
                  <li>
                    Reproducible fault fixtures, deterministic tests, and
                    integration checks.
                  </li>
                  <li>
                    Reviewed replay export, this interactive site, and
                    deployment workflow.
                  </li>
                </ul>
              </article>
              <article>
                <span className="eyebrow">Existing software</span>
                <p>
                  The official <a href={UPSTREAM}>OpenTelemetry Demo 3.1.0</a>{" "}
                  supplies the application and fault scenarios. I pinned its
                  version for reproducible tests.
                </p>
                <p>
                  Prometheus, OpenSearch, Jaeger, Kubernetes, the OpenTelemetry
                  SDK, and the OpenAI SDK are dependencies used by Sentinel.
                </p>
              </article>
            </div>
          </section>
          <section id="decisions" className="project-section">
            <p className="eyebrow">04 / Decisions & alternatives</p>
            <h2>Design choices</h2>
            <div className="decision-cards">
              {decisions.map((d) => (
                <article key={d.title}>
                  <h3>{d.title}</h3>
                  <p>{d.why}</p>
                  <p className="tradeoff">{d.alternative}</p>
                  <a href={`${REPO}/blob/main/${d.link}`} className="text-link">
                    Code and notes <Icon name="external" size={13} />
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
          <section id="lessons" className="project-section">
            <p className="eyebrow">05 / Lessons from the build</p>
            <h2>What I learned</h2>
            <div className="lesson-list">
              {lessons.map((l) => (
                <article key={l.number}>
                  <span className="lesson-number mono">{l.number}</span>
                  <div>
                    <h3>{l.title}</h3>
                    <p>{l.body}</p>
                  </div>
                </article>
              ))}
            </div>
            <p className="fine-print">
              The repository contains the failure records, fixes, and learning
              notes.
            </p>
            <a
              href={`${REPO}/blob/main/docs/learning/investigation.md`}
              className="text-link"
            >
              Learning notes & interview questions{" "}
              <Icon name="external" size={14} />
            </a>
          </section>
          <section id="validation" className="project-section">
            <p className="eyebrow">06 / Measured validation</p>
            <h2>Test results</h2>
            <div className="validation-grid">
              <div>
                <strong>122</strong>
                <span>deterministic Python tests passed</span>
              </div>
              <div>
                <strong>6 + 2</strong>
                <span>live telemetry + isolated Kubernetes checks</span>
              </div>
              <div>
                <strong>3</strong>
                <span>real faults with deterministic captures</span>
              </div>
              <div>
                <strong>1</strong>
                <span>correct live AI diagnosis</span>
              </div>
            </div>
            <p>
              Eight live checks are separate from ordinary Python tests. Three
              faults were captured and reset: payment, EmptyCart, and
              intermittent ad errors. Only the payment case has a correct AI
              diagnosis. The site also passed 22 desktop/mobile browser checks.
            </p>
            <ErrorComparison />
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
                    <td>Developer exercise reset; agent recommendation only</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p>
              Two earlier model runs failed. One correct case does not establish
              an accuracy rate. The public record includes usage, selected
              evidence, and source-record hashes.
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
            <p className="eyebrow">07 / Failure modes & current limits</p>
            <h2>Current limitations</h2>
            <ul className="limits-list">
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
            <div className="roadmap">
              <span className="eyebrow">Planned work</span>
              <p>
                FastAPI/PostgreSQL persistence, incident chat, GitHub deployment
                context, ten or more evaluated AI scenarios, controlled
                remediation with human approval, MCP integration, and a
                temporary AWS/Terraform deployment are not implemented.
              </p>
            </div>
          </section>
          <section id="reproduce" className="project-section">
            <p className="eyebrow">08 / Reproduce</p>
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
