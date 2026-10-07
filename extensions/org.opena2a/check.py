#!/usr/bin/env python3
"""Consistency check for the org.opena2a vendor attribute folder.

Checks that registry.yaml defines exactly the five org.opena2a.* attributes at
stability `development`, each citing its home; that example-span.json is one
span whose attributes are all defined and whose values fit their definitions;
and that README.md carries a relation table row for every attribute.

Usage: python3 check.py [folder]   (exit 0 when consistent, 1 otherwise)
Requires PyYAML.
"""

import json
import pathlib
import re
import sys

import yaml

PREFIX = "org.opena2a."
EXPECTED_IDS = {
    "org.opena2a.session.label",
    "org.opena2a.data.labels_accessed",
    "org.opena2a.grant.id",
    "org.opena2a.egress.decision",
    "org.opena2a.threat.technique_id",
}
# Attributes the example span may carry that are defined upstream, not here.
UPSTREAM_ATTRIBUTES = {"gen_ai.agent.id": "string"}
FORBIDDEN_NAMESPACE = re.compile(r"^(gen_ai|fga)\.")
NAME = re.compile(r"^[a-z][a-z0-9_.]*[a-z0-9]$")
CONSECUTIVE_DELIMITERS = re.compile(r"[._]{2,}")
VALUE_PATTERNS = {
    "org.opena2a.grant.id": re.compile(r"^[0-9a-f]{32}$"),
    "org.opena2a.threat.technique_id": re.compile(r"^T-[0-9]{4}(\.[0-9]{3})?$"),
}
SEMCONV_RELEASE = "v1.44.0"


def load_attributes(registry):
    attrs = []
    for group in registry.get("groups") or []:
        attrs.extend(group.get("attributes") or [])
    return attrs


def check_registry(attrs):
    errors = []
    ids = [a.get("id") for a in attrs]
    if sorted(ids) != sorted(EXPECTED_IDS):
        errors.append(f"registry defines {sorted(ids)}, expected exactly {sorted(EXPECTED_IDS)}")
    for attr in attrs:
        aid = attr.get("id") or "<missing id>"
        if FORBIDDEN_NAMESPACE.match(aid):
            errors.append(f"{aid}: gen_ai.* and fga.* are not this folder's namespace")
        if not aid.startswith(PREFIX):
            errors.append(f"{aid}: not in the {PREFIX}* namespace")
        if not NAME.match(aid) or CONSECUTIVE_DELIMITERS.search(aid):
            errors.append(f"{aid}: name does not follow the semantic-conventions name format")
        if attr.get("stability") != "development":
            errors.append(f"{aid}: stability is {attr.get('stability')!r}, expected 'development'")
        if not str(attr.get("brief") or "").strip():
            errors.append(f"{aid}: brief is empty")
        if "Home:" not in str(attr.get("note") or ""):
            errors.append(f"{aid}: note does not cite the attribute's home")
        if not attr.get("examples"):
            errors.append(f"{aid}: no examples")
        atype = attr.get("type")
        if isinstance(atype, dict):
            members = atype.get("members") or []
            for field in ("id", "value"):
                seen = [m.get(field) for m in members]
                if len(seen) != len(set(seen)):
                    errors.append(f"{aid}: duplicate enum member {field}")
            for m in members:
                if m.get("stability") != "development":
                    errors.append(f"{aid}: member {m.get('id')} stability is not 'development'")
                if not str(m.get("brief") or "").strip():
                    errors.append(f"{aid}: member {m.get('id')} has no brief")
        elif atype not in ("string", "string[]"):
            errors.append(f"{aid}: unexpected type {atype!r}")
    return errors


def span_attributes(otlp):
    spans = [
        span
        for rs in otlp.get("resourceSpans") or []
        for ss in rs.get("scopeSpans") or []
        for span in ss.get("spans") or []
    ]
    if len(spans) != 1:
        raise ValueError(f"expected one example span, found {len(spans)}")
    return {a["key"]: a.get("value") or {} for a in spans[0].get("attributes") or []}


def _string_array(value):
    values = (value.get("arrayValue") or {}).get("values")
    if not isinstance(values, list) or not all("stringValue" in v for v in values):
        return None
    return [v["stringValue"] for v in values]


def check_span(span_attrs, attrs):
    errors = []
    defined = {a["id"]: a for a in attrs if "id" in a}
    for key, value in span_attrs.items():
        if key in UPSTREAM_ATTRIBUTES:
            if "stringValue" not in value:
                errors.append(f"span {key}: expected a string value")
            continue
        attr = defined.get(key)
        if attr is None:
            errors.append(f"span {key}: not defined in registry.yaml")
            continue
        atype = attr.get("type")
        if atype == "string[]":
            items = _string_array(value)
            if items is None:
                errors.append(f"span {key}: expected an array of strings")
            elif items != sorted(set(items)):
                errors.append(f"span {key}: label set is not sorted and duplicate-free")
            continue
        if "stringValue" not in value:
            errors.append(f"span {key}: expected a string value")
            continue
        text = value["stringValue"]
        if isinstance(atype, dict):
            allowed = [m.get("value") for m in atype.get("members") or []]
            if text not in allowed:
                errors.append(f"span {key}: {text!r} is not one of {allowed}")
        pattern = VALUE_PATTERNS.get(key)
        if pattern and not pattern.match(text):
            errors.append(f"span {key}: {text!r} does not match {pattern.pattern}")
    accessed = span_attrs.get("org.opena2a.data.labels_accessed")
    session = span_attrs.get("org.opena2a.session.label")
    if accessed is not None and session is not None:
        a, s = _string_array(accessed), _string_array(session)
        if a is not None and s is not None and not set(a) <= set(s):
            errors.append("span: data.labels_accessed is not a subset of session.label")
    return errors


def check_readme(text, attrs):
    errors = []
    if "not filed" not in text.lower():
        errors.append("README: status line does not say the attributes are not filed")
    section = re.search(r"^## Relation to OpenTelemetry[^\n]*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if section is None:
        return errors + ["README: no relation section"]
    relation = section.group(1)
    if SEMCONV_RELEASE not in relation:
        errors.append(f"README: relation table does not name semantic-conventions {SEMCONV_RELEASE}")
    for attr in attrs:
        row = re.compile(r"^\|\s*`" + re.escape(attr.get("id", "")) + r"`\s*\|", re.MULTILINE)
        if not row.search(relation):
            errors.append(f"README: no relation table row for {attr.get('id')}")
    return errors


def check_folder(folder):
    folder = pathlib.Path(folder)
    attrs = load_attributes(yaml.safe_load((folder / "registry.yaml").read_text()))
    errors = check_registry(attrs)
    try:
        span = span_attributes(json.loads((folder / "example-span.json").read_text()))
    except ValueError as exc:
        errors.append(f"example-span.json: {exc}")
    else:
        errors.extend(check_span(span, attrs))
    errors.extend(check_readme((folder / "README.md").read_text(), attrs))
    return errors


def main(argv):
    folder = argv[1] if len(argv) > 1 else pathlib.Path(__file__).resolve().parent
    errors = check_folder(folder)
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print(f"OK {len(EXPECTED_IDS)} attributes, example span and relation table consistent")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
