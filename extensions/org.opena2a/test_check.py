import contextlib
import copy
import io
import json
import pathlib
import shutil
import tempfile
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


def copy_folder(target):
    for name in ("registry.yaml", "example-span.json", "README.md"):
        shutil.copy(FOLDER / name, target / name)
    return target


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

    def test_reports_attribute_without_id(self):
        attrs = registry_attrs()
        attrs[2] = {k: v for k, v in attrs[2].items() if k != "id"}
        attrs[3] = dict(attrs[3], id=None)
        errors = check.check_registry(attrs)
        self.assertTrue(any("2 attribute(s) without an id" in e for e in errors), errors)
        check.check_span(example_span(), attrs)
        check.check_readme((FOLDER / "README.md").read_text(), attrs)

    def test_rejects_id_outside_prefix(self):
        attrs = registry_attrs()
        attrs[2] = dict(attrs[2], id="com.example.grant.id")
        errors = check.check_registry(attrs)
        self.assertTrue(any("not in the org.opena2a.* namespace" in e for e in errors), errors)

    def test_rejects_name_with_invalid_characters(self):
        attrs = registry_attrs()
        attrs[2] = dict(attrs[2], id="org.opena2a.Grant.id")
        self.assertTrue(any("name format" in e for e in check.check_registry(attrs)))

    def test_rejects_empty_brief(self):
        attrs = registry_attrs()
        attrs[0] = dict(attrs[0], brief="  ")
        self.assertTrue(any("brief is empty" in e for e in check.check_registry(attrs)))

    def test_rejects_missing_examples(self):
        attrs = registry_attrs()
        attrs[1] = {k: v for k, v in attrs[1].items() if k != "examples"}
        self.assertTrue(any("no examples" in e for e in check.check_registry(attrs)))

    def test_rejects_duplicate_enum_member(self):
        attrs = registry_attrs()
        members = attrs[3]["type"]["members"]
        members.append(copy.deepcopy(members[0]))
        self.assertTrue(any("duplicate enum member" in e for e in check.check_registry(attrs)))

    def test_rejects_enum_member_at_other_stability(self):
        attrs = registry_attrs()
        attrs[3]["type"]["members"][1]["stability"] = "stable"
        errors = check.check_registry(attrs)
        self.assertTrue(any("member denied stability" in e for e in errors), errors)

    def test_rejects_enum_member_without_brief(self):
        attrs = registry_attrs()
        attrs[3]["type"]["members"][2]["brief"] = ""
        self.assertTrue(any("has no brief" in e for e in check.check_registry(attrs)))

    def test_rejects_unexpected_type(self):
        attrs = registry_attrs()
        attrs[2] = dict(attrs[2], type="int")
        self.assertTrue(any("unexpected type" in e for e in check.check_registry(attrs)))


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

    def test_rejects_duplicate_attribute_key(self):
        otlp = json.loads((FOLDER / "example-span.json").read_text())
        attributes = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
        index = [a["key"] for a in attributes].index("org.opena2a.egress.decision")
        attributes.insert(index, {"key": "org.opena2a.egress.decision", "value": {"stringValue": "bogus"}})
        with self.assertRaisesRegex(ValueError, "duplicate attribute keys"):
            check.span_attributes(otlp)

    def test_rejects_non_string_upstream_attribute(self):
        span = example_span()
        span["gen_ai.agent.id"] = {"intValue": "7"}
        errors = check.check_span(span, registry_attrs())
        self.assertIn("span gen_ai.agent.id: expected a string value", errors)

    def test_rejects_label_set_that_is_not_a_string_array(self):
        span = example_span()
        span["org.opena2a.session.label"] = {"stringValue": "internal"}
        self.assertTrue(any("expected an array of strings" in e for e in check.check_span(span, registry_attrs())))

    def test_rejects_non_string_value(self):
        span = example_span()
        span["org.opena2a.grant.id"] = {"intValue": "1"}
        errors = check.check_span(span, registry_attrs())
        self.assertIn("span org.opena2a.grant.id: expected a string value", errors)


class ReadmeTest(unittest.TestCase):
    def test_rejects_missing_relation_row(self):
        text = (FOLDER / "README.md").read_text()
        head, relation = text.split("## Relation to OpenTelemetry", 1)
        relation = "\n".join(
            line for line in relation.splitlines() if not line.startswith("| `org.opena2a.grant.id`")
        )
        errors = check.check_readme(head + "## Relation to OpenTelemetry" + relation, registry_attrs())
        self.assertTrue(any("org.opena2a.grant.id" in e for e in errors), errors)

    def test_rejects_status_without_not_filed(self):
        text = (FOLDER / "README.md").read_text().replace("not filed", "filed")
        self.assertTrue(any("not filed" in e for e in check.check_readme(text, registry_attrs())))

    def test_rejects_relation_section_without_release_name(self):
        text = (FOLDER / "README.md").read_text().replace(check.SEMCONV_RELEASE, "v0.0.0")
        errors = check.check_readme(text, registry_attrs())
        self.assertTrue(any(f"semantic-conventions {check.SEMCONV_RELEASE}" in e for e in errors), errors)

    def test_rejects_missing_relation_section(self):
        text = (FOLDER / "README.md").read_text().replace("## Relation to OpenTelemetry", "## Relation")
        self.assertIn("README: no relation section", check.check_readme(text, registry_attrs()))


class MainTest(unittest.TestCase):
    def run_main(self, folder):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check.main(["check.py", str(folder)])
        return code, out.getvalue()

    def test_exits_zero_when_consistent(self):
        code, out = self.run_main(FOLDER)
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("OK "), out)

    def test_exits_one_and_prints_fail_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = copy_folder(pathlib.Path(tmp))
            readme = folder / "README.md"
            readme.write_text(readme.read_text().replace("not filed", "filed"))
            code, out = self.run_main(folder)
        self.assertEqual(code, 1)
        self.assertIn("FAIL README: status line", out)

    def test_reports_attribute_without_id_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = copy_folder(pathlib.Path(tmp))
            registry = yaml.safe_load((folder / "registry.yaml").read_text())
            del registry["groups"][0]["attributes"][2]["id"]
            (folder / "registry.yaml").write_text(yaml.safe_dump(registry, sort_keys=False))
            code, out = self.run_main(folder)
        self.assertEqual(code, 1)
        self.assertIn("FAIL registry: 1 attribute(s) without an id", out)

    def test_reports_duplicate_span_attribute_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = copy_folder(pathlib.Path(tmp))
            otlp = json.loads((folder / "example-span.json").read_text())
            attributes = otlp["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["attributes"]
            attributes.insert(0, {"key": "org.opena2a.egress.decision", "value": {"stringValue": "bogus"}})
            (folder / "example-span.json").write_text(json.dumps(otlp))
            code, out = self.run_main(folder)
        self.assertEqual(code, 1)
        self.assertIn("duplicate attribute keys ['org.opena2a.egress.decision']", out)


if __name__ == "__main__":
    unittest.main()
