# org.opena2a vendor attributes

**Status: not filed. There is no upstream venue for these attributes. They use the `org.opena2a.*` vendor namespace, as the OpenTelemetry naming guidance recommends for company-specific names. Privacy: a label set recorded in telemetry reveals which data classes an agent touched.**

Five attributes for agent authorization spans: the data labels a session has accumulated, the labels one operation admitted, the grant an operation ran under, the outcome of the broker's egress check, and the threat technique a producer associates with a decision. No producer emits them yet.

This folder is separate from the proposal filed upstream. The `gen_ai.agent.*` and `fga.*` definitions in [`registry/`](../../registry/) do not change, and nothing here is part of [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291).

## Files

| File | Contents |
|---|---|
| [`registry.yaml`](registry.yaml) | Attribute definitions in the semantic-conventions model format, stability `development`. |
| [`example-span.json`](example-span.json) | One span in OTLP JSON carrying the attributes. |
| [`check.py`](check.py) | Consistency check for this folder (requires PyYAML). |
| [`test_check.py`](test_check.py) | Tests for the check. |

Check the folder:

```bash
python3 extensions/org.opena2a/check.py
python3 -m unittest discover -s extensions/org.opena2a -p 'test_*.py'
```

## The attributes

Each attribute records a value that another specification already defines. The home is where that value's meaning lives; the registry note on each attribute cites the section.

| Attribute | Type | Home |
|---|---|---|
| `org.opena2a.session.label` | string[] | [AAP](https://github.com/opena2a-standards/agent-authorization-protocol) AAP-SPEC §4.4.2 and §6.4 (the L3 BAC `session_label` claim); broker profile §6.10 rule 2 |
| `org.opena2a.data.labels_accessed` | string[] | AAP-SPEC §4.4.2; broker profile §6.10 rule 1 |
| `org.opena2a.grant.id` | string | AAP-SPEC §4.2 (CGT `jti`), §5 (DA), §7.3 (grant revocation list) |
| `org.opena2a.egress.decision` | enum: `allowed`, `denied`, `escalation_approved` | Broker profile §6.10 rule 3; AAP-SPEC §4.4.1 (`egressCeiling`) |
| `org.opena2a.threat.technique_id` | string | [AI Agent Threat Matrix](https://threats.opena2a.org) technique ids (`T-NNNN`, `T-NNNN.NNN`) |

Labels are sets, not levels, as AAP-SPEC §4.4.2 defines them. Producers SHOULD emit a label set sorted and without duplicates, so equal sets compare equal. `org.opena2a.session.label` keeps a singular name although its value is an array: it names one value, the AAP session label, which is itself a set, and mirrors the `session_label` claim. An empty array and an absent attribute mean different things: an empty `session.label` says the session has admitted no labeled field, while an absent one says the producer holds no session label for the agent.

## Example span

[`example-span.json`](example-span.json) is a broker span for a tool call that would carry data out of the session. The session has already admitted fields labeled `internal` and `residency:eu`. The grant's `mcp_tool` entry has no `egressCeiling`, so its ceiling is the empty set and the broker denies the egress (broker profile §6.10 rule 3). The producer associates the attempt with technique T-8004, Tool Chain Exfiltration. No data was admitted by this operation, so the span does not carry `org.opena2a.data.labels_accessed`.

The agent receives the same opaque denial whatever the cause (broker profile §6.6). These attributes are operator-side telemetry and are never returned to the agent context.

## Privacy

A label set says which classes of data an agent touched, for example that a session read health records or EU-resident data. Anyone who can read the trace learns that, even though no field value is recorded. Treat these attributes with the access controls of the data they describe: restrict who can query spans that carry them, and apply the same retention as the audit log.

## Relation to OpenTelemetry semantic conventions

Measured against [semantic-conventions v1.44.0](https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.44.0) (released 2026-08-04: 734 active attribute ids in `model/`) and [semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai) at commit `4f85037` (no release yet: 89 active attribute ids). The GenAI conventions moved to that repository in v1.42.0. Neither defines any of the five names or any `org.*` attribute. The search covered every attribute id for the terms label, grant, egress, technique, threat, clearance and sensitivity, plus the closest concepts by meaning.

| Attribute | Nearest upstream attribute | Relation |
|---|---|---|
| `org.opena2a.session.label` | `session.id` (v1.44.0); `gen_ai.conversation.id` (GenAI) | Different concept. Those identify a session; this records the sensitivity labels the session has accumulated. An AAP session is keyed by the agent's DID at the broker, not by a client session id. |
| `org.opena2a.data.labels_accessed` | `container.label`, `k8s.pod.label` and the other `*.label` templates (v1.44.0); `gen_ai.evaluation.score.label` (GenAI) | Same word, different meaning. Those are resource key/value metadata or an evaluation result, not data sensitivity classes. |
| `org.opena2a.grant.id` | None. `enduser.scope` is deprecated in v1.44.0 with no replacement; `aspnetcore.authorization.policy` names a framework policy. | No equivalent. Neither identifies a minted grant token or the key of a revocation list. |
| `org.opena2a.egress.decision` | `aspnetcore.authorization.result` (v1.44.0, `success` / `failure`) | Same pattern, different scope. That attribute is specific to ASP.NET Core and records whether authorization succeeded; this records a label-ceiling egress check, including approval through an escalation hook. |
| `org.opena2a.threat.technique_id` | `security_rule.category`, `security_rule.reference`, `security_rule.uuid` (v1.44.0) | Complementary. `security_rule.*` describes the detection rule that fired; the technique id names the attack technique in a public taxonomy. Both can appear on one span. |

`fga.outcome` ([open-telemetry/semantic-conventions-genai#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180), deferred from #291) records the outcome of a fine-grained authorization step. `org.opena2a.egress.decision` records a later, separate check: whether the data a session already holds may leave it.

## Why a vendor namespace

The [naming guidance](https://github.com/open-telemetry/semantic-conventions/blob/v1.44.0/docs/general/naming.md#recommendations-for-application-developers) recommends prefixing company-specific names with the company's reverse domain name, and advises against using an existing OpenTelemetry namespace such as `gen_ai.*` for them. These attributes would move to an upstream namespace only through a proposal a working group accepts, with the old names deprecated in favor of the new ones.
