from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any, Iterable
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

from artifact_core.contracts import file_fact, sha256_file

OOXML_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _safe_zip_names(names: Iterable[str]) -> list[str]:
    bad: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            bad.append(name)
    return bad


def _relationship_base(rels_name: str) -> str:
    if rels_name == "_rels/.rels":
        return ""
    marker = "/_rels/"
    if marker not in rels_name or not rels_name.endswith(".rels"):
        return ""
    left, right = rels_name.split(marker, 1)
    owner = posixpath.join(left, right[:-5])
    return posixpath.dirname(owner)


def _resolve_relationship_target(base: str, target: str) -> str | None:
    target = target.split("#", 1)[0]
    parsed = urllib.parse.urlparse(target)
    if parsed.scheme:
        return None
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(base, target))
    if resolved.startswith("../") or resolved == "..":
        return None
    return resolved


def inspect_pptx(path: Path, placeholder_patterns: Iterable[str] = ()) -> dict[str, Any]:
    artifact = file_fact(path)
    failures: list[str] = []
    warnings: list[str] = []
    unresolved_relationships: list[dict[str, str]] = []
    font_names: set[str] = set()
    render_explicit_font_names: set[str] = set()
    placeholder_hits: list[dict[str, str]] = []
    slide_count = 0
    hidden_slides = 0
    slide_size: dict[str, int] | None = None

    if not zipfile.is_zipfile(path):
        return {"status": "FAIL", "artifact": artifact, "failures": ["not a ZIP/OPC package"]}

    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        unsafe = _safe_zip_names(names)
        if unsafe:
            failures.append(f"unsafe package paths: {unsafe[:5]}")
        required = {
            "[Content_Types].xml",
            "_rels/.rels",
            "ppt/presentation.xml",
            "ppt/_rels/presentation.xml.rels",
        }
        missing = sorted(required - names)
        if missing:
            failures.append("missing required OPC/PPTX parts: " + ", ".join(missing))

        for rels_name in sorted(name for name in names if name.endswith(".rels")):
            try:
                root = ET.fromstring(package.read(rels_name))
            except Exception as error:
                failures.append(f"invalid relationships XML {rels_name}: {error}")
                continue
            base = _relationship_base(rels_name)
            for rel in root.findall(f"{{{OOXML_REL_NS}}}Relationship"):
                if rel.attrib.get("TargetMode") == "External":
                    continue
                target = rel.attrib.get("Target", "")
                resolved = _resolve_relationship_target(base, target)
                if resolved is None:
                    warnings.append(
                        f"unresolved non-file relationship target in {rels_name}: {target}"
                    )
                    continue
                if resolved not in names:
                    unresolved_relationships.append(
                        {"rels": rels_name, "target": target, "resolved": resolved}
                    )
        if unresolved_relationships:
            failures.append(
                f"{len(unresolved_relationships)} internal relationship target(s) are missing"
            )

        if "ppt/presentation.xml" in names:
            try:
                root = ET.fromstring(package.read("ppt/presentation.xml"))
                ids = root.findall(f".//{{{PRESENTATION_NS}}}sldId")
                slide_count = len(ids)
                size_node = root.find(f".//{{{PRESENTATION_NS}}}sldSz")
                if size_node is not None:
                    try:
                        cx = int(size_node.attrib.get("cx", "0"))
                        cy = int(size_node.attrib.get("cy", "0"))
                        if cx > 0 and cy > 0:
                            slide_size = {"cx": cx, "cy": cy}
                    except (TypeError, ValueError):
                        pass
            except Exception as error:
                failures.append(f"invalid ppt/presentation.xml: {error}")

        patterns = [re.compile(pattern, re.IGNORECASE) for pattern in placeholder_patterns]
        render_xml_names = sorted(
            name
            for name in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            or re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)
            or re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", name)
        )
        for xml_name in render_xml_names:
            try:
                root = ET.fromstring(package.read(xml_name))
            except Exception as error:
                failures.append(f"invalid render-relevant XML {xml_name}: {error}")
                continue
            is_slide = bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", xml_name))
            if is_slide and root.attrib.get("show") in {"0", "false", "False"}:
                hidden_slides += 1
            if is_slide:
                texts = [
                    node.text or ""
                    for node in root.findall(f".//{{{DRAWING_NS}}}t")
                ]
                joined = "\n".join(texts)
                for pattern in patterns:
                    match = pattern.search(joined)
                    if match:
                        placeholder_hits.append(
                            {
                                "slide": xml_name,
                                "pattern": pattern.pattern,
                                "match": match.group(0),
                            }
                        )
            for node in root.iter():
                typeface = node.attrib.get("typeface")
                if typeface and not typeface.startswith("+"):
                    font_names.add(typeface)
                    render_explicit_font_names.add(typeface)

        for xml_name in sorted(
            name
            for name in names
            if name.startswith("ppt/theme/") and name.endswith(".xml")
        ):
            try:
                root = ET.fromstring(package.read(xml_name))
            except Exception:
                continue
            for node in root.iter():
                typeface = node.attrib.get("typeface")
                if typeface and not typeface.startswith("+"):
                    font_names.add(typeface)

    if slide_count <= 0:
        failures.append("presentation has no slides")
    if placeholder_hits:
        failures.append(
            f"placeholder text found in {len(placeholder_hits)} slide occurrence(s)"
        )
    return {
        "status": "PASS" if not failures else "FAIL",
        "artifact": artifact,
        "package": {
            "kind": "OOXML/OPC PPTX",
            "slideCount": slide_count,
            "hiddenSlideCount": hidden_slides,
            "slideSizeEmu": slide_size,
            "aspectRatio": (
                round(slide_size["cx"] / slide_size["cy"], 8) if slide_size else None
            ),
            "referencedTypefaceNames": sorted(font_names),
            "renderExplicitTypefaceNames": sorted(render_explicit_font_names),
            "unresolvedRelationships": unresolved_relationships,
            "placeholderHits": placeholder_hits,
        },
        "scope": {
            "packageChecks": "performed",
            "OOXMLSchemaValidation": "NOT_RUN",
            "note": (
                "Package/relationship/XML checks do not replace an ISO/IEC 29500 "
                "schema validator such as Open XML SDK validation."
            ),
        },
        "warnings": warnings,
        "failures": failures,
    }


def verify_openxml_evidence(evidence_path: Path, artifact: Path) -> dict[str, Any]:
    value = json.loads(evidence_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    expected_digest = sha256_file(artifact)
    if value.get("artifact", {}).get("sha256") != expected_digest:
        failures.append("Open XML validation evidence artifact digest mismatch")
    validator = value.get("validator", {})
    if validator.get("implementation") != "DocumentFormat.OpenXml":
        failures.append(
            "Open XML validation evidence did not use DocumentFormat.OpenXml"
        )
    if validator.get("api") != "OpenXmlValidator":
        failures.append("Open XML validation evidence did not use OpenXmlValidator")
    if not validator.get("packageVersion"):
        failures.append("Open XML validation evidence omitted package version")
    if value.get("status") != "PASS":
        failures.append("Open XML validator did not PASS")
    if int(value.get("validationErrorCount", -1)) != 0:
        failures.append("Open XML validator reported validation errors")
    return {
        "status": "PASS" if not failures else "FAIL",
        "evidencePath": str(evidence_path.resolve()),
        "validator": validator,
        "failures": failures,
    }
