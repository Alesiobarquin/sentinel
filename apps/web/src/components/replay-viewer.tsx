"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EvidencePanel, Hypotheses, Citation } from "./evidence";
import { ErrorComparison } from "./error-comparison";
import { Icon } from "./icons";
import {
  evidenceTitle,
  number,
  replay,
  REPO,
  seconds,
  stepTitle,
  totalTokens,
  utc,
} from "@/lib/replay";

export function ReplayViewer() {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [evidenceId, setEvidence] = useState<string | null>(
    replay.evidence[0].id,
  );
  const recoveryIndex = replay.steps.length;
  const current = replay.steps[index];
  const isRecovery = index === recoveryIndex;
  const diagnosed = current?.action === "diagnose";
  const available = isRecovery
    ? replay.evidence
    : replay.evidence.slice(
        0,
        current.action === "diagnose" ? replay.evidence.length : index + 1,
      );
  const selected = replay.evidence.find((e) => e.id === evidenceId);

  useEffect(() => {
    const match = window.location.hash.match(/^#step-(\d+)$/);
    if (match) setIndex(Math.min(recoveryIndex, Number(match[1])));
  }, [recoveryIndex]);
  useEffect(() => {
    setEvidence(
      replay.steps[index]?.evidence_id ??
        (index === recoveryIndex ? null : "ev_006"),
    );
    if (index === recoveryIndex) setPlaying(false);
    window.history.replaceState(null, "", `#step-${index}`);
  }, [index, recoveryIndex]);
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () => setIndex((i) => Math.min(recoveryIndex, i + 1)),
      3800,
    );
    return () => window.clearInterval(timer);
  }, [playing, recoveryIndex]);
  function selectStep(next: number) {
    setPlaying(false);
    setIndex(next);
  }

  return (
    <div className="container demo-shell">
      <div className="demo-heading">
        <div>
          <p className="eyebrow">
            <span className="status-dot" /> Recorded investigation / October 5,
            2026
          </p>
          <h1>Payment investigation</h1>
          <p>
            This recording shows how Sentinel identified the cause of a failed
            payment test. View the result, or step through the original
            investigation.
          </p>
        </div>
        <Link href="/project/" className="text-link">
          Project overview <Icon name="arrow" />
        </Link>
      </div>
      <div className="recording-notice">
        <span className="pill recorded">Recorded · real telemetry</span>
        <p>
          Use the step controls to see the original reads. Evidence buttons open
          the data behind a decision. Playback is condensed; measurements are
          from the recorded run.
        </p>
      </div>
      <div className="demo-stats">
        <div>
          <span>Symptom</span>
          <strong>Payment charge failures</strong>
        </div>
        <div>
          <span>Model / calls</span>
          <strong>
            {replay.model} / {replay.model_calls}
          </strong>
        </div>
        <div>
          <span>Recorded run</span>
          <strong>
            {seconds(replay.latency_ms)} / {replay.tool_calls} reads
          </strong>
        </div>
        <div>
          <span>Reported tokens</span>
          <strong>
            {number(totalTokens)} / {number(replay.budget.max_total_tokens)}
          </strong>
        </div>
      </div>
      <div className="playback-controls">
        <div className="playback-buttons">
          <button
            className="button primary small"
            onClick={() => {
              if (index === recoveryIndex) setIndex(0);
              setPlaying((p) => !p);
            }}
            aria-label={playing ? "Pause replay" : "Play replay"}
          >
            <Icon name={playing ? "pause" : "play"} size={15} />
            {playing ? "Pause" : "Play replay"}
          </button>
          <button
            className="icon-button"
            aria-label="Previous step"
            disabled={index === 0}
            onClick={() => selectStep(index - 1)}
          >
            <Icon name="back" />
          </button>
          <button
            className="icon-button"
            aria-label="Next step"
            disabled={isRecovery}
            onClick={() => selectStep(index + 1)}
          >
            <Icon name="arrow" />
          </button>
          <button
            className="icon-button"
            aria-label="Reset replay"
            onClick={() => selectStep(0)}
          >
            <Icon name="reset" size={16} />
          </button>
          <span className="mono playback-counter">
            {String(index + 1).padStart(2, "0")} / {recoveryIndex + 1}
          </span>
        </div>
        <button
          className="text-button"
          onClick={() => selectStep(recoveryIndex - 1)}
        >
          View result <Icon name="arrow" size={15} />
        </button>
      </div>
      <div className="replay-grid">
        <aside className="timeline">
          <h2 className="eyebrow">Investigation steps</h2>
          <ol>
            {replay.steps.map((step, i) => (
              <li
                key={i}
                className={i === index ? "active" : i < index ? "visited" : ""}
              >
                <button
                  aria-current={i === index ? "step" : undefined}
                  aria-label={`Step ${i + 1}: ${stepTitle(step)}`}
                  onClick={() => selectStep(i)}
                >
                  <span className="timeline-index">
                    {i < index ? (
                      <Icon name="check" size={12} />
                    ) : (
                      String(i + 1).padStart(2, "0")
                    )}
                  </span>
                  <span>
                    <strong>{stepTitle(step)}</strong>
                    <small>
                      {step.evidence_id ?? "6 final citations"} · +
                      {seconds(step.at_ms)}
                    </small>
                  </span>
                </button>
              </li>
            ))}
            <li className={isRecovery ? "active recovery" : "recovery"}>
              <button
                aria-current={isRecovery ? "step" : undefined}
                onClick={() => selectStep(recoveryIndex)}
                aria-label="Step 10: Developer reset and recovery"
              >
                <span className="timeline-index">10</span>
                <span>
                  <strong>Reset & recovery</strong>
                  <small>Test helper · recovery checks</small>
                </span>
              </button>
            </li>
          </ol>
          <div className="timeline-footnote">
            <Icon name="check" size={15} />
            <p>
              Eight read-only tools. Recommendations cannot execute changes.
            </p>
          </div>
        </aside>
        <section
          className="replay-workspace"
          aria-label="Current investigation step"
        >
          <div className="step-heading">
            <div>
              <span className="eyebrow">
                {isRecovery
                  ? "Developer exercise"
                  : diagnosed
                    ? "Investigation outcome"
                    : `Read ${index + 1} of ${replay.tool_calls}`}
              </span>
              <h2>{isRecovery ? "Recovery checks" : stepTitle(current)}</h2>
            </div>
            <span className="pill">
              {isRecovery
                ? "After reset"
                : current.model_call
                  ? `Model decision ${current.model_call}`
                  : "Initial read"}
            </span>
          </div>
          <p className="sr-only" aria-live="polite">
            Step {index + 1}:{" "}
            {isRecovery ? "Recovery checks" : stepTitle(current)}
          </p>
          {isRecovery ? (
            <section className="recovery-panel">
              <div className="recovery-success">
                <span className="signal-icon">
                  <Icon name="check" size={26} />
                </span>
                <div>
                  <h3>No payment errors in the recovery samples</h3>
                  <p>
                    The test helper restored the prior flag at{" "}
                    {utc(replay.reset_at)} UTC. Sentinel did not execute
                    remediation.
                  </p>
                </div>
              </div>
              <ErrorComparison />
              <div className="recovery-facts">
                <div>
                  <strong>
                    {replay.recovery.selected_service_error_spans}
                  </strong>
                  <span>selected payment error spans</span>
                </div>
                <div>
                  <strong>
                    {replay.recovery.sampled_warning_or_error_logs}
                  </strong>
                  <span>sampled warning/error logs</span>
                </div>
                <div>
                  <strong>
                    {replay.recovery.all_reads_succeeded ? "5/5" : "Partial"}
                  </strong>
                  <span>recovery reads succeeded</span>
                </div>
              </div>
              <p className="fine-print">
                Sampled signals and successful reads do not prove complete
                application health. All fault defaults were verified off; the
                tracked fault was absent. The helper owns scenario cleanup,
                while the agent remains read-only.
              </p>
              <Link href="/project/#validation" className="text-link">
                Validation and remaining limitations <Icon name="arrow" />
              </Link>
            </section>
          ) : (
            <>
              <div className="decision-reason">
                <span className="eyebrow">Recorded decision</span>
                <p>{current.reason}</p>
                {current.usage && (
                  <span className="fine-print">
                    This model call: {number(current.usage.input_tokens)} input
                    + {number(current.usage.output_tokens)} output tokens ·{" "}
                    {seconds(current.model_latency_ms!)}
                  </span>
                )}
              </div>
              {diagnosed && (
                <article className="diagnosis-panel">
                  <div>
                    <span className="pill success">Cause supported</span>
                    <span className="fine-print">
                      Model ranking score {replay.diagnosis.confidence} · not a
                      probability
                    </span>
                  </div>
                  <h3>Payment failure setting enabled</h3>
                  <p>
                    A test setting was causing payment requests to fail. The
                    agent matched the errors to the enabled setting and the
                    corresponding source-code branch.
                  </p>
                  <details className="limitations">
                    <summary>Original model explanation</summary>
                    <p>{replay.diagnosis.root_cause}</p>
                  </details>
                  <div className="citation-row">
                    {replay.diagnosis.evidence_ids.map((id) => (
                      <Citation key={id} id={id} onSelect={setEvidence} />
                    ))}
                  </div>
                  <div className="recommendation">
                    <span className="eyebrow">
                      Recommendation / approval required
                    </span>
                    <p>{replay.diagnosis.recommended_remediation}</p>
                    <span className="pill">
                      The agent cannot execute this recommendation
                    </span>
                  </div>
                  <details className="limitations">
                    <summary>Diagnosis limitations</summary>
                    <ul>
                      {replay.diagnosis.limitations.map((value) => (
                        <li key={value}>{value}</li>
                      ))}
                    </ul>
                  </details>
                </article>
              )}
              <div className="evidence-tabs" aria-label="Collected evidence">
                {available.map((e) => (
                  <button
                    key={e.id}
                    aria-label={`View evidence ${e.id}`}
                    aria-pressed={e.id === evidenceId}
                    className={e.id === evidenceId ? "selected" : ""}
                    onClick={() => setEvidence(e.id)}
                  >
                    <span className="mono">{e.id}</span>
                    <span>{e.kind === "source_code" ? "source" : e.kind}</span>
                  </button>
                ))}
              </div>
              <div className="step-content">
                <div>
                  {selected && (
                    <>
                      <h3 className="evidence-title">
                        {evidenceTitle(selected)}
                      </h3>
                      <EvidencePanel evidence={selected} />
                    </>
                  )}
                </div>
                <Hypotheses
                  values={current.hypotheses}
                  onSelect={setEvidence}
                />
              </div>
            </>
          )}
        </section>
      </div>
      <div className="recording-footer">
        <div>
          <span className="eyebrow">Audit & provenance</span>
          <p className="mono">{replay.run_id}</p>
          <span>
            ChatGPT subscription run; exact credit use is unavailable. Browsing
            this replay makes no model requests.
          </span>
        </div>
        <div>
          <a href="/sentinel/investigation.json" download className="text-link">
            Download public record <Icon name="arrow" size={14} />
          </a>
          <a
            href={`${REPO}/blob/main/docs/checkpoints/02-first-investigation.md`}
            className="text-link"
          >
            Investigation review <Icon name="external" size={14} />
          </a>
        </div>
      </div>
    </div>
  );
}
