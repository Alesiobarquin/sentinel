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
  title: "The project & lessons",
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
    why: "Keep the decision process visible and testable. Structured reads, hypotheses, and conclusions have clear transitions.",
    alternative:
      "A multi-agent framework would add coordination and failure modes before evaluation demonstrated a benefit.",
    link: "docs/decisions/007-bounded-investigation.md",
  },
  {
    title: "Reduce data before inference",
    why: "Exact log grouping, compact traces, fixed metric queries, and bounded source excerpts control context size while retaining evidence IDs and coverage.",
    alternative:
      "Sending raw telemetry would use more context and make omissions harder to inspect. Selection can still miss evidence, so limits are explicit.",
    link: "sentinel/agent/context.py",
  },
  {
    title: "Policy outside the prompt",
    why: "Pydantic validates decisions; code restricts tools and observed services; Kubernetes RBAC limits the reader. Recommendations have no executor.",
    alternative:
      "A prompt alone cannot authorize a tool, validate a citation, or prevent an infrastructure write.",
    link: "docs/decisions/004-safety-boundaries.md",
  },
  {
    title: "Local execution, public replay",
    why: "Keep the full 28-service target and model use local. Publish a small static export that stays available to recruiters.",
    alternative:
      "An always-running cluster or expiring student-funded backend would add recurring resource needs for evidence browsing. Pages has no Python runtime.",
    link: "docs/decisions/009-recruiter-demo-hosting.md",
  },
];
const lessons = [
  {
    number: "01",
    title: "A completed response can still need stream assembly.",
    body: "The first real model investigation failed because its subscription stream delivered the finalized function call in output_item.done while the terminal response's output was empty. The adapter now accepts finalized items only after successful completion and reported usage. It retains scope, count, size, duplicate-index, and consistency checks. Captured native stream replay made the fix testable offline.",
  },
  {
    number: "02",
    title: "Runtime validators are not a model-facing contract.",
    body: "The next investigation reached source evidence, then supplied a service argument to a global configuration read. The application blocked it. Python validators had enforced the rule, but JSON Schema did not express it. Explicit argument families now distinguish global/scoped and timed/untimed tools. The successful run used the same small model and existing budgets.",
  },
  {
    number: "03",
    title: "Missing evidence is not evidence of health.",
    body: "An absent counter increase differs from zero errors. A bounded trace sample can miss an intermittent fault; current configuration cannot establish historical evaluation. Counter sample counts, omitted traces/spans, matching log coverage, export delay, and pinned-source limits stay visible instead of being converted into certainty.",
  },
  {
    number: "04",
    title: "An error string is a clue, not a cause.",
    body: "“Invalid token” suggested a credential problem until the source revealed an intentional throw controlled by paymentFailure. Baseline comparison and the current enabled flag supported that mechanism. The gold attribute is assigned inside the injected branch, so it does not prove a pre-existing gold-customer cohort.",
  },
  {
    number: "05",
    title: "Shared local resources can invalidate a test setup.",
    body: "Running the full Compose lab alongside kind exhausted the shared Docker VM and OOM-killed Kubernetes components. Those failures remain recorded. Running the telemetry and Kubernetes checks separately restored meaningful validation; increasing only the small fixture's memory limit had not solved the VM-wide problem.",
  },
];

