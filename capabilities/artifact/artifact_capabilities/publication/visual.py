from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


class PublicationVisualProbeError(RuntimeError):
    pass


def _tool(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise PublicationVisualProbeError(f"required mature visual tool is unavailable: {name}")
    return value


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _natural_page_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)(?=\.png$)", path.name)
    return (int(match.group(1)) if match else 10**9, path.name)


def raster_pdf(pdf_path: Path, output_dir: Path, *, dpi: int = 140) -> tuple[Path, ...]:
    """Raster one PDF through Poppler using a stable page-image naming convention."""

    if dpi < 72 or dpi > 600:
        raise ValueError("dpi must be in [72, 600]")
    pdf = pdf_path.resolve()
    if not pdf.is_file():
        raise PublicationVisualProbeError(f"PDF does not exist: {pdf}")
    out = output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prefix = out / "page"
    completed = subprocess.run(
        [_tool("pdftoppm"), "-png", "-r", str(dpi), str(pdf), str(prefix)],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if completed.returncode != 0:
        raise PublicationVisualProbeError(completed.stderr or "pdftoppm failed")
    pages = tuple(sorted(out.glob("page-*.png"), key=_natural_page_key))
    if not pages:
        raise PublicationVisualProbeError("pdftoppm produced no page rasters")
    return pages


def raster_manifest(page_paths: tuple[Path, ...], *, ink_threshold: int = 245) -> dict[str, Any]:
    if not 1 <= ink_threshold <= 254:
        raise ValueError("ink_threshold must be in [1, 254]")

    pages: list[dict[str, Any]] = []
    for page_number, path in enumerate(page_paths, start=1):
        with Image.open(path) as raw:
            gray = raw.convert("L")
            width, height = gray.size
            histogram = gray.histogram()
            total = width * height
            ink = sum(histogram[:ink_threshold])
            very_dark = sum(histogram[:64])
            mask = gray.point(lambda value: 255 if value < ink_threshold else 0)
            bbox = mask.getbbox()
            if bbox is None:
                margins = [width, height, width, height]
                blank = True
            else:
                left, top, right, bottom = bbox
                margins = [left, top, width - right, height - bottom]
                blank = False
            pages.append(
                {
                    "page": page_number,
                    "file": path.name,
                    "sha256": "sha256:" + _sha256(path),
                    "sizePx": [width, height],
                    "marginsPx": margins,
                    "blank": blank,
                    "inkFraction": round(ink / total, 8),
                    "veryDarkFraction": round(very_dark / total, 8),
                }
            )

    return {
        "schemaVersion": 1,
        "kind": "publication-canonical-raster-manifest",
        "pageCount": len(pages),
        "pages": pages,
    }


def compare_raster_sets(
    baseline_paths: tuple[Path, ...],
    candidate_paths: tuple[Path, ...],
) -> dict[str, Any]:
    if len(baseline_paths) != len(candidate_paths):
        return {
            "schemaVersion": 1,
            "kind": "publication-visual-regression",
            "standing": "FAIL",
            "reason": "PAGE_COUNT_CHANGED",
            "baselinePages": len(baseline_paths),
            "candidatePages": len(candidate_paths),
            "changedPages": [],
        }

    changed: list[dict[str, Any]] = []
    for page_number, (before_path, after_path) in enumerate(
        zip(baseline_paths, candidate_paths, strict=True),
        start=1,
    ):
        with Image.open(before_path) as before_raw, Image.open(after_path) as after_raw:
            before = before_raw.convert("RGB")
            after = after_raw.convert("RGB")
            if before.size != after.size:
                changed.append(
                    {
                        "page": page_number,
                        "reason": "PAGE_RASTER_SIZE_CHANGED",
                        "baselineSizePx": list(before.size),
                        "candidateSizePx": list(after.size),
                    }
                )
                continue
            diff = ImageChops.difference(before, after).convert("L")
            histogram = diff.histogram()
            changed_pixels = sum(histogram[1:])
            total = before.size[0] * before.size[1]
            bbox = diff.getbbox()
            if changed_pixels:
                changed.append(
                    {
                        "page": page_number,
                        "reason": "PIXEL_CHANGE",
                        "changedPixelFraction": round(changed_pixels / total, 10),
                        "changedBoundingBoxPx": list(bbox) if bbox is not None else None,
                    }
                )

    return {
        "schemaVersion": 1,
        "kind": "publication-visual-regression",
        "standing": "PASS" if not changed else "CHANGED",
        "baselinePages": len(baseline_paths),
        "candidatePages": len(candidate_paths),
        "changedPages": changed,
        "unexpectedChangeCount": None,
        "nonClaim": (
            "Pixel change detection identifies differences; "
            "source/change attribution remains external."
        ),
    }
