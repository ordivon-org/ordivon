#!/usr/bin/env python3
"""Standards-first shadow verifier for bounded native FLAC audio artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = ROOT / "artifact-delivery/shadow-contracts/audio-flac-contract-v1.schema.json"
FLAC = Path(os.environ.get("ARTIFACT_FLAC", "/opt/ordivon/external/flac/1.5.0-1/flac"))
METAFLAC = Path(os.environ.get("ARTIFACT_METAFLAC", "/opt/ordivon/external/flac/1.5.0-1/metaflac"))
FFMPEG = Path(os.environ.get("ARTIFACT_FFMPEG", "/usr/bin/ffmpeg"))
FFPROBE = Path(os.environ.get("ARTIFACT_FFPROBE", "/usr/bin/ffprobe"))
ALLOWED_BLOCK_TYPES = {0, 1, 3, 4}
BLOCK_TYPE_RE = re.compile(r"^\s*type:\s*(\d+)\s*\(([^)]+)\)", re.MULTILINE)


def run(argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def md5_bytes(data: bytes) -> str:
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def artifact_fact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "name": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)}


def text(p: subprocess.CompletedProcess[bytes]) -> tuple[str, str]:
    return p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def metaflac_value(path: Path, option: str) -> tuple[int, str, str]:
    p = run([str(METAFLAC), option, str(path)])
    out, err = text(p)
    return p.returncode, out.strip(), err


def validate_contract(contract: dict[str, Any]) -> list[str]:
    schema = json.loads(CONTRACT_SCHEMA.read_text())
    return [f"audio contract schema invalid: {e.message}" for e in sorted(jsonschema.Draft202012Validator(schema).iter_errors(contract), key=lambda e: list(e.path))]


def verify_flac(path: Path, contract_path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {"schemaVersion": 1, "kind": "artifact-audio-verification", "profileId": "audio-flac-pcm16-r1", "status": "FAIL", "failures": ["input is not a regular file"]}
    try:
        contract = json.loads(contract_path.read_text())
    except Exception as error:
        return {"schemaVersion": 1, "kind": "artifact-audio-verification", "profileId": "audio-flac-pcm16-r1", "status": "FAIL", "artifact": artifact_fact(path), "failures": [f"contract unreadable: {error}"]}
    failures = validate_contract(contract)
    evidence_dir = evidence_dir or Path(tempfile.mkdtemp(prefix="artifact-audio-evidence-"))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "artifact-audio-verification",
        "profileId": "audio-flac-pcm16-r1",
        "status": "FAIL",
        "artifact": artifact_fact(path),
        "contract": {"path": str(contract_path.resolve()), "sha256": sha256_file(contract_path), "canonicalDigest": canonical_digest(contract)},
        "tools": {},
        "failures": failures,
    }
    if failures:
        result["boundary"] = "Invalid audio object contracts fail before decoder evidence can be promoted."
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    for name, tool in (("flac", FLAC), ("metaflac", METAFLAC), ("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
        if not tool.is_file() or not os.access(tool, os.X_OK):
            failures.append(f"required mature external capability unavailable: {name}")
        else:
            result["tools"][name] = {"path": str(tool.resolve()), "sha256": sha256_file(tool)}
    if failures:
        result["failures"] = failures
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # Reference implementation full-stream integrity test.
    test = run([str(FLAC), "-t", str(path)])
    tout, terr = text(test)
    (evidence_dir / "flac-test.txt").write_text(tout + terr)
    reference_ok = test.returncode == 0
    if not reference_ok:
        failures.append("reference FLAC full-stream test failed")

    # Native metadata blocks and STREAMINFO.
    listing = run([str(METAFLAC), "--list", str(path)])
    lout, lerr = text(listing)
    (evidence_dir / "metaflac-list.txt").write_text(lout + lerr)
    block_types = [{"type": int(n), "name": name} for n, name in BLOCK_TYPE_RE.findall(lout)] if listing.returncode == 0 else []
    block_failures: list[str] = []
    if listing.returncode != 0 or not block_types:
        block_failures.append("metaflac could not enumerate metadata blocks")
    else:
        observed = {x["type"] for x in block_types}
        forbidden = sorted(observed - ALLOWED_BLOCK_TYPES)
        if forbidden:
            block_failures.append("metadata block type(s) outside R1 allow-list: " + ",".join(map(str, forbidden)))
        if block_types[0]["type"] != 0:
            block_failures.append("STREAMINFO is not the first metadata block")
    failures.extend(block_failures)

    options = {
        "sampleRateHz": "--show-sample-rate",
        "channels": "--show-channels",
        "bitsPerSample": "--show-bps",
        "totalSamples": "--show-total-samples",
        "streamInfoMd5": "--show-md5sum",
    }
    streaminfo: dict[str, Any] = {}
    stream_failures: list[str] = []
    for key, option in options.items():
        rc, value, err = metaflac_value(path, option)
        if rc != 0 or not value:
            stream_failures.append(f"metaflac failed to read {key}")
            continue
        if key == "streamInfoMd5":
            streaminfo[key] = value.lower()
        else:
            try: streaminfo[key] = int(value)
            except ValueError: stream_failures.append(f"metaflac returned non-integer {key}")
    want = contract["audio"]
    for key in ("sampleRateHz", "channels", "bitsPerSample", "totalSamples"):
        if streaminfo.get(key) != want[key]: stream_failures.append(f"STREAMINFO {key} differs from contract")
    md5 = str(streaminfo.get("streamInfoMd5") or "")
    if not re.fullmatch(r"[0-9a-f]{32}", md5) or md5 == "0" * 32:
        stream_failures.append("R1 requires a non-zero valid STREAMINFO decoded-audio MD5")
    failures.extend(stream_failures)

    # Independent FFprobe technical interpretation.
    probe = run([str(FFPROBE), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    pout, perr = text(probe)
    (evidence_dir / "ffprobe.json").write_text(pout if pout else perr)
    probe_failures: list[str] = []
    try: pobj = json.loads(pout) if probe.returncode == 0 else {}
    except json.JSONDecodeError: pobj = {}
    streams = pobj.get("streams") if isinstance(pobj, dict) else None
    stream = streams[0] if isinstance(streams, list) and len(streams) == 1 else None
    if not isinstance(stream, dict):
        probe_failures.append("FFprobe did not expose exactly one audio stream")
        stream = {}
    if stream.get("codec_type") != "audio" or stream.get("codec_name") != "flac": probe_failures.append("FFprobe does not identify a native FLAC audio stream")
    if (pobj.get("format") or {}).get("format_name") != "flac": probe_failures.append("FFprobe container/format is not native FLAC")
    def as_int(v: Any, default: int = -1) -> int:
        try: return int(v)
        except Exception: return default
    if as_int(stream.get("sample_rate")) != want["sampleRateHz"]: probe_failures.append("FFprobe sample rate differs from contract")
    if as_int(stream.get("channels")) != want["channels"]: probe_failures.append("FFprobe channel count differs from contract")
    if as_int(stream.get("bits_per_raw_sample")) != want["bitsPerSample"]: probe_failures.append("FFprobe raw bit depth differs from contract")
    if as_int(stream.get("duration_ts")) != want["totalSamples"]: probe_failures.append("FFprobe sample count/duration_ts differs from contract")
    failures.extend(probe_failures)

    # Canonical PCM decoder matrix. R1 fixes 16-bit signed little-endian interleaved PCM.
    ref = run([str(FLAC), "-d", "-c", "--silent", "--force-raw-format", "--endian=little", "--sign=signed", str(path)])
    ff = run([str(FFMPEG), "-v", "error", "-i", str(path), "-map", "0:a:0", "-f", "s16le", "-acodec", "pcm_s16le", "-"])
    (evidence_dir / "reference-decoder.stderr.txt").write_bytes(ref.stderr)
    (evidence_dir / "ffmpeg-decoder.stderr.txt").write_bytes(ff.stderr)
    decoder_failures: list[str] = []
    if ref.returncode != 0: decoder_failures.append("reference FLAC PCM decode failed")
    if ff.returncode != 0: decoder_failures.append("FFmpeg PCM decode failed")
    ref_sha = sha256_bytes(ref.stdout); ff_sha = sha256_bytes(ff.stdout)
    exact = ref.returncode == 0 and ff.returncode == 0 and ref.stdout == ff.stdout
    if not exact: decoder_failures.append("reference FLAC and FFmpeg canonical PCM bytes differ")
    expected_bytes = want["totalSamples"] * want["channels"] * 2
    if len(ref.stdout) != expected_bytes: decoder_failures.append("reference canonical PCM byte count differs from contract-derived size")
    if len(ff.stdout) != expected_bytes: decoder_failures.append("FFmpeg canonical PCM byte count differs from contract-derived size")
    failures.extend(decoder_failures)

    pcm_md5 = md5_bytes(ref.stdout) if ref.returncode == 0 else ""
    pcm_failures: list[str] = []
    if md5 and pcm_md5 != md5: pcm_failures.append("STREAMINFO MD5 differs from canonical decoded PCM MD5")
    expected_sha = want.get("expectedPcmSha256")
    if expected_sha and ref_sha != expected_sha: pcm_failures.append("canonical decoded PCM SHA-256 differs from object contract")
    failures.extend(pcm_failures)

    result.update({
        "referenceIntegrity": {"status": "PASS" if reference_ok else "FAIL", "returnCode": test.returncode, "evidenceSha256": sha256_file(evidence_dir / "flac-test.txt")},
        "metadataBlockPolicy": {"status": "PASS" if not block_failures else "FAIL", "observedBlocks": block_types, "allowedTypeIds": sorted(ALLOWED_BLOCK_TYPES), "failures": block_failures},
        "streamInfo": {"status": "PASS" if not stream_failures else "FAIL", **streaminfo, "failures": stream_failures},
        "independentTechnicalView": {"status": "PASS" if not probe_failures else "FAIL", "codecName": stream.get("codec_name"), "sampleRateHz": as_int(stream.get("sample_rate")), "channels": as_int(stream.get("channels")), "bitsPerRawSample": as_int(stream.get("bits_per_raw_sample")), "totalSamples": as_int(stream.get("duration_ts")), "failures": probe_failures, "evidenceSha256": sha256_file(evidence_dir / "ffprobe.json")},
        "decoderMatrix": {"status": "PASS" if not decoder_failures else "FAIL", "canonicalFormat": "s16le", "referencePcmSha256": ref_sha, "ffmpegPcmSha256": ff_sha, "exactByteMatch": exact, "pcmBytes": len(ref.stdout), "expectedPcmBytes": expected_bytes, "failures": decoder_failures},
        "pcmIdentity": {"status": "PASS" if not pcm_failures else "FAIL", "streamInfoMd5": md5, "decodedPcmMd5": pcm_md5, "decodedPcmSha256": ref_sha, "contractExpectedPcmSha256": expected_sha, "failures": pcm_failures},
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "boundary": "PASS is bounded to native RFC 9639 FLAC carrying 16-bit signed PCM with one or two channels under one exact audio object contract. It establishes reference-stream integrity, bounded metadata-block policy, STREAMINFO/FFprobe technical agreement, exact independent-decoder PCM agreement, decoded-audio MD5 identity and optional contract PCM SHA-256. It does not establish artistic/factual correctness, subjective audio quality, loudness/mastering compliance, tag truth, excluded metadata semantics or general preservation-policy compliance."
    })
    (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--evidence-directory", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    value = verify_flac(args.input, args.contract, args.evidence_directory)
    text_out = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text_out)
    else: print(text_out, end="")
    return 0 if value.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
