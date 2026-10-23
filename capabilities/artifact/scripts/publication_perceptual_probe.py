#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from artifact_capabilities.publication.geometry import evaluate_raster_geometry
from artifact_capabilities.publication.inventory import build_carrier_inventory
from artifact_capabilities.publication.probe import probe_pdf_carrier
from artifact_capabilities.publication.semantic_layout import (
    build_semantic_layout_graph,
    evaluate_semantic_layout_graph,
)
from artifact_capabilities.publication.visual import (
    attribute_visual_regression,
    compare_raster_sets,
    raster_manifest,
    raster_pdf,
)


def _fresh_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic publication perception inputs: inventory, canonical rasters, "
            "geometry, semantic-layout projection, and optional baseline visual regression."
        )
    )
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--baseline-pdf", type=Path)
    parser.add_argument("--dpi", type=int, default=140)
    parser.add_argument("--minimum-edge-clearance-px", type=int, default=25)
    parser.add_argument("--compiler-log", type=Path)
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    candidate_raster = out / "candidate-raster"
    _fresh_dir(candidate_raster)

    observation = probe_pdf_carrier(
        args.pdf,
        compiler_log_path=args.compiler_log,
        human_perceptual_signoff=False,
    )
    inventory = build_carrier_inventory(observation)
    pages = raster_pdf(args.pdf, candidate_raster, dpi=args.dpi)
    raster = raster_manifest(pages)
    geometry = evaluate_raster_geometry(
        raster,
        minimum_edge_clearance_px=args.minimum_edge_clearance_px,
    )
    graph = build_semantic_layout_graph(inventory)
    semantic = evaluate_semantic_layout_graph(graph)

    visual_regression = {
        "schemaVersion": 1,
        "kind": "publication-visual-regression",
        "standing": "NOT_APPLICABLE",
        "reason": "NO_BASELINE_SUPPLIED",
    }
    visual_attribution = {
        "schemaVersion": 1,
        "kind": "publication-visual-regression-attribution",
        "standing": "NOT_APPLICABLE",
        "reason": "NO_BASELINE_SUPPLIED",
        "unexpectedChangeCount": 0,
    }
    if args.baseline_pdf is not None:
        baseline_raster = out / "baseline-raster"
        _fresh_dir(baseline_raster)
        baseline_observation = probe_pdf_carrier(
            args.baseline_pdf,
            human_perceptual_signoff=False,
        )
        baseline_pages = raster_pdf(args.baseline_pdf, baseline_raster, dpi=args.dpi)
        visual_regression = compare_raster_sets(baseline_pages, pages)
        visual_attribution = attribute_visual_regression(
            visual_regression,
            baseline_pages_text=baseline_observation.pages,
            candidate_pages_text=observation.pages,
        )

    outputs = {
        "carrier-inventory-r1.json": inventory,
        "canonical-raster-manifest-r1.json": raster,
        "raster-geometry-r1.json": geometry,
        "semantic-layout-graph-r1.json": graph,
        "semantic-layout-evaluation-r1.json": semantic,
        "visual-regression-r1.json": visual_regression,
        "visual-regression-attribution-r1.json": visual_attribution,
    }
    for name, value in outputs.items():
        (out / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    summary = {
        "schemaVersion": 1,
        "kind": "publication-perceptual-probe-summary",
        "pdfSha256": inventory["pdfSha256"],
        "pageCount": inventory["pageCount"],
        "figureCaptionOccurrences": len(inventory["figures"]),
        "tableCaptionOccurrences": len(inventory["tables"]),
        "rasterDpi": args.dpi,
        "geometryStanding": geometry["standing"],
        "semanticLayoutStanding": semantic["standing"],
        "visualRegressionStanding": visual_regression["standing"],
        "visualAttributionStanding": visual_attribution["standing"],
        "unexpectedVisualChangeCount": visual_attribution.get("unexpectedChangeCount", 0),
        "standing": (
            "PASS"
            if geometry["standing"] == "PASS"
            and semantic["standing"] == "PASS"
            and visual_attribution["standing"] in {"PASS", "NOT_APPLICABLE"}
            else "PENDING_EXPLANATION"
            if geometry["standing"] == "PASS"
            and semantic["standing"] == "PASS"
            and visual_attribution["standing"] == "PENDING_EXPLANATION"
            else "FAIL"
        ),
        "nonClaim": (
            "Visual attribution explains why changed pixels are expected to exist; "
            "perceptual observers still judge whether the resulting layout is acceptable."
        ),
    }
    (out / "summary-r1.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["standing"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
