"""Compile precise Studio equipment intents using native external tools.

This module only constructs execution descriptions. It neither discovers equipment
nor executes processes; Workstation provides bindings and Runtime performs execution.
The caller supplies the four physical-resolution callbacks, keeping this compiler
independent from local machine identity and preserving the existing Studio API.
"""

from __future__ import annotations

import glob
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EquipmentPlan:
    equipment_id: str
    capability: str
    transport: str
    executable: str | None
    args: tuple[str, ...]
    notes: tuple[str, ...] = ()
    environment: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "equipmentId": self.equipment_id,
            "capability": self.capability,
            "transport": self.transport,
            "executable": self.executable,
            "args": list(self.args),
            "notes": list(self.notes),
            "environment": dict(self.environment),
        }


def _require_existing(path: str) -> str:
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    return path


def _windows_native_argument(path: str) -> str:
    """Translate a WSL-mounted Windows absolute path for a Windows-native process.

    Relative paths intentionally remain relative: WSL interop can project the Runtime
    Workspace as the Windows process working directory, as proven by Blender dogfood.
    """
    if len(path) >= 7 and path.startswith("/mnt/") and path[5].isalpha() and path[6] == "/":
        drive = path[5].upper()
        rest = path[7:].replace("/", "\\")
        return f"{drive}:\\{rest}"
    return path


