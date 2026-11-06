"""Compile Studio creative equipment intents into exact native proposals.

The data/engineering/delivery family lives in equipment_plan_delivery;
this module retains the existing stable Studio API and media-specific provider
selection. Workstation owns physical bindings and Runtime owns execution.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .equipment_plan_contracts import (
    EquipmentPlan,
    _first_existing,
    _require_existing,
    _windows_native_argument,
)
from .equipment_plan_delivery import compile_delivery_operation

def compile_operation(
    equipment_id: str,
    capability: str,
    parameters: Mapping[str, Any],
    *,
    require_existing: Callable[[str], str],
    first_existing: Callable[..., str],
    workstation_binding: Callable[..., dict[str, Any] | None],
    binding_environment: Callable[[Mapping[str, Any]], dict[str, str]],
) -> EquipmentPlan:
    """Compile one narrow Studio equipment intent into an exact Runtime-ready proposal.

    Precondition: a caller-selected equipment/capability pair with declared input
    parameters and a physical-resolution callback for each needed tool binding.
    Postcondition: an exact process/provider description, or a concrete exception
    for an unsupported operation or missing executable. Effects: no process runs;
    no assets, catalog state, provider sessions or production state are mutated.
    Runtime alone owns execution and the producer/Artifact boundary owns readback.
    """
    delivery_plan = compile_delivery_operation(
        equipment_id,
        capability,
        parameters,
        require_existing=require_existing,
    )
    if delivery_plan is not None:
        return delivery_plan
    if equipment_id == "typst" and capability == "document.compile.pdf":
        source = str(parameters["source"])
        output = str(parameters["output"])
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/typst"), ("compile", source, output))
    if equipment_id == "imagemagick" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/magick"), (input_path, "-resize", f"{width}x{height}!", output))
    if equipment_id == "inkscape" and capability == "vector.export":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        args = [input_path, "--export-filename", output]
        if parameters.get("width") is not None:
            args.extend(["--export-width", str(int(parameters["width"]))])
        binding = workstation_binding("game-inkscape-e1", mode="managed")
        if binding is not None:
            environment = tuple(sorted(binding_environment(binding).items()))
            return EquipmentPlan(
                equipment_id, capability, "process", str(binding["executable"]), tuple(args),
                (f"Resolved through Workstation EquipmentBinding {binding.get('bindingDigest')}; Studio retains vector semantics and Runtime retains execution authority.",),
                environment,
            )
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/inkscape"), tuple(args))
    if equipment_id == "aseprite" and capability in {"sprite.source.author", "sprite.runtime.export"}:
        binding = workstation_binding("game-aseprite-e1", mode="managed")
        if binding is None:
            raise FileNotFoundError("Workstation binding game-aseprite-e1 is unavailable")
        environment = tuple(sorted(binding_environment(binding).items()))
        if capability == "sprite.source.author":
            script = str(parameters["script"])
            output = str(parameters["output"])
            args = ("--batch", "--script-param", f"output={output}", "--script", script)
        else:
            source = str(parameters["source"])
            output = str(parameters["output"])
            args = ("--batch", source, "--save-as", output)
        return EquipmentPlan(
            equipment_id, capability, "process", str(binding["executable"]), args,
            (
                f"Resolved through Workstation EquipmentBinding {binding.get('bindingDigest')}; Media retains sprite production semantics and Runtime retains execution authority.",
                "Game/domain semantics are not inferred from sprite filenames, pixels, tags, or export metadata.",
            ),
            environment,
        )
    if equipment_id == "blender" and capability in {"scene.create", "scene.edit", "scene.render", "animation.render", "asset.export.gltf", "geometry.procedural", "camera.control", "material.control"}:
        script = str(parameters["script"])
        executable = first_existing(
            "/usr/bin/blender",
            "/mnt/c/Users/*/AppData/Local/Programs/Blender-5.2-Portable/blender.exe",
        )
        args = ("--background", "--factory-startup", "-Y", "--python", script)
        return EquipmentPlan(
            equipment_id,
            capability,
            "process",
            executable,
            args,
            (
                "Blender Python owns native scene mutation; Runtime owns process execution.",
                "Do not infer script success from Blender exit code alone; require the declared artifact/state postcondition.",
                "-Y disables automatic execution embedded in opened .blend files; the explicit --python script remains caller-selected authority.",
            ),
        )
    if equipment_id == "godot" and capability in {"interactive.run.headless", "interactive.script", "state.trace"}:
        script = str(parameters["script"])
        extra = tuple(str(value) for value in parameters.get("args", []))
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/godot"), ("--headless", "--script", script, "--", *extra))
    if equipment_id == "ffmpeg" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/ffmpeg"), ("-v", "error", "-y", "-i", input_path, "-vf", f"scale={width}:{height}", "-frames:v", "1", output))
    if equipment_id == "rsvg-convert" and capability == "svg.rasterize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/rsvg-convert"), ("--width", str(width), "--height", str(height), "-o", output, input_path))
    if equipment_id == "davinci-resolve":
        return EquipmentPlan(equipment_id, capability, "existing-studio-adapter", None, (), ("Use `ordivon-studio resolve ...`; current adapter is version-specific and menu-mediated where required.",))
    if equipment_id == "obs-studio":
        return EquipmentPlan(
            equipment_id,
            capability,
            "provider-descriptor-only",
            None,
            (),
            (
                "E8 proved authenticated obs-websocket semantics once, but AF8 falsified a reliable autonomous startup/shutdown lifecycle under OBS 32.x unclean-shutdown handling.",
                "Keep the WebSocket server disabled by default and treat all current Live actions as descriptive until a real production need re-earns a bounded provider.",
                "Do not infer current Agent actionability from the installed OBS executable or historical dogfood alone.",
            ),
        )
    if equipment_id == "figma":
        return EquipmentPlan(
            equipment_id,
            capability,
            "figma-mcp-or-plugin",
            None,
            (),
            (
                "Prefer the official Figma MCP for Agent-native node/variable/design context when user OAuth authority is available; in-editor plugin writes remain an alternate bounded transport.",
                "Do not claim remote MCP connectivity until the user has completed Figma OAuth consent and a real design read/write round has been observed.",
            ),
        )
    if equipment_id == "reaper":
        executable = first_existing(
            "/mnt/c/Program Files/REAPER (x64)/reaper.exe",
            "/mnt/c/Users/*/AppData/Local/Programs/REAPER-Portable/reaper.exe",
            "/usr/bin/reaper",
        )
        if capability == "audio.project.render":
            project = _windows_native_argument(str(parameters["project"]))
            return EquipmentPlan(
                equipment_id,
                capability,
                "process",
                executable,
                ("-nosplash", "-renderproject", project),
                ("The persisted .rpp owns native track/item/mix state; verify the rendered output independently after REAPER exits.",),
            )
        if capability == "script.reascript":
            script = str(parameters["script"])
            return EquipmentPlan(
                equipment_id,
                capability,
                "reaper-workstation",
                executable,
                ("-nonewinst", script),
                ("-nonewinst targets an already-running REAPER workstation instance; observe the script's declared postcondition rather than command admission alone.",),
            )
        return EquipmentPlan(
            equipment_id,
            capability,
            "reascript-or-osc",
            executable,
            (),
            (
                "REAPER 7.78 portable is locally validated for ReaScript-created native multitrack project state and independent -renderproject reconstruction.",
                "Use ReaScript/OSC for native DAW state instead of flattening multitrack editing into FFmpeg command composition.",
            ),
        )
    raise ValueError(f"unsupported equipment operation: {equipment_id} {capability}")
