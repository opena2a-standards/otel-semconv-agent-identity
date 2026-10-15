# OpenTelemetry SemConv for Agent Identity

OpenTelemetry semantic conventions for AI agent authorization observability. Reference implementation for the proposal filed at https://github.com/open-telemetry/semantic-conventions-genai/issues/180.

## The attributes

See [`registry/agent.yaml`](registry/agent.yaml) and [`registry/fga.yaml`](registry/fga.yaml) for full definitions.

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

The `trust.score`, `drift.score`, and `scan.verdict` attributes are producer-emitted decision inputs, not normative computed values: see [Framing](docs/framing.md#framing).

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

## Vendor attributes

`extensions/org.opena2a/` defines five `org.opena2a.*` vendor attributes for agent authorization spans: session and accessed data labels, the grant id, the egress decision, and the threat technique id. They are not filed upstream and are not part of #291 or #180. See `extensions/org.opena2a/README.md` for the definitions, an example span and the consistency check.

## Try it

Run the AIM backend OTel demo stack at `apps/backend/deployments/otel-demo` and observe FGA authorization spans in Grafana Tempo. The run steps, dashboards and sample queries are in [`docs/REFERENCE-IMPLEMENTATION.md`](docs/REFERENCE-IMPLEMENTATION.md#quick-start).

## Standards process

This proposal is tracked at https://github.com/open-telemetry/semantic-conventions-genai/issues/180. Comments and review welcome there.

## Documentation

- [`docs/framing.md`](docs/framing.md): what this proposal is, and why the trust, drift and scan attributes are producer-emitted decision inputs.
- [`docs/REFERENCE-IMPLEMENTATION.md`](docs/REFERENCE-IMPLEMENTATION.md#reference-implementation): how the AIM backend emits these attributes, its naming note, its demo stack and sample queries.
- [`examples/README.md`](examples/README.md): the LangChain to OpenTelemetry bridge.
- [`extensions/org.opena2a/README.md`](extensions/org.opena2a/README.md): the vendor attribute definitions, an example span and the consistency check.
- [`CHANGELOG.md`](CHANGELOG.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## License

[Apache 2.0](LICENSE).
