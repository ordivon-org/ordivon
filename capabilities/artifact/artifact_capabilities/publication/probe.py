from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from .contract import CarrierObservation


class PublicationProbeError(RuntimeError):
    pass


def _tool(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise PublicationProbeError(f"required mature PDF tool is unavailable: {name}")
    return value


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_page_count(pdfinfo: str) -> int:
    match = re.search(r"(?m)^Pages:\s+(\d+)\s*$", pdfinfo)
    if match is None:
        raise PublicationProbeError("pdfinfo did not expose a Pages field")
    return int(match.group(1))


def _parse_fonts(pdffonts: str) -> tuple[bool, int]:
    all_embedded = True
    type3 = 0
    for line in pdffonts.splitlines()[2:]:
        if not line.strip():
            continue
        if re.search(r"\sType\s+3\s+", line):
            type3 += 1
        match = re.search(
            r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",
            line,
            re.IGNORECASE,
        )
        if match is None:
            raise PublicationProbeError(f"cannot parse pdffonts row: {line}")
        if match.group(1).casefold() != "yes":
            all_embedded = False
    return all_embedded, type3


def _compiler_counts(log_path: Path | None) -> tuple[int | None, int | None, int | None]:
    if log_path is None:
        return None, None, None
    if not log_path.is_file():
        raise PublicationProbeError(f"compiler log does not exist: {log_path}")
    text = log_path.read_text(encoding="utf-8", errors="replace")
    overfull = len(re.findall(r"Overfull \\[hv]box", text))
    undefined_citations = len(
        re.findall(r"undefined citations|Citation .* undefined", text, re.IGNORECASE)
    )
    undefined_references = len(
        re.findall(r"undefined references|Reference .* undefined", text, re.IGNORECASE)
    )
    return overfull, undefined_citations, undefined_references


def probe_pdf_carrier(
    pdf_path: Path,
    *,
    compiler_log_path: Path | None = None,
    human_perceptual_signoff: bool = False,
) -> CarrierObservation:
    pdf = pdf_path.resolve()
    if not pdf.is_file():
        raise PublicationProbeError(f"PDF does not exist: {pdf}")

    qpdf = _run([_tool("qpdf"), "--check", str(pdf)])
    info = _run([_tool("pdfinfo"), str(pdf)])
    text = _run([_tool("pdftotext"), "-layout", str(pdf), "-"])
    fonts = _run([_tool("pdffonts"), str(pdf)])

    if info.returncode != 0:
        raise PublicationProbeError(info.stderr or "pdfinfo failed")
    if text.returncode != 0:
        raise PublicationProbeError(text.stderr or "pdftotext failed")
    if fonts.returncode != 0:
        raise PublicationProbeError(fonts.stderr or "pdffonts failed")

    page_count = _parse_page_count(info.stdout)
    pages = tuple(text.stdout.split("\f"))
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    if len(pages) != page_count:
        raise PublicationProbeError(
            f"pdftotext page count {len(pages)} != pdfinfo page count {page_count}"
        )

    all_fonts_embedded, type3_fonts = _parse_fonts(fonts.stdout)
    overfull, undefined_citations, undefined_references = _compiler_counts(
        compiler_log_path.resolve() if compiler_log_path is not None else None
    )

    return CarrierObservation(
        pdf_sha256=_sha256(pdf),
        page_count=page_count,
        text=text.stdout,
        pages=pages,
        qpdf_pass=qpdf.returncode == 0,
        all_fonts_embedded=all_fonts_embedded,
        type3_fonts=type3_fonts,
        overfull_boxes=overfull,
        undefined_citations=undefined_citations,
        undefined_references=undefined_references,
        human_perceptual_signoff=human_perceptual_signoff,
    )
