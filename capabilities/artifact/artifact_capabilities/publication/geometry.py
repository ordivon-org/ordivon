from __future__ import annotations

from typing import Any


def evaluate_raster_geometry(
    raster_manifest: dict[str, Any],
    *,
    minimum_edge_clearance_px: int = 25,
) -> dict[str, Any]:
    """Evaluate deterministic page-level raster geometry.

    This does not claim readability. It catches blank pages and ink that reaches
    too close to page edges under one declared raster profile.
    """

    if minimum_edge_clearance_px < 0:
        raise ValueError("minimum_edge_clearance_px must be non-negative")
    if raster_manifest.get("kind") != "publication-canonical-raster-manifest":
        raise ValueError("invalid canonical raster manifest")

    findings: list[dict[str, Any]] = []
    pages = raster_manifest.get("pages", [])
    for page in pages:
        number = page["page"]
        if page.get("blank"):
            findings.append(
                {
                    "id": f"blank-page:{number}",
                    "page": number,
                    "severity": "BLOCKER",
                    "predicate": "PAGE_NOT_BLANK",
                }
            )
            continue
        margins = page.get("marginsPx")
        if not isinstance(margins, list) or len(margins) != 4:
            findings.append(
                {
                    "id": f"geometry-unobserved:{number}",
                    "page": number,
                    "severity": "UNCERTAIN",
                    "predicate": "PAGE_GEOMETRY_OBSERVED",
                }
            )
            continue
        minimum = min(margins)
        if minimum < minimum_edge_clearance_px:
            findings.append(
                {
                    "id": f"edge-clearance:{number}",
                    "page": number,
                    "severity": "MAJOR",
                    "predicate": "MINIMUM_EDGE_CLEARANCE",
                    "evidence": {
                        "observedPx": minimum,
                        "requiredPx": minimum_edge_clearance_px,
                        "marginsPx": margins,
                    },
                }
            )

    blocker = any(x["severity"] in {"BLOCKER", "MAJOR"} for x in findings)
    uncertain = any(x["severity"] == "UNCERTAIN" for x in findings)
    if blocker:
        standing = "FAIL"
    elif uncertain:
        standing = "UNCERTAIN"
    else:
        standing = "PASS"

    observed_minimum = min(
        (
            min(page["marginsPx"])
            for page in pages
            if not page.get("blank")
            and isinstance(page.get("marginsPx"), list)
            and len(page["marginsPx"]) == 4
        ),
        default=None,
    )
    return {
        "schemaVersion": 1,
        "kind": "publication-raster-geometry-evaluation",
        "pageCount": len(pages),
        "minimumRequiredEdgeClearancePx": minimum_edge_clearance_px,
        "minimumObservedEdgeClearancePx": observed_minimum,
        "findings": findings,
        "standing": standing,
        "nonClaim": "geometry PASS is not normal-scale readability",
    }
