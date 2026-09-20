from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_delivery_opc", ROOT / "scripts/artifact_delivery.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def manifest_for(package: Path, members: list[tuple[str, bytes, str]]) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-opc-member-projection",
        "projectionId": "test-opc-r1",
        "parentPackage": {
            "format": "pptx",
            "sha256": "sha256:" + MODULE.sha256_file(package),
            "expectedSizeBytes": package.stat().st_size,
        },
        "members": [
            {
                "part": part,
                "sha256": digest(data),
                "expectedSizeBytes": len(data),
                "outputRelativePath": output,
            }
            for part, data, output in members
        ],
        "nonClaims": ["test-only"],
    }


class ArtifactOpcProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        if importlib.util.find_spec("jsonschema") is None:
            self.skipTest("jsonschema is required for OPC projection contract tests")

    def make_package(self, root: Path, entries: list[tuple[str, bytes]]) -> Path:
        package = root / "source.pptx"
        with zipfile.ZipFile(package, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
        return package

    def write_manifest(self, root: Path, value: dict) -> Path:
        path = root / "projection.json"
        path.write_text(json.dumps(value))
        return path

    def test_exact_projection_and_replay_are_digest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            one, two = b"visual-one", b"visual-two"
            package = self.make_package(root, [("ppt/media/one.jpeg", one), ("ppt/media/two.jpeg", two), ("ignored.bin", b"ignored")])
            manifest = self.write_manifest(root, manifest_for(package, [
                ("ppt/media/one.jpeg", one, "slide-01.jpeg"),
                ("ppt/media/two.jpeg", two, "slide-02.jpeg"),
            ]))
            out = root / "out"
            first = MODULE.project_opc_members(package, manifest, out)
            self.assertEqual(first["status"], "PASS", first)
            self.assertEqual(first["replayedMemberCount"], 0)
            self.assertEqual((out / "slide-01.jpeg").read_bytes(), one)
            self.assertFalse((out / "ignored.bin").exists())
            replay = MODULE.project_opc_members(package, manifest, out)
            self.assertEqual(replay["status"], "PASS", replay)
            self.assertEqual(replay["replayedMemberCount"], 2)

    def test_parent_digest_drift_fails_before_projection(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = b"visual"
            package = self.make_package(root, [("ppt/media/one.jpeg", data)])
            value = manifest_for(package, [("ppt/media/one.jpeg", data, "slide-01.jpeg")])
            value["parentPackage"]["sha256"] = "sha256:" + "0" * 64
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "parent package digest mismatch"):
                MODULE.project_opc_members(package, manifest, root / "out")
            self.assertFalse((root / "out" / "slide-01.jpeg").exists())

    def test_member_digest_and_size_are_both_fenced(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = b"visual"
            package = self.make_package(root, [("ppt/media/one.jpeg", data)])
            value = manifest_for(package, [("ppt/media/one.jpeg", data, "slide-01.jpeg")])
            value["members"][0]["expectedSizeBytes"] += 1
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "part size mismatch"):
                MODULE.project_opc_members(package, manifest, root / "out")
            value = manifest_for(package, [("ppt/media/one.jpeg", data, "slide-01.jpeg")])
            value["members"][0]["sha256"] = "sha256:" + "1" * 64
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "part digest mismatch"):
                MODULE.project_opc_members(package, manifest, root / "out2")

    def test_duplicate_archive_member_and_duplicate_output_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            package = root / "duplicate.pptx"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("ppt/media/one.jpeg", b"one")
                archive.writestr("ppt/media/one.jpeg", b"two")
            value = manifest_for(package, [("ppt/media/one.jpeg", b"one", "slide-01.jpeg")])
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "occur exactly once"):
                MODULE.project_opc_members(package, manifest, root / "out")

            package = self.make_package(root, [("ppt/media/one.jpeg", b"one"), ("ppt/media/two.jpeg", b"two")])
            value = manifest_for(package, [
                ("ppt/media/one.jpeg", b"one", "same.jpeg"),
                ("ppt/media/two.jpeg", b"two", "same.jpeg"),
            ])
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "duplicates outputRelativePath"):
                MODULE.project_opc_members(package, manifest, root / "out2")

    def test_symlink_parent_package_and_conflicting_output_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = b"visual"
            package = self.make_package(root, [("ppt/media/one.jpeg", data)])
            manifest = self.write_manifest(root, manifest_for(package, [("ppt/media/one.jpeg", data, "slide-01.jpeg")]))
            link = root / "linked.pptx"
            os.symlink(package, link)
            with self.assertRaisesRegex(RuntimeError, "non-symlink"):
                MODULE.project_opc_members(link, manifest, root / "out-link")
            out = root / "out"
            out.mkdir()
            (out / "slide-01.jpeg").write_bytes(b"conflict")
            with self.assertRaisesRegex(RuntimeError, "refuses to overwrite"):
                MODULE.project_opc_members(package, manifest, out)
            self.assertEqual((out / "slide-01.jpeg").read_bytes(), b"conflict")

    def test_manifest_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = b"visual"
            package = self.make_package(root, [("ppt/media/one.jpeg", data)])
            value = manifest_for(package, [("ppt/media/one.jpeg", data, "../escape.jpeg")])
            manifest = self.write_manifest(root, value)
            with self.assertRaisesRegex(RuntimeError, "normalized POSIX relative path"):
                MODULE.project_opc_members(package, manifest, root / "out")
            self.assertFalse((root / "escape.jpeg").exists())

    def test_pdu_sdu_r2_parent_binding_and_eight_opc_parts_are_frozen(self) -> None:
        package_input = json.loads((
            ROOT / "artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-runtime-package-input-set-r2.json"
        ).read_text())
        self.assertEqual(package_input["standing"], "PARENT_PACKAGE_BINDING_FROZEN_NOT_YET_MATERIALIZED")
        self.assertEqual(package_input["admission"], "workspace.execBound")
        self.assertEqual(len(package_input["bindings"]), 1)
        binding = package_input["bindings"][0]
        self.assertEqual(binding["authority"], "artifact-golden-r1")
        self.assertEqual(binding["expectedDigest"], "sha256:b50ab3025c4b285c728d029416492b4c7a03de1fc9e0bfe3f05293bfaf5f468c")
        self.assertEqual(binding["relativeObject"], "pdu-sdu/34x10/PDU_SDU_34x10_8页演示稿.pptx")

        projection = json.loads((
            ROOT / "artifact-delivery/golden/pdu-sdu-34x10-r1/pdu-sdu-34x10-opc-member-projection-r2.json"
        ).read_text())
        self.assertEqual(projection["parentPackage"]["expectedSizeBytes"], 2791610)
        self.assertEqual(projection["parentPackage"]["sha256"], binding["expectedDigest"])
        self.assertEqual(len(projection["members"]), 8)
        expected = [
            ("ppt/media/image-1-1.jpeg", 325158, "97237ff50567e495b0ec56543dd644143fed4a5241dd038814c775c732ceb998"),
            ("ppt/media/image-2-1.jpeg", 348056, "fc9e38e60aa35f36050cef2d0493d716ebc20977b13a126bdd1560dc6643b168"),
            ("ppt/media/image-3-1.jpeg", 346502, "bd511f6736bf5c8eee439c412e4e32fc7f0ca57953da6baee4a9e716c86cdec9"),
            ("ppt/media/image-4-1.jpeg", 347807, "116de845c183109a27c68fb2ada0c5f1038ea55ea5b4f682bf37dee3017fc875"),
            ("ppt/media/image-5-1.jpeg", 348821, "23c7b1a818feb6a8e7de9f009f57542acffea306e22fd7a83eb6c10063340d65"),
            ("ppt/media/image-6-1.jpeg", 316885, "2eb714c894a4115fcd3e55a0729d28ddd93e3e92ec2621c0274a0b6131bbfeb5"),
            ("ppt/media/image-7-1.jpeg", 343411, "67287373393b0fb170b0d0f3957661115a01a4e9cd43655c65d344729708379a"),
            ("ppt/media/image-8-1.jpeg", 332596, "f1727f930369788b5c6a314c4fe2d3baf9f4c27e2eb361ae8ef2ff2964ef1628"),
        ]
        actual = [(m["part"], m["expectedSizeBytes"], m["sha256"].removeprefix("sha256:")) for m in projection["members"]]
        self.assertEqual(actual, expected)
        self.assertEqual([m["outputRelativePath"] for m in projection["members"]], [f"slide-{i:02d}.jpeg" for i in range(1, 9)])

    def test_reference_map_and_semantic_overlay_compose_without_promoting_acceptance(self) -> None:
        if importlib.util.find_spec("pptx") is None or importlib.util.find_spec("PIL") is None:
            self.skipTest("python-pptx/Pillow are required for hybrid build test")
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            visual_root = root / "visual"
            visual_root.mkdir()
            visual = visual_root / "slide-01.jpeg"
            Image.new("RGB", (8, 3), (255, 255, 255)).save(visual, format="JPEG")
            sha = MODULE.sha256_file(visual)
            semantic = {
                "$schema": "../../presentation-source-v1.schema.json",
                "schemaVersion": 1,
                "kind": "presentation-source",
                "presentationId": "presentation:test-semantic",
                "profileId": "presentation-ultrawide-34x10-r1",
                "sourceMode": "native-composition",
                "locale": "en-US",
                "aspectRatio": "34:10",
                "slideSizeInches": {"width": 34.0, "height": 10.0},
                "slides": [{
                    "id": "slide-01", "title": "T", "layoutId": "Blank",
                    "elements": [{"kind":"text","id":"t","text":"T","box":{"x":1,"y":1,"w":3,"h":1},"fontFamily":"Arial","fontSizePt":20,"colorHex":"000000","opacity":0.0}]
                }],
                "notes": "semantic only"
            }
            reference = {
                **semantic,
                "presentationId": "presentation:test-reference",
                "sourceMode": "reference-map",
                "slides": [{"id":"slide-01","title":"T","layoutId":"Blank","legacySource":{"artifactName":"legacy.jpeg","sha256":sha,"slideIndex":1}}],
                "notes":"reference only"
            }
            semantic_path = root / "semantic.json"; semantic_path.write_text(json.dumps(semantic))
            reference_path = root / "reference.json"; reference_path.write_text(json.dumps(reference))
            hybrid_path = root / "hybrid.json"
            receipt = MODULE.compose_reference_hybrid_source(semantic_path, reference_path, visual_root, hybrid_path)
            self.assertEqual(receipt["status"], "PASS", receipt)
            hybrid = json.loads(hybrid_path.read_text())
            self.assertEqual(hybrid["slides"][0]["elements"][0]["kind"], "image")
            self.assertFalse(hybrid["slides"][0]["elements"][0]["decorative"])
            self.assertIn("accessibility/use review is still required", hybrid["slides"][0]["elements"][0]["altText"])
            self.assertEqual(hybrid["slides"][0]["elements"][1]["id"], "t")
            built = MODULE.build_presentation_source(
                hybrid_path,
                ROOT / "artifact-delivery/examples/presentation-ultrawide-34x10-r1.json",
                root / "hybrid.pptx",
            )
            self.assertEqual(built["status"], "PASS", built)
            self.assertEqual(len(built["mediaBindings"]), 1)
            with zipfile.ZipFile(root / "hybrid.pptx") as package:
                slide_xml = package.read("ppt/slides/slide1.xml").decode("utf-8")
                self.assertLess(slide_xml.index("<p:pic>"), slide_xml.index("<p:sp>"))
                self.assertIn('a:alpha val="0"', slide_xml)
