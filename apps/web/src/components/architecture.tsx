"use client";
import { useState } from "react";
import { REPO } from "@/lib/replay";
import { Icon } from "./icons";

const components = [
  {
    id: "telemetry",
    title: "Telemetry lab",
    label: "Prometheus · OpenSearch · Jaeger",
    detail:
      "OpenTelemetry Demo generates requests, metrics, logs, and traces. Test helpers inject and reset faults. The model receives the service and incident window; the expected cause is kept outside its context.",
    file: "infra/docker/demo.lock.json",
  },
  {
    id: "tools",
    title: "Read-only tools",
    label: "Fixed queries → reduced evidence",
    detail:
      "Python adapters parse backend responses. Tools use fixed queries, group logs, select spans, and limit source excerpts. The model cannot choose arbitrary queries, endpoints, files, or commands.",
    file: "sentinel/agent/diagnostics.py",
  },
  {
    id: "agent",
    title: "Investigation loop",
    label: "Read → test hypotheses → cite",
    detail:
      "The loop validates model decisions, checks tool permissions and run limits, and requires citations to successful earlier reads. It sends at most 32 KB of selected context through the OpenAI SDK.",
    file: "sentinel/agent/runner.py",
  },
  {
    id: "audit",
    title: "Full local audit",
    label: "Results · events · usage · OTel",
    detail:
      "Local files retain full tool results, decisions, contexts, model responses, usage, and trace spans. PostgreSQL is not implemented. OTLP export failed during the recorded run; its 25 local spans were retained.",
    file: "sentinel/observability.py",
  },
  {
    id: "viewer",
    title: "Public replay",
    label: "Reviewed export → Next.js → Pages",
    detail:
      "A reviewed export selects the recorded decisions and evidence for this Next.js site. Private fields stay local. GitHub Pages serves the recording without running the agent or connecting to telemetry backends.",
    file: "sentinel/replay.py",
  },
];
export function Architecture() {
  const [selected, select] = useState("tools");
  const current = components.find((c) => c.id === selected)!;
  return (
    <div className="architecture">
      <div className="arch-flow" aria-label="Architecture components">
        {components.map((component, index) => (
          <div className="arch-node-wrap" key={component.id}>
            <button
              type="button"
              className={`arch-node ${selected === component.id ? "selected" : ""}`}
              aria-pressed={selected === component.id}
              onClick={() => select(component.id)}
            >
              <span className="mono">0{index + 1}</span>
              <strong>{component.title}</strong>
              <span>{component.label}</span>
            </button>
            {index < components.length - 1 && (
              <span className="arch-arrow" aria-hidden="true">
                →
              </span>
            )}
          </div>
        ))}
      </div>
      <p className="fine-print arch-caption">
        Select a component for details. Python enforces tool permissions and run
        limits; full audit files are separate from model context.
      </p>
      <div className="arch-detail" aria-live="polite">
        <span className="eyebrow">{current.title}</span>
        <p>{current.detail}</p>
        <a href={`${REPO}/blob/main/${current.file}`} className="text-link">
          Source code <Icon name="external" size={14} />
        </a>
      </div>
    </div>
  );
}
