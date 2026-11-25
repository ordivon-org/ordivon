"""Pure bounded TMJ map admission; no native process or filesystem effects.

The R1 subset deliberately excludes resources whose identity depends on a
Tiled project, external file, template, tileset or class definition.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_sha(v: Any) -> str:
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def property_issues(owner: dict[str, Any], location: str) -> list[str]:
    """Check all map/layer/object properties before any native read."""
    properties = owner.get("properties", [])
    if not isinstance(properties, list):
        return [f"{location} properties must be an array"]
    issues = []
    primitive = {"string", "int", "float", "bool", "color", "object"}
    for index, prop in enumerate(properties):
        label = f"{location} property {index}"
        if not isinstance(prop, dict):
            issues.append(f"{label} must be an object")
            continue
        kind = prop.get("type")
        if kind == "file":
            issues.append(f"{label} has external file property")
        elif kind == "class" or prop.get("propertytype"):
            issues.append(f"{label} has unqualified custom/class property")
        elif not isinstance(kind, str) or kind not in primitive:
            issues.append(f"{label} has unsupported property type")
        elif isinstance(prop.get("value"), (dict, list)):
            issues.append(f"{label} has unsupported non-scalar property value")
    return issues


def object_shape(o: dict[str, Any]) -> str:
    if "polyline" in o:
        return "polyline"
    if any(k in o for k in ("polygon", "ellipse", "point", "text", "gid", "template")):
        return "unsupported"
    return "rectangle"


def assess_bounded_map(src: Any, want: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    # Bounded object-map subset: format identity and no external/resource-heavy features.
    bounded = []
    if not isinstance(src, dict):
        return {}, ["Tiled root must be a JSON object"]
    layers = src.get("layers")
    bounded.extend(property_issues(src, "map"))
    if src.get("type") != "map":
        bounded.append("Tiled root type must be map")
    if src.get("orientation") != "orthogonal":
        bounded.append("R1 requires orthogonal orientation")
    if src.get("infinite") is not False:
        bounded.append("R1 requires finite map")
    if src.get("tilesets") not in ([], None):
        bounded.append("R1 forbids tilesets")
    if not isinstance(layers, list) or not layers:
        bounded.append("R1 requires at least one object layer")
        layers = []
    layer_ids = []
    object_ids = []
    objects = []
    for l in layers:
        if not isinstance(l, dict) or l.get("type") != "objectgroup":
            bounded.append("R1 allows objectgroup layers only")
            continue
        bounded.extend(property_issues(l, f"layer {l.get('id')}"))
        layer_id = l.get("id")
        if type(layer_id) is not int or layer_id <= 0:
            bounded.append("layer ID must be a positive integer")
        else:
            layer_ids.append(layer_id)
        lo = l.get("objects")
        if not isinstance(lo, list):
            bounded.append(f"object layer {l.get('name')} lacks objects array")
            continue
        for o in lo:
            if not isinstance(o, dict):
                bounded.append("object must be JSON object")
                continue
            objects.append(o)
            object_id = o.get("id")
            if type(object_id) is not int or object_id <= 0:
                bounded.append("object ID must be a positive integer")
            else:
                object_ids.append(object_id)
            if "class" in o:
                bounded.append(
                    f"object {o.get('id')} uses legacy class field instead of current type"
                )
            if not isinstance(o.get("type"), str) or not o.get("type"):
                bounded.append(f"object {o.get('id')} requires non-empty current Tiled type")
            shape = object_shape(o)
            if shape not in ("rectangle", "polyline"):
                bounded.append(f"object {o.get('id')} shape outside R1: {shape}")
            if "template" in o:
                bounded.append(f"object {o.get('id')} uses external template")
            bounded.extend(property_issues(o, f"object {o.get('id')}"))
    if len(layer_ids) != len(set(layer_ids)):
        bounded.append("layer IDs are not unique")
    if len(object_ids) != len(set(object_ids)):
        bounded.append("object IDs are not unique")
    facts = {
        "formatVersion": str(src.get("version")),
        "tiledVersion": str(src.get("tiledversion")),
        "orientation": src.get("orientation"),
        "width": src.get("width"),
        "height": src.get("height"),
        "tileWidth": src.get("tilewidth"),
        "tileHeight": src.get("tileheight"),
        "layerCount": len(layers),
        "objectCount": len(objects),
        "canonicalJsonSha256": canonical_sha(src),
        "layerTypes": [l.get("type") for l in layers if isinstance(l, dict)],
        "objectShapeCounts": {
            k: sum(object_shape(o) == k for o in objects)
            for k in ("rectangle", "polyline", "unsupported")
        },
    }
    for ck, fk in [
        ("formatVersion", "formatVersion"),
        ("tiledVersion", "tiledVersion"),
        ("orientation", "orientation"),
        ("width", "width"),
        ("height", "height"),
        ("tileWidth", "tileWidth"),
        ("tileHeight", "tileHeight"),
        ("layerCount", "layerCount"),
        ("objectCount", "objectCount"),
    ]:
        if facts[fk] != want.get(ck):
            bounded.append(f"{fk} differs from object contract")
    return facts, bounded
