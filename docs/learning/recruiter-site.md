# Learning review: public recruiter delivery

Read [the site operation guide](../recruiter-site.md) and
[ADR 009](../decisions/009-recruiter-demo-hosting.md) before changing the viewer.
The public site runs independently of the local incident lab. Understand these
boundaries before describing the project in an interview.

1. Draw the path from an actual local tool call through its audit/evidence record,
   reviewed export, Next.js build, and browser evidence panel. Which data is
   intentionally excluded, and where does the full record remain?
2. Explain why a static export still supports interactive React playback without
   running Python, telemetry backends, or a model in public. Which features would
   require a different deployment architecture?
3. Explain why `/sentinel` belongs in routes, assets, downloads, and public browser
   checks. Why can a working development server hide deployment failures?
4. Demonstrate one diagnosis citation and one hypothesis at an earlier step.
   What prevents a hypothesis from citing a future read? What do record hashes
   establish, and what still requires human causal/privacy review?
5. Reproduce the mobile layout issue conceptually: how can a grid's minimum
   content width create overflow and make visible controls fail normal taps?
6. Distinguish 122 deterministic cases, 22 browser checks, six telemetry and two
   Kubernetes integrations, three fault scenarios, and one correct AI diagnosis.
   Why do these results not establish an accuracy rate?
7. Explain deployment permissions and cleanup. Why does publishing through a
   developer's CLI not enable Sentinel's investigation agent to write to GitHub?

Use [the delivery review](../checkpoints/05-recruiter-delivery.md) for demo flow,
current limitations, and resume wording that matches demonstrated behavior.
