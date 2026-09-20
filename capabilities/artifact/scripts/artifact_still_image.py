#!/usr/bin/env python3
"""Standards-first shadow verifier for bounded still-image profiles.

This is deliberately not a PNG parser. PNG validity is delegated to pngcheck;
metadata observation to ExifTool; pixel decoding to ImageMagick and libvips.
The local code only binds profile facts and compares independent evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PNGCHECK = Path(os.environ.get("ARTIFACT_PNGCHECK", "/opt/ordivon/external/pngcheck/4.0.1/bin/pngcheck"))
EXIFTOOL = Path(os.environ.get("ARTIFACT_EXIFTOOL", "/opt/ordivon/external/exiftool/13.55-1/exiftool"))
MAGICK = Path(os.environ.get("ARTIFACT_MAGICK", "/usr/bin/magick"))
VIPS = Path(os.environ.get("ARTIFACT_VIPS", "/usr/bin/vips"))
VIPSHEADER = Path(os.environ.get("ARTIFACT_VIPSHEADER", "/usr/bin/vipsheader"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}


def run(argv: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def _claim_result(status: str, pointer: str) -> dict[str, Any]:
    return {
        "status": status,
        "observationIds": [pointer.rsplit("/", 1)[-1]],
        "evidenceRefs": [],
        "nativePointers": [pointer],
        "nonClaims": [],
    }


def _claim_results(
    *,
    datastream: str = "NOT_EVALUATED",
    metadata: str = "NOT_EVALUATED",
    decoder: str = "NOT_EVALUATED",
    profile_facts: str = "NOT_EVALUATED",
) -> dict[str, Any]:
    return {
        "datastreamValidity": _claim_result(datastream, "/datastreamValidity"),
        "decoderMatrix": _claim_result(decoder, "/decoderMatrix"),
        "metadataObservation": _claim_result(metadata, "/metadata"),
        "profileFacts": _claim_result(profile_facts, "/profileFacts"),
    }


def tool_fact(path: Path, version_argv: list[str] | None = None) -> dict[str, Any]:
    if not path.is_file() or not os.access(path, os.X_OK):
        return {"status": "NOT_AVAILABLE", "path": str(path)}
    value: dict[str, Any] = {"status": "PASS", "path": str(path.resolve()), "sha256": sha256(path)}
    if version_argv:
        p = run([str(path), *version_argv], timeout=15)
        value["versionReturnCode"] = p.returncode
        value["versionOutput"] = (p.stdout + p.stderr).strip().splitlines()[:4]
    return value


def verify_png_srgb(path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    failures: list[str] = []
    if not path.is_file():
        return {"schemaVersion": 1, "kind": "artifact-still-image-verification", "profileId": "still-image-png-srgb-r1", "status": "FAIL", "claimResults": _claim_results(), "failures": ["input is not a regular file"]}
    tools = {
        "pngcheck": tool_fact(PNGCHECK),
        "exiftool": tool_fact(EXIFTOOL, ["-ver"]),
        "imagemagick": tool_fact(MAGICK, ["-version"]),
        "vips": tool_fact(VIPS, ["--version"]),
        "vipsheader": tool_fact(VIPSHEADER),
    }
    for name, value in tools.items():
        if value.get("status") != "PASS":
            failures.append(f"required external tool unavailable: {name}")
    if failures:
        return {"schemaVersion": 1, "kind": "artifact-still-image-verification", "profileId": "still-image-png-srgb-r1", "status": "FAIL", "artifact": fact(path), "tools": tools, "claimResults": _claim_results(), "failures": failures}

    evidence_dir = evidence_dir or Path(tempfile.mkdtemp(prefix="artifact-still-image-evidence-"))
    evidence_dir.mkdir(parents=True, exist_ok=True)

    quiet = run([str(PNGCHECK), "-q", str(path)])
    verbose = run([str(PNGCHECK), "-v", str(path)])
    (evidence_dir / "pngcheck.txt").write_text(verbose.stdout + verbose.stderr)
    png_text = verbose.stdout + verbose.stderr
    if quiet.returncode != 0 or verbose.returncode != 0:
        failures.append("pngcheck rejected the PNG datastream")
    chunks = re.findall(r"chunk ([A-Za-z0-9]{4}) at offset", png_text)
    required = {"sRGB"}
    prohibited = {"acTL", "fcTL", "fdAT", "iCCP", "cICP"}
    missing = sorted(required - set(chunks))
    forbidden = sorted(prohibited & set(chunks))
    if missing:
        failures.append("missing required PNG chunk(s): " + ",".join(missing))
    if forbidden:
        failures.append("prohibited PNG chunk(s) for bounded sRGB/static profile: " + ",".join(forbidden))

    identify = run([str(MAGICK), "identify", "-format", "%m\\n%w\\n%h\\n%z\\n%[colorspace]\\n%[channels]\\n", str(path)])
    if identify.returncode != 0:
        failures.append("ImageMagick identify failed")
        image_fact: dict[str, Any] = {"status": "FAIL", "stderr": identify.stderr[-2000:]}
    else:
        lines = identify.stdout.splitlines()
        if len(lines) < 6:
            failures.append("ImageMagick identify returned incomplete facts")
            image_fact = {"status": "FAIL", "output": identify.stdout}
        else:
            fmt, width, height, depth, colorspace, channels = lines[:6]
            image_fact = {"status": "PASS", "format": fmt, "width": int(width), "height": int(height), "depth": int(depth), "colorspace": colorspace, "channels": channels}
            if fmt != "PNG": failures.append("ImageMagick format is not PNG")
            if int(depth) != 8: failures.append("profile requires 8-bit PNG samples")
            if colorspace.casefold() != "srgb": failures.append("profile requires sRGB color interpretation")
            normalized_channels = re.sub(r"\s+", " ", channels.strip()).casefold()
            image_fact["channelsNormalized"] = normalized_channels
            if normalized_channels not in {"srgb 3.0", "srgba 4.0"}:
                failures.append("profile requires RGB or RGBA channels")

    metadata = run([str(EXIFTOOL), "-j", "-G1", "-s", str(path)])
    (evidence_dir / "exiftool.json").write_text(metadata.stdout)
    if metadata.returncode != 0:
        failures.append("ExifTool metadata extraction failed")
        metadata_summary: dict[str, Any] = {"status": "FAIL", "stderr": metadata.stderr[-2000:]}
    else:
        try:
            records = json.loads(metadata.stdout)
            record = records[0] if isinstance(records, list) and records else {}
            metadata_summary = {
                "status": "PASS",
                "observedGroupPropertyCount": len(record),
                "fileType": record.get("File:FileType"),
                "mimeType": record.get("File:MIMEType"),
                "groupsObserved": sorted({key.split(":", 1)[0] for key in record if ":" in key}),
                "rawEvidenceSha256": sha256(evidence_dir / "exiftool.json"),
            }
        except Exception as error:
            failures.append("ExifTool returned invalid JSON")
            metadata_summary = {"status": "FAIL", "error": str(error)}

    decode: dict[str, Any] = {"status": "FAIL"}
    if image_fact.get("status") == "PASS" and image_fact.get("depth") == 8:
        with tempfile.TemporaryDirectory(prefix="artifact-still-image-decode-") as d:
            td = Path(d)
            im_raw = td / "imagemagick.rgba"
            vips_native = td / "vips-native.v"
            vips_rgba = td / "vips-rgba.v"
            vips_raw = td / "vips.rgba"
            im = run([str(MAGICK), str(path), "-colorspace", "sRGB", "-depth", "8", f"RGBA:{im_raw}"])
            vc = run([str(VIPS), "colourspace", str(path), str(vips_native), "srgb"])
            if im.returncode != 0 or vc.returncode != 0:
                failures.append("independent decoder normalization failed")
            else:
                b = run([str(VIPSHEADER), "-f", "bands", str(vips_native)])
                f = run([str(VIPSHEADER), "-f", "format", str(vips_native)])
                bands = int(b.stdout.strip()) if b.returncode == 0 and b.stdout.strip().isdigit() else -1
                sample_format = f.stdout.strip() if f.returncode == 0 else ""
                sample_format_normalized = sample_format.upper()
                if "VIPS_FORMAT_UCHAR" not in sample_format_normalized and sample_format.strip().casefold() != "uchar":
                    failures.append(f"libvips normalized sample format is not uchar: {sample_format}")
                elif bands == 3:
                    join = run([str(VIPS), "bandjoin_const", str(vips_native), str(vips_rgba), "255"])
                    if join.returncode != 0:
                        failures.append("libvips alpha normalization failed")
                    vips_source = vips_rgba
                elif bands == 4:
                    vips_source = vips_native
                else:
                    failures.append(f"libvips normalized band count is not RGB/RGBA: {bands}")
                    vips_source = vips_native
                if not failures or all("libvips" not in item and "decoder" not in item for item in failures):
                    vr = run([str(VIPS), "rawsave", str(vips_source), str(vips_raw)])
                    if vr.returncode != 0 or not im_raw.is_file() or not vips_raw.is_file():
                        failures.append("independent raw sample extraction failed")
                    else:
                        im_sha, vips_sha = sha256(im_raw), sha256(vips_raw)
                        exact = im_raw.read_bytes() == vips_raw.read_bytes()
                        if not exact:
                            failures.append("ImageMagick and libvips decoded sample bytes differ")
                        decode = {"status": "PASS" if exact else "FAIL", "normalization": "8-bit sRGB RGBA", "imageMagickPixelSha256": im_sha, "libvipsPixelSha256": vips_sha, "exactMatch": exact, "byteCount": im_raw.stat().st_size}

    datastream_failures = (
        []
        if quiet.returncode == 0 and verbose.returncode == 0
        else ["pngcheck rejected the PNG datastream"]
    )
    profile_fact_failures: list[str] = []
    if missing:
        profile_fact_failures.append(
            "missing required PNG chunk(s): " + ",".join(missing)
        )
    if forbidden:
        profile_fact_failures.append(
            "prohibited PNG chunk(s) for bounded sRGB/static profile: "
            + ",".join(forbidden)
        )
    if image_fact.get("status") != "PASS":
        profile_fact_failures.append("ImageMagick profile facts are unavailable")
    else:
        if image_fact.get("format") != "PNG":
            profile_fact_failures.append("ImageMagick format is not PNG")
        if image_fact.get("depth") != 8:
            profile_fact_failures.append("profile requires 8-bit PNG samples")
        if str(image_fact.get("colorspace", "")).casefold() != "srgb":
            profile_fact_failures.append("profile requires sRGB color interpretation")
        if image_fact.get("channelsNormalized") not in {"srgb 3.0", "srgba 4.0"}:
            profile_fact_failures.append("profile requires RGB or RGBA channels")
    datastream_validity = {
        "status": "PASS" if not datastream_failures else "FAIL",
        "pngcheckReturnCode": quiet.returncode,
        "failures": datastream_failures,
    }
    profile_facts = {
        "status": "PASS" if not profile_fact_failures else "FAIL",
        "requiredChunks": sorted(required),
        "missingRequiredChunks": missing,
        "prohibitedChunksPresent": forbidden,
        "image": image_fact,
        "failures": profile_fact_failures,
    }
    claim_results = _claim_results(
        datastream=datastream_validity["status"],
        metadata="PASS" if metadata_summary.get("status") == "PASS" else "FAIL",
        decoder="PASS" if decode.get("status") == "PASS" else "FAIL",
        profile_facts=profile_facts["status"],
    )

    result = {
        "schemaVersion": 1,
        "kind": "artifact-still-image-verification",
        "profileId": "still-image-png-srgb-r1",
        "status": "PASS" if not failures else "FAIL",
        "artifact": fact(path),
        "tools": tools,
        "png": {"pngcheckReturnCode": quiet.returncode, "chunks": chunks, "requiredChunks": sorted(required), "prohibitedChunks": sorted(prohibited), "rawEvidenceSha256": sha256(evidence_dir / "pngcheck.txt")},
        "datastreamValidity": datastream_validity,
        "image": image_fact,
        "metadata": metadata_summary,
        "decoderMatrix": decode,
        "profileFacts": profile_facts,
        "claimResults": claim_results,
        "failures": failures,
        "boundary": "PASS is bounded to a static 8-bit sRGB PNG display/exchange profile: pngcheck validity evidence, explicit chunk/profile restrictions, metadata observation, and exact ImageMagick/libvips decoded RGBA sample equality. It does not establish aesthetic quality, semantic truth, human accessibility, rights validity, print color accuracy, HDR/APNG behavior, or general PNG encoder/decoder/editor implementation conformance."
    }
    (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--evidence-directory", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    value = verify_png_srgb(args.input, args.evidence_directory)
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if value.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
