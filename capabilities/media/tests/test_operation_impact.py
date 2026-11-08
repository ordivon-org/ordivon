from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.production_context import build_production_context

ROOT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def make_case(root: Path) -> tuple[Path, Path, Path]:
    intermediate = root / "render" / "source.wav"
    intermediate.parent.mkdir(parents=True)
    source = root / "generate.py"
    master = root / "render" / "master.wav"
    delivery = root / "render" / "delivery.ogg"
    source.write_bytes(b"v1 generator source")
    intermediate.write_bytes(b"v1 intermediate")
    master.write_bytes(b"v1 master")
    delivery.write_bytes(b"v1 delivery")
    production = {
        "id": "sample",
        "status": "review",
        "sourceBindings": [],
        "sources": {
            "claims": "claims.json",
            "scripts": ["generate.py"],
            "sourceDocuments": ["operation-lineage.json"],
        },
        "outputs": [
            {
                "id": "master",
                "kind": "audio",
                "status": "approved",
                "blobDigest": digest(master.read_bytes()),
                "outputCarrier": "render/master.wav",
            },
            {
                "id": "delivery",
                "kind": "audio",
                "status": "rendered",
                "blobDigest": digest(delivery.read_bytes()),
                "outputCarrier": "render/delivery.ogg",
            },
        ],
    }
    lineage = {
        "schemaVersion": 1,
        "kind": "ordivon.media.operation-lineage",
        "productionId": "sample",
        "operations": [
            {
                "id": "synthesize",
                "dependsOn": [],
                "toolFamily": "Python",
                "inputFiles": [{"path": "generate.py", "digest": digest(source.read_bytes())}],
                "retainedFile": {
                    "path": "render/source.wav",
                    "digest": digest(intermediate.read_bytes()),
                },
                "outputIds": [],
            },
            {
                "id": "mastering",
                "dependsOn": ["synthesize"],
                "toolFamily": "SoX",
                "inputFiles": [],
                "outputIds": ["master"],
            },
            {
                "id": "deliver",
                "dependsOn": ["mastering"],
                "toolFamily": "unqualified",
                "inputFiles": [],
                "outputIds": ["delivery"],
            },
        ],
    }
    (root / "claims.json").write_text(json.dumps({"productionId": "sample", "claims": []}))
    (root / "production.json").write_text(json.dumps(production))
    (root / "operation-lineage.json").write_text(json.dumps(lineage))
    return source, intermediate, delivery


def impact(root: Path) -> dict:
    projection = build_production_context(root)["operationLineage"]
    assert projection is not None
    return projection


class ProductionOperationImpactTests(unittest.TestCase):
    def test_real_sonic_five_step_cut_is_observed_but_not_cache_authorized(self) -> None:
        projected = impact(ROOT / "productions/convergence-sonic-ident")
        self.assertEqual(len(projected["steps"]), 5)
        self.assertEqual(projected["revalidateStepIds"], [])
        self.assertEqual(projected["unresolvedStepIds"], [])
        self.assertEqual(
            {row["stepId"] for row in projected["steps"]},
            {"generate-source", "master-audio", "encode-flac", "encode-ogg", "render-waveform"},
        )
        for step in projected["steps"]:
            self.assertEqual(step["directByteStanding"], "MATCHES_DECLARED_BYTES")
            self.assertEqual(step["impactStanding"], "NO_BYTE_DRIFT_OBSERVED")
            self.assertIsNone(step["actionKey"])
            self.assertFalse(step["cacheReuseAuthorized"])
            self.assertEqual(step["toolAndEnvironmentQualification"], "UNKNOWN")
        self.assertFalse(projected["executionOrPublicationAuthorized"])

    def test_local_input_change_only_invalidates_dependent_closure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, intermediate, delivery = make_case(root)
            self.assertEqual(impact(root)["revalidateStepIds"], [])
            source.write_bytes(b"changed generator")
            changed = impact(root)
            self.assertEqual(changed["revalidateStepIds"], ["synthesize", "mastering", "deliver"])
            self.assertEqual(changed["unresolvedStepIds"], [])
            self.assertEqual(changed["steps"][0]["directByteStanding"], "BYTE_DRIFT_OBSERVED")
            self.assertEqual(changed["steps"][1]["directByteStanding"], "MATCHES_DECLARED_BYTES")

            source.write_bytes(b"v1 generator source")
            intermediate.write_bytes(b"changed intermediate")
            changed = impact(root)
            self.assertEqual(changed["revalidateStepIds"], ["synthesize", "mastering", "deliver"])

            intermediate.write_bytes(b"v1 intermediate")
            delivery.write_bytes(b"mutated delivery")
            changed = impact(root)
            self.assertEqual(changed["revalidateStepIds"], ["deliver"])
            self.assertEqual(changed["steps"][1]["impactStanding"], "NO_BYTE_DRIFT_OBSERVED")

    def test_missing_input_is_unknown_and_does_not_assert_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, _ = make_case(root)
            source.unlink()
            projection = impact(root)
            self.assertEqual(projection["revalidateStepIds"], [])
            self.assertEqual(
                projection["unresolvedStepIds"], ["synthesize", "mastering", "deliver"]
            )
            self.assertTrue(
                all(row["impactStanding"] == "UNKNOWN_UPSTREAM" for row in projection["steps"])
            )

    def test_invalid_cycle_unknown_step_duplicate_output_and_path_escape_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_case(root)
            path = root / "operation-lineage.json"
            original = json.loads(path.read_text())
            cycle = json.loads(json.dumps(original))
            cycle["operations"][0]["dependsOn"] = ["deliver"]
            path.write_text(json.dumps(cycle))
            with self.assertRaisesRegex(ValueError, "dependency cycle"):
                impact(root)

            missing_dep = json.loads(json.dumps(original))
            missing_dep["operations"][0]["dependsOn"] = ["does-not-exist"]
            path.write_text(json.dumps(missing_dep))
            with self.assertRaisesRegex(ValueError, "unknown step"):
                impact(root)

            duplicate = json.loads(json.dumps(original))
            duplicate["operations"][2]["outputIds"] = ["master"]
            path.write_text(json.dumps(duplicate))
            with self.assertRaisesRegex(ValueError, "claims output twice"):
                impact(root)

            escaped = json.loads(json.dumps(original))
            escaped["operations"][0]["inputFiles"][0]["path"] = "../outside.py"
            path.write_text(json.dumps(escaped))
            with self.assertRaisesRegex(ValueError, "safely relative"):
                impact(root)

            path.write_text(json.dumps(original))
            self.assertEqual(impact(root)["revalidateStepIds"], [])

    def test_invalid_carrier_binding_is_unknown_not_observed_byte_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_case(root)
            manifest_path = root / "production.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["outputs"][0]["sourceCarrier"] = "render/master.wav"
            manifest_path.write_text(json.dumps(manifest))
            projection = impact(root)
            by_id = {row["stepId"]: row for row in projection["steps"]}
            self.assertEqual(
                by_id["mastering"]["directByteStanding"],
                "UNKNOWN_INVALID_BYTE_BINDING",
            )
            self.assertEqual(projection["revalidateStepIds"], [])
            self.assertEqual(projection["unresolvedStepIds"], ["mastering", "deliver"])

    def test_nondeclared_graph_never_auto_activates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_case(root)
            manifest_path = root / "production.json"
            manifest = json.loads(manifest_path.read_text())
            del manifest["sources"]["sourceDocuments"]
            manifest_path.write_text(json.dumps(manifest))
            self.assertIsNone(build_production_context(root)["operationLineage"])


if __name__ == "__main__":
    unittest.main()
