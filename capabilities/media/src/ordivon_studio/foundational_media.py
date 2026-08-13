from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


M7_EVIDENCE_KIND = "ordivon.studio-m7-foundational-media-evidence"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _probe_image(path: Path, ffprobe: str = "/usr/bin/ffprobe") -> dict[str, Any]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,pix_fmt,codec_name", "-of", "json", str(path)],
        capture_output=True,
        check=True,
        text=True,
    )
    value = json.loads(result.stdout)
    streams = value.get("streams", [])
    if len(streams) != 1:
        raise ValueError("still image requires exactly one video/image stream")
    return streams[0]


def still_visual_features(
    path: Path,
    *,
    width_bins: int = 16,
    height_bins: int = 9,
    ffmpeg: str = "/usr/bin/ffmpeg",
    ffprobe: str = "/usr/bin/ffprobe",
) -> dict[str, Any]:
    """Return a deliberately low-level pixel-layout signature for a rendered still.

    The vector is useful for controlled sensitivity/ablation only. It does not
    identify objects, meaning, beauty, hierarchy, or visual quality.
    """
    if width_bins < 2 or height_bins < 2:
        raise ValueError("still visual grid must be at least 2x2")
    stream = _probe_image(path, ffprobe)
    result = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(path),
            "-vf",
            f"scale={width_bins}:{height_bins}:flags=area",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        capture_output=True,
        check=True,
    )
    expected = width_bins * height_bins * 3
    if len(result.stdout) != expected:
        raise ValueError(f"unexpected still signature bytes: expected {expected}, got {len(result.stdout)}")
    vector = [byte / 255.0 for byte in result.stdout]
    luminance: list[float] = []
    saturation: list[float] = []
    for index in range(0, len(vector), 3):
        r, g, b = vector[index : index + 3]
        luminance.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        hi, lo = max(r, g, b), min(r, g, b)
        saturation.append(0.0 if hi == 0 else (hi - lo) / hi)
    return {
        "technical": {
            "width": int(stream["width"]),
            "height": int(stream["height"]),
            "codec": stream.get("codec_name"),
            "pixelFormat": stream.get("pix_fmt"),
            "grid": [width_bins, height_bins],
        },
        "structuralVector": vector,
        "meanLuminance": statistics.fmean(luminance),
        "meanSaturation": statistics.fmean(saturation),
        "digest": sha256_file(path),
        "interpretationBoundary": "Downsampled RGB layout is mechanical rendered-pixel evidence. It can prove a controlled still changed after rendering; it does not establish semantic importance, beauty, or observer preference.",
    }


def vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector lengths differ")
    if not left:
        return 0.0
    return math.sqrt(statistics.fmean((a - b) ** 2 for a, b in zip(left, right)))


