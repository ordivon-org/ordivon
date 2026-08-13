from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ordivon_studio.foundational_media import (  # noqa: E402
    M7_EVIDENCE_KIND,
    ProfileArm,
    RegisteredCase,
    canonical_digest,
    haptic_challenger_report,
    live_realtime_experiment,
    profile_distinction_report,
    sha256_file,
    spatial_reference_experiment,
    still_intervention_report,
    still_visual_features,
)
from ordivon_studio.rich_perception import audio_structure_features, media_intervention_report  # noqa: E402


COMMON_TEXT = (
    "The response was lost. The operation outcome is unknown. "
    "Recover the same operation identity before concluding success or failure."
)


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def _write_svg(path: Path, *, mode: str) -> None:
    if mode == "baseline":
        background = "#111318"
        panel = "#f1efe9"
        accent = "#6f63ff"
        unknown_fill = "#e8e4d8"
        unknown_text = "#25262a"
        unknown_x, unknown_y, unknown_w, unknown_h = 625, 120, 330, 190
        footer = "UNKNOWN IS A STATE, NOT A FAILURE"
    elif mode == "outcome-color":
        background = "#111318"
        panel = "#f1efe9"
        accent = "#b00020"
        unknown_fill = "#b00020"
        unknown_text = "#ffffff"
        unknown_x, unknown_y, unknown_w, unknown_h = 610, 85, 370, 260
        footer = "UNKNOWN IS A STATE, NOT A FAILURE"
    elif mode == "crop-pressure":
        background = "#111318"
        panel = "#f1efe9"
        accent = "#6f63ff"
        unknown_fill = "#e8e4d8"
        unknown_text = "#25262a"
        unknown_x, unknown_y, unknown_w, unknown_h = 625, 120, 330, 190
        footer = "UNKNOWN IS A STATE, NOT A FAILURE"
    else:
        raise ValueError(mode)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="{background}"/>
<text x="80" y="78" fill="#f5f3ee" font-size="34" font-family="sans-serif" font-weight="700">RECOVERY STATE</text>
<rect x="80" y="120" width="330" height="190" rx="22" fill="{panel}"/>
<text x="115" y="180" fill="#25262a" font-size="22" font-family="sans-serif">1 · RESPONSE LOST</text>
<text x="115" y="225" fill="#25262a" font-size="18" font-family="sans-serif">No terminal result is visible.</text>
<line x1="410" y1="215" x2="{unknown_x}" y2="215" stroke="{accent}" stroke-width="10"/>
<polygon points="{unknown_x-18},200 {unknown_x},215 {unknown_x-18},230" fill="{accent}"/>
<rect x="{unknown_x}" y="{unknown_y}" width="{unknown_w}" height="{unknown_h}" rx="22" fill="{unknown_fill}"/>
<text x="{unknown_x+35}" y="{unknown_y+68}" fill="{unknown_text}" font-size="24" font-family="sans-serif" font-weight="700">2 · OUTCOME UNKNOWN</text>
<text x="{unknown_x+35}" y="{unknown_y+112}" fill="{unknown_text}" font-size="18" font-family="sans-serif">Do not infer success or failure.</text>
<text x="{unknown_x+35}" y="{unknown_y+150}" fill="{unknown_text}" font-size="18" font-family="sans-serif">Recover the same identity.</text>
<rect x="80" y="380" width="875" height="112" rx="18" fill="#1d2028" stroke="#444a58" stroke-width="2"/>
<text x="115" y="430" fill="#f5f3ee" font-size="22" font-family="sans-serif">{footer}</text>
<text x="115" y="468" fill="#b8bbc4" font-size="17" font-family="sans-serif">Same words. Different visual framing is the intervention.</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")


