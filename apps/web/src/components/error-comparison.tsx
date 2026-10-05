import { incidentErrors, replay } from "@/lib/replay";

export function ErrorComparison({ compact = false }: { compact?: boolean }) {
  const values = [
    replay.baseline.estimated_server_error_calls,
    incidentErrors,
    replay.recovery.estimated_server_error_calls,
  ];
  return (
    <figure className={`error-comparison ${compact ? "compact" : ""}`}>
      <figcaption>
        Estimated payment server errors{" "}
        <span>Three recorded 180-second windows</span>
      </figcaption>
      <div className="comparison-bars">
        {["Baseline", "Incident", "Recovery"].map((label, index) => (
          <div
            className={`comparison-row ${index === 1 ? "incident" : ""}`}
            key={label}
          >
            <span>{label}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width:
                    values[index] === null
                      ? "0%"
                      : `${Math.max(0, (values[index]! / 10) * 100)}%`,
                }}
              />
            </div>
            <strong>
              {values[index] === null ? "Unknown" : values[index]!.toFixed(1)}
            </strong>
          </div>
        ))}
      </div>
      <p className="fine-print">
        Span-derived estimates; export delay and extrapolation apply. Recovery
        followed the developer helper&apos;s reset.
      </p>
    </figure>
  );
}
