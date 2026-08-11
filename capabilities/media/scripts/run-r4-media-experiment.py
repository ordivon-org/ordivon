from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from ordivon_studio.rich_perception import (
    audio_structure_features,
    canonical_digest,
    crossmodal_circular_shift_null,
    crossmodal_profile_coupling,
    cue_boundary_silence_score,
    media_intervention_report,
    video_structure_features,
)


FFMPEG = "/usr/bin/ffmpeg"


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"command failed: {args}")


def chunk_bounds(duration: float, count: int) -> list[tuple[float, float]]:
    step = duration / count
    return [(index * step, (index + 1) * step) for index in range(count)]


def video_variant(source: Path, output: Path, order: Sequence[int], *, duration: float = 78.0) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = len(order)
    splits = "".join(f"[v{index}]" for index in range(count))
    filters = [f"[0:v]split={count}{splits}"]
    for index, (start, end) in enumerate(chunk_bounds(duration, count)):
        filters.append(f"[v{index}]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[c{index}]")
    concat = "".join(f"[c{index}]" for index in order)
    filters.append(f"{concat}concat=n={count}:v=1:a=0,scale=320:180:flags=bicubic,fps=30,format=yuv420p[outv]")
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-an",
            str(output),
        ]
    )


def audio_variant(source: Path, output: Path, order: Sequence[int], *, duration: float = 78.0) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = len(order)
    splits = "".join(f"[a{index}]" for index in range(count))
    filters = [f"[0:a]asplit={count}{splits}"]
    for index, (start, end) in enumerate(chunk_bounds(duration, count)):
        filters.append(f"[a{index}]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[c{index}]")
    concat = "".join(f"[c{index}]" for index in order)
    filters.append(f"{concat}concat=n={count}:v=0:a=1[outa]")
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outa]",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s24le",
            str(output),
        ]
    )


def av_baseline(video: Path, audio: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-t",
            "78",
            str(output),
        ]
    )


def av_cyclic_audio_shift(video: Path, audio: Path, output: Path, shift: float, *, duration: float = 78.0) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    filters = (
        f"[1:a]asplit=2[a0][a1];"
        f"[a0]atrim=start={shift:.6f}:end={duration:.6f},asetpts=PTS-STARTPTS[x];"
        f"[a1]atrim=start=0:end={shift:.6f},asetpts=PTS-STARTPTS[y];"
        "[x][y]concat=n=2:v=0:a=1[outa]"
    )
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-filter_complex",
            filters,
            "-map",
            "0:v:0",
            "-map",
            "[outa]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-t",
            "78",
            str(output),
        ]
    )


