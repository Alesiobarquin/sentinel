import {
  type Evidence,
  type Hypothesis,
  utc,
} from "@/lib/replay";
import { Icon } from "./icons";

export function Citation({
  id,
  onSelect,
  negative = false,
}: {
  id: string;
  onSelect: (id: string) => void;
  negative?: boolean;
}) {
  return (
    <button
      type="button"
      className={`citation ${negative ? "negative" : ""}`}
      onClick={() => onSelect(id)}
      aria-label={`Inspect evidence ${id}`}
    >
      {id}
      <Icon name="external" size={10} />
    </button>
  );
}

export function Hypotheses({
  values,
  onSelect,
}: {
  values: Hypothesis[];
  onSelect: (id: string) => void;
}) {
  return (
    <aside className="hypotheses">
      <div className="panel-heading">
        <span className="eyebrow">Hypotheses at this decision</span>
        <span className="mono">{values.length}</span>
      </div>
      {values.length === 0 ? (
        <p className="empty-hypotheses">
          The initial inventory read happens before the model forms hypotheses.
        </p>
      ) : (
        values.map((h) => (
          <article className={`hypothesis ${h.status}`} key={h.name}>
            <span className={`hypothesis-status ${h.status}`}>{h.status}</span>
            <h3>{h.name}</h3>
            <p>{h.explanation}</p>
            {h.supporting_evidence.length > 0 && (
              <div className="hypothesis-refs">
                <span>Supports</span>
                <div>
                  {h.supporting_evidence.map((id) => (
                    <Citation key={id} id={id} onSelect={onSelect} />
                  ))}
                </div>
              </div>
            )}
            {h.contradicting_evidence.length > 0 && (
              <div className="hypothesis-refs">
                <span>Contradicts</span>
                <div>
                  {h.contradicting_evidence.map((id) => (
                    <Citation key={id} id={id} onSelect={onSelect} negative />
                  ))}
                </div>
              </div>
            )}
          </article>
        ))
      )}
      <p className="fine-print">
        These are concise recorded hypotheses. Confidence ranks explanations; it
        is not a probability.
      </p>
    </aside>
  );
}