def run_still(root: Path) -> dict:
    target = root / "still"
    target.mkdir(parents=True, exist_ok=True)
    svgs = {}
    pngs = {}
    for mode in ("baseline", "outcome-color", "crop-pressure"):
        svg = target / f"{mode}.svg"
        png = target / f"{mode}.png"
        _write_svg(svg, mode=mode)
        _run(["/usr/bin/rsvg-convert", "--width", "1200", "--height", "630", "-o", str(png), str(svg)])
        svgs[mode] = svg
        pngs[mode] = png
    control = target / "baseline-reencode.png"
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(pngs["baseline"]), "-frames:v", "1", str(control)])
    # Crop the registered qualifier out of one delivered view, then rescale to the same delivery dimensions.
    cropped = target / "crop-pressure-delivery.png"
    _run([
        "/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(pngs["crop-pressure"]),
        "-vf", "crop=1200:360:0:0,scale=1200:630:flags=lanczos", "-frames:v", "1", str(cropped),
    ])
    baseline = still_visual_features(pngs["baseline"])
    control_features = still_visual_features(control)
    color = still_visual_features(pngs["outcome-color"])
    crop = still_visual_features(cropped)
    sensitivity = still_intervention_report(
        baseline,
        controls=[("lossless-ish-reencode", control_features)],
        perturbations=[("outcome-color-severity", color), ("qualifier-crop", crop)],
    )
    cases = [
        RegisteredCase("still.crop", "crop-removes-qualifier", "still-visual"),
        RegisteredCase("still.distance", "viewing-distance-legibility", "still-visual"),
        RegisteredCase("still.reproduction", "reproduction-changes-hierarchy", "still-visual"),
        RegisteredCase("still.geometry", "diagram-geometry-implies-relation", "still-visual"),
    ]
    distinction = profile_distinction_report(
        cases,
        [
            ProfileArm("core-only", frozenset({"diagram-geometry-implies-relation"}), 170),
            ProfileArm("still-candidate", frozenset(case.failure_class for case in cases), 250, 30),
            ProfileArm("wrong-motion", frozenset({"temporal-causality", "motion-implies-state"}), 250, 30),
            ProfileArm("sham", frozenset(), 250, 10),
        ],
    )
    return {
        "commonText": COMMON_TEXT,
        "artifacts": {name: {"path": str(path.relative_to(ROOT)), "digest": sha256_file(path)} for name, path in {**pngs, "baseline-reencode": control, "crop-delivery": cropped}.items()},
        "sensitivity": sensitivity,
        "distinction": distinction,
        "ordinaryProductionCounterevidence": {
            "production": "productions/site-social-card",
            "observation": "Core + rendered preview inspection already solved one viewing-distance/legibility defect while Still remained provisional.",
            "consequence": "Still-specific knowledge may be useful without earning a large resident profile; deletion must include ordinary-production evidence rather than only registered lab cases.",
        },
        "disposition": "retain-provisional-compress" if sensitivity["strictSeparation"] else "reject-current-equipment",
    }


def _windows_path(path: Path) -> str:
    return _run(["/usr/bin/wslpath", "-w", str(path)]).stdout.strip()


