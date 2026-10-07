import copy
import json
import pathlib
import unittest

import yaml

import check

FOLDER = pathlib.Path(__file__).resolve().parent


def registry_attrs():
    return check.load_attributes(yaml.safe_load((FOLDER / "registry.yaml").read_text()))


def example_span():
    return check.span_attributes(json.loads((FOLDER / "example-span.json").read_text()))


def string_array(*items):
    return {"arrayValue": {"values": [{"stringValue": i} for i in items]}}


class FolderTest(unittest.TestCase):
    def test_folder_is_consistent(self):
        self.assertEqual(check.check_folder(FOLDER), [])

    def test_no_gen_ai_or_fga_ids(self):
        text = (FOLDER / "registry.yaml").read_text()
        self.assertNotRegex(text, r"(?m)^\s*-?\s*id:\s*(gen_ai|fga)\.")


class RegistryTest(unittest.TestCase):
    def test_rejects_gen_ai_attribute(self):
        attrs = registry_attrs()
        attrs[0] = dict(attrs[0], id="gen_ai.agent.session.label")
        errors = check.check_registry(attrs)
        self.assertTrue(any("not this folder's namespace" in e for e in errors), errors)

    def test_rejects_sixth_attribute(self):
        attrs = registry_attrs()
        attrs.append(dict(attrs[2], id="org.opena2a.grant.issuer"))
        self.assertTrue(any("expected exactly" in e for e in check.check_registry(attrs)))

    def test_rejects_other_stability(self):
        attrs = registry_attrs()
        attrs[1] = dict(attrs[1], stability="experimental")
        self.assertTrue(any("stability" in e for e in check.check_registry(attrs)))

    def test_rejects_attribute_without_home(self):
        attrs = registry_attrs()
        attrs[3] = dict(attrs[3], note="No source given.")
        self.assertTrue(any("home" in e for e in check.check_registry(attrs)))

    def test_rejects_consecutive_delimiters(self):
        attrs = registry_attrs()
        attrs[4] = dict(attrs[4], id="org.opena2a.threat..technique_id")
        self.assertTrue(any("name format" in e for e in check.check_registry(attrs)))


class SpanTest(unittest.TestCase):
    def test_rejects_undefined_attribute(self):
        span = example_span()
        span["org.opena2a.grant.scope"] = {"stringValue": "orders.read"}
        self.assertTrue(any("not defined" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_value_outside_enum(self):
        span = example_span()
        span["org.opena2a.egress.decision"] = {"stringValue": "blocked"}
        self.assertTrue(any("not one of" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_malformed_technique_id(self):
        span = example_span()
        span["org.opena2a.threat.technique_id"] = {"stringValue": "AML.T0051"}
        self.assertTrue(any("does not match" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_malformed_grant_id(self):
        span = example_span()
        span["org.opena2a.grant.id"] = {"stringValue": "grant://orders-db"}
        self.assertTrue(any("does not match" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_unsorted_label_set(self):
        span = example_span()
        span["org.opena2a.session.label"] = string_array("residency:eu", "internal")
        self.assertTrue(any("sorted" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_accessed_labels_outside_session_label(self):
        span = copy.deepcopy(example_span())
        span["org.opena2a.data.labels_accessed"] = string_array("secret")
        self.assertTrue(any("subset" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_more_than_one_span(self):
        otlp = json.loads((FOLDER / "example-span.json").read_text())
        spans = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"]
        spans.append(copy.deepcopy(spans[0]))
        with self.assertRaises(ValueError):
            check.span_attributes(otlp)


class ReadmeTest(unittest.TestCase):
    def test_rejects_missing_relation_row(self):
        text = (FOLDER / "README.md").read_text()
        head, relation = text.split("## Relation to OpenTelemetry", 1)
        relation = "\n".join(
            line for line in relation.splitlines() if not line.startswith("| `org.opena2a.grant.id`")
        )
        errors = check.check_readme(head + "## Relation to OpenTelemetry" + relation, registry_attrs())
        self.assertTrue(any("org.opena2a.grant.id" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
