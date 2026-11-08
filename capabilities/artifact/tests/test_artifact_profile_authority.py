"""Native source authority and bounded semantic refinement adversarial tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from artifact_core.json_validation import load_json
from artifact_core.profile_refinement import assess_v1_v2_refinement
from artifact_core.profiles import ProfileRegistry

ART = Path(__file__).resolve().parents[1] / "artifact-delivery"


def copy_profile(destination: Path, name: str, *, v1: bool = False) -> Path:
    origin = (
        ART / "examples" / f"{name}.json" if v1 else
        ART / "shadow-v2/examples" / f"{name}-v2.json"
    )
    target = destination / ("examples" if v1 else "shadow-v2/examples") / origin.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(origin.read_bytes())
    return target


class ArtifactProfileAuthorityTests(unittest.TestCase):
    def test_all_canonical_profiles_and_legacy_projection_really_load(self):
        registry = ProfileRegistry(ART)
        self.assertEqual(len(registry.ids()), 28)
        indexed = [registry.resolve(name) for name in registry.ids()]
        self.assertEqual(sum(p.source_kind == "production-v1-adapted" for p in indexed), 8)
        self.assertEqual(
            sum(p.source_kind == "native-v2-shadow" for p in indexed), 20
        )

    def test_bad_canonical_file_is_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = copy_profile(root, "audio-wave-pcm16-r1")
            target.write_text("{ not valid JSON")
            with self.assertRaisesRegex(RuntimeError, "invalid Artifact JSON authority"):
                ProfileRegistry(root)

    def test_nested_duplicate_fields_are_rejected_before_schema_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = copy_profile(root, "still-image-png-srgb-r1")
            content = path.read_text()
            content = content.replace('"profileVersion": 2', '"profileVersion": 2, "profileVersion": 2')
            path.write_text(content)
            with self.assertRaisesRegex(RuntimeError, "duplicate JSON key: profileVersion"):
                ProfileRegistry(root)

    def test_invalid_version_and_schema_never_enter_index(self):
        for mutation, message in (
            (lambda doc: doc.update(profileVersion=3), "version mismatch"),
            (lambda doc: doc.update(classification={"family": "audio"}), "Schema violation"),
        ):
            with self.subTest(expected=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = copy_profile(root, "audio-wave-pcm16-r1")
                doc = json.loads(target.read_text())
                mutation(doc)
                target.write_text(json.dumps(doc))
                with self.assertRaisesRegex(RuntimeError, message):
                    ProfileRegistry(root)

    def test_profile_id_must_match_authoritative_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = copy_profile(root, "audio-wave-pcm16-r1")
            doc = json.loads(target.read_text())
            doc["id"] = "different-profile-id"
            target.write_text(json.dumps(doc))
            with self.assertRaisesRegex(RuntimeError, "filename and identity disagree"):
                ProfileRegistry(root)

    def test_nonprofile_examples_remain_compatible_but_corrupt_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_profile(root, "document-r1", v1=True)
            copy_profile(root, "document-r1")
            source = root / "examples/reference-source-r1.json"
            source.write_text(json.dumps({"kind": "artifact-source", "path": "sample"}))
            registry = ProfileRegistry(root)
            self.assertEqual(registry.ids(), ["document-r1"])
            source.write_text('{"kind": "source", "kind": "spoofed"}')
            with self.assertRaisesRegex(RuntimeError, "duplicate JSON key: kind"):
                ProfileRegistry(root)

    def test_production_profile_wrong_version_fails_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_profile(root, "document-r1")
            target = copy_profile(root, "document-r1", v1=True)
            data = load_json(target)
            data["profileVersion"] = 2
            target.write_text(json.dumps(data))
            with self.assertRaisesRegex(RuntimeError, "version mismatch"):
                ProfileRegistry(root)

    def test_canonical_drift_rejects_cached_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = copy_profile(root, "audio-wave-pcm16-r1")
            registry = ProfileRegistry(root)
            self.assertEqual(registry.resolve("audio-wave-pcm16-r1").source_kind, "native-v2-shadow")
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "canonical Profile changed"):
                registry.resolve("audio-wave-pcm16-r1")

    def test_source_drift_rejects_cached_refinement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_profile(root, "pdu-sdu-presentation-r1")
            target = copy_profile(root, "pdu-sdu-presentation-r1", v1=True)
            registry = ProfileRegistry(root)
            registry.resolve("pdu-sdu-presentation-r1")
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaisesRegex(RuntimeError, "production Profile changed"):
                registry.resolve("pdu-sdu-presentation-r1")

    def test_partial_v1_v2_refinement_is_explicitly_falsifiable(self):
        for name in (
            "document-r1", "pdf-accessible-r1", "pdf-fixed-r1",
            "pdu-sdu-presentation-r1", "presentation-local-development-r1",
            "presentation-ultrawide-34x10-r1", "spreadsheet-r1", "web-r1",
        ):
            with self.subTest(profile=name):
                v1 = load_json(ART / "examples" / f"{name}.json")
                v2 = load_json(ART / "shadow-v2/examples" / f"{name}-v2.json")
                report = assess_v1_v2_refinement(v1, v2)
                self.assertTrue(report["complete"], report)
                for field, mutate in (
                    ("id", lambda d: d.update(id="wrong")),
                    ("classification.family", lambda d: d["classification"].update(family="wrong")),
                    ("outputs", lambda d: d["outputs"][0].update(required=False)),
                    ("targetAuthorities.primary.required", lambda d: d["targetAuthorities"][0].update(
                        required=not d["targetAuthorities"][0]["required"]
                    )),
                ):
                    changed = json.loads(json.dumps(v2))
                    mutate(changed)
                    observed = assess_v1_v2_refinement(v1, changed)
                    self.assertFalse(observed["complete"], (name, field, observed))
                    self.assertIn(field, observed["mismatches"])

    def test_registry_resolution_fails_closed_for_divergent_v2_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_profile(root, "pdu-sdu-presentation-r1", v1=True)
            target = copy_profile(root, "pdu-sdu-presentation-r1")
            profile = load_json(target)
            profile["outputs"][0]["required"] = False
            target.write_text(json.dumps(profile))
            registry = ProfileRegistry(root)
            with self.assertRaisesRegex(RuntimeError, "refinement mismatch"):
                registry.resolve("pdu-sdu-presentation-r1")

    def test_callers_cannot_mutate_registry_authority_through_returned_dict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_profile(root, "audio-wave-pcm16-r1")
            registry = ProfileRegistry(root)
            first = registry.resolve("audio-wave-pcm16-r1")
            first.canonical["classification"]["family"] = "wrong"
            second = registry.resolve("audio-wave-pcm16-r1")
            self.assertEqual(second.canonical["classification"]["family"], "audio")


if __name__ == "__main__":
    unittest.main()
