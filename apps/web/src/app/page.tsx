import Link from "next/link";
import { Icon } from "@/components/icons";
import { ErrorComparison } from "@/components/error-comparison";
import { number, replay, seconds, totalTokens } from "@/lib/replay";

export default function Home() {
  return (
    <main id="main">
      <section className="hero container">
        <div className="hero-copy">
          <p className="eyebrow">Student project · incident investigation</p>
          <h1>Sentinel</h1>
          <p className="hero-description">
            I built a Python agent that investigates failures in a local
            distributed system. It reads metrics, logs, traces, source code, and
            configuration, then records a diagnosis with supporting evidence.
          </p>
          <div className="hero-actions">
            <Link className="button primary" href="/demo/">
              View demo <Icon name="arrow" />
            </Link>
            <Link className="button secondary" href="/project/">
              Project notes
            </Link>
          </div>
          <p className="hero-note">
            The demo replays one real investigation. No sign-in required.
          </p>
          <div className="stack-line">
            <span>Python</span>
            <span>OpenTelemetry</span>
            <span>OpenAI SDK</span>
            <span>Next.js</span>
          </div>
        </div>
        <div className="incident-preview">
          <div className="preview-top">
            <span className="mono">INCIDENT / PAYMENT</span>
            <span className="pill recorded">
              <span className="status-dot" /> Recorded
            </span>
          </div>
          <div className="preview-title">
            <span className="signal-icon">
              <Icon name="signal" size={25} />
            </span>
            <div>
              <h2>Payment failure test</h2>
              <p>October 5, 2026 · local distributed-system lab</p>
            </div>
          </div>
          <ErrorComparison compact />
          <div className="preview-verdict">
            <span className="eyebrow">Recorded diagnosis</span>
            <h3>The paymentFailure flag was enabled.</h3>
            <div className="preview-citations">
              <span>Metrics</span>
              <span>Logs</span>
              <span>Traces</span>
              <span>Source</span>
              <span>Config</span>
            </div>
            <p>
              The flag snapshot showed <code>100%</code>. The source branch
              throws the same token error found in the logs and traces.
            </p>
          </div>
          <div className="preview-bottom">
            <Icon name="check" size={16} />
            <span>
              The test helper reset the flag. Recovery samples showed no errors.
            </span>
          </div>
        </div>
      </section>
      <section
        className="container proof-strip"
        aria-label="Measured investigation results"
      >
        <div>
          <strong>{replay.tool_calls}</strong>
          <span>read-only tool calls</span>
        </div>
        <div>
          <strong>{seconds(replay.latency_ms)}</strong>
          <span>investigation duration</span>
        </div>
        <div>
          <strong>{number(totalTokens)}</strong>
          <span>reported model tokens</span>
        </div>
        <div>
          <strong>1</strong>
          <span>correct diagnosis recorded</span>
        </div>
      </section>
      <section className="container home-flow">
        <div className="section-heading">
          <div>
            <h2>How it works</h2>
          </div>
          <p>
            The investigation starts with a service and time window. One model
            loop chooses read-only tools and compares possible causes.
          </p>
        </div>
        <div className="flow-cards">
          <article>
            <span className="flow-number">01</span>
            <h3>Collect telemetry</h3>
            <p>
              Python adapters query Prometheus, OpenSearch, and Jaeger. Results
              are grouped and limited before reaching the model.
            </p>
          </article>
          <article>
            <span className="flow-number">02</span>
            <h3>Compare hypotheses</h3>
            <p>
              The model selects its next read and updates hypotheses. Python
              validates tool arguments, evidence references, and run limits.
            </p>
          </article>
          <article>
            <span className="flow-number">03</span>
            <h3>Record the result</h3>
            <p>
              The run saves its diagnosis, evidence, tool calls, timing, and
              token usage. Remediation is a recommendation; the agent cannot
              change infrastructure.
            </p>
          </article>
        </div>
      </section>
      <section className="container home-story">
        <div>
          <h2>What I built</h2>
          <p>
            My work covers the Python tools, data reduction, agent loop,
            validation, authentication, audit records, tests, and this viewer.
            The application under test is the existing OpenTelemetry Demo.
          </p>
          <Link href="/project/" className="text-link">
            Architecture and lessons <Icon name="arrow" />
          </Link>
        </div>
        <div className="story-notes">
          <div>
            <Icon name="code" />
            <h3>Recorded investigation</h3>
            <p>
              The demo includes the original tool calls, hypotheses, evidence,
              diagnosis, and recovery checks from the local test.
            </p>
          </div>
          <div>
            <Icon name="check" />
            <h3>Testing and fixes</h3>
            <p>
              Two earlier runs failed in model transport and tool validation. I
              fixed those issues and added regression tests. One correct case is
              not an accuracy benchmark.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
