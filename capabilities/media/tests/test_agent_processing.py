from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.agent_processing import processing_profiles
from ordivon_studio.agent_surface import execute_surface_action, surface_projection


class ProcessingDiscoveryTests(unittest.TestCase):
    def test_discovery_is_digest_bound_and_does_not_claim_tool_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profiles = root / "processing/profiles"
            adapters = root / "processing/bin"
            profiles.mkdir(parents=True)
            adapters.mkdir(parents=True)
            data = {
                "schemaVersion": 1,
                "kind": "ordivon.media.v2.av-profile",
                "id": "test-av",
                "video": {"codec": "h264"},
            }
            raw = json.dumps(data, sort_keys=True).encode()
            (profiles / "test-av.json").write_bytes(raw)
            (adapters / "probe-av.sh").write_text("#!/bin/sh\\n", encoding="utf-8")
            result = processing_profiles(root)
            self.assertTrue(result["catalogPresent"])
            self.assertEqual(len(result["profiles"]), 1)
            item = result["profiles"][0]
            self.assertEqual(item["profilePath"], "processing/profiles/test-av.json")
            self.assertEqual(item["profileDigest"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(item["adapterPath"], "processing/bin/probe-av.sh")
            self.assertTrue(item["adapterPresent"])
            self.assertEqual(item["externalToolReadiness"], "not-observed")
            self.assertEqual(
                execute_surface_action("studio_processing_profiles", {}, root=root), result
            )
            self.assertIn("studio_processing_profiles", [
                item["name"] for item in surface_projection()["tools"]
            ])

    def test_unknown_profiles_are_visible_without_fabricating_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "processing/profiles/special.json"
            profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps({
                "schemaVersion": 1, "kind": "custom-experimental", "id": "special"
            }), encoding="utf-8")
            result = processing_profiles(root)
            item = result["profiles"][0]
            self.assertIsNone(item["adapterPath"])
            self.assertFalse(item["adapterPresent"])
            self.assertEqual(item["externalToolReadiness"], "not-observed")

    def test_duplicate_profile_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profiles = root / "processing/profiles"
            profiles.mkdir(parents=True)
            raw = json.dumps({
                "schemaVersion": 1, "kind": "ordivon.media.v2.av-profile", "id": "same"
            })
            (profiles / "a.json").write_text(raw, encoding="utf-8")
            (profiles / "b.json").write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate Media processing profile id"):
                processing_profiles(root)
