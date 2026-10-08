# OpenTelemetry SemConv for Agent Identity

OpenTelemetry semantic conventions for AI agent authorization observability. Reference implementation for the proposal filed at https://github.com/open-telemetry/semantic-conventions-genai/issues/180.

## What this is

A focused proposal capturing agent authorization decisions in OpenTelemetry traces, metrics, and logs. The attributes are scoped under the `gen_ai.agent.*` namespace per the OpenTelemetry GenAI semantic conventions; the proposal is filed upstream as [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) (issue [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180)). The OpenA2A Agent Identity Management (AIM) backend is the reference producer; see the Reference implementation section for its current emission status.

## Use cases

### An agent's tool call was denied, or allowed, and nobody can say why

An agent's request was refused, or worse, it went through, and the trace shows an HTTP call and a status code. It does not show which agent made it, which capability it exercised, what its trust score was at that moment, or which policy step said no. The on-call engineer rebuilds the story from three systems.

These conventions put that story on the span: the agent id and key algorithm, the capability invoked, the trust, drift and scan signals as producer-emitted inputs with their method tokens, and the authorization decision path with its step and outcome.

What you can do today: instrument a LangChain agent with [`examples/langchain.py`](examples/langchain.py), or run the reference producer's demo stack at `apps/backend/deployments/otel-demo` in [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management) and view the authorization spans in Grafana Tempo.

Where it stops today: the upstream pull request is open and not merged.

### Your SIEM needs the same technique ids as your threat model

A broker denies a tool call that would have carried data out of a session. The operators want to know which grant it ran under, which data labels the session had accumulated, and which catalogued attack technique the denial relates to, in the telemetry they already collect.

Five vendor attributes under `org.opena2a.*` carry the session's labels, the labels one operation admitted, the grant id, the egress decision and the AI Agent Threat Matrix technique id, each defined by the specification that owns the value.

What you can do today:

```bash
git clone https://github.com/opena2a-standards/otel-semconv-agent-identity
cd otel-semconv-agent-identity
python3 extensions/org.opena2a/check.py
```

Where it stops today: these five attributes are vendor-namespaced and not filed upstream; they are operator-side telemetry and are never returned to the agent.

Why you can check this yourself: the attribute definitions are [`registry/agent.yaml`](registry/agent.yaml) and [`registry/fga.yaml`](registry/fga.yaml); the upstream filing is [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) (issue [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180)); the vendor extension, its example span and its check with tests are under [`extensions/org.opena2a/`](extensions/org.opena2a/); the LangChain bridge is in [`examples/`](examples/); and the reference producer is the AIM backend.

## The attributes

Core identity:
- `gen_ai.agent.id`
- `gen_ai.agent.public_key.algorithm` (fail-closed verifier guidance on unknown algorithm identifiers)

Action context:
- `gen_ai.agent.capability`

Decision inputs (producer-emitted), each paired with an opaque method/version token:
- `gen_ai.agent.trust.score` / `gen_ai.agent.trust.method`
- `gen_ai.agent.drift.score` / `gen_ai.agent.drift.method`
- `gen_ai.agent.scan.verdict` / `gen_ai.agent.scan.method`

FGA decision path (namespace placement pending the working-group decision in #180; deferred from #291):
- `fga.step`
- `fga.outcome`
- `fga.denied_by`

See `registry/agent.yaml` and `registry/fga.yaml` for full definitions.

## Vendor attributes

`extensions/org.opena2a/` defines five `org.opena2a.*` vendor attributes for agent authorization spans: session and accessed data labels, the grant id, the egress decision, and the threat technique id. They are not filed upstream and are not part of #291 or #180. See `extensions/org.opena2a/README.md` for the definitions, an example span and the consistency check.

## Framing

The `trust.score`, `drift.score`, and `scan.verdict` attributes are producer-emitted decision inputs, not normative computed values. The producer computes the score (or selects the verdict) using whatever method makes sense for their domain. The convention only standardizes the attribute name, type, and range (or value set) so downstream observers can correlate. Each is paired with a `.method` token — an opaque, producer-scoped string for the method and version that produced the value, compared for equality only — so a consumer can distinguish a change in the scoring method from a real change in the agent's behaviour. Producers documenting their scoring or scanning methodology is recommended but not normative.

For `scan.verdict` specifically: in the OpenA2A reference implementation, the value is read from a per-agent `agent_security_contexts` record that is intended to be written by an integration with the HackMyAgent scanner via the Registry's `PATCH /internal/asc/:agentId` endpoint. That producer integration is on the roadmap; the demo seeds a `'CLEAN'` value into the same record so the attribute appears on the trace end-to-end. Other producers can wire any scanner they trust to the same convention.

## Reference implementation

The AIM backend at https://github.com/opena2a-org/agent-identity-management computes the producer-side signals today in `apps/backend/internal/application/fga_engine.go` — identity, capability, trust and drift scores, and the FGA decision path are emitted live; the scan verdict is read from a producer-populated `agent_security_contexts` record (see the Framing section for the scanner integration status).

Note on naming: the AIM backend dual-emits both name sets on the `fga.authorize` span. It sets the scoped `gen_ai.agent.*` attributes from this proposal and upstream #291 (`gen_ai.agent.capability`, `gen_ai.agent.public_key.algorithm`, and the trust, drift and scan `.score`/`.verdict` values with their `.method` tokens) in `apps/backend/internal/telemetry/genai_attrs.go`. It also keeps the pre-scoping names (`agent.trust_score`, `agent.drift_score`, `agent.scan_verdict`, etc.) documented in `docs/REFERENCE-IMPLEMENTATION.md`. The pre-scoping `agent.*` set is retired once the dashboards that read it move to the scoped names.

A LangChain instrumentation example is at `examples/langchain.py`.

## Try it

Run the AIM backend OTel demo stack at `apps/backend/deployments/otel-demo` and observe FGA authorization spans in Grafana Tempo with these 9 attributes attached.

## Standards process

This proposal is tracked at https://github.com/open-telemetry/semantic-conventions-genai/issues/180. Comments and review welcome there.

## Contributing

See `CONTRIBUTING.md`.

## License

Apache 2.0.
