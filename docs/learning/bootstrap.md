# Bootstrap learning guide

Metrics describe numeric behavior over time. Logs record events. Traces connect
individual operations across service boundaries. Their value during an incident
comes from matching service identity and time windows, then using one signal to
test explanations suggested by another.

OpenTelemetry standardizes instrumentation and transport. The Collector receives
signals, processes them, and exports them to storage/query backends. Prometheus,
Jaeger, and OpenSearch fill different roles; installing a Collector alone does
not give Sentinel a historical query API.

Docker Compose establishes a local group of containers and their networking.
Kubernetes later adds deployments, reconciliation, scheduling, service discovery,
RBAC, and cluster evidence. Terraform is for provisioning the later disposable
AWS environment; it is not needed to test the current local telemetry adapters.

The adapters translate backend JSON to explicit Python types. That is a
contract boundary. Actual reasoning must eventually operate on
reduced evidence, competing hypotheses, and observable tool calls. A missing
sample or failed tool request must not masquerade as a healthy metric.

## Questions the developer should be able to answer

1. Which parts of this repository are original Sentinel code, and which are
   downloaded upstream assets?
2. What does pinning a source commit guarantee, and what remains mutable when
   container images are only pinned by tag?
3. How do telemetry signals reach the query backends from the demo application?
4. Why is `up` absent in this deployment? When it is present, why does `up = 1`
   fail to prove that payment charges are succeeding?
5. What is the difference between an instant query and a range query?
6. Why must NaN, empty matches, warnings, and request errors remain distinguishable?
7. How would you establish that a payment failure is the cause of a checkout
   symptom rather than a coincidental event?
8. Why should percentiles not be averaged or recomputed from percentile samples?
9. What does the current audit record prove, and what does it not guarantee?
10. Why keep manual lab writes outside the future agent tool registry?
11. What must be tested against the actual demo before the first AI investigation?
12. Why do we wait for checkpoint acknowledgment before major agent implementation?

## Telemetry adapter questions

1. Why do trace queries use microseconds while dependency queries use milliseconds?
2. Why does summing overlapping spans exaggerate a trace's observed duration?
3. What evidence might be omitted by selecting only five spans from a trace?
4. Why does an exact service filter require a keyword field, and why might its
   `.keyword` multi-field be absent from `_source`?
5. How does a count of two repeated errors in the newest 50 logs differ from a
   frequency across every log in the incident window?
6. What makes a timed-out or partially successful search unsuitable as complete
   evidence, even if it returns plausible documents?
7. How would you verify a trace/log correlation independently in the backends?
8. Why would filtering payment logs by uppercase `ERROR` miss this fault?
9. Why can a cumulative error counter remain nonzero or increase briefly after
   the flag is reset? How do new transaction logs and traces help verify recovery?

At checkpoint 1, demonstrate the local data flow and manually reproduce one
incident. Use these questions to explain the system before adding AI complexity.
