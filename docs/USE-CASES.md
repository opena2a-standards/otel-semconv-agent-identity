# Use cases

Who reads these conventions, the question each reader brings, and where the definitions answer it. The attribute definitions in [`registry/agent.yaml`](../registry/agent.yaml) and [`registry/fga.yaml`](../registry/fga.yaml) are the proposal's normative text; [`extensions/org.opena2a/registry.yaml`](../extensions/org.opena2a/registry.yaml) defines the vendor attributes. Each citation below points into one of those files or into the notes beside them.

## Who reads this

| Reader | The question they bring | Where it is answered |
|---|---|---|
| Security leader or CISO | What should every agent platform record about an authorization decision, and what must I not compare between vendors? | [`registry/agent.yaml:40-64`](../registry/agent.yaml) and [`registry/fga.yaml:12-43`](../registry/fga.yaml); the use case [A security leader asks what to require of every agent platform](#a-security-leader-asks-what-to-require-of-every-agent-platform) |
| IAM professional or identity architect | How do the agent id, key algorithm and grant on a span relate to the identity systems I run? | [`registry/agent.yaml:10-26`](../registry/agent.yaml) and [`extensions/org.opena2a/registry.yaml:60-77`](../extensions/org.opena2a/registry.yaml); the use case [An identity team wants each decision tied to a key and a grant](#an-identity-team-wants-each-decision-tied-to-a-key-and-a-grant) |
| Platform or security engineer | Why was a call refused, and where do the spans come from? | The first use case below, and the run steps and troubleshooting in [`REFERENCE-IMPLEMENTATION.md`](REFERENCE-IMPLEMENTATION.md#quick-start) |
| Agent developer or implementer | What do I emit first, and how do I check it? | The LangChain bridge in [`examples/README.md`](../examples/README.md), and the check and tests in [`extensions/org.opena2a/`](../extensions/org.opena2a/README.md) |
| GRC, audit or compliance reader | What is the record of one decision, and who may read it? | The [privacy section](../extensions/org.opena2a/README.md#privacy) of the vendor attributes; the use case [An auditor asks for the record of one refused action](#an-auditor-asks-for-the-record-of-one-refused-action) |
| Standards reviewer (IETF, AIW or OpenTelemetry participant) | What problem is this, what does OpenTelemetry define already, and what is its status? | [`framing.md`](framing.md), the [relation to the semantic conventions](../extensions/org.opena2a/README.md#relation-to-opentelemetry-semantic-conventions), and the upstream [issue #180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180) and [pull request #291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291); every attribute is `experimental` or `development` |

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

## A security leader asks what to require of every agent platform

Three teams run agents on three different platforms. After an incident the security leader asks each team the same questions: which agent did this, what was it trying to do, and which rule allowed or refused it? Each platform records something different, and one reports a "trust score" that means nothing next to the others.

Reader: security leader or CISO.

Without the conventions: each platform records authorization decisions in its own words, so the evidence after an incident depends on where the agent ran, and a decision may not be traceable to an agent and a rule at all.

What the conventions do: they name what an authorization span carries: the agent's id and key algorithm ([`registry/agent.yaml:10-26`](../registry/agent.yaml)), the capability it tried to invoke ([`registry/agent.yaml:30-39`](../registry/agent.yaml)), and the decision path: the authorization step, the outcome, and on a denial the step that denied ([`registry/fga.yaml:12-43`](../registry/fga.yaml)). A requirement can name those attributes. The trust and drift scores are producer-defined and not comparable between producers ([`registry/agent.yaml:43-46`](../registry/agent.yaml), [`registry/agent.yaml:61-64`](../registry/agent.yaml)), and a producer that emits one SHOULD also emit its method token, which changes when the scoring method changes rather than the agent ([`registry/agent.yaml:47-54`](../registry/agent.yaml)). The requirement to write is therefore the method token with every score, never one vendor's score compared with another's.

What you can do today: read what the reference producer emits under [What the backend emits](REFERENCE-IMPLEMENTATION.md#what-the-backend-emits). Not runnable here: the reference producer's demo stack lives in the AIM repository and needs Docker, and the LangChain example needs `langchain-core` and the OpenTelemetry SDK, which this repository does not install.

Where it stops today: every attribute here has stability `experimental` ([`registry/agent.yaml:12`](../registry/agent.yaml)), the upstream pull request is open and not merged, and the namespace of the `fga.*` attributes is still to be decided ([`registry/fga.yaml:5-10`](../registry/fga.yaml)). The reference producer emits the earlier `agent.*` names beside the scoped ones ([`REFERENCE-IMPLEMENTATION.md:11`](REFERENCE-IMPLEMENTATION.md#reference-implementation)).

Out of scope: how a score or verdict is computed. The conventions standardize the name, type and range, and leave the method to the producer ([`framing.md:9`](framing.md#framing)). They record decisions; they do not make them.

## An identity team wants each decision tied to a key and a grant

An agent did something it should not have. The identity team needs two answers quickly: which identity was it acting as, and what do we revoke? The trace shows a service name and a status code; the agent's key and the grant it acted under sit in other systems, if they were recorded at all.

Reader: IAM professional or identity architect.

Without the conventions: the path from a decision to the agent's key and to the grant is rebuilt by hand.

What the conventions do: `gen_ai.agent.id` is a stable identifier for the agent instance, and its examples include a DID ([`registry/agent.yaml:10-16`](../registry/agent.yaml)). `gen_ai.agent.public_key.algorithm` records the algorithm of the agent's identity keypair, aligned with the JSON Web Key registries (RFC 7517 section 4.1), and a verifier that meets an identifier it does not recognise SHOULD refuse to verify rather than make a best effort ([`registry/agent.yaml:17-26`](../registry/agent.yaml)). The vendor attribute `org.opena2a.grant.id` records the `jti` claim of the Agent Authorization Protocol grant the operation ran under, so an operator can go from a span to the exact grant to revoke; instrumentation MUST NOT record the token itself or any downstream credential ([`extensions/org.opena2a/registry.yaml:60-75`](../extensions/org.opena2a/registry.yaml)).

How it maps onto what the team runs: the span reuses identifiers the identity side already holds, the algorithm names of the JSON Web Key registries and the `jti` of a grant. The conventions do not mention OAuth 2.0, OpenID Connect, SPIFFE or X.509 certificates, and they do not say how an agent id is issued or how a key is verified.

What you can do today: run the vendor attribute check, then read the agent id and grant id from the example span.

```bash
python3 extensions/org.opena2a/check.py
jq -c '.resourceSpans[].scopeSpans[].spans[].attributes[] | select(.key == "gen_ai.agent.id" or .key == "org.opena2a.grant.id") | {(.key): .value.stringValue}' extensions/org.opena2a/example-span.json
```

```
OK 5 attributes, example span and relation table consistent
{"gen_ai.agent.id":"did:opena2a:agent:acme/orders-reader"}
{"org.opena2a.grant.id":"4b1d2c3e5f60718293a4b5c6d7e8f901"}
```

Where it stops today: no producer emits the `org.opena2a.*` attributes yet, and they are not filed upstream ([`extensions/org.opena2a/README.md:3-5`](../extensions/org.opena2a/README.md)).

Out of scope: authenticating the agent, verifying its key and enforcing the grant. The attributes are operator-side telemetry; the egress decision MUST NOT be returned to the agent context ([`extensions/org.opena2a/registry.yaml:109-111`](../extensions/org.opena2a/registry.yaml)).

## An auditor asks for the record of one refused action

A tool call that would have sent data out of a session was refused. Months later an auditor asks for the record: which agent, under which grant, what kinds of data the session had touched, and which known attack the refusal relates to. That record says which kinds of data the agent touched, so it is sensitive in its own right.

Reader: GRC, audit or compliance reader.

Without the conventions: the record is spread across logs with no shared names, and nobody has decided who may read it.

What the conventions do: one span carries the agent id, the grant id, the session's data labels, the egress decision and the threat technique id, and each value is defined by the specification that owns it, cited in the attribute's registry note ([`extensions/org.opena2a/registry.yaml:11-132`](../extensions/org.opena2a/registry.yaml)). A technique id MUST resolve to a technique in the AI Agent Threat Matrix, and producers MUST NOT mint their own ([`extensions/org.opena2a/registry.yaml:120-125`](../extensions/org.opena2a/registry.yaml)). The privacy section says a label set reveals which classes of data an agent touched, and asks that these attributes get the access controls of the data they describe and the same retention as the audit log ([`extensions/org.opena2a/README.md:45-47`](../extensions/org.opena2a/README.md#privacy)). The repository maps the attributes to sections of the Agent Authorization Protocol and to threat matrix technique ids; it maps them to no control framework.

What you can do today: read the example span, the record an auditor would be shown.

```bash
jq -c '.resourceSpans[].scopeSpans[].spans[] | {name, attributes: ([.attributes[] | {(.key): (.value.stringValue // [.value.arrayValue.values[].stringValue])}] | add)}' extensions/org.opena2a/example-span.json
```

```
{"name":"egress mcp_tool","attributes":{"gen_ai.agent.id":"did:opena2a:agent:acme/orders-reader","org.opena2a.grant.id":"4b1d2c3e5f60718293a4b5c6d7e8f901","org.opena2a.session.label":["internal","residency:eu"],"org.opena2a.egress.decision":"denied","org.opena2a.threat.technique_id":"T-8004"}}
```

Where it stops today: the example span is a fixture written for this repository, not a recording from a running broker, and no producer emits these attributes yet ([`extensions/org.opena2a/README.md:5`](../extensions/org.opena2a/README.md)).

Out of scope: the retention period and the access policy themselves, which belong to the deployment.

Why you can check this yourself: the attribute definitions are [`registry/agent.yaml`](../registry/agent.yaml) and [`registry/fga.yaml`](../registry/fga.yaml); the upstream filing is [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) (issue [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180)); the vendor extension, its example span and its check with tests are under [`extensions/org.opena2a/`](../extensions/org.opena2a/); the LangChain bridge is in [`examples/`](../examples/); and the reference producer is the AIM backend.
