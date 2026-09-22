from __future__ import annotations

import re
from typing import Any

from .contract import CarrierObservation

_FIGURE_CAPTION = re.compile(r"^\s*(?:Fig\.|Figure)\s+(\d+)\s*[:.]\s*", re.IGNORECASE)
_TABLE_CAPTION = re.compile(r"^\s*Table\s+(\d+)\s*[:.]\s*", re.IGNORECASE)


def build_carrier_inventory(observation: CarrierObservation) -> dict[str, Any]:
    """Build deterministic routing inventory from the PDF text layer."""

    figures: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []

    for page_number, page in enumerate(observation.pages, start=1):
        page_lines = page.splitlines()
        pages.append(
            {
                "page": page_number,
                "lineCount": len(page_lines),
                "nonWhitespaceCharacters": len(re.sub(r"\s+", "", page)),
            }
        )
        for line_number, line in enumerate(page_lines, start=1):
            figure = _FIGURE_CAPTION.search(line)
            if figure is not None:
                figures.append(
                    {
                        "id": figure.group(1),
                        "page": page_number,
                        "line": line_number,
                        "captionLine": line.strip(),
                    }
                )
            table = _TABLE_CAPTION.search(line)
            if table is not None:
                tables.append(
                    {
                        "id": table.group(1),
                        "page": page_number,
                        "line": line_number,
                        "captionLine": line.strip(),
                    }
                )

    return {
        "schemaVersion": 1,
        "kind": "publication-carrier-inventory",
        "truthRole": "deterministic-routing-inventory-not-document-semantic-truth",
        "pdfSha256": "sha256:" + observation.pdf_sha256.lower(),
        "pageCount": observation.page_count,
        "pages": pages,
        "figures": figures,
        "tables": tables,
        "coverageBasis": {
            "pages": observation.page_count,
            "figureCaptionOccurrences": len(figures),
            "tableCaptionOccurrences": len(tables),
        },
    }
