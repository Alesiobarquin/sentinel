import Link from "next/link";
import { Icon } from "@/components/icons";
import { ErrorComparison } from "@/components/error-comparison";
import { number, replay, REPO, seconds, totalTokens } from "@/lib/replay";

export default function Home() {
  return (
    <main id="main">
      <section className="hero container">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="status-dot" /> AI incident investigation ·
            read-only
          </p>
          <h1>
            An incident,
            <br />
            <em>investigated.</em>
          </h1>
          <p className="hero-description">
            Scattered signals become a defensible diagnosis. Sentinel tests
            hypotheses against real metrics, logs, traces, and source code—then
            shows its evidence.
          </p>
          <div className="hero-actions">
            <Link className="button primary" href="/demo/">
              Explore the investigation <Icon name="arrow" />
            </Link>
            <Link className="button secondary" href="/project/">
              Read the project
            </Link>
          </div>
          <p className="hero-note">
            A real recorded run. Explore it without signing in.
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
              <h2>Charge requests are failing.</h2>
              <p>October 5, 2026 · local distributed-system lab</p>
            </div>
          </div>
          <ErrorComparison compact />
          <div className="preview-verdict">
            <span className="eyebrow">Cause supported by evidence</span>
            <h3>
              A flag-controlled failure,
              <br />
              disguised as a token error.
            </h3>
            <div className="preview-citations">
              <span>Metrics</span>
              <span>Logs</span>
              <span>Traces</span>
              <span>Source</span>
              <span>Config</span>
            </div>
            <p>
              The source throws the exact observed error when{" "}
              <code>paymentFailure</code> is active. The current snapshot
              selects <code>100%</code>.
            </p>
          </div>
          <div className="preview-bottom">
            <Icon name="check" size={16} />
            <span>
              Fault reset by the developer helper; sampled recovery verified.
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
          <span>recorded investigation</span>
        </div>
        <div>
          <strong>{number(totalTokens)}</strong>
          <span>reported model tokens</span>
        </div>
        <div>
          <strong>1</strong>
          <span>correct live case · no accuracy claim</span>
        </div>
      </section>
      <section className="container home-flow">
        <div className="section-heading">
          <div>
            <p className="eyebrow">From symptom to explanation</p>
            <h2>Every conclusion needs a trail.</h2>
          </div>
          <p>
            The interesting part is how the agent gets there. Follow what it
            reads, what it considers, and what the evidence can actually prove.
          </p>
        </div>
        <div className="flow-cards">
          <article>
            <span className="flow-number">01 / OBSERVE</span>
            <h3>Read the real system</h3>
            <p>
              Fixed telemetry queries and typed adapters reduce backend data
              before it reaches the model. Evidence keeps its source, window,
              and coverage.
            </p>
          </article>
          <article>
            <span className="flow-number">02 / INVESTIGATE</span>
            <h3>Test competing explanations</h3>
            <p>
              One bounded loop selects a read, updates hypotheses, and cites
              observations. Application policy validates every decision outside
              the prompt.
            </p>
          </article>
          <article>
            <span className="flow-number">03 / REVIEW</span>
            <h3>Make the cause inspectable</h3>
            <p>
              The diagnosis links back to evidence and states its limits.
              Proposed infrastructure changes need approval; this version cannot
              execute them.
            </p>
          </article>
        </div>
      </section>
      <section className="container home-story">
        <div>
          <p className="eyebrow">The engineering behind it</p>
          <h2>
            A small agent.
            <br />A real systems problem.
          </h2>
          <p>
            Sentinel&apos;s original work is the tool layer, evidence reduction,
            contracts, agent loop, authentication, policy, auditing, and this
            viewer. The OpenTelemetry Demo is the external application under
            investigation.
          </p>
          <Link href="/project/" className="text-link">
            Architecture, decisions, lessons, and limitations{" "}
            <Icon name="arrow" />
          </Link>
        </div>
        <div className="story-notes">
          <div>
            <Icon name="code" />
            <h3>An audit you can inspect</h3>
            <p>
              Original evidence IDs, recorded decisions, measured usage, and
              source-record hashes—not a scripted diagnosis.
            </p>
          </div>
          <div>
            <Icon name="check" />
            <h3>Failures stay visible</h3>
            <p>
              Two earlier investigations failed at transport and validation
              boundaries. Those outcomes led to concrete fixes and regression
              tests.
            </p>
          </div>
        </div>
      </section>
      <section className="container closing-banner">
        <div>
          <span className="eyebrow">Start with one incident</span>
          <h2>See the decision. Check the evidence.</h2>
        </div>
        <Link href="/demo/" className="button primary">
          Open the demo <Icon name="arrow" />
        </Link>
        <a href={REPO} className="text-link">
          Browse the source <Icon name="external" size={15} />
        </a>
      </section>
    </main>
  );
}
