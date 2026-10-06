import Link from "next/link";
import { REPO, UPSTREAM } from "@/lib/replay";

export default function Home() {
  return (
    <main id="main" className="container project-intro">
      <header className="intro-heading">
        <p className="eyebrow">Student project · incident investigation</p>
        <h1>Sentinel</h1>
        <p className="intro-description">
          A local experiment in using an AI agent to investigate service
          failures.
        </p>
        <p>
          I built a Python investigation loop with tools for reading logs,
          metrics, request traces, application code, and configuration. The
          model chooses what to read next and records an explanation with
          references to the data it used.
        </p>
        <nav className="intro-links" aria-label="Explore the project">
          <Link href="/demo/#step-8">View demo</Link>
          <Link href="/project/">Project notes</Link>
          <a href={REPO}>Source on GitHub</a>
        </nav>
      </header>

      <section className="intro-section" aria-labelledby="experiment-title">
        <h2 id="experiment-title">The experiment</h2>
        <p>
          I used the existing <a href={UPSTREAM}>OpenTelemetry Demo</a> as a
          local test application. A test helper enabled its payment failure
          flag. The agent received the symptom and time window, without the
          expected cause.
        </p>
        <p>
          Payment logs reported <code>Invalid token</code>. Checking the source
          showed that a feature flag deliberately throws that error. The agent
          read the flag&apos;s current setting, compared the earlier healthy
          window, and identified the injected fault. A separate helper reset the
          flag; the recovery samples showed no payment errors.
        </p>
        <p>
          The demo is that saved investigation. You can inspect its reads,
          hypotheses, evidence, and original explanation in the browser.
        </p>
        <div className="intro-evidence-links">
          <Link href="/demo/#step-2">Payment logs</Link>
          <Link href="/demo/#step-4">Source branch</Link>
          <Link href="/demo/#step-5">Flag snapshot</Link>
        </div>
      </section>

      <section className="intro-section" aria-labelledby="implementation-title">
        <h2 id="implementation-title">What I worked on</h2>
        <p>
          The Sentinel code handles telemetry parsing, data reduction, tool
          validation, the model loop, and run records. Python enforces the
          allowed reads and usage limits. Full tool results stay in local files;
          the model receives a smaller selection with explicit omissions.
          Remediation is a recommendation for human review.
        </p>
        <p>
          The application and its fault mechanisms come from OpenTelemetry. The
          Next.js site displays a reviewed export of the run, so viewing it
          needs no running lab or model account.
        </p>
        <Link href="/project/#implementation">
          Implementation and source links
        </Link>
      </section>

      <section className="intro-section" aria-labelledby="development-title">
        <h2 id="development-title">What happened during development</h2>
        <p>
          Two earlier investigations failed: the streaming adapter missed a
          completed tool call, then the model requested an invalid argument for
          a configuration tool. Those failures led to parser and schema changes
          with regression tests. The successful run still had a trace export
          timeout.
        </p>
        <p>
          I then captured 12 fault and control cases and ran 48 AI evaluation
          attempts, including a comparison of context strategies. Nine of 27
          primary fault trials produced the correct cause; failed decisions and
          exhausted budgets remain in that denominator. The{" "}
          <a href={`${REPO}/blob/main/docs/validation/resume-evaluation.md`}>
            evaluation report
          </a>{" "}
          includes grounding reviews and the provider failures that blocked an
          abstention follow-up.
        </p>
        <Link href="/project/#development">
          Failure history, changes, and tests
        </Link>
      </section>
    </main>
  );
}