def run_audio(root: Path) -> dict:
    target = root / "audio"
    target.mkdir(parents=True, exist_ok=True)
    cues = target / "cues.json"
    cues.write_text(json.dumps({"cues": [{"id": "same-words", "text": COMMON_TEXT}]}, ensure_ascii=False), encoding="utf-8")
    script = ROOT / "scripts" / "synthesize-sapi-cues.ps1"
    _run([
        "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", _windows_path(script),
        "-InputJson", _windows_path(cues), "-OutputDir", _windows_path(target), "-Rate", "0",
    ])
    baseline = target / "same-words.wav"
    variants = {
        "reencode-control": target / "reencode-control.wav",
        "fast": target / "fast.wav",
        "slow": target / "slow.wav",
        "loud": target / "loud.wav",
        "masked": target / "masked.wav",
        "delayed-onset": target / "delayed-onset.wav",
    }
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline), "-c:a", "pcm_s16le", str(variants["reencode-control"])])
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline), "-af", "atempo=1.35", str(variants["fast"])])
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline), "-af", "atempo=0.75", str(variants["slow"])])
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline), "-af", "volume=6dB,alimiter=limit=0.95", str(variants["loud"])])
    _run([
        "/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline),
        "-f", "lavfi", "-i", "anoisesrc=color=pink:amplitude=0.10:sample_rate=48000",
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:weights='1 0.55':normalize=0,alimiter=limit=0.95",
        str(variants["masked"]),
    ])
    _run(["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(baseline), "-af", "adelay=900:all=1", str(variants["delayed-onset"])])
    base_features = audio_structure_features(baseline, bins=24)
    values = {name: audio_structure_features(path, bins=24) for name, path in variants.items()}
    sensitivity = media_intervention_report(
        baseline=base_features,
        controls=[("pcm-reencode", values["reencode-control"])],
        perturbations=[(name, value) for name, value in values.items() if name != "reencode-control"],
    )
    cases = [
        RegisteredCase("audio.prosody", "prosody-implies-confidence", "audio"),
        RegisteredCase("audio.masking", "masking-breaks-intelligibility", "audio"),
        RegisteredCase("audio.loudness", "loudness-implies-emphasis", "audio"),
        RegisteredCase("audio.silence", "silence-changes-temporal-meaning", "audio"),
        RegisteredCase("audio.playback", "playback-chain-changes-balance", "audio"),
    ]
    distinction = profile_distinction_report(
        cases,
        [
            ProfileArm("core-only", frozenset({"loudness-implies-emphasis"}), 170),
            ProfileArm("audio-candidate", frozenset(case.failure_class for case in cases), 290, 35),
            ProfileArm("wrong-writing-motion", frozenset({"silence-changes-temporal-meaning"}), 290, 35),
            ProfileArm("sham", frozenset(), 290, 10),
        ],
    )
    return {
        "commonText": COMMON_TEXT,
        "lexicalIdentity": "All perturbations derive from one exact SAPI waveform; no spoken words are added, removed, or substituted after synthesis.",
        "artifacts": {"baseline": {"path": str(baseline.relative_to(ROOT)), "digest": sha256_file(baseline)}, **{name: {"path": str(path.relative_to(ROOT)), "digest": sha256_file(path)} for name, path in variants.items()}},
        "sensitivity": sensitivity,
        "distinction": distinction,
        "ordinaryProductionEvidence": {
            "production": "productions/runtime-introduction",
            "facts": ["declared 48 kHz / 24-bit audio working profile", "SAPI narration receipt", "TimedText alignment", "Motion profile already treats sound/image relation as semantic"],
        },
        "disposition": "graduate-audio-profile" if sensitivity["strictSeparation"] else "retain-provisional",
    }


def run_live() -> dict:
    traces = [live_realtime_experiment(seed=seed) for seed in (20260813, 20260814, 20260815, 20260816, 20260817)]
    stale_windows = [item["naiveMisleadingExposureMs"] for item in traces]
    return {
        "traces": traces,
        "replicates": len(traces),
        "allGuardedFlagStale": all(item["guardedFlagsStale"] for item in traces),
        "allNaiveExposeStaleAsCurrent": all(item["naiveMarksStaleCurrent"] for item in traces),
        "meanNaiveMisleadingExposureMs": sum(stale_windows) / len(stale_windows),
        "disposition": "foundation-supported-candidate-not-active",
        "reason": "Real-time traces prove unknown-future/currentness/correction pressure, but no ordinary public live production or human live encounter exists yet.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="out/m7-foundations/evidence.json")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    root = output.parent
    root.mkdir(parents=True, exist_ok=True)
    required = ["/usr/bin/ffmpeg", "/usr/bin/ffprobe", "/usr/bin/rsvg-convert", "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"]
    missing = [item for item in required if not Path(item).exists()]
    if missing:
        raise SystemExit(f"missing M7 equipment: {missing}")
    report = {
        "schemaVersion": 1,
        "kind": M7_EVIDENCE_KIND,
        "observedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "commonProposition": COMMON_TEXT,
        "stillVisual": run_still(root),
        "audio": run_audio(root),
        "spatial3d": spatial_reference_experiment(),
        "liveRealtime": run_live(),
        "hapticPhysical": haptic_challenger_report(),
    }
    report["evidenceDigest"] = canonical_digest(report)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "ok": True,
        "output": str(output.relative_to(ROOT)),
        "digest": report["evidenceDigest"],
        "still": report["stillVisual"]["disposition"],
        "audio": report["audio"]["disposition"],
        "spatial": report["spatial3d"]["boundary"],
        "live": report["liveRealtime"]["disposition"],
        "haptic": report["hapticPhysical"]["disposition"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
