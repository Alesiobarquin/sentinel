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
      "The pinned external OpenTelemetry Demo generates real requests, metrics, logs, and distributed traces. Developer-owned helpers inject reversible faults. The model receives an incident window, not the scenario's expected answer.",
    file: "infra/docker/demo.lock.json",
  },
  {
    id: "tools",
    title: "Native read-only tools",
    label: "Fixed queries → reduced evidence",
    detail:
      "Typed adapters parse backend responses. Semantic tools choose fixed queries and deterministic grouping, ranking, span selection, and bounded source excerpts. The application allows observed services; the model cannot choose arbitrary queries, endpoints, files, or commands.",
    file: "sentinel/agent/diagnostics.py",
  },
  {
    id: "agent",
    title: "One bounded agent",
    label: "Read → test hypotheses → cite",
    detail:
      "The explicit loop validates structured model decisions, enforces tool scope and budgets, and checks that citations refer to successful prior evidence. The model sees at most 32 KB of selected context; omissions remain explicit. A direct model adapter uses the OpenAI SDK. There is no multi-agent framework.",
    file: "sentinel/agent/runner.py",
  },
  {
    id: "audit",
    title: "Full local audit",
    label: "Results · events · usage · OTel",
    detail:
      "Full tool payloads, model decisions, contexts, native responses, audit events, usage, and self-trace spans remain outside selected model context in local run files. The current system uses file persistence; PostgreSQL is a later phase. OTLP delivery failed during the showcased run, while its 25 local spans remained.",
    file: "sentinel/observability.py",
  },
  {
    id: "viewer",
    title: "Public replay",
    label: "Reviewed export → Next.js → Pages",
    detail:
      "A developer-acknowledged causal review and source-record hashes admit an offline publication. Field allowlists remove private data. This static Next.js site displays the actual recorded decisions and selected evidence. Browsing does not start model inference or connect to local telemetry.",
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
        Application policy surrounds the tool/agent boundary. Full audit and
        selected model context are separate. Select a component to inspect it.
      </p>
      <div className="arch-detail" aria-live="polite">
        <span className="eyebrow">{current.title}</span>
        <p>{current.detail}</p>
        <a href={`${REPO}/blob/main/${current.file}`} className="text-link">
          Read the implementation <Icon name="external" size={14} />
        </a>
      </div>
    </div>
  );
}