def _first_existing(*patterns: str) -> str:
    for pattern in patterns:
        for raw in sorted(glob.glob(pattern)):
            if Path(raw).is_file():
                return raw
    raise FileNotFoundError(patterns[0] if patterns else "no equipment path supplied")


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
    if equipment_id == "tiled" and capability == "world2d.canonicalize.tmj":
        source = str(parameters["source"]); output = str(parameters["output"])
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/tiled"),
            ("--export-map", source, output),
            (
                "Tiled owns native TMJ parsing/export canonicalization; Runtime owns process execution.",
                "Artifact owns bounded TMJ semantic identity, TMJ→TMX→TMJ round-trip and raster readback. Game/domain meaning is not inferred from object names/types.",
            ),
            (("QT_QPA_PLATFORM", "offscreen"),),
        )
    if equipment_id == "tiled" and capability == "world2d.render.preview":
        source = str(parameters["source"]); output = str(parameters["output"])
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/tmxrasterizer"),
            (source, output),
            ("tmxrasterizer owns technical raster preview; preview pixels do not establish game or cartographic meaning.",),
            (("QT_QPA_PLATFORM", "offscreen"),),
        )
    if equipment_id == "duckdb" and capability in {"dataset.sql.execute", "dataset.query", "dataset.transform"}:
        source = str(parameters["sqlFile"])
        executable = require_existing("/opt/ordivon/external/duckdb/1.5.5-1/duckdb")
        return EquipmentPlan(
            equipment_id, capability, "process", executable, ("-c", f".read {source}"),
            (
                "DuckDB owns deterministic SQL query/transform semantics; Runtime owns process execution.",
                "DuckDB's current Parquet writer does not preserve the required/not-null field semantics needed by Artifact Parquet R1, so no strict delivery claim is inferred from DuckDB COPY alone.",
            ),
        )
    if equipment_id == "pyarrow" and capability == "dataset.export.parquet":
        script = str(Path(__file__).resolve().parents[2] / "scripts/produce-parquet.py")
        args=(script,"--output",str(parameters["output"]),"--schema",str(parameters["schema"]),"--rows",str(parameters["rows"]))
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/opt/ordivon/external/pyarrow/25.0.1/python"), args,
            (
                "PyArrow owns exact flat primitive schema/nullability and Parquet serialization; Runtime owns process execution.",
                "Artifact independently re-reads exact bytes through both PyArrow and DuckDB and owns schema/key/row-contract standing.",
            ),
        )
    if equipment_id == "gdal-ogr" and capability == "geospatial.export.geopackage":
        source = str(parameters["source"]); output = str(parameters["output"]); layer = str(parameters["layer"]); srs = str(parameters.get("srs", "EPSG:4326"))
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/ogr2ogr"),
            ("-f", "GPKG", output, source, "-nln", layer, "-a_srs", srs, "-dsco", "VERSION=1.4", "-lco", "GEOMETRY_NAME=geom"),
            (
                "OGR owns source interpretation and GeoPackage writing; Runtime owns process execution.",
                "Artifact owns OGC conformance, SQLite container checks, CRS/schema contract and cross-view verification.",
            ),
        )
    if equipment_id == "gdal-ogr" and capability in {"geospatial.inspect", "geospatial.transform"}:
        source = str(parameters["source"]); return EquipmentPlan(equipment_id, capability, "process", require_existing("/usr/bin/ogrinfo"), ("-ro", "-so", "-json", source))
    if equipment_id == "warcio" and capability == "web.capture.response.warc":
        script = str(Path(__file__).resolve().parents[2] / "scripts/produce-warc-response.py")
        args=(script,"--output",str(parameters["output"]),"--payload",str(parameters["payload"]),"--target-uri",str(parameters["targetUri"]),"--warc-date",str(parameters["warcDate"]),"--record-id",str(parameters["recordId"]),"--status",str(parameters.get("status","200 OK")),"--content-type",str(parameters["contentType"]))
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/python"), args,
            (
                "The thin Media adapter delegates WARC record creation/digests to pinned warcio 1.8.1.",
                "Artifact independently checks WARC/1.1 integrity and exact response identity through warcio Python and warcio.js.",
            ),
            (("ORDIVON_WARCIO_SITE","/opt/ordivon/external/warcio-py/1.8.1/site-packages"),),
        )
    if equipment_id == "python-email" and capability == "message.compose.rfc5322":
        script = str(Path(__file__).resolve().parents[2] / "scripts/produce-internet-message.py")
        args=(script,"--output",str(parameters["output"]),"--from-address",str(parameters["fromAddress"]),"--from-name",str(parameters.get("fromName","")),"--to-address",str(parameters["toAddress"]),"--to-name",str(parameters.get("toName","")),"--subject",str(parameters["subject"]),"--message-id",str(parameters["messageId"]),"--date",str(parameters["date"]),"--body-file",str(parameters["bodyFile"]))
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/python"), args,
            (
                "Python stdlib email owns RFC5322/MIME serialization for the bounded single-part message.",
                "Artifact independently checks raw CRLF/header policy plus Python-email/mailparser agreement; SMTP delivery/authentication are not implied.",
            ),
        )
    if equipment_id == "cadquery" and capability in {"cad.script.author", "cad.export.step", "cad.export.stl"}:
        script = str(parameters["script"])
        extra = tuple(str(value) for value in parameters.get("args", []))
        executable = require_existing("/root/.local/share/ordivon/laboratory/engineering-py312/bin/python")
        return EquipmentPlan(
            equipment_id, capability, "process", executable, (script, *extra),
            (
                "CadQuery/Python owns script-based parametric BREP construction and requested export; Runtime owns process execution.",
                "The persistent Laboratory launcher is a Workstation materialization fact, while Media freshly observes CadQuery package presence/version before selection.",
                "Do not infer STEP schema/conformance, manufacturability, tolerance/GD&T, assembly semantics or physical behavior from successful authoring/export; admitted delivery verification belongs to Artifact.",
            ),
        )
    if equipment_id == "kicad" and capability in {"pcb.drc", "pcb.export.svg", "pcb.export.gerber", "pcb.export.drill"}:
        source = str(parameters["source"])
        executable = require_existing("/usr/bin/kicad-cli")
        if capability == "pcb.drc":
            output = str(parameters["output"])
            args = ("pcb", "drc", "--severity-error", "--exit-code-violations", "--output", output, source)
        elif capability == "pcb.export.svg":
            output = str(parameters["output"])
            layers = str(parameters.get("layers", "F.Cu,F.Silkscreen,Edge.Cuts"))
            args = ("pcb", "export", "svg", "--layers", layers, "--mode-single", "--black-and-white", "--page-size-mode", "2", "--exclude-drawing-sheet", "--output", output, source)
        elif capability == "pcb.export.gerber":
            output = str(parameters["output"])
            layers = str(parameters.get("layers", "F.Cu,B.Cu,Edge.Cuts"))
            args = ("pcb", "export", "gerbers", "--layers", layers, "--output", output, source)
        else:
            output = str(parameters["output"])
            args = ("pcb", "export", "drill", "--format", "excellon", "--output", output, source)
        return EquipmentPlan(
            equipment_id, capability, "process", executable, args,
            (
                "KiCad owns PCB parsing, DRC and native export semantics; Runtime owns process execution.",
                "Media treats the result as creative/production equipment evidence only. Electrical correctness, schematic parity, manufacturability and safety remain outside Media.",
            ),
        )
    if equipment_id == "ngspice" and capability == "circuit.simulate.transient":
        source = str(parameters["source"])
        log = str(parameters["log"])
        raw = parameters.get("raw")
        args = ["-n", "-b", "-o", log]
        if raw is not None:
            args.extend(["-r", str(raw)])
        args.append(source)
        return EquipmentPlan(
            equipment_id, capability, "process", require_existing("/usr/bin/ngspice"), tuple(args),
            (
                "ngspice owns parse/simulation semantics; Runtime owns process execution.",
                "A successful process is not a circuit-quality claim. Artifact's EDA profile owns bounded measurement/range verification when delivery evidence is required.",
            ),
        )
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
