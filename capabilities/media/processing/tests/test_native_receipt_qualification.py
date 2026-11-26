"""Real adapter -> existing Agent surface -> selected receipt consumer."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.agent_processing import processing_probe_plan, processing_profiles
from ordivon_studio.agent_surface import execute_surface_action

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class NativeReceiptQualificationTests(unittest.TestCase):
    def qualify(self, plan, exit_code, expected):
        return execute_surface_action(
            "studio_processing_receipt_qualify",
            {"plan": plan, "exitCode": exit_code, "expectedReceiptDigest": expected},
            root=ROOT,
        )

    def native(self, profile_file, source, directory, expected_exit=0):
        profile_id = json.loads((ROOT / "processing/profiles" / profile_file).read_bytes())["id"]
        row = next(row for row in processing_profiles(ROOT)["profiles"] if row["id"] == profile_id)
        plan = processing_probe_plan(
            ROOT, profile_id=profile_id, expected_profile_digest=row["profileDigest"],
            expected_adapter_digest=row["adapterDigest"], expected_source_closure_digest=row["sourceClosureDigest"],
            input_path=str(source), expected_input_digest=digest(source), evidence_directory=str(directory),
        )
        result = subprocess.run(
            [plan["execution"]["executable"], *plan["execution"]["args"]],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, expected_exit, result.stderr)
        receipt = directory / "evidence.json"
        qualified = self.qualify(plan, result.returncode, digest(receipt))
        self.assertEqual(qualified["standing"], "QUALIFIED")
        self.assertIs(qualified["mechanicalOk"], expected_exit == 0)
        self.assertEqual(qualified["runtimeWitness"], "not-verified")
        self.assertEqual(qualified["publicationStanding"], "not-evaluated")
        return plan, receipt, qualified

    def test_native_four_adapters_and_negative_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            av = root / "video.mp4"
            wav = root / "audio.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=1920x1080:r=30:d=0.3", "-vf",
                            "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(av)], check=True, timeout=30)
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "sine=frequency=1000:sample_rate=48000:duration=3",
                            "-af", "volume=-2dB", "-c:a", "pcm_s24le", str(wav)], check=True, timeout=30)
            sources = [
                ("av-sdr-web-1080p30-noaudio.json", av, 4),
                ("audio-program-48k-mono-lufs23.json", wav, 6),
                ("otio-runtime-introduction-v2.json",
                 ROOT / "productions/runtime-introduction/timeline/assembly.v2.otio", 4),
                ("timed-text-runtime-introduction-en.json",
                 ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml", 5),
            ]
            for i, (profile, source, count) in enumerate(sources):
                with self.subTest(profile=profile):
                    _, _, result = self.native(profile, source, root / f"out-{i}")
                    self.assertEqual(len(result["verifiedFiles"]), count)
            bad = root / "bad.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                            "color=c=black:s=320x240:r=30:d=0.3",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bad)], check=True, timeout=30)
            self.native(sources[0][0], bad, root / "negative", expected_exit=2)

    def test_native_selected_identity_and_raw_drift_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml"
            plan, receipt, _ = self.native("timed-text-runtime-introduction-en.json", source, root / "evidence")
            # Mutate the selected plan, not the native provider or its retained bytes.
            expected = digest(receipt)
            from ordivon_studio.processing_plan_identity import closure_digest

            def remove_helper_and_rebind(value):
                closure = value["sourceClosureBinding"]
                removed = next(row for row in closure["files"] if row["path"].endswith("strict_json.py"))
                closure["files"].remove(removed)
                closure["digest"] = closure_digest(closure["files"])
                value["execution"]["hostDependencies"] = [
                    row for row in value["execution"]["hostDependencies"]
                    if not row["path"].endswith("/" + removed["path"])
                ]

            def extra_helper_and_rebind(value):
                closure = value["sourceClosureBinding"]
                extra = {"path": "unselected.py", "digest": "sha256:" + "0" * 64}
                closure["files"].append(extra)
                closure["files"].sort(key=lambda row: row["path"])
                closure["digest"] = closure_digest(closure["files"])
                host = value["execution"]["hostDependencies"]
                host.append({"path": str(ROOT / extra["path"]), "expectedDigest": extra["digest"]})
                host.sort(key=lambda row: row["path"])

            mutants = {
                "empty closure": lambda p: p["sourceClosureBinding"].update(files=[]),
                "missing host commitments": lambda p: p["execution"].pop("hostDependencies"),
                "wrong adapter": lambda p: p.update(adapterDigest="sha256:" + "0" * 64),
                "wrong closure": lambda p: p["sourceClosureBinding"].update(digest="sha256:" + "0" * 64),
                "missing helper coherently rehashed": remove_helper_and_rebind,
                "foreign helper coherently rehashed": extra_helper_and_rebind,
                "duplicate closure path": lambda p: p["sourceClosureBinding"]["files"].append(
                    p["sourceClosureBinding"]["files"][0]),
                "noncanonical order": lambda p: p["sourceClosureBinding"]["files"].reverse(),
                "duplicate commitment": lambda p: p["execution"]["hostDependencies"].append(
                    p["execution"]["hostDependencies"][0]),
                "wrong commitment digest": lambda p: p["execution"]["hostDependencies"][0].update(
                    expectedDigest="sha256:" + "0" * 64),
                "wrong closure scope": lambda p: p["sourceClosureBinding"].update(scope="runtime-witness"),
                "path alias": lambda p: p["execution"]["args"].__setitem__(1, str(source.parent) + "/./" + source.name),
            }
            for name, mutate in mutants.items():
                with self.subTest(plan_mutation=name):
                    wrong = copy.deepcopy(plan)
                    mutate(wrong)
                    with self.assertRaises(ValueError):
                        self.qualify(wrong, 0, expected)
            self.assertTrue(self.qualify(plan, 0, expected)["mechanicalOk"])
            original = receipt.read_bytes()
            expected = digest(receipt)
            self.assertEqual(self.qualify(plan, None, expected)["standing"], "UNKNOWN")
            self.assertEqual(self.qualify(plan, 3, expected)["standing"], "UNKNOWN")
            for invalid in (True, 2):
                with self.assertRaises(ValueError):
                    self.qualify(plan, invalid, expected)
            stale = copy.deepcopy(plan)
            stale["execution"]["args"][3] = str(root / "other")
            stale["expectedReceipt"] = str(root / "other/evidence.json")
            self.assertEqual(self.qualify(stale, 0, expected)["standing"], "UNKNOWN")
            for mutate in (
                lambda x: x["input"].update(digest="sha256:" + "0"*64),
                lambda x: x["profile"].update(path="/different/profile.json"),
                lambda x: x.update(evidenceDirectory=str(root / "other")),
                lambda x: x.update(schemaVersion=True),
                lambda x: x["mechanicalDelivery"].update(ok=1),
            ):
                value = json.loads(original)
                mutate(value)
                receipt.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    self.qualify(plan, 0, digest(receipt))
            receipt.write_bytes(original.replace(b'{', b'{"schemaVersion":1,', 1))
            with self.assertRaises(ValueError):
                self.qualify(plan, 0, digest(receipt))
            receipt.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                self.qualify(plan, 0, expected)
            receipt.write_bytes(original)
            raw = receipt.parent / "raw/normalized.vtt"
            bytes_before = raw.read_bytes()
            raw.write_bytes(bytes_before + b"\nchanged")
            with self.assertRaisesRegex(ValueError, "raw evidence digest mismatch"):
                self.qualify(plan, 0, expected)
            raw.unlink()
            self.assertEqual(self.qualify(plan, 0, expected)["standing"], "UNKNOWN")
            raw.write_bytes(bytes_before)
            self.assertIs(self.qualify(plan, 0, expected)["mechanicalOk"], True)
