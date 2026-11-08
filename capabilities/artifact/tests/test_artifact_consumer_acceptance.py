"""Real native-output -> Artifact verification service -> consumer readback.

Independent consumers prove only the stated format/content facts, not artistic
quality, production deployment, accessibility or domain-specific approval.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_verify_consumer", ROOT / "scripts/artifact_verify.py")
SERVICE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVICE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_request(
    root: Path, profile_id: str, subject: Path, contract: Path | None = None,
) -> Path:
    profile = SERVICE.PROFILE_REGISTRY.resolve(profile_id).canonical_path
    envelope = {
        "schemaVersion": 1,
        "kind": "artifact-verification-request",
        "requestId": "consumer-e2e-" + profile_id,
        "profile": {"id": profile_id, "path": str(profile), "sha256": digest(profile)},
        "subject": {"path": str(subject), "sha256": digest(subject)},
        "evidenceDirectory": str(root / "artifact-evidence"),
        "consumer": {"id": "consumer-readback-fixture", "purpose": "bounded native readback"},
    }
    if contract is not None:
        envelope["objectContract"] = {"path": str(contract), "sha256": digest(contract)}
    request_path = root / "request.json"
    request_path.write_text(json.dumps(envelope))
    return request_path


def make_wave(root: Path, frames: int = 4800, channels: int = 2) -> tuple[Path, bytes]:
    subject = root / "asset.wav"
    raw = b"".join(
        struct.pack("<" + "h" * channels, *(
            (index * (channel + 5) * 23) % 20000 - 10000
            for channel in range(channels)
        ))
        for index in range(frames)
    )
    with wave.open(str(subject), "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(2)
        writer.setframerate(48000)
        writer.writeframes(raw)
    return subject, raw


def audio_contract(root: Path, profile_id: str, raw: bytes, frames: int) -> Path:
    audio = {
        "sampleRateHz": 48000,
        "channels": 2,
        "bitsPerSample": 16,
        "expectedPcmSha256": hashlib.sha256(raw).hexdigest(),
    }
    if profile_id == "audio-wave-pcm16-r1":
        audio["frameCount"] = frames
    else:
        audio["totalSamples"] = frames
    value = {
        "contractVersion": 1, "id": "consumer-audio-acceptance",
        "profileId": profile_id, "audio": audio,
    }
    contract = root / "contract.json"
    contract.write_text(json.dumps(value))
    return contract


class ArtifactConsumerServiceTests(unittest.TestCase):
    @staticmethod
    def require(*tools: Path) -> None:
        for tool in tools:
            if not tool.is_file():
                raise unittest.SkipTest(f"native executable unavailable: {tool}")

    def test_wave_game_asset_native_consumer_readback(self):
        from scripts import artifact_wave as wave_verifier
        self.require(
            wave_verifier.SNDFILE_INFO, wave_verifier.SOX,
            wave_verifier.SOXI, wave_verifier.FFMPEG, wave_verifier.FFPROBE,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject, raw = make_wave(root)
            contract = audio_contract(root, "audio-wave-pcm16-r1", raw, 4800)
            result = SERVICE.verify_request(make_request(root, "audio-wave-pcm16-r1", subject, contract))
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["profileVerificationComplete"], result)
            self.assertEqual(result["requiredEvidenceAssessment"]["status"], "COMPLETE")
            self.assertEqual(
                result["toolIdentityAssessment"]["status"], "OBSERVED_POSTRUN_CONSISTENT"
            )
            self.assertFalse(result["toolIdentityAssessment"]["dependenciesComplete"])
            with wave.open(str(subject), "rb") as consumer:
                self.assertEqual(consumer.getnchannels(), 2)
                self.assertEqual(consumer.getsampwidth(), 2)
                self.assertEqual(consumer.getframerate(), 48000)
                self.assertEqual(consumer.readframes(4800), raw)
            self.assertEqual(json.loads((root / "artifact-evidence/service-result.json").read_text())["status"], "PASS")

    def test_flac_native_media_consumer_decoded_pcm_readback(self):
        from scripts import artifact_audio as flac_verifier
        self.require(
            flac_verifier.FLAC, flac_verifier.METAFLAC,
            flac_verifier.FFMPEG, flac_verifier.FFPROBE,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wave_subject, raw = make_wave(root)
            subject = root / "asset.flac"
            encoder = subprocess.run(
                [str(flac_verifier.FLAC), "-f", "--silent", "-o", str(subject), str(wave_subject)],
                capture_output=True,
            )
            self.assertEqual(encoder.returncode, 0, encoder.stderr.decode(errors="replace"))
            contract = audio_contract(root, "audio-flac-pcm16-r1", raw, 4800)
            result = SERVICE.verify_request(make_request(root, "audio-flac-pcm16-r1", subject, contract))
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["profileVerificationComplete"], result)
            consumer = subprocess.run([
                str(flac_verifier.FFMPEG), "-v", "error", "-i", str(subject),
                "-f", "s16le", "-acodec", "pcm_s16le", "-",
            ], capture_output=True)
            self.assertEqual(consumer.returncode, 0, consumer.stderr.decode(errors="replace"))
            self.assertEqual(consumer.stdout, raw)

    def test_png_media_display_consumer_pixel_readback(self):
        from scripts import artifact_still_image as png_verifier
        self.require(
            png_verifier.MAGICK, png_verifier.PNGCHECK,
            png_verifier.EXIFTOOL, png_verifier.VIPS,
            png_verifier.VIPSHEADER,
        )
        from PIL import Image, PngImagePlugin
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject = root / "asset.png"
            png_info = PngImagePlugin.PngInfo()
            png_info.add(b"sRGB", bytes([0]))
            Image.new("RGB", (6, 5), (68, 136, 204)).save(
                subject, pnginfo=png_info
            )
            result = SERVICE.verify_request(make_request(root, "still-image-png-srgb-r1", subject))
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["profileVerificationComplete"], result)
            with Image.open(subject) as consumer:
                self.assertEqual(consumer.size, (6, 5))
                self.assertEqual(consumer.convert("RGB").getpixel((0, 0)), (68, 136, 204))

    def test_parquet_research_dataset_readback_is_not_profile_claim_promotion(self):
        from scripts import artifact_dataset as dataset
        self.require(dataset.PYARROW_PYTHON, dataset.DUCKDB)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject = root / "dataset.parquet"
            writer = r"""
