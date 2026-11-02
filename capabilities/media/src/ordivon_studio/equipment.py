from __future__ import annotations

import glob
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import equipment_capabilities as capability_projection

DEFAULT_WORLD = Path("research/equipment/equipment-world.json")
WINDOWS_POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")


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


def load_equipment_world(path: Path = DEFAULT_WORLD) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("id") != "studio.equipment-world":
        raise ValueError("unsupported equipment world")
    ids = [item["id"] for item in value.get("equipment", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equipment id")
    return value


def _first_line(value: str) -> str:
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        if set(line) <= set("*-=~_"):
            continue
        return line[:500]
    return ""


def _run_version(executable: Path, args: Sequence[str], environment: Mapping[str, str] | None = None) -> str | None:
    try:
        result = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, **dict(environment or {}), "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = result.stdout or result.stderr
    return _first_line(text) or None


def _decode_process_bytes(value: bytes) -> str:
    if not value:
        return ""
    for encoding in ("utf-8-sig", "utf-16-le", "gb18030"):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("utf-8", errors="replace")


def _windows_file_version(path: Path) -> str | None:
    if not WINDOWS_POWERSHELL.is_file():
        return None
    windows_path = str(path).replace("/mnt/c/", "C:/")
    literal = windows_path.replace("'", "''")
    command = f"[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); $v=(Get-Item -LiteralPath '{literal}').VersionInfo; if($v.ProductVersion){{$v.ProductVersion}}else{{$v.FileVersion}}"
    try:
        result = subprocess.run(
            [str(WINDOWS_POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=False,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _first_line(_decode_process_bytes(result.stdout)) or None




def _workstation_equipment_binding(
    equipment_id: str,
    executable: str | None = None,
    *,
    mode: str = "isolated",
) -> dict[str, Any] | None:
    tool = Path(os.environ.get("ORDIVON_EQUIPMENT_BINDING", "/root/tools/bin/equipment-binding"))
    if not tool.is_file() or not os.access(tool, os.X_OK):
        return None
    if mode not in {"isolated", "managed"}:
        raise ValueError(f"unsupported Workstation equipment binding mode: {mode}")
    if mode == "isolated" and not executable:
        raise ValueError("isolated Workstation equipment binding requires executable identity")
    arguments = [str(tool), mode, "--equipment-id", equipment_id]
    if mode == "isolated":
        arguments.extend(["--executable", str(executable)])
    try:
        result = subprocess.run(
            arguments,
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.workstation-equipment-binding":
        return None
    if value.get("state") != "AVAILABLE" or value.get("executionTarget") != "local_linux":
        return None
    path = value.get("executable")
    if not isinstance(path, str) or not Path(path).is_file():
        return None
    return value


def _binding_environment(binding: Mapping[str, Any]) -> dict[str, str]:
    projected = binding.get("environment")
    if not isinstance(projected, Mapping):
        return {}
    environment: dict[str, str] = {}
    library_dirs = projected.get("libraryDirs")
    if isinstance(library_dirs, list) and all(isinstance(value, str) for value in library_dirs) and library_dirs:
        existing = os.environ.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = ":".join([*library_dirs, *([existing] if existing else [])])
    python_sites = projected.get("pythonSitePackages")
    if isinstance(python_sites, list) and all(isinstance(value, str) for value in python_sites) and python_sites:
        existing = os.environ.get("PYTHONPATH")
        environment["PYTHONPATH"] = ":".join([*python_sites, *([existing] if existing else [])])
    return environment

def _discovery_paths(spec: Mapping[str, Any]) -> list[Path]:
    if "path" in spec:
        return [Path(spec["path"])]
    if "glob" in spec:
        return [Path(value) for value in sorted(glob.glob(spec["glob"]))]
    return []


def _safe_configuration_projection(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    if spec.get("kind") != "glob":
        return []
    results: list[dict[str, Any]] = []
    redacted = set(spec.get("redact", []))
    for raw in sorted(glob.glob(spec["pattern"])):
        path = Path(raw)
        row: dict[str, Any] = {"path": str(path), "exists": path.is_file()}
        if path.is_file() and path.suffix.lower() == ".json":
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                value = None
            if isinstance(value, dict):
                projection: dict[str, Any] = {}
                for key, item in value.items():
                    if key in redacted or "password" in key.lower() or "token" in key.lower() or "secret" in key.lower():
                        projection[key] = "<redacted-present>" if item else "<redacted-empty>"
                    elif isinstance(item, (str, int, float, bool)) or item is None:
                        projection[key] = item
                row["safeProjection"] = projection
        results.append(row)
    return results


def discover_equipment(world: Mapping[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for item in world.get("equipment", []):
        candidates: list[dict[str, Any]] = []
        for spec in item.get("discovery", []):
            if spec.get("kind") in {"workstation-isolated-binding", "workstation-managed-binding"}:
                binding_mode = "managed" if spec.get("kind") == "workstation-managed-binding" else "isolated"
                binding = _workstation_equipment_binding(
                    str(spec["equipmentId"]),
                    str(spec["executable"]) if binding_mode == "isolated" else None,
                    mode=binding_mode,
                )
                if binding is not None:
                    path = Path(str(binding["executable"]))
                    version = _run_version(path, spec.get("versionArgs", ["--version"]), _binding_environment(binding))
                    candidates.append({
                        "path": str(path), "version": version, "platform": spec.get("platform"),
                        "provider": binding.get("provider"), "bindingDigest": binding.get("bindingDigest"),
                        "providerIdentity": binding.get("providerIdentity"), "validUntilMs": binding.get("validUntilMs"),
                    })
                continue
            for path in _discovery_paths(spec):
                if not path.is_file():
                    continue
                if spec.get("versionKind") == "windows-file":
                    version = _windows_file_version(path)
                else:
                    environment = spec.get("environment") if isinstance(spec.get("environment"), Mapping) else None
                    version = _run_version(path, spec.get("versionArgs", ["--version"]), environment)
                candidates.append({"path": str(path), "version": version, "platform": spec.get("platform")})
        configuration: list[dict[str, Any]] = []
        for spec in item.get("configuration", []):
            configuration.extend(_safe_configuration_projection(spec))
        records.append(
            {
                "id": item["id"],
                "family": item["family"],
                "present": bool(candidates),
                "candidates": candidates,
                "configuration": configuration,
                "capabilities": item.get("capabilities", []),
                "retention": item.get("retention"),
                "reason": item.get("reason"),
            }
        )
    return {"schemaVersion": 1, "kind": "ordivon.studio-equipment-inventory", "equipment": records}


def equipment_by_id(world: Mapping[str, Any], equipment_id: str) -> Mapping[str, Any]:
    for item in world.get("equipment", []):
        if item.get("id") == equipment_id:
            return item
    raise KeyError(equipment_id)


def discover_equipment_for_capability(world: Mapping[str, Any], capability: str) -> dict[str, Any]:
    """Observe only physical candidates relevant to one Studio capability.

    This is deliberately not a cache: every returned candidate is freshly observed, but
    irrelevant Windows/GUI equipment is not probed merely because it exists in the world.
    """
    scoped = dict(world)
    scoped["equipment"] = [
        item for item in world.get("equipment", [])
        if capability in item.get("capabilities", [])
    ]
    return discover_equipment(scoped)



def propose_operation(
    world: Mapping[str, Any],
    capability: str,
    parameters: Mapping[str, Any],
    *,
    equipment_id: str | None = None,
    local: bool = True,
) -> dict[str, Any]:
    """Compile one truthful Agent-facing proposal without executing it.

    Selection, physical currentness, actionability, exact plan and completion contract are
    projected together so callers do not reconstruct Studio/Workstation folklore.
    """
    inventory = discover_equipment_for_capability(world, capability) if local else None
    matches = capability_projection.select_for_capability(world, capability, inventory=inventory)
    if equipment_id is not None:
        matches = [item for item in matches if item["id"] == equipment_id]
    if not matches:
        raise ValueError(f"no equipment advertises capability: {capability}")
    candidate = matches[0]
    proposal: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-equipment-operation-proposal",
        "capability": capability,
        "candidate": candidate,
        "plan": None,
        "verification": None,
        "authorityTransition": None,
        "ready": False,
        "blockers": [],
    }
    if not candidate["selectable"]:
        proposal["blockers"].append(candidate["readiness"])
        if candidate["actionability"] not in {"DIRECTLY_INVOCABLE", "STUDIO_NATIVE", "PROVIDER_MEDIATED"}:
            proposal["blockers"].append(candidate["actionability"])
        proposal["authorityTransition"] = capability_projection.external_authority_transition(candidate["id"])
        return proposal
    if candidate["actionability"] == "STUDIO_NATIVE":
        proposal["blockers"].append("USE_STUDIO_NATIVE_COMMAND")
        return proposal
    plan = compile_operation(candidate["id"], capability, parameters)
    verification = capability_projection.verification_contract(candidate["id"], capability, parameters)
    proposal["plan"] = plan.as_dict()
    proposal["verification"] = verification
    if verification.get("ready") is not True:
        proposal["blockers"].append("VERIFICATION_CONTRACT_INCOMPLETE")
        return proposal
    proposal["ready"] = True
    return proposal


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


def compile_operation(equipment_id: str, capability: str, parameters: Mapping[str, Any]) -> EquipmentPlan:
    """Compile one narrow Studio equipment intent into an exact Runtime-ready proposal.

    This function does not execute the program. Runtime remains process authority.
    """
    if equipment_id == "tiled" and capability == "world2d.canonicalize.tmj":
        source = str(parameters["source"]); output = str(parameters["output"])
        return EquipmentPlan(
            equipment_id, capability, "process", _require_existing("/usr/bin/tiled"),
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
            equipment_id, capability, "process", _require_existing("/usr/bin/tmxrasterizer"),
            (source, output),
            ("tmxrasterizer owns technical raster preview; preview pixels do not establish game or cartographic meaning.",),
            (("QT_QPA_PLATFORM", "offscreen"),),
        )
    if equipment_id == "duckdb" and capability in {"dataset.sql.execute", "dataset.query", "dataset.transform"}:
        source = str(parameters["sqlFile"])
        executable = _require_existing("/opt/ordivon/external/duckdb/1.5.5-1/duckdb")
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
            equipment_id, capability, "process", _require_existing("/opt/ordivon/external/pyarrow/25.0.1/python"), args,
            (
                "PyArrow owns exact flat primitive schema/nullability and Parquet serialization; Runtime owns process execution.",
                "Artifact independently re-reads exact bytes through both PyArrow and DuckDB and owns schema/key/row-contract standing.",
            ),
        )
    if equipment_id == "gdal-ogr" and capability == "geospatial.export.geopackage":
        source = str(parameters["source"]); output = str(parameters["output"]); layer = str(parameters["layer"]); srs = str(parameters.get("srs", "EPSG:4326"))
        return EquipmentPlan(
            equipment_id, capability, "process", _require_existing("/usr/bin/ogr2ogr"),
            ("-f", "GPKG", output, source, "-nln", layer, "-a_srs", srs, "-dsco", "VERSION=1.4", "-lco", "GEOMETRY_NAME=geom"),
            (
                "OGR owns source interpretation and GeoPackage writing; Runtime owns process execution.",
                "Artifact owns OGC conformance, SQLite container checks, CRS/schema contract and cross-view verification.",
            ),
        )
    if equipment_id == "gdal-ogr" and capability in {"geospatial.inspect", "geospatial.transform"}:
        source = str(parameters["source"]); return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/ogrinfo"), ("-ro", "-so", "-json", source))
    if equipment_id == "warcio" and capability == "web.capture.response.warc":
        script = str(Path(__file__).resolve().parents[2] / "scripts/produce-warc-response.py")
        args=(script,"--output",str(parameters["output"]),"--payload",str(parameters["payload"]),"--target-uri",str(parameters["targetUri"]),"--warc-date",str(parameters["warcDate"]),"--record-id",str(parameters["recordId"]),"--status",str(parameters.get("status","200 OK")),"--content-type",str(parameters["contentType"]))
        return EquipmentPlan(
            equipment_id, capability, "process", _require_existing("/usr/bin/python"), args,
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
            equipment_id, capability, "process", _require_existing("/usr/bin/python"), args,
            (
                "Python stdlib email owns RFC5322/MIME serialization for the bounded single-part message.",
                "Artifact independently checks raw CRLF/header policy plus Python-email/mailparser agreement; SMTP delivery/authentication are not implied.",
            ),
        )
    if equipment_id == "cadquery" and capability in {"cad.script.author", "cad.export.step", "cad.export.stl"}:
        script = str(parameters["script"])
        extra = tuple(str(value) for value in parameters.get("args", []))
        executable = _require_existing("/root/.local/share/ordivon/laboratory/engineering-py312/bin/python")
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
        executable = _require_existing("/usr/bin/kicad-cli")
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
            equipment_id, capability, "process", _require_existing("/usr/bin/ngspice"), tuple(args),
            (
                "ngspice owns parse/simulation semantics; Runtime owns process execution.",
                "A successful process is not a circuit-quality claim. Artifact's EDA profile owns bounded measurement/range verification when delivery evidence is required.",
            ),
        )
    if equipment_id == "typst" and capability == "document.compile.pdf":
        source = str(parameters["source"])
        output = str(parameters["output"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/typst"), ("compile", source, output))
    if equipment_id == "imagemagick" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/magick"), (input_path, "-resize", f"{width}x{height}!", output))
    if equipment_id == "inkscape" and capability == "vector.export":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        args = [input_path, "--export-filename", output]
        if parameters.get("width") is not None:
            args.extend(["--export-width", str(int(parameters["width"]))])
        binding = _workstation_equipment_binding("game-inkscape-e1", mode="managed")
        if binding is not None:
            environment = tuple(sorted(_binding_environment(binding).items()))
            return EquipmentPlan(
                equipment_id, capability, "process", str(binding["executable"]), tuple(args),
                (f"Resolved through Workstation EquipmentBinding {binding.get('bindingDigest')}; Studio retains vector semantics and Runtime retains execution authority.",),
                environment,
            )
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/inkscape"), tuple(args))
    if equipment_id == "aseprite" and capability in {"sprite.source.author", "sprite.runtime.export"}:
        binding = _workstation_equipment_binding("game-aseprite-e1", mode="managed")
        if binding is None:
            raise FileNotFoundError("Workstation binding game-aseprite-e1 is unavailable")
        environment = tuple(sorted(_binding_environment(binding).items()))
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
        executable = _first_existing(
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
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/godot"), ("--headless", "--script", script, "--", *extra))
    if equipment_id == "ffmpeg" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/ffmpeg"), ("-v", "error", "-y", "-i", input_path, "-vf", f"scale={width}:{height}", "-frames:v", "1", output))
    if equipment_id == "rsvg-convert" and capability == "svg.rasterize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/rsvg-convert"), ("--width", str(width), "--height", str(height), "-o", output, input_path))
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
        executable = _first_existing(
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
