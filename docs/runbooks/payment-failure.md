# First manual incident: payment failures

This developer lab scenario was reproduced on 2026-10-04 with real metrics,
traces, and logs; cleanup and successful new transactions were verified. See
[the measured record](../validation/payment-failure.md). It is manual evidence
collection, not an AI evaluation. It uses the upstream `paymentFailure` feature
flag, whose `100%` variant forces charge failures. See the
[pinned flag configuration](https://github.com/open-telemetry/opentelemetry-demo/blob/dedc0178918e260823323b8d95005a8cb924b007/src/flagd/demo.flagd.json).
The service is named `payment` in this release; PRD names such as
`payment-service` and example Redis incidents are illustrative.

## Procedure

1. Start the target with `make demo-up`; allow synthetic traffic to warm up.
2. Run `make demo-verify`, `make metric-names`, `make metrics`, and `make services`.
   Use the verified schema in `infra/docker/log-schema.json` and run the opt-in
   live tests shown in [the telemetry guide](../telemetry.md). Reinspect schema
   mappings if the target has changed. Skipped tests are pending validation.
3. Confirm successful checkout traffic in the demo load generator and Jaeger.
   Record a healthy baseline with `uv run python scripts/capture.py baseline --seconds 120`.
   If there are no charge requests, an injected
   charge fault cannot produce useful investigation evidence.
4. Run `make lab-inject SCENARIO=payment-failure`. Record the flag file's write
   time using the commands below. This is not a runtime propagation acknowledgment.
   Leave the load generator running for at least two minutes so real requests
   and exported counter samples enter the incident window.
5. Query traces with `uv run python -m sentinel traces --service payment --start <unix-seconds> --end <unix-seconds>`.
   Inspect affected checkout traces and failing payment spans in Jaeger. Save
   trace/span IDs and relevant error information, not just a screenshot.
6. Query logs with `uv run python -m sentinel logs --service payment --index 'otel-logs*' --schema infra/docker/log-schema.json --start <unix-seconds> --end <unix-seconds> --severity warn`.
   Inspect logs in Grafana/OpenSearch and confirm the actual payment error and
   resource/timestamp fields. Group counts describe the returned sample. Confirm that failures overlap the incident
   window and correlate with the failing spans.
7. Capture the incident using `scripts/capture.py` below. It records service
   discovery, payment server-call counters by span status, server-span p95 in
   milliseconds, bounded traces/log groups, and dependency edges. Inspect the
   exact expressions in the capture. `up` is absent in this deployment; backend
   availability would not establish successful charge operations anyway.
8. Run `make lab-reset`, then verify new payment requests succeed and error
   signals recover. Wait at least two minutes and collect a recovery capture.
   If any collection fails, reset the fault before troubleshooting. Stop the
   lab with `make demo-down` when finished, or leave it healthy for review.

Capture precise windows with these developer commands. The variable names refer
to file-write timestamps; inspect traces/logs to determine runtime behavior.

```bash
uv run python scripts/capture.py baseline --seconds 120
make lab-inject SCENARIO=payment-failure
FAULT_START=$(uv run python -c 'from pathlib import Path; print(Path(".cache/demo/source/src/flagd/demo.flagd.json").stat().st_mtime)')
# Allow synthetic traffic to run for at least two minutes.
uv run python scripts/capture.py incident --start "$FAULT_START"
make lab-reset
RESET_START=$(uv run python -c 'from pathlib import Path; print(Path(".cache/demo/source/src/flagd/demo.flagd.json").stat().st_mtime)')
# Allow new requests and telemetry export for at least two minutes.
uv run python scripts/capture.py recovery --start "$RESET_START"
```

Default output filenames include the phase and timestamp and are never overwritten.
Each capture uses the fixed localhost lab endpoints, records independent tool
errors, and exits nonzero if any signal fails. `complete=true` means all reads
succeeded; inspect sample limits, backend warnings, and actual observations
before making a diagnosis or a coverage claim.

## Ground truth and cleanup

Use real timestamps for baseline, incident, and recovery windows; replace the
angle-bracket placeholders above. Record exact commands, trace/span IDs,
index/document IDs, field configuration, and tool audit records. Re-run the
queries over a recovery window after reset. The first run's captures are local,
ignored files in `var/live-validation/`; the durable validation document records
their observed windows and representative IDs. Synthetic tests establish parser
behavior and are separate from this incident evidence.

The injected cause is the enabled payment-failure flag, not an inferred deployment
regression. The pinned `src/payment/charge.js` evaluates the flag numerically,
assigns the `gold` attribute inside the fault branch, and throws
`Payment request failed. Invalid token. demo.user_context.loyalty_level=gold`.
It does not restrict failures to customers who already belong to a gold cohort.
The catch path records an exception and ERROR span status; `src/payment/index.js`
logs it at lowercase `warn` and returns a gRPC error. Checkout then returns an
error to the frontend. Use trace references and shared log trace IDs to verify
this propagation; an error string alone cannot establish its cause.

Counter observations may lag logs and remain nonzero after recovery because
they are cumulative. Check new transaction completion logs, new successful
traces, and a flattened error counter after the export transition. The first
validation record preserves a late counter increase instead of hiding it.

The helper persists the prior variant in `.cache/demo/fault-state.json` before
changing the watched configuration. Reset restores that variant, even if it was
not `off`, and leaves other flags alone. Do not use the feature UI to change the
same flag concurrently with the tracked scenario. If the session stops early,
run `make lab-reset` before the next investigation.

Checkpoint 1 was acknowledged after this manual validation. The implemented
agent now awaits the first live AI diagnosis and checkpoint 2 review; see
[the investigation guide](../investigation.md).
