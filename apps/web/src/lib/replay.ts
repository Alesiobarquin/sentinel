import recording from "../../public/investigation.json";

export const REPO = "https://github.com/Alesiobarquin/sentinel";
export const DEMO_COMMIT = "dedc0178918e260823323b8d95005a8cb924b007";
export const UPSTREAM = `https://github.com/open-telemetry/opentelemetry-demo/tree/${DEMO_COMMIT}`;

export type Hypothesis = {
  name: string;
  explanation: string;
  confidence: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  status: "active" | "supported" | "rejected";
};
export type Usage = {
  input_tokens: number;
  output_tokens: number;
  cached_input_tokens: number;
};
export type Tool = {
  name: string;
  service: string | null;
  period: "incident" | "baseline" | null;
};
type Window = { start: number; end: number };
export type Metric = {
  query: string;
  values: {
    labels: { status_code?: string; service_name?: string };
    timestamp: number;
    value: number;
  }[];
  warnings: string[];
  omitted_series: number;
  interpretation?: string;
};
export type MetricSummary = {
  service: string;
  window: Window;
  calls: Metric;
  p95_duration_ms: Metric;
  minimum_counter_samples: Metric;
  interpretation: string;
};
export type LogSummary = {
  service: string;
  window: Window;
  matched_count: number;
  matched_count_relation: string;
  returned_count: number;
  sample_complete: boolean;
  omitted_groups: number;
  record_examples_per_group: number;
  groups: {
    severity: string | null;
    message_excerpt: string;
    message_truncated: boolean;
    sample_count: number;
    first_seen: number;
    last_seen: number;
    records: { timestamp: number; trace_id: string | null }[];
  }[];
};
export type Span = {
  span_id: string;
  service: string;
  operation: string;
  start_time: number;
  duration_ms: number;
  is_error: boolean;
  references: { kind: string; trace_id: string; span_id: string }[];
  attributes: Record<string, string | number | boolean>;
};
export type TraceSummary = {
  service: string;
  window: Window;
  trace_count: number;
  omitted_traces: number;
  limit: number;
  limit_reached: boolean;
  traces: {
    trace_id: string;
    span_count: number;
    error_span_count: number;
    omitted_span_count: number;
    spans: Span[];
    warnings: string[];
  }[];
};
export type SourceSummary = {
  service: string;
  commit: string;
  limitation: string;
  files: {
    file: string;
    excerpt: string;
    sha256: string;
    complete: boolean;
    excerpt_truncated: boolean;
    selected_lines: number;
    total_lines: number;
  }[];
};
export type ConfigurationSummary = {
  observed_at: number;
  limitation: string;
  flags: {
    name: string;
    state: string;
    default_variant: string;
    variants: Record<string, number>;
    has_targeting: boolean;
  }[];
};
type EvidenceBase = {
  id: string;
  source: string;
  observed_at: number;
  tool: Tool;
  success: boolean;
  latency_ms: number;
  payload_sha256: string;
};
export type Evidence = EvidenceBase &
  (
    | { kind: "inventory"; summary: { services: string[] } }
    | { kind: "metric"; summary: MetricSummary }
    | { kind: "log"; summary: LogSummary }
    | { kind: "trace"; summary: TraceSummary }
    | { kind: "source_code"; summary: SourceSummary }
    | { kind: "configuration"; summary: ConfigurationSummary }
  );
export type Step = {
  number: number;
  action: "read" | "diagnose";
  reason: string;
  evidence_id: string | null;
  model_call: number | null;
  at_ms: number;
  hypotheses: Hypothesis[];
  usage: Usage | null;
  model_latency_ms: number | null;
};
export type Observation = {
  estimated_server_error_calls: number | null;
  selected_service_error_spans: number;
  sampled_log_groups: number;
  sampled_warning_or_error_logs: number;
  all_reads_succeeded: boolean;
};
export type Replay = {
  schema_version: number;
  run_id: string;
  recorded_at: string;
  model: string;
  billing_mode: string;
  model_calls: number;
  tool_calls: number;
  input_tokens: number;
  output_tokens: number;
  cached_input_tokens: number;
  approximate_api_cost_usd: number | null;
  usage_unknown: boolean;
  latency_ms: number;
  incident: Window & {
    service: string;
    symptom: string;
    baseline_start: number;
    baseline_end: number;
  };
  budget: {
    max_model_calls: number;
    max_tool_calls: number;
    max_total_tokens: number;
    max_context_bytes: number;
    max_response_bytes: number;
    max_seconds: number;
  };
  diagnosis: {
    root_cause: string;
    confidence: number;
    evidence_ids: string[];
    affected_services: string[];
    recommended_remediation: string;
    remediation_kind: string;
    limitations: string[];
    requires_human_approval: boolean;
    requires_human_review: boolean;
    remediation_execution_available: boolean;
    remediation_executed: boolean;
  };
  evidence: Evidence[];
  steps: Step[];
  baseline: Observation;
  recovery: Observation;
  injected_at: number;
  reset_at: number;
  remediation_executed_by_agent: boolean;
  cleanup_performed_by_developer_exercise: boolean;
  review: {
    acknowledged_on: string;
    note: string;
    expected_cause: string;
    limitations: string[];
    source_hashes: Record<string, string>;
  };
};

// The Python publication validator checks this immutable bundle during CI.
export const replay = recording as unknown as Replay;
export const totalTokens = replay.input_tokens + replay.output_tokens;
export const number = (n: number) => new Intl.NumberFormat("en-US").format(n);
export const seconds = (ms: number) => `${(ms / 1000).toFixed(1)}s`;
export const utc = (epoch: number) =>
  new Date(epoch * 1000).toISOString().slice(11, 19);
export function metricValue(evidence: Evidence, status: string): number | null {
  return evidence.kind === "metric"
    ? (evidence.summary.calls.values.find(
        (v) => v.labels.status_code === status,
      )?.value ?? null)
    : null;
}
export const incidentErrors = metricValue(
  replay.evidence.find((e) => e.id === "ev_002")!,
  "STATUS_CODE_ERROR",
);
export function evidenceTitle(e: Evidence): string {
  const names = {
    inventory: "Service inventory",
    metric: "Payment metrics",
    log: "Payment logs",
    trace: "Distributed traces",
    source_code: "Pinned payment source",
    configuration: "Runtime flag snapshot",
  };
  return `${names[e.kind]}${e.tool.period === "baseline" ? " · baseline" : ""}`;
}
export function stepTitle(step: Step): string {
  return step.action === "diagnose"
    ? "Diagnosis"
    : evidenceTitle(replay.evidence.find((e) => e.id === step.evidence_id)!);
}