import pyarrow as pa
import pyarrow.parquet as pq
import sys
schema = pa.schema([
 pa.field("id", pa.int64(), nullable=False),
 pa.field("name", pa.string(), nullable=False),
 pa.field("score", pa.float64(), nullable=True),
 pa.field("active", pa.bool_(), nullable=False),
])
rows = [
 {"id": 2, "name": "beta", "score": None, "active": False},
 {"id": 1, "name": "alpha", "score": 1.25, "active": True},
 {"id": 3, "name": "gamma", "score": -4.5, "active": True},
]
pq.write_table(pa.Table.from_pylist(rows, schema=schema), sys.argv[1], compression="zstd", version="2.6")
"""
            produced = subprocess.run(
                [str(dataset.PYARROW_PYTHON), "-c", writer, str(subject)],
                capture_output=True,
            )
            self.assertEqual(produced.returncode, 0, produced.stderr.decode(errors="replace"))
            contract = ROOT / "artifact-delivery/shadow-contracts/dataset-parquet-flat-smoke-r1.json"
            result = SERVICE.verify_request(make_request(root, "dataset-parquet-flat-r1", subject, contract))
            self.assertEqual(result["status"], "PASS", result)
            self.assertFalse(result["profileVerificationComplete"])
            self.assertEqual(result["requiredEvidenceAssessment"]["status"], "NOT_EVALUATED")
            self.assertEqual(result["inputIdentity"]["subject"], "EXACT_BYTES_SNAPSHOT")
            self.assertEqual(result["inputIdentity"]["objectContract"], "EXACT_BYTES_SNAPSHOT")
            self.assertEqual(
                result["toolIdentityAssessment"]["status"], "OBSERVED_POSTRUN_CONSISTENT"
            )
            self.assertNotEqual(result["verification"]["artifact"]["path"], str(subject))
            safe_path = str(subject).replace("'", "''")
            consumer = subprocess.run([
                str(dataset.DUCKDB), "-json", "-c",
                f"SELECT id, name FROM read_parquet('{safe_path}') ORDER BY id",
            ], text=True, capture_output=True)
            self.assertEqual(consumer.returncode, 0, consumer.stderr)
            self.assertEqual(
                json.loads(consumer.stdout),
                [{"id": 1, "name": "alpha"}, {"id": 2, "name": "beta"}, {"id": 3, "name": "gamma"}],
            )

    def test_aggregate_pass_missing_claims_is_not_accepted_by_strict_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject, raw = make_wave(root)
            contract = audio_contract(root, "audio-wave-pcm16-r1", raw, 4800)
            request = make_request(root, "audio-wave-pcm16-r1", subject, contract)
            with mock.patch.object(
                SERVICE, "load_function",
                return_value=(lambda *args: {"status": "PASS", "failures": []}, "f" * 64),
            ):
                result = SERVICE.verify_request(request)
            self.assertEqual(result["status"], "FAIL", result)
            self.assertFalse(result["profileVerificationComplete"])
            self.assertEqual(result["requiredEvidenceAssessment"]["status"], "NOT_EVALUATED")
            self.assertTrue(any("requiredEvidence" in s for s in result["failures"]))

    def test_duplicate_request_json_rejected_before_provider_or_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject, raw = make_wave(root)
            contract = audio_contract(root, "audio-wave-pcm16-r1", raw, 4800)
            request = make_request(root, "audio-wave-pcm16-r1", subject, contract)
            original = request.read_text()
            request.write_text(original.replace(
                '"schemaVersion": 1,', '"schemaVersion": 1, "schemaVersion": 1,', 1
            ))
            with mock.patch.object(SERVICE, "load_function") as delegate:
                result = SERVICE.verify_request(request)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("duplicate JSON key" in error for error in result["failures"]))
            delegate.assert_not_called()
            self.assertFalse((root / "artifact-evidence").exists())


if __name__ == "__main__":
    unittest.main()
