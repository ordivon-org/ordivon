from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ordivon_studio.equipment import discover_equipment, load_equipment_world, summarize_trial  # noqa: E402

OUT = ROOT / "out" / "equipment" / "e7"
E6 = ROOT / "out" / "equipment" / "e6"


def median_ms(command: Sequence[str], repeats: int = 5) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"benchmark command failed: {command[0]} {command[1:3]}")
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return statistics.median(samples)


def pacman_size_mib(package: str) -> float | None:
    result = subprocess.run(["/usr/bin/pacman", "-Qi", package], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("Installed Size"):
            raw = line.split(":", 1)[1].strip().split()
            if len(raw) >= 2:
                value = float(raw[0]); unit = raw[1]
                if unit == "KiB": return value / 1024.0
                if unit == "MiB": return value
                if unit == "GiB": return value * 1024.0
    return None


def require_e6() -> dict[str, Any]:
    evidence = E6 / "evidence.json"
    if not evidence.is_file():
        result = subprocess.run([sys.executable, str(ROOT / "scripts/run-e6-equipment-dogfood.py")], cwd=ROOT, capture_output=True, text=True, check=False, timeout=240)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
    return json.loads(evidence.read_text(encoding="utf-8"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    e6 = require_e6()
    world = load_equipment_world(ROOT / "research/equipment/equipment-world.json")
    inventory = discover_equipment(world)
    present = {item["id"]: item for item in inventory["equipment"]}

    source_png = E6 / "vector.png"
    magick_out = OUT / "resize-magick.png"
    ffmpeg_out = OUT / "resize-ffmpeg.png"
    magick_cmd = ["/usr/bin/magick", str(source_png), "-resize", "600x315!", str(magick_out)]
    ffmpeg_cmd = ["/usr/bin/ffmpeg", "-v", "error", "-y", "-i", str(source_png), "-vf", "scale=600:315", "-frames:v", "1", str(ffmpeg_out)]
    magick_ms = median_ms(magick_cmd, 7)
    ffmpeg_ms = median_ms(ffmpeg_cmd, 7)

    svg = E6 / "recovery.svg"
    rsvg_out = OUT / "render-rsvg.png"
    inkscape_out = OUT / "render-inkscape.png"
    rsvg_cmd = ["/usr/bin/rsvg-convert", "--width", "1200", "--height", "630", "-o", str(rsvg_out), str(svg)]
    rsvg_ms = median_ms(rsvg_cmd, 5)
    inkscape_cmd = ["/usr/bin/inkscape", str(svg), "--export-filename", str(inkscape_out), "--export-width", "1200"]
    inkscape_ms = median_ms(inkscape_cmd, 5) if Path("/usr/bin/inkscape").is_file() else None

    fallback = OUT / "state-fallback.py"
    fallback.write_text(
        "import json,sys\nfrom pathlib import Path\n"
        "states=[{'event':'response-lost','state':'unknown'},{'event':'recover-same-identity','state':'checking'},{'event':'no-terminal-evidence','state':'unknown'}]\n"
        "Path(sys.argv[1]).write_text(json.dumps({'operationId':'op-recovery-42','states':states},sort_keys=True))\n",
        encoding="utf-8",
    )
    py_trace = OUT / "trace-python.json"
    gd_trace = OUT / "trace-godot.json"
    python_cmd = [sys.executable, str(fallback), str(py_trace)]
    godot_cmd = ["/usr/bin/godot", "--headless", "--script", str(E6 / "trace.gd"), "--", str(gd_trace)]
    python_ms = median_ms(python_cmd, 5)
    godot_ms = median_ms(godot_cmd, 5)

    e6_times = {item["name"]: item["wallMs"] for item in e6["commands"]}
    trials = []
    trials.append(summarize_trial(
        equipment_id="imagemagick", fallback_id="ffmpeg", capability_delta=[],
        friction_delta={"argumentTokensReduced": max(0, len(ffmpeg_cmd) - len(magick_cmd)), "medianWallTimeRatio": magick_ms / ffmpeg_ms, "batchabilityGain": True},
        ceiling_delta=["image-specific operators beyond current Studio FFmpeg wrappers"],
        costs={"packageMiB": pacman_size_mib("imagemagick"), "highPersistentCost": False, "guiStateCoupled": False}, evidence_level="executed",
    ))
    if inkscape_ms is not None:
        trials.append(summarize_trial(
            equipment_id="inkscape", fallback_id="rsvg-convert", capability_delta=["editable-vector-workstation", "vector-query-and-transform"],
            friction_delta={"argumentTokensReduced": max(0, len(rsvg_cmd) - len(inkscape_cmd)), "medianWallTimeRatio": inkscape_ms / rsvg_ms},
            ceiling_delta=["vector-native editing and export surface"],
            costs={"packageMiB": pacman_size_mib("inkscape"), "highPersistentCost": True, "guiStateCoupled": True}, evidence_level="executed",
        ))
    else:
        trials.append(summarize_trial(
            equipment_id="inkscape", fallback_id="rsvg-convert+figma", capability_delta=["local-vector-query-and-transform"],
            friction_delta={}, ceiling_delta=["vector-native local workstation"],
            costs={"notInstalledBecause": "existing rsvg/Figma cover current ordinary work; installation must be demand-pulled", "highPersistentCost": True, "guiStateCoupled": True}, evidence_level="external-only",
        ))
    trials.append(summarize_trial(
        equipment_id="typst", fallback_id="web-html-print", capability_delta=["Studio-local structured PDF compiler", "queryable document model"],
        friction_delta={"manualHandoffsReduced": 1, "batchabilityGain": True, "observedCompileMs": e6_times.get("typst-compile")},
        ceiling_delta=["high-quality deterministic typesetting"],
        costs={"packageMiB": pacman_size_mib("typst"), "highPersistentCost": False, "guiStateCoupled": False}, evidence_level="executed",
    ))
    if present.get("blender", {}).get("present") and e6_times.get("blender-scene") is not None:
        trials.append(summarize_trial(
            equipment_id="blender", fallback_id="python-spatial-projection", capability_delta=["editable 3D scene", "real camera render", "GLB interchange asset"],
            friction_delta={"batchabilityGain": True, "observedSceneMs": e6_times.get("blender-scene")},
            ceiling_delta=["professional 3D geometry/material/lighting/animation environment"],
            costs={"packageMiB": pacman_size_mib("blender"), "highPersistentCost": True, "guiStateCoupled": False}, evidence_level="executed",
        ))
    else:
        trials.append(summarize_trial(
            equipment_id="blender", fallback_id="python-spatial-projection", capability_delta=["editable 3D scene", "real camera render", "GLB interchange asset"],
            friction_delta={}, ceiling_delta=["professional 3D geometry/material/lighting/animation environment"],
            costs={"attemptedTransactionDownloadMiB": 743.20, "attemptedTransactionInstalledMiB": 3069.84, "provisioningTimeoutMs": 900000, "installed": False, "highPersistentCost": True, "guiStateCoupled": False}, evidence_level="external-only",
        ))
    trials.append(summarize_trial(
        equipment_id="godot", fallback_id="python-state-machine", capability_delta=["non-Web interactive runtime", "exportable application/game runtime", "XR-capable engine path"],
        friction_delta={"medianWallTimeRatio": godot_ms / python_ms, "batchabilityGain": True, "simpleTracePythonMs": python_ms, "simpleTraceGodotMs": godot_ms},
        ceiling_delta=["real 2D/3D/input/audio/runtime encounter"],
        costs={"packageMiB": pacman_size_mib("godot"), "highPersistentCost": True, "guiStateCoupled": False}, evidence_level="executed",
    ))
    resolve = summarize_trial(
        equipment_id="davinci-resolve", fallback_id="ffmpeg+otio", capability_delta=["editable NLE/color/Fusion/Fairlight master"],
        friction_delta={"manualHandoffsReduced": 10, "recoveryStepsReduced": 1, "batchabilityGain": True},
        ceiling_delta=["professional editorial/color/audio finishing"],
        costs={"highPersistentCost": True, "guiStateCoupled": True, "versionSpecificAdapter": True}, evidence_level="ordinary-production",
    ); resolve["decision"] = "external-workstation-retain"; trials.append(resolve)
    obs = summarize_trial(
        equipment_id="obs-studio", fallback_id="ffmpeg-capture", capability_delta=["stateful realtime scene/source graph", "record/stream lifecycle events"],
        friction_delta={}, ceiling_delta=["live production scene composition"],
        costs={"installed": present.get("obs-studio", {}).get("present", False), "highPersistentCost": True, "guiStateCoupled": True, "authenticatedControlRequired": True, "currentWebSocketServerEnabled": False}, evidence_level="external-only",
    ); obs["decision"] = "external-workstation-integration-provisional"; trials.append(obs)
    figma = summarize_trial(
        equipment_id="figma", fallback_id="raw-svg+web", capability_delta=["collaborative editable design graph", "in-editor node write API"],
        friction_delta={}, ceiling_delta=["professional collaborative design surface"],
        costs={"installed": present.get("figma", {}).get("present", False), "highPersistentCost": True, "guiStateCoupled": True, "authOrPluginContext": True}, evidence_level="external-only",
    ); figma["decision"] = "external-workstation-integration-provisional"; trials.append(figma)
    reaper = summarize_trial(
        equipment_id="reaper", fallback_id="ffmpeg+sapi+resolve-fairlight", capability_delta=["scriptable multitrack DAW", "OSC control surface"], friction_delta={},
        ceiling_delta=["audio-first edit/mix/master workflow"], costs={"portableArchiveMiB": 12.97, "portableBinarySha256": "26eda629227de216724d1d623f239af9a9198d2733d43b44406beed3f4601606", "stockHeadlessProbe": "failed-libSwell-gdk_init_check", "headlessCustomLibSwellRequired": True, "license": "evaluation/commercial", "highPersistentCost": False, "guiStateCoupled": True}, evidence_level="external-only",
    ); reaper["decision"] = "candidate-headless-integration"; trials.append(reaper)
    trials.append(summarize_trial(
        equipment_id="touchdesigner", fallback_id="obs+godot+blender", capability_delta=["live node-based generative/sensor graph"], friction_delta={}, ceiling_delta=["installation/projection/realtime visual ceiling"], costs={"licenseContext": True, "highPersistentCost": True, "guiStateCoupled": True}, evidence_level="external-only",
    ))
    trials.append(summarize_trial(
        equipment_id="stream-deck", fallback_id="keyboard/web-controls", capability_delta=["physical low-latency action and state display"], friction_delta={}, ceiling_delta=[], costs={"hardwareRequired": True}, evidence_level="physical-missing",
    ))
    trials.append(summarize_trial(
        equipment_id="bhaptics", fallback_id=None, capability_delta=["physical tactile output"], friction_delta={}, ceiling_delta=[], costs={"hardwareRequired": True}, evidence_level="physical-missing",
    ))

    report = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-e7-equipment-economics",
        "observedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "provisioningEvidence": {
            "initialFiveToolAttempt": {"requested": ["typst", "imagemagick", "inkscape", "blender", "godot"], "plannedDownloadMiB": 902.28, "plannedInstalledMiB": 3717.24, "result": "timed-out-before-transaction"},
            "typstImageMagick": {"downloadMiB": 24.83, "installedMiB": 67.41, "postcondition": "installed", "runtimeDisposition": "EXECUTABLE_RUNTIME_DRIFT-after-package-effect"},
            "godot": {"downloadMiB": 88.12, "installedMiB": 229.29, "postcondition": "installed", "runtimeDisposition": "EXECUTABLE_RUNTIME_DRIFT-after-package-effect"},
            "blender": {"plannedDownloadMiB": 743.20, "plannedInstalledMiB": 3069.84, "result": "timed-out-after-900000ms-before-transaction", "postcondition": "not-installed"},
            "inkscape": {"plannedDownloadMiB": 77.89, "plannedInstalledMiB": 524.97, "result": "timed-out-after-300000ms-before-transaction", "postcondition": "not-installed", "orphanDownloaderObserved": true},
            "recovery": {"stalePacmanLocksSafelyClearedAfterNoHolderWasConfirmed": 3, "currentInkscapeLockDeliberatelyPreservedWhileOrphanDownloaderInUninterruptibleIo": true},
            "architectureConclusion": "System package provisioning changes host executable topology and should be a Host/Computer provisioning concern, not ordinary Studio Workspace execution semantics."
        },
        "benchmarks": {
            "imageResize": {"imagemagickMedianMs": magick_ms, "ffmpegMedianMs": ffmpeg_ms, "ratio": magick_ms / ffmpeg_ms, "argumentCount": {"imagemagick": len(magick_cmd)-1, "ffmpeg": len(ffmpeg_cmd)-1}},
            "svgRaster": {"rsvgMedianMs": rsvg_ms, "inkscapeMedianMs": inkscape_ms, "ratio": (inkscape_ms / rsvg_ms) if inkscape_ms is not None else None, "argumentCount": {"rsvg": len(rsvg_cmd)-1, "inkscape": len(inkscape_cmd)-1}},
            "simpleStateTrace": {"pythonMedianMs": python_ms, "godotMedianMs": godot_ms, "ratio": godot_ms / python_ms}
        },
        "inventory": inventory,
        "trials": trials,
        "decisionRule": "Retain tools that uniquely add needed capability OR materially reduce actual friction OR raise a used professional ceiling at justified cost. A tool can survive capability ablation solely through friction reduction; conversely a powerful tool can remain on-demand if footprint/state/maintenance dominates ordinary value.",
        "boundary": "No heterogeneous scalar ROI is computed. Capability, friction, ceiling and cost remain inspectable typed evidence.",
    }
    evidence = OUT / "evidence.json"
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "evidence": str(evidence.relative_to(ROOT)), "benchmarks": report["benchmarks"], "decisions": {item["equipmentId"]: item["decision"] for item in trials}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
