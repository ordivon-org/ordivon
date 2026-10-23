from __future__ import annotations

import unittest

from artifact_capabilities.publication.geometry import evaluate_raster_geometry
from artifact_capabilities.publication.semantic_layout import (
    build_semantic_layout_graph,
    evaluate_semantic_layout_graph,
)


class PublicationGeometrySemanticR1Tests(unittest.TestCase):
    def test_geometry_passes_clear_nonblank_pages(self) -> None:
        manifest = {
            "kind": "publication-canonical-raster-manifest",
            "pages": [
                {"page": 1, "blank": False, "marginsPx": [40, 50, 40, 50]},
                {"page": 2, "blank": False, "marginsPx": [30, 30, 30, 30]},
            ],
        }
        result = evaluate_raster_geometry(manifest, minimum_edge_clearance_px=25)
        self.assertEqual(result["standing"], "PASS")
        self.assertEqual(result["minimumObservedEdgeClearancePx"], 30)

    def test_geometry_fails_blank_or_tight_page(self) -> None:
        manifest = {
            "kind": "publication-canonical-raster-manifest",
            "pages": [
                {"page": 1, "blank": True, "marginsPx": [100, 100, 100, 100]},
                {"page": 2, "blank": False, "marginsPx": [10, 40, 40, 40]},
            ],
        }
        result = evaluate_raster_geometry(manifest, minimum_edge_clearance_px=25)
        self.assertEqual(result["standing"], "FAIL")
        ids = {x["id"] for x in result["findings"]}
        self.assertIn("blank-page:1", ids)
        self.assertIn("edge-clearance:2", ids)

    def test_semantic_layout_detects_duplicate_caption_identity(self) -> None:
        inventory = {
            "kind": "publication-carrier-inventory",
            "pdfSha256": "sha256:" + "a" * 64,
            "pages": [{"page": 1}],
            "figures": [
                {"id": "1", "page": 1, "line": 10, "captionLine": "Fig. 1. A"},
                {"id": "1", "page": 1, "line": 20, "captionLine": "Figure 1. A"},
            ],
            "tables": [],
        }
        graph = build_semantic_layout_graph(inventory)
        result = evaluate_semantic_layout_graph(graph)
        self.assertEqual(result["standing"], "FAIL")
        self.assertEqual(result["findings"][0]["id"], "duplicate-node:figure:1")


if __name__ == "__main__":
    unittest.main()
