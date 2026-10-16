# Use cases

## An agent's tool call was denied, or allowed, and nobody can say why

An agent's request was refused, or worse, it went through, and the trace shows an HTTP call and a status code. It does not show which agent made it, which capability it exercised, what its trust score was at that moment, or which policy step said no. The on-call engineer rebuilds the story from three systems.

These conventions put that story on the span: the agent id and key algorithm, the capability invoked, the trust, drift and scan signals as producer-emitted inputs with their method tokens, and the authorization decision path with its step and outcome.

What you can do today: instrument a LangChain agent with [`examples/langchain.py`](../examples/langchain.py), or run the reference producer's demo stack at `apps/backend/deployments/otel-demo` in [OpenA2A AIM (Agent Identity Management)](https://github.com/opena2a-org/agent-identity-management) and view the authorization spans in Grafana Tempo.

Where it stops today: the upstream pull request is open and not merged.

## Your SIEM needs the same technique ids as your threat model

A broker denies a tool call that would have carried data out of a session. The operators want to know which grant it ran under, which data labels the session had accumulated, and which catalogued attack technique the denial relates to, in the telemetry they already collect.

Five vendor attributes under `org.opena2a.*` carry the session's labels, the labels one operation admitted, the grant id, the egress decision and the AI Agent Threat Matrix technique id, each defined by the specification that owns the value.

What you can do today:

```bash
git clone https://github.com/opena2a-standards/otel-semconv-agent-identity
cd otel-semconv-agent-identity
python3 extensions/org.opena2a/check.py
```

Where it stops today: these five attributes are vendor-namespaced and not filed upstream; they are operator-side telemetry and are never returned to the agent.

Why you can check this yourself: the attribute definitions are [`registry/agent.yaml`](../registry/agent.yaml) and [`registry/fga.yaml`](../registry/fga.yaml); the upstream filing is [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) (issue [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180)); the vendor extension, its example span and its check with tests are under [`extensions/org.opena2a/`](../extensions/org.opena2a/); the LangChain bridge is in [`examples/`](../examples/); and the reference producer is the AIM backend.
