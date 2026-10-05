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
        {compact
          ? "Payment errors during the test"
          : "Estimated payment server errors"}{" "}
        <span>Three recorded 3-minute windows</span>
      </figcaption>
      <div className="comparison-bars">
        {(compact
          ? ["Before failure", "During failure", "After reset"]
          : ["Baseline", "Incident", "Recovery"]
        ).map((label, index) => (
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
        {compact
          ? "Estimates from recorded requests. The test helper reset the failure setting before checking recovery."
          : "Span-derived estimates; export delay and extrapolation apply. Recovery followed the test helper's reset."}
      </p>
    </figure>
  );
}
