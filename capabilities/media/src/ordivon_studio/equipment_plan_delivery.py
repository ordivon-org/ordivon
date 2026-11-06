"""Native data, engineering and delivery production LEGO.

These are exact command proposals to mature providers (Tiled, DuckDB,
PyArrow, GDAL/OGR, warcio, stdlib email, CadQuery, KiCad and ngspice).
The consumer/Artifact Owner checks the resulting bytes; this module
neither runs the process nor decides Media creative or publication standing.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .equipment_plan_contracts import EquipmentPlan


def compile_delivery_operation(
    equipment_id: str,
    capability: str,
    parameters: Mapping[str, Any],
    *,
    require_existing: Callable[[str], str],
) -> EquipmentPlan | None:
    """Return a native delivery plan when this capability belongs here, else None."""
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
    return None