def still_intervention_report(
    baseline: dict[str, Any],
    *,
    controls: Sequence[tuple[str, dict[str, Any]]],
    perturbations: Sequence[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    control = [{"id": name, "distance": vector_distance(baseline["structuralVector"], value["structuralVector"])} for name, value in controls]
    changed = [{"id": name, "distance": vector_distance(baseline["structuralVector"], value["structuralVector"])} for name, value in perturbations]
    max_control = max((item["distance"] for item in control), default=0.0)
    min_changed = min((item["distance"] for item in changed), default=0.0)
    return {
        "controls": control,
        "perturbations": changed,
        "maxControlDistance": max_control,
        "minPerturbationDistance": min_changed,
        "strictSeparation": bool(changed) and min_changed > max_control,
        "separationRatio": min_changed / max_control if max_control else None,
        "interpretationBoundary": "Strict separation means the rendered-pixel equipment detects registered visual interventions above control variation. It does not say those interventions are better, worse, or human-visible at every viewing condition.",
    }


@dataclass(frozen=True)
class RegisteredCase:
    case_id: str
    failure_class: str
    medium: str


@dataclass(frozen=True)
class ProfileArm:
    arm_id: str
    detectors: frozenset[str]
    context_words: int
    persistent_complexity: int = 0


def profile_distinction_report(cases: Sequence[RegisteredCase], arms: Sequence[ProfileArm]) -> dict[str, Any]:
    if not cases or not arms:
        raise ValueError("cases and arms are required")
    rows: list[dict[str, Any]] = []
    for arm in arms:
        detected = [case.case_id for case in cases if case.failure_class in arm.detectors]
        recall = len(detected) / len(cases)
        cost = max(1, arm.context_words + arm.persistent_complexity)
        rows.append(
            {
                "arm": arm.arm_id,
                "detected": detected,
                "caseCount": len(cases),
                "recall": recall,
                "contextWords": arm.context_words,
                "persistentComplexity": arm.persistent_complexity,
                "benefitPerKCost": recall * 1000.0 / cost,
            }
        )
    return {
        "cases": [{"id": case.case_id, "failureClass": case.failure_class, "medium": case.medium} for case in cases],
        "arms": rows,
        "boundary": "This is preregistered failure-class coverage, not a human quality score. It tests whether a profile contains target-specific diagnostic information beyond Core/wrong/sham controls at roughly comparable context cost.",
    }


def spatial_projection(point: tuple[float, float, float], *, camera_x: float = 0.0, camera_z: float = 0.0, focal: float = 1.0) -> tuple[float, float]:
    x, y, z = point
    depth = z - camera_z
    if depth <= 0.05:
        raise ValueError("point is behind or too close to camera")
    return ((x - camera_x) * focal / depth, y * focal / depth)


def spatial_reference_experiment() -> dict[str, Any]:
    """Bounded spatial falsifier: same local coordinates under different declared spaces/viewpoints."""
    target_local = (0.6, 0.0, 2.0)
    anchor_local = (0.0, 0.0, 1.0)
    view_a = {
        "target": spatial_projection(target_local, camera_x=0.0),
        "anchor": spatial_projection(anchor_local, camera_x=0.0),
    }
    view_b = {
        "target": spatial_projection(target_local, camera_x=0.45),
        "anchor": spatial_projection(anchor_local, camera_x=0.45),
    }
    local_to_stage_offset = 1.25
    target_stage = (target_local[0] + local_to_stage_offset, target_local[1], target_local[2])
    wrong_space_projection = spatial_projection(target_stage, camera_x=0.0)
    displacement = math.dist(view_a["target"], view_b["target"])
    reference_error = math.dist(view_a["target"], wrong_space_projection)
    return {
        "sameObjectLocalCoordinate": list(target_local),
        "viewA": view_a,
        "viewB": view_b,
        "referenceSpaceOffset": local_to_stage_offset,
        "wrongSpaceProjection": wrong_space_projection,
        "viewpointDisplacement": displacement,
        "referenceFrameError": reference_error,
        "fixedViewAblationLosesViewpointEffect": displacement > 0.05,
        "undeclaredReferenceSpaceCreatesMaterialError": reference_error > 0.05,
        "boundary": "This proves coordinate/reference-space and viewpoint dependence in a controlled projection model. It is not an XR comfort, embodiment, presence, or human depth-perception result and cannot by itself graduate Spatial/3D.",
    }


def _live_policy_guarded(event: Mapping[str, Any], state: dict[str, Any], now_ms: float) -> None:
    kind = event["kind"]
    if kind == "update":
        state["display"] = event["value"]
        state["sourceTimestampMs"] = event["sourceTimestampMs"]
        age = now_ms - float(event["sourceTimestampMs"])
        state["status"] = "stale-unverified" if age > float(event["freshnessBudgetMs"]) else "current"
    elif kind == "correction":
        state["display"] = event["value"]
        state["status"] = "corrected"
        state["sourceTimestampMs"] = event["sourceTimestampMs"]
    elif kind == "interrupt":
        state["status"] = "interrupted-awaiting-current-state"


def _live_policy_naive(event: Mapping[str, Any], state: dict[str, Any], now_ms: float) -> None:
    kind = event["kind"]
    if kind in {"update", "correction"}:
        state["display"] = event["value"]
        state["status"] = "current"
        state["sourceTimestampMs"] = event["sourceTimestampMs"]
    elif kind == "interrupt":
        state["status"] = "current"


def live_realtime_experiment(*, seed: int | None = None) -> dict[str, Any]:
    """Run a short real-time trace where the next event is not exposed to the policy in advance."""
    if seed is None:
        seed = random.SystemRandom().randrange(1, 2**31)
    rng = random.Random(seed)
    start = time.monotonic_ns()
    source_origin = time.time() * 1000.0
    stale_age = rng.randint(180, 260)
    freshness_budget = 100
    schedule = [
        (rng.uniform(0.005, 0.015), {"kind": "update", "value": "A", "sourceTimestampMs": source_origin, "freshnessBudgetMs": freshness_budget}),
        (rng.uniform(0.005, 0.015), {"kind": "interrupt"}),
        (rng.uniform(0.005, 0.015), {"kind": "update", "value": "B", "sourceTimestampMs": source_origin - stale_age, "freshnessBudgetMs": freshness_budget}),
        (rng.uniform(0.005, 0.015), {"kind": "correction", "value": "C", "sourceTimestampMs": source_origin + 1.0, "freshnessBudgetMs": freshness_budget}),
    ]
    states = {
        "guarded": {"display": None, "status": "unknown", "sourceTimestampMs": None},
        "naive": {"display": None, "status": "unknown", "sourceTimestampMs": None},
    }
    trace: list[dict[str, Any]] = []
    stale_exposure_start: float | None = None
    stale_exposure_ms = 0.0
    for delay, event in schedule:
        time.sleep(delay)
        elapsed_ms = (time.monotonic_ns() - start) / 1_000_000.0
        now_ms = source_origin + elapsed_ms
        _live_policy_guarded(event, states["guarded"], now_ms)
        _live_policy_naive(event, states["naive"], now_ms)
        if event["kind"] == "update" and event["value"] == "B":
            stale_exposure_start = elapsed_ms
        if event["kind"] == "correction" and stale_exposure_start is not None:
            stale_exposure_ms = max(0.0, elapsed_ms - stale_exposure_start)
        trace.append({"elapsedMs": elapsed_ms, "event": dict(event), "guarded": dict(states["guarded"]), "naive": dict(states["naive"])})
    guarded_flags_stale = any(item["guarded"]["status"] == "stale-unverified" for item in trace)
    naive_marks_stale_current = any(item["event"].get("value") == "B" and item["naive"]["status"] == "current" for item in trace)
    return {
        "seed": seed,
        "futureScheduleHiddenFromPolicy": True,
        "trace": trace,
        "guardedFlagsStale": guarded_flags_stale,
        "naiveMarksStaleCurrent": naive_marks_stale_current,
        "naiveMisleadingExposureMs": stale_exposure_ms if naive_marks_stale_current else 0.0,
        "editedReplayCanRemoveCorrectionWindow": stale_exposure_ms > 0.0,
        "boundary": "This is a bounded real-time software encounter with future events withheld until arrival. It demonstrates currentness/correction pressure under liveness, not audience trust, broadcast-scale moderation, or human live-performance quality.",
    }


def haptic_challenger_report() -> dict[str, Any]:
    return {
        "observerRelation": "tactile output can be delivered without visual or acoustic output",
        "localPhysicalOutputAvailable": False,
        "standardsEvidence": ["OpenXR output haptics", "W3C Vibration API tactile feedback"],
        "candidateFailureClasses": ["missing-feedback", "false-confirmation", "timing-pattern", "intensity-pattern", "body-location"],
        "disposition": "retain-challenger-no-profile",
        "reason": "The environment has standards-level evidence but no verified tactile hardware encounter. Synthetic timing traces cannot establish perceptual distinctness or justify a resident profile.",
    }
