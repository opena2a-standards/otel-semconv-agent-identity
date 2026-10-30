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

## Vendor attributes

`extensions/org.opena2a/` defines five `org.opena2a.*` vendor attributes for agent authorization spans: session and accessed data labels, the grant id, the egress decision, and the threat technique id. They are not filed upstream and are not part of #291 or #180. See `extensions/org.opena2a/README.md` for the definitions, an example span and the consistency check.

## Try it

Run the AIM backend OTel demo stack at `apps/backend/deployments/otel-demo` and observe FGA authorization spans in Grafana Tempo. The run steps, dashboards and sample queries are in [`docs/REFERENCE-IMPLEMENTATION.md`](docs/REFERENCE-IMPLEMENTATION.md#quick-start).

## Who this is for

- **Security leaders and CISOs**: what to require every agent platform to record about an authorization decision.
- **IAM professionals and identity architects**: how the agent id, key algorithm and grant on a span relate to the identities you issue.
- **Platform and security engineers, and agent developers**: why a call was refused, and how to emit and check these attributes.
- **GRC, audit and compliance readers, and standards reviewers**: the record of one decision, and how it relates to existing OpenTelemetry conventions.

[`docs/USE-CASES.md`](docs/USE-CASES.md) gives each reader's question, where the definitions answer it, and the use cases for each.

## Standards process

This proposal is tracked at https://github.com/open-telemetry/semantic-conventions-genai/issues/180. Comments and review welcome there.

## Documentation

- [`docs/framing.md`](docs/framing.md): what this proposal is, and why the trust, drift and scan attributes are producer-emitted decision inputs.
- [`docs/USE-CASES.md`](docs/USE-CASES.md): who reads these conventions, and five use cases, each with what you can check today and where it stops.
- [`docs/REFERENCE-IMPLEMENTATION.md`](docs/REFERENCE-IMPLEMENTATION.md#reference-implementation): how the AIM backend emits these attributes, its naming note, its demo stack and sample queries.
- [`examples/README.md`](examples/README.md): the LangChain to OpenTelemetry bridge.
- [`extensions/org.opena2a/README.md`](extensions/org.opena2a/README.md): the vendor attribute definitions, an example span and the consistency check.
- [`CHANGELOG.md`](CHANGELOG.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## License

[Apache 2.0](LICENSE).