export default function Project() {
  return (
    <main id="main" className="container project-shell">
      <header className="project-heading">
        <p className="eyebrow">Project case study / Sentinel</p>
        <h1>
          The work behind
          <br />
          <em>the diagnosis.</em>
        </h1>
        <p>
          A deliberately small agent, a real distributed system, and an evidence
          trail you can inspect. Here&apos;s what was built, why the design
          looks this way, and what the failures taught.
        </p>
        <div className="hero-actions">
          <Link href="/demo/" className="button primary">
            Explore the demo <Icon name="arrow" />
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
                <span className="mono" aria-hidden="true">0{index + 1}</span>
                {name}
              </a>
            ))}
          </nav>
          <div className="index-note">
            <strong>Current delivery</strong>
            <p>
              Read-only investigation CLI + public recorded viewer. Later PRD
              features are listed below.
            </p>
          </div>
        </aside>
        <div className="project-content">
          <section id="problem" className="project-section">
            <p className="eyebrow">01 / Problem</p>
            <h2>Incident evidence is fragmented.</h2>
            <p>
              A failed checkout can leave a warning in one service, an error
              span in another, a metric change, and a configuration clue
              elsewhere. Reading one signal often produces a plausible story
              without establishing the cause.
            </p>
            <p>
              Sentinel makes that investigation explicit: start with a service
              and time window, select typed reads, test competing hypotheses,
              cite the observations, and preserve what remains unknown. It
              supports investigation rather than replacing the observability
              backends.
            </p>
          </section>
          <section id="architecture" className="project-section">
            <p className="eyebrow">02 / Architecture</p>
            <h2>Small boundaries, inspectable transitions.</h2>
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
            <h2>
              The investigator is Sentinel.
              <br />
              The application under test is external.
            </h2>
            <div className="contribution-grid">
              <article>
                <span className="eyebrow">Sentinel implementation</span>
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
                <span className="eyebrow">External dependencies & target</span>
                <p>
                  The official <a href={UPSTREAM}>OpenTelemetry Demo 3.1.0</a>{" "}
                  supplies the distributed application and fault branches. Its
                  commit is pinned and its source is attributed.
                </p>
                <p>
                  Prometheus, OpenSearch, Jaeger, Kubernetes, the OpenTelemetry
                  SDK, and the OpenAI SDK are existing systems integrated by
                  Sentinel. Their implementation is not presented as original
                  project work.
                </p>
              </article>
            </div>
          </section>
          <section id="decisions" className="project-section">
            <p className="eyebrow">04 / Decisions & alternatives</p>
            <h2>Each addition has a job.</h2>
            <div className="decision-cards">
              {decisions.map((d) => (
                <article key={d.title}>
                  <h3>{d.title}</h3>
                  <p>{d.why}</p>
                  <p className="tradeoff">{d.alternative}</p>
                  <a href={`${REPO}/blob/main/${d.link}`} className="text-link">
                    Decision / implementation <Icon name="external" size={13} />
                  </a>
                </article>
              ))}
            </div>
            <div className="callout">
              <strong>Authentication and cost</strong>
              <p>
                The real run used the developer&apos;s supported ChatGPT sign-in
                and an explicitly available small model,{" "}
                <code>{replay.model}</code>. State, PKCE, nonce, identity
                signatures, and permissions are validated; credentials stay
                outside the repository. API-key billing is a separate mode.
              </p>
              <p>
                Local call, byte, wall-time, and reported-token limits bound the
                loop. Subscription preview does not expose exact credit/dollar
                use or an enforceable server-side output-token cap. A single
                response may cross a local usage limit before further work is
                stopped.
              </p>
            </div>
          </section>
          <section id="lessons" className="project-section">
            <p className="eyebrow">05 / Lessons from the build</p>
            <h2>The failures changed the design.</h2>
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
              These lessons are tied to retained runs and tests. The
              repository&apos;s learning notes include questions for explaining
              the design and modifying it safely.
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
            <h2>What the evidence establishes.</h2>
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
              The ordinary Python suite skips eight opt-in live checks. The six
              telemetry checks and two Kubernetes checks were run separately
              against real local backends. The payment, EmptyCart, and
              intermittent ad scenarios produced real fault evidence; they are
              not three successful AI diagnoses.
            </p>
            <ErrorComparison />
            <div className="table-scroll">
              <table>
                <caption>Showcased AI run · {replay.run_id}</caption>
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
              The correct diagnosis followed two failed model investigations.
              There is no measured general accuracy rate. Confidence is a
              ranking indicator. The full source-record hashes, usage, and
              selected evidence are available in the public recording.
            </p>
            <div className="inline-links">
              <a
                href={`${REPO}/blob/main/docs/checkpoints/02-first-investigation.md`}
              >
                Causal review <Icon name="external" size={13} />
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
            <h2>A useful result has boundaries.</h2>
            <ul className="limits-list">
              <li>
                <strong>Sampling and missing data.</strong> Top-k evidence can
                miss faults. Late exports and insufficient counter samples can
                make metrics unknown. Current configuration and pinned source do
                not establish historical effective evaluation or deployed image
                contents.
              </li>
              <li>
                <strong>Model failures remain possible.</strong> Malformed
                decisions, unavailable evidence, repeated requests, or exhausted
                budgets stop the run. The system does not force a cause through
                retries.
              </li>
              <li>
                <strong>Self-observability can fail.</strong> OTLP export timed
                out in the showcased run. Twenty-five local spans remained;
                complete delivery of that run&apos;s self-trace to Jaeger is
                unverified.
              </li>
              <li>
                <strong>Persistence is local.</strong> File-backed audits
                preserve this run, but do not provide the transactions,
                multi-user access, or concurrent lifecycle management planned
                for PostgreSQL.
              </li>
              <li>
                <strong>This public site is a recording.</strong> Pages hosts
                static HTML, JavaScript, and reviewed data. It does not run the
                Python agent, make new model calls, or provide a live telemetry
                connection.
              </li>
            </ul>
            <div className="roadmap">
              <span className="eyebrow">Remaining full-guide scope</span>
              <p>
                FastAPI/PostgreSQL product persistence, incident chat, GitHub
                code/deployment context, ten or more evaluated AI scenarios,
                controlled remediation with human approval, MCP integration, and
                a disposable AWS/Terraform deployment remain later work.
              </p>
              <p>
                The current recruiter delivery does not declare those features
                or the full PRD portfolio acceptance criteria complete. No paid
                infrastructure was created for this website.
              </p>
            </div>
          </section>
          <section id="reproduce" className="project-section">
            <p className="eyebrow">08 / Reproduce & explore</p>
            <h2>Run the system behind the recording.</h2>
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
              Choose an available smaller model from your own account catalog.
              The exercise captures baseline, injects one reversible fault,
              investigates, restores its owned flag even on failure, and
              captures recovery. A repeat can fail or differ; inspect and retain
              the outcome.
            </p>
            <p>
              Before modifying the system, trace a citation from a decision to
              its evidence payload, explain every budget limit, and identify the
              code boundary that prevents a write.
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
      <section className="closing-banner">
        <div>
          <span className="eyebrow">Inspect the implemented behavior</span>
          <h2>Follow the original eight reads.</h2>
        </div>
        <Link href="/demo/" className="button primary">
          Explore the investigation <Icon name="arrow" />
        </Link>
      </section>
    </main>
  );
}
