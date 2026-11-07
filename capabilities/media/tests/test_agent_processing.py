from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.agent_processing import processing_profiles
from ordivon_studio.agent_surface import execute_surface_action, surface_projection


class ProcessingDiscoveryTests(unittest.TestCase):
    def test_catalog_can_be_consumed_before_studio_dependencies_materialize(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts/studio-agent-surface.py"
        command = [sys.executable, "-S", str(script), "studio_processing_profiles"]
        result = subprocess.run(
            [*command, "--arguments", "{}"],
            cwd=root, capture_output=True, text=True, check=True,
        )
        catalog = json.loads(result.stdout)
        self.assertEqual(catalog["kind"], "ordivon.media.processing-profile-discovery")
        self.assertEqual(len(catalog["profiles"]), 4)
        source_role_by_id = {
            "av-sdr-web-1080p30-noaudio": "videoSource",
            "audio-program-48k-mono-lufs23": "audioSource",
            "runtime-introduction-assembly-v2": "editorialTimeline",
            "runtime-introduction-en-ttml": "timedTextDocument",
        }
        for profile in catalog["profiles"]:
            self.assertTrue(profile["profileDigest"].startswith("sha256:"))
            self.assertTrue(profile["adapterDigest"].startswith("sha256:"))
            self.assertEqual(
                profile["inputRoles"],
                [source_role_by_id[profile["id"]], "profile", "evidenceDirectory"],
            )
        invalid = subprocess.run(
            [*command, "--arguments", '{"unknown":1}'],
            cwd=root, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("invalid arguments", invalid.stderr)

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
            self.assertEqual(item["adapterDigest"], "sha256:" + hashlib.sha256(b"#!/bin/sh\\n").hexdigest())
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
            self.assertEqual(item["inputRoles"], [])
            self.assertEqual(item["externalToolReadiness"], "not-observed")

    def test_native_probe_plan_reuses_discovered_bytes_and_refuses_drift(self) -> None:
        root = Path(__file__).resolve().parents[1]
        catalog = execute_surface_action("studio_processing_profiles", {}, root=root)
        profile = next(item for item in catalog["profiles"]
                       if item["id"] == "av-sdr-web-1080p30-noaudio")
        args = {
            "profileId": profile["id"],
            "expectedProfileDigest": profile["profileDigest"],
            "expectedAdapterDigest": profile["adapterDigest"],
            "inputPath": "/tmp/media-demo.mp4",
            "evidenceDirectory": "/tmp/media-demo-evidence",
        }
        result = execute_surface_action("studio_processing_probe_plan", args, root=root)
        self.assertEqual(result["execution"], {
            "executionTarget": "local_linux",
            "executable": "/usr/bin/bash",
            "args": [
                profile["adapterPath"],
                args["inputPath"],
                profile["profilePath"],
                args["evidenceDirectory"],
            ],
            "cwdRelative": "capabilities/media",
        })
        self.assertEqual(result["profileDigest"], profile["profileDigest"])
        self.assertEqual(result["adapterDigest"], profile["adapterDigest"])
        args["expectedAdapterDigest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "adapter digest changed"):
            execute_surface_action("studio_processing_probe_plan", args, root=root)
        args["expectedAdapterDigest"] = profile["adapterDigest"]
        args["expectedProfileDigest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "profile digest changed"):
            execute_surface_action("studio_processing_probe_plan", args, root=root)

    def test_source_byte_drift_rebinds_both_profile_and_adapter(self) -> None:
        """One real compiler-consumer trace, not a claim of mathematical code refinement."""
        from ordivon_studio.agent_processing import processing_probe_plan

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "processing/profiles/video.json"
            adapter = root / "processing/bin/probe-av.sh"
            profile.parent.mkdir(parents=True)
            adapter.parent.mkdir(parents=True)
            value = {
                "schemaVersion": 1,
                "kind": "ordivon.media.v2.av-profile",
                "id": "bound-video",
                "video": {"codec": "h264"},
            }
            profile.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
            adapter.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

            def compile_selected(row: dict[str, object]) -> dict[str, object]:
                return processing_probe_plan(
                    root,
                    profile_id=str(row["id"]),
                    expected_profile_digest=str(row["profileDigest"]),
                    expected_adapter_digest=str(row["adapterDigest"]),
                    input_path="selected-input.mp4",
                    evidence_directory="consumer-evidence",
                )

            first = processing_profiles(root)["profiles"][0]
            self.assertEqual(first["externalToolReadiness"], "not-observed")
            accepted = compile_selected(first)
            self.assertEqual(accepted["profileDigest"], first["profileDigest"])
            self.assertEqual(accepted["adapterDigest"], first["adapterDigest"])
            self.assertEqual(accepted["execution"]["args"][0], first["adapterPath"])

            # A same-identity JSON edit must invalidate the old discovery.
            value["video"]["codec"] = "hevc"
            profile.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "profile digest changed"):
                compile_selected(first)

            second = processing_profiles(root)["profiles"][0]
            self.assertNotEqual(second["profileDigest"], first["profileDigest"])
            adapter.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "adapter digest changed"):
                compile_selected(second)

            third = processing_profiles(root)["profiles"][0]
            accepted_again = compile_selected(third)
            self.assertEqual(accepted_again["adapterDigest"], third["adapterDigest"])
            self.assertEqual(accepted_again["execution"]["args"][2], third["profilePath"])

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
