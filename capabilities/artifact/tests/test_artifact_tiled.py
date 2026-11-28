import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_tiled", ROOT / "scripts/artifact_tiled.py")
M = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(M)


def canonical(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical_map(root: Path, legacy=False, tileset=False):
    seed = {
        "compressionlevel": -1,
        "height": 2,
        "infinite": False,
        "layers": [
            {
                "draworder": "topdown",
                "id": 1,
                "name": "Objects",
                "objects": [
                    {
                        "height": 16,
                        "id": 1,
                        "name": "box",
                        "opacity": 1,
                        "rotation": 0,
                        "type": "thing",
                        "visible": True,
                        "width": 16,
                        "x": 4,
                        "y": 4,
                    }
                ],
                "opacity": 1,
                "type": "objectgroup",
                "visible": True,
                "x": 0,
                "y": 0,
            }
        ],
        "nextlayerid": 2,
        "nextobjectid": 2,
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "tiledversion": "1.12.2",
        "tileheight": 16,
        "tilesets": [],
        "tilewidth": 16,
        "type": "map",
        "version": "1.10",
        "width": 2,
    }
    if legacy:
        seed["layers"][0]["objects"][0]["class"] = "thing"
        seed["layers"][0]["objects"][0]["type"] = ""
    if tileset:
        seed["tilesets"] = [{"firstgid": 1, "source": "x.tsj"}]
    p = root / "seed.tmj"
    p.write_text(json.dumps(seed))
    out = root / "canonical.tmj"
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    r = subprocess.run(
        ["/usr/bin/tiled", "--export-map", str(p), str(out)], env=env, capture_output=True
    )
    assert r.returncode == 0, r.stderr.decode()
    return p if legacy or tileset else out


def contract(root: Path, map_path: Path, override=None):
    x = json.loads(map_path.read_text())
    objs = [o for l in x["layers"] for o in l.get("objects", [])]
    c = {
        "contractVersion": 1,
        "id": "tiled-smoke-r1",
        "profileId": "design-2d-tiled-tmj-object-map-r1",
        "map": {
            "formatVersion": str(x["version"]),
            "tiledVersion": str(x["tiledversion"]),
            "orientation": x["orientation"],
            "width": x["width"],
            "height": x["height"],
            "tileWidth": x["tilewidth"],
            "tileHeight": x["tileheight"],
            "layerCount": len(x["layers"]),
            "objectCount": len(objs),
            "expectedCanonicalJsonSha256": canonical(x),
        },
    }
    if override:
        c["map"].update(override)
    p = root / "contract.json"
    p.write_text(json.dumps(c))
    return p


class ArtifactTiledTests(unittest.TestCase):
    def req(self):
        for p in (M.TILED, M.TMXRASTERIZER):
            if not p.is_file():
                self.skipTest(str(p))

    def test_canonical_object_map_passes_native_roundtrips_and_raster(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r)
            c = contract(r, m)
            v = M.verify_tiled_tmj(m, c, r / "e")
            self.assertEqual(v["status"], "PASS", v)
            self.assertEqual(v["nativeTmjRoundTrip"]["status"], "PASS")
            self.assertEqual(v["nativeCrossFormatRoundTrip"]["status"], "PASS")
            self.assertTrue(v["nativeRasterReadback"]["render"]["nonEmptyAlpha"])

    def test_legacy_object_class_field_fails_closed(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r, legacy=True)
            c = contract(r, m)
            v = M.verify_tiled_tmj(m, c, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertTrue(any("legacy class" in z for z in v["failures"]))

    def test_tileset_external_reference_fails_bounded_profile(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r, tileset=True)
            c = contract(r, m)
            v = M.verify_tiled_tmj(m, c, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertTrue(any("tilesets" in z for z in v["failures"]))

    def test_wrong_canonical_digest_fails_before_native_roundtrip(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r)
            c = contract(r, m, {"expectedCanonicalJsonSha256": "0" * 64})
            v = M.verify_tiled_tmj(m, c, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertEqual(v["canonicalSemanticIdentity"]["status"], "FAIL")

    def test_file_properties_on_map_layer_and_custom_class_are_rejected_before_native(self):
        self.req()
        for location in ("map", "layer", "class"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as d:
                r = Path(d)
                m = canonical_map(r)
                data = json.loads(m.read_text())
                prop = {"name": "asset", "type": "file", "value": "sidecar.txt"}
                if location == "map":
                    data["properties"] = [prop]
                elif location == "layer":
                    data["layers"][0]["properties"] = [prop]
                else:
                    data["layers"][0]["objects"][0]["properties"] = [
                        {
                            "name": "custom",
                            "type": "class",
                            "propertytype": "Resource",
                            "value": {"asset": "sidecar.txt"},
                        }
                    ]
                m.write_text(json.dumps(data))
                c = contract(r, m)
                with mock.patch.object(
                    M, "run", side_effect=AssertionError("native ran before closure admission")
                ) as runner:
                    v = M.verify_tiled_tmj(m, c, r / "e")
                runner.assert_not_called()
                self.assertEqual(v["status"], "FAIL", v)
                self.assertTrue(
                    any("external" in x or "class property" in x for x in v["failures"]), v
                )

    def test_service_native_snapshot_resists_original_path_aba(self):
        self.req()
        from scripts import artifact_verify as service

        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r)
            c = contract(r, m)
            original = m.read_bytes()
            original_contract = c.read_bytes()
            pid = "design-2d-tiled-tmj-object-map-r1"
            profile = service.PROFILE_REGISTRY.resolve(pid).canonical_path
            request = r / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "kind": "artifact-verification-request",
                        "requestId": "test:tiled:aba",
                        "profile": {"id": pid, "path": str(profile), "sha256": M.sha_file(profile)},
                        "subject": {"path": str(m), "sha256": M.sha_file(m)},
                        "objectContract": {"path": str(c), "sha256": M.sha_file(c)},
                        "evidenceDirectory": str(r / "e"),
                        "consumer": {"id": "game-test", "purpose": "bounded object map"},
                    }
                )
            )
            loader = service.load_function
            paths = []

            def load(*args):
                real, digest = loader(*args)

                def verify(subject, object_contract, evidence):
                    paths.extend((subject, object_contract))
                    self.assertNotEqual(subject, m)
                    self.assertNotEqual(object_contract, c)
                    m.write_bytes(b"{invalid")
                    c.write_bytes(b"{invalid")
                    try:
                        return real(subject, object_contract, evidence)
                    finally:
                        m.write_bytes(original)
                        c.write_bytes(original_contract)

                return verify, digest

            with mock.patch.object(service, "load_function", side_effect=load):
                result = service.verify_request(request)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["inputIdentity"]["subject"], "EXACT_BYTES_SNAPSHOT")
            self.assertEqual(result["inputIdentity"]["objectContract"], "EXACT_BYTES_SNAPSHOT")
            self.assertFalse(result["profileVerificationComplete"])
            self.assertEqual(result["verification"]["nativeCrossFormatRoundTrip"]["status"], "PASS")
            self.assertEqual(result["verification"]["nativeRasterReadback"]["status"], "PASS")
            self.assertEqual(result["subject"]["sha256"], hashlib.sha256(original).hexdigest())
            self.assertTrue(paths)
            self.assertTrue(all(not p.exists() for p in paths))

    def test_malformed_ids_and_duplicate_keys_fail_before_native(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = canonical_map(r)
            c = contract(r, m)
            data = json.loads(m.read_text())
            data["layers"][0]["id"] = []
            m.write_text(json.dumps(data))
            with mock.patch.object(M, "run", side_effect=AssertionError("native called")):
                self.assertIn(
                    "layer ID must be a positive integer",
                    M.verify_tiled_tmj(m, c, r / "e")["failures"],
                )
                m.write_text('{"type":"map","type":"map"}')
                self.assertTrue(
                    any(
                        "duplicate" in x.lower()
                        for x in M.verify_tiled_tmj(m, c, r / "e")["failures"]
                    )
                )

    def test_invalid_json_fails_closed(self):
        self.req()
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            m = r / "bad.tmj"
            m.write_text("{")
            c = r / "contract.json"
            c.write_text(
                json.dumps(
                    {
                        "contractVersion": 1,
                        "id": "bad",
                        "profileId": "design-2d-tiled-tmj-object-map-r1",
                        "map": {
                            "formatVersion": "1.10",
                            "tiledVersion": "1.12.2",
                            "orientation": "orthogonal",
                            "width": 1,
                            "height": 1,
                            "tileWidth": 16,
                            "tileHeight": 16,
                            "layerCount": 1,
                            "objectCount": 1,
                            "expectedCanonicalJsonSha256": "0" * 64,
                        },
                    }
                )
            )
            v = M.verify_tiled_tmj(m, c, r / "e")
            self.assertEqual(v["status"], "FAIL")
            self.assertTrue(any("valid JSON" in z for z in v["failures"]))


if __name__ == "__main__":
    unittest.main()