export function EvidenceBody({ evidence }: { evidence: Evidence }) {
  if (evidence.kind === "inventory")
    return (
      <>
        <p className="body-intro">
          Discovered traced identities define the service allowlist for later
          reads. Inventory alone does not establish health.
        </p>
        <div className="service-chips">
          {evidence.summary.services.map((service) => (
            <span
              key={service}
              className={service === "payment" ? "selected" : ""}
            >
              {service}
            </span>
          ))}
        </div>
        <div className="coverage-note">
          <Icon name="check" />
          <span>
            Read succeeded · {evidence.summary.services.length} identities
            returned, including Sentinel&apos;s own instrumentation.
          </span>
        </div>
      </>
    );
  if (evidence.kind === "metric") {
    const s = evidence.summary;
    return (
      <>
        <div className="evidence-stat-grid">
          {s.calls.values.map((v) => (
            <div key={v.labels.status_code}>
              <span>
                {v.labels.status_code === "STATUS_CODE_ERROR"
                  ? "Estimated server errors"
                  : "Estimated unset-status calls"}
              </span>
              <strong
                className={
                  v.labels.status_code === "STATUS_CODE_ERROR" && v.value > 0
                    ? "error-text"
                    : ""
                }
              >
                {v.value.toFixed(2)}
              </strong>
            </div>
          ))}
          <div>
            <span>p95 server-span duration</span>
            <strong>
              {s.p95_duration_ms.values[0]?.value.toFixed(1) ?? "Unknown"}
              <small> ms</small>
            </strong>
          </div>
        </div>
        <div className="coverage-note">
          <Icon name="signal" />
          <span>
            {s.minimum_counter_samples.values.length
              ? `${Math.min(...s.minimum_counter_samples.values.map((v) => v.value))} minimum raw counter samples per status.`
              : "Raw counter sample coverage is unknown."}{" "}
            These are samples, not requests.
          </span>
        </div>
        <p className="fine-print">
          {s.interpretation} Unset span status does not by itself prove success.
        </p>
        <details className="code-details">
          <summary>Inspect the fixed Prometheus query</summary>
          <pre>
            <code>{s.calls.query}</code>
          </pre>
          <p className="fine-print">
            Window {utc(s.window.start)}–{utc(s.window.end)} UTC · missing
            values are unknown, not zero.
          </p>
        </details>
      </>
    );
  }
  if (evidence.kind === "log") {
    const s = evidence.summary;
    return (
      <>
        <div className="evidence-meta">
          <span>
            {s.returned_count} returned / {s.matched_count} matched (
            {s.matched_count_relation})
          </span>
          <span>
            {s.sample_complete ? "Matching sample complete" : "Partial sample"}
          </span>
        </div>
        <div className="log-groups">
          {s.groups.map((g, index) => (
            <article
              className={`log-group ${g.severity === "warn" ? "warning" : ""}`}
              key={index}
            >
              <div>
                <span className="log-level">{g.severity ?? "unknown"}</span>
                <span className="mono">{g.sample_count} records</span>
              </div>
              <code>{g.message_excerpt}</code>
              <div className="log-time">
                {utc(g.first_seen)}–{utc(g.last_seen)} UTC
                {g.message_truncated && " · message truncated"}
              </div>
              <details>
                <summary>Trace correlation examples</summary>
                {g.records.map((r, i) => (
                  <p className="mono correlation" key={i}>
                    {r.trace_id ?? "No trace ID"}
                    <span>{utc(r.timestamp)} UTC</span>
                  </p>
                ))}
              </details>
            </article>
          ))}
        </div>
        <p className="fine-print">
          Exact message/severity groups from the bounded read.{" "}
          {s.omitted_groups} groups omitted; at most{" "}
          {s.record_examples_per_group} correlation examples per group. Complete
          here refers to matching returned records, not all application
          activity.
        </p>
      </>
    );
  }
  if (evidence.kind === "trace") {
    const s = evidence.summary;
    return (
      <>
        <div className="evidence-meta">
          <span>
            {s.trace_count} traces returned · {s.traces.length} selected
          </span>
          <span className="warning-text">
            {s.limit_reached ? "Read limit reached" : "Within read limit"}
          </span>
        </div>
        <p className="body-intro">
          Payment errors propagate into checkout and the frontend path. The
          model sees bounded spans, with parent references retained.
        </p>
        <div className="trace-groups">
          {s.traces.map((trace, i) => (
            <details key={trace.trace_id} open={i === 0}>
              <summary>
                <span className="mono">{trace.trace_id.slice(0, 12)}…</span>
                <span>
                  {trace.error_span_count} error spans in returned trace
                </span>
              </summary>
              <p className="mono trace-id">{trace.trace_id}</p>
              <div className="span-list">
                {trace.spans.map((span) => (
                  <div className="span-row" key={span.span_id}>
                    <span className="span-dot" />
                    <div>
                      <strong>{span.service}</strong>
                      <code>{span.operation}</code>
                    </div>
                    <span>{span.duration_ms.toFixed(1)} ms</span>
                  </div>
                ))}
              </div>
              <p className="trace-error">
                {String(
                  trace.spans.find((span) => span.service === "payment")
                    ?.attributes["otel.status_description"] ??
                    "No selected payment status description",
                )}
              </p>
              <p className="fine-print">
                {trace.spans.length} selected of {trace.span_count} returned
                spans · {trace.omitted_span_count} spans omitted.{" "}
                <span className="mono">{trace.spans[0]?.span_id}</span> is the
                first selected span ID.
              </p>
            </details>
          ))}
        </div>
        <p className="fine-print">
          {s.omitted_traces} traces omitted from selected model context.
          Sampling and selected spans cannot exclude every other dependency
          issue.
        </p>
      </>
    );
  }
  if (evidence.kind === "source_code") {
    const s = evidence.summary;
    return (
      <>
        <p className="body-intro">
          This is the external application&apos;s source. The payment branch
          generates the exact error seen in logs and traces.
        </p>
        {s.files.map((file) => (
          <div className="source-file" key={file.file}>
            <a
              className="file-link"
              href={`https://github.com/open-telemetry/opentelemetry-demo/blob/${s.commit}/${file.file}`}
            >
              <Icon name="code" size={16} />
              <span>{file.file}</span>
              <Icon name="external" size={13} />
            </a>
            {file.file.endsWith("charge.js") && (
              <pre className="source-excerpt">
                <code>
                  {file.excerpt
                    .split("\n")
                    .filter((line) => {
                      const n = Number(line.split(":")[0]);
                      return n >= 38 && n <= 50;
                    })
                    .join("\n")}
                </code>
              </pre>
            )}
            <details className="code-details">
              <summary>
                Full selected excerpt · {file.selected_lines}/{file.total_lines}{" "}
                lines
              </summary>
              <pre>
                <code>{file.excerpt}</code>
              </pre>
              <p className="mono hash">SHA-256 {file.sha256}</p>
            </details>
          </div>
        ))}
        <p className="fine-print">
          Pinned commit <code>{s.commit.slice(0, 12)}</code>. {s.limitation} The
          gold attribute is assigned inside the failure branch; it is not a
          preselected customer cohort.
        </p>
      </>
    );
  }
  const s = evidence.summary;
  return (
    <>
      {s.flags.map((flag) => (
        <article className="flag-record" key={flag.name}>
          <div>
            <span className="mono">{flag.name}</span>
            <strong>{flag.default_variant}</strong>
          </div>
          <p>
            State <code>{flag.state}</code> · configured numeric value{" "}
            <code>{flag.variants[flag.default_variant]}</code> · targeting{" "}
            {flag.has_targeting ? "present" : "absent"}
          </p>
          <div className="flag-variants">
            {Object.entries(flag.variants).map(([name, value]) => (
              <span
                className={name === flag.default_variant ? "selected" : ""}
                key={name}
              >
                {name}
                <small>{value}</small>
              </span>
            ))}
          </div>
        </article>
      ))}
      <div className="coverage-note">
        <Icon name="signal" />
        <span>
          Snapshot observed at {utc(s.observed_at)} UTC. The tool is global:
          service and period arguments are null.
        </span>
      </div>
      <p className="fine-print">{s.limitation}</p>
    </>
  );
}

export function EvidencePanel({ evidence }: { evidence: Evidence }) {
  return (
    <section className="evidence-panel" aria-label="Selected evidence">
      <div className="panel-heading">
        <span className="eyebrow">{evidence.source.replaceAll("_", " ")}</span>
        <span className="evidence-id mono">{evidence.id}</span>
      </div>
      <EvidenceBody evidence={evidence} />
      <details className="provenance">
        <summary>Tool arguments & provenance</summary>
        <pre>
          <code>{JSON.stringify(evidence.tool, null, 2)}</code>
        </pre>
        <p>
          Read latency: {evidence.latency_ms.toFixed(3)} ms · observed at{" "}
          {utc(evidence.observed_at)} UTC
        </p>
        <p className="mono hash">
          Original payload SHA-256: {evidence.payload_sha256}
        </p>
        <p className="fine-print">
          This export contains selected evidence. The full local payload is
          retained outside the website.
        </p>
      </details>
    </section>
  );
}
