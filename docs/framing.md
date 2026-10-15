# Proposal framing

## What this is

A focused proposal capturing agent authorization decisions in OpenTelemetry traces, metrics, and logs. The attributes are scoped under the `gen_ai.agent.*` namespace per the OpenTelemetry GenAI semantic conventions; the proposal is filed upstream as [open-telemetry/semantic-conventions-genai#291](https://github.com/open-telemetry/semantic-conventions-genai/pull/291) (issue [#180](https://github.com/open-telemetry/semantic-conventions-genai/issues/180)). The OpenA2A Agent Identity Management (AIM) backend is the reference producer; see the [Reference implementation](REFERENCE-IMPLEMENTATION.md#reference-implementation) section for its current emission status.

## Framing

The `trust.score`, `drift.score`, and `scan.verdict` attributes are producer-emitted decision inputs, not normative computed values. The producer computes the score (or selects the verdict) using whatever method makes sense for their domain. The convention only standardizes the attribute name, type, and range (or value set) so downstream observers can correlate. Each is paired with a `.method` token — an opaque, producer-scoped string for the method and version that produced the value, compared for equality only — so a consumer can distinguish a change in the scoring method from a real change in the agent's behaviour. Producers documenting their scoring or scanning methodology is recommended but not normative.

For `scan.verdict` specifically: in the OpenA2A reference implementation, the value is read from a per-agent `agent_security_contexts` record that is intended to be written by an integration with the HackMyAgent scanner via the Registry's `PATCH /internal/asc/:agentId` endpoint. That producer integration is on the roadmap; the demo seeds a `'CLEAN'` value into the same record so the attribute appears on the trace end-to-end. Other producers can wire any scanner they trust to the same convention.