def exact_technical_match(reference: dict[str, Any], others: Sequence[dict[str, Any]], *, tolerance_seconds: float = 0.05) -> dict[str, Any]:
    ref = reference["technical"]
    checks = []
    for features in others:
        current = features["technical"]
        same = True
        for key in set(ref) | set(current):
            if key == "durationSeconds":
                same = same and abs(float(ref.get(key, 0.0)) - float(current.get(key, 0.0))) <= tolerance_seconds
            else:
                same = same and ref.get(key) == current.get(key)
        checks.append(same)
    return {"allMatch": all(checks), "checks": checks, "reference": ref}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="owned picture-master path")
    parser.add_argument("--audio", required=True, help="owned narration/music-audio path")
    parser.add_argument("--timed-text", required=True)
    parser.add_argument("--article-report")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output = Path(args.output_dir)
    media = output / "media"
    video_source = Path(args.video)
    audio_source = Path(args.audio)
    timed_text = json.loads(Path(args.timed_text).read_text(encoding="utf-8"))

    orders = {
        "same-a": [0, 1, 2, 3, 4, 5],
        "same-b": [0, 1, 2, 3, 4, 5],
        "swap-middle": [0, 2, 1, 3, 4, 5],
        "alternating": [0, 2, 4, 1, 3, 5],
        "reverse": [5, 4, 3, 2, 1, 0],
    }

    video_paths: dict[str, Path] = {}
    for name, order in orders.items():
        path = media / f"video-{name}.mp4"
        video_variant(video_source, path, order)
        video_paths[name] = path
    video_features = {name: video_structure_features(path, bins=24, sample_step_frames=6) for name, path in video_paths.items()}
    video_report = media_intervention_report(
        baseline=video_features["same-a"],
        controls=[("same-b", video_features["same-b"])],
        perturbations=[(name, video_features[name]) for name in ("swap-middle", "alternating", "reverse")],
    )
    video_report["technicalMatch"] = exact_technical_match(video_features["same-a"], list(video_features.values())[1:])
    video_report["profiles"] = {name: features["signatures"] for name, features in video_features.items()}

    audio_paths: dict[str, Path] = {}
    for name, order in orders.items():
        path = media / f"audio-{name}.wav"
        audio_variant(audio_source, path, order)
        audio_paths[name] = path
    audio_features = {name: audio_structure_features(path, bins=24) for name, path in audio_paths.items()}
    audio_report = media_intervention_report(
        baseline=audio_features["same-a"],
        controls=[("same-b", audio_features["same-b"])],
        perturbations=[(name, audio_features[name]) for name in ("swap-middle", "alternating", "reverse")],
    )
    audio_report["technicalMatch"] = exact_technical_match(audio_features["same-a"], list(audio_features.values())[1:])
    audio_report["profiles"] = {name: features["signatures"] for name, features in audio_features.items()}

    av_base = media / "av-baseline.mp4"
    av_baseline(video_source, audio_source, av_base)
    shifts = (5.0, 11.0, 17.0)
    av_shifted: dict[float, Path] = {}
    for shift in shifts:
        path = media / f"av-shift-{int(shift)}s.mp4"
        av_cyclic_audio_shift(video_source, audio_source, path, shift)
        av_shifted[shift] = path

    video_for_coupling = video_structure_features(video_paths["same-a"], bins=156, sample_step_frames=15)
    av_audio = {"baseline": audio_structure_features(av_base, bins=156)}
    for shift, path in av_shifted.items():
        av_audio[f"shift-{int(shift)}s"] = audio_structure_features(path, bins=156)
    alignment = {}
    for name, features in av_audio.items():
        alignment[name] = {
            "cueBoundary": cue_boundary_silence_score(features, timed_text, window_seconds=0.75),
            "crossmodal": crossmodal_profile_coupling(video_for_coupling, features),
        }
    baseline_silence = alignment["baseline"]["cueBoundary"]["boundarySilenceContrastZ"]
    shifted_silence = [alignment[name]["cueBoundary"]["boundarySilenceContrastZ"] for name in alignment if name != "baseline"]
    circular_null = crossmodal_circular_shift_null(video_for_coupling, av_audio["baseline"])
    av_report = {
        "alignment": alignment,
        "baselineBoundarySilenceContrastZ": baseline_silence,
        "maxShiftedBoundarySilenceContrastZ": max(shifted_silence),
        "baselineRanksAboveAllShifts": baseline_silence > max(shifted_silence),
        "circularShiftNull": circular_null,
        "equipmentDecision": "bounded-alignment-diagnostic" if circular_null["disposition"] == "bounded-positive-alignment-signal" else "no-robust-controlled-alignment-sensitivity",
        "promotionDecision": "do-not-promote-as-congruence-detector",
        "boundary": "Audio is cyclically shifted while picture timing and marginal media content remain fixed. Cue-boundary and crossmodal metrics measure temporal relation only, not semantic or aesthetic congruence. A bounded positive circular-shift signal is retained as a diagnostic, not a creative law.",
    }

    article = None
    if args.article_report:
        article = json.loads(Path(args.article_report).read_text(encoding="utf-8"))

    article_signature = None
    if article and article.get("records"):
        article_signature = article["records"][0]["candidate"]["positionSignature"]
    shared_signature_keys = sorted(video_features["same-a"]["signatures"]["change"].keys())
    cross_medium = {
        "sharedProfileSignatureDimensions": shared_signature_keys,
        "articleParagraphProfileSignature": article_signature,
        "videoChangeProfileSignature": video_features["same-a"]["signatures"]["change"],
        "audioRmsProfileSignature": audio_features["same-a"]["signatures"]["rmsAmplitude"],
        "claimBoundary": "Shared profile operators provide a reusable measurement grammar for position, variation, repetition, and concentration. Equal field names do not imply equal semantics or a shared success direction across media.",
        "informationGainMatrix": {
            "articleSelectionAccuracyGain": article.get("accuracyGainOverShallow") if article else None,
            "videoControlledSensitivity": video_report["equipmentDecision"],
            "audioControlledSensitivity": audio_report["equipmentDecision"],
            "avAlignmentSensitivity": av_report["equipmentDecision"],
        },
    }

    report = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-r4-rich-media-acceptance",
        "ownedInputs": {
            "video": str(video_source),
            "audio": str(audio_source),
            "timedText": args.timed_text,
        },
        "r4bVideo": video_report,
        "r4cAudio": audio_report,
        "r4bMultimodal": av_report,
        "r4dCrossMedium": cross_medium,
        "retentionBoundary": {
            "videoTemporalSignals": video_report["equipmentDecision"],
            "audioStructuralSignals": audio_report["equipmentDecision"],
            "audioCueAlignment": av_report["equipmentDecision"],
            "articleMechanicalSelectionModel": article.get("equipmentDecision") if article else None,
        },
    }
    report["reportDigest"] = canonical_digest(report)
    output.mkdir(parents=True, exist_ok=True)
    (output / "r4bcd-rich-media.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "video": {k: video_report[k] for k in ("equipmentDecision", "maxControlDistance", "minPerturbationDistance", "medianPerturbationDistance", "separationRatio", "technicalMatch")},
                "audio": {k: audio_report[k] for k in ("equipmentDecision", "maxControlDistance", "minPerturbationDistance", "medianPerturbationDistance", "separationRatio", "technicalMatch")},
                "multimodal": av_report,
                "crossMedium": cross_medium,
                "digest": report["reportDigest"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
