# Read-only Kubernetes fixture

The official application runs in Compose. A separate kind cluster demonstrates
Kubernetes adapter and RBAC behavior without running another full copy of the
demo. This follows Compose first, then kind; migration of the investigation
target to Kubernetes remains future work.

```bash
make demo-down
make kind-up
make pods
make kind-verify
SENTINEL_K8_LIVE_TESTS=1 uv run python -m unittest discover -s tests -p test_live_kubernetes.py
make kind-down
make demo-up
```

`kind_lab.py` downloads kind `v0.33.0` into the ignored repository cache and
verifies its published SHA-256. The node is pinned to
`kindest/node:v1.34.11@sha256:44e222ee2132dab25ff87301682f89eb82c7880ea3a1bf543bfe9708fd08d67d`,
compatible with local kubectl 1.34. Cluster `sentinel-lab` binds its API to
loopback; `kind.json` and `fixture.json` describe the complete local setup.
No global kubeconfig is changed and no existing cluster is deleted.

The developer bootstrap uses an admin identity to create the namespace, fixture
pod, service account, Role, and RoleBinding. That identity is never used by the
agent. The reader Role grants only `get`/`list` on `pods`/`events` in
`sentinel-fixture`. There is no secret access, cluster-wide visibility, write
permission, exec, or arbitrary kubectl tool.

The adapter uses HTTPS with the cluster CA and a protected, one-hour reader
token. It constructs only namespaced GET paths for pods/events, fixes the label
selector, validates identities, limits response size, rejects redirects, and
retains readiness, restart counts, current/last termination reasons, event
counts, timestamps, and sampling indicators. Environment variables, mounted
secrets, and arbitrary pod specifications never enter its output.

It reads up to 15 pods and events for at most five of them, up to ten events each.
Pagination is visible. Missing status is unknown; zero returned pods does not
establish that a service is healthy. Events are sampled and may be expired or
unordered; this is current state, not deployment history or metrics-server data.

The live permission check uses the actual reader kubeconfig with `auth can-i`,
not merely admin impersonation. It proves pod/event reads are allowed, while
pod creation/patching, secrets, and another namespace are denied. It performs
no negative write attempt. Adapter and permission tests passed against kind.

Files under `.cache/kind/` are owner-only. `admin.conf` belongs only to developer
setup; `reader.json`, `reader.conf`, CA, and token belong to reads. Renew an
expired token using `make kind-credentials`. For a configured Kubernetes target,
export `SENTINEL_KUBERNETES_CONFIG` explicitly. Do not point a Compose incident at
the fixture and claim its pods belong to the application.

Kind shares Docker resources with the demo and other projects. The original
32 MiB fixture recorded OOM restarts; its limit was increased to 64 MiB and the
fixture was recreated for validation. Later the 64 MiB fixture and CoreDNS were
also OOM-killed, while the shared Docker VM had about 459 MiB available memory
and essentially no free swap. Raising only the fixture's limit did not resolve
the simultaneous-runtime problem. A combined suite hit Kubernetes API timeouts;
the failure record is retained. Validate Compose and kind separately on this
shared VM, as shown above. Stop the isolated cluster after tests. `kind-down` removes
only `sentinel-lab` and its local credentials; rebuilding is reproducible.

Before changing RBAC, understand the separate admin/reader identities, the
transport path allowlist, TLS validation, response bounds, and missing-data
semantics. Agent infrastructure writes still require checkpoint 3. See the
[official kind release](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0)
and [Kubernetes RBAC documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/).
