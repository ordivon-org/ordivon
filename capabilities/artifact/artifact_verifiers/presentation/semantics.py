from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from artifact_core.contracts import sha256_file


def verify_presentation_semantics(
    profile: dict[str, Any],
    pptx_result: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    package = pptx_result.get("package", {})
    slide_count = int(package.get("slideCount", 0))
    policy = profile.get("semanticPolicy", {})
    minimum = policy.get("minimumSlideCount")
    maximum = policy.get("maximumSlideCount")
    if isinstance(minimum, int) and slide_count < minimum:
        failures.append(f"slide count {slide_count} is below minimum {minimum}")
    if isinstance(maximum, int) and slide_count > maximum:
        failures.append(f"slide count {slide_count} exceeds maximum {maximum}")
    declared_aspect = profile.get("aspectRatio")
    observed = package.get("aspectRatio")
    target_ratios = {"16:9": 16 / 9, "4:3": 4 / 3}
    if declared_aspect in target_ratios:
        if not isinstance(observed, (int, float)):
            failures.append("presentation slide size/aspect ratio is unavailable")
        elif abs(float(observed) - target_ratios[declared_aspect]) > 0.002:
            failures.append(
                f"presentation aspect ratio {observed:.6f} does not satisfy profile {declared_aspect}"
            )
    return {
        "status": "PASS" if not failures else "FAIL",
        "slideCount": slide_count,
        "minimumSlideCount": minimum,
        "maximumSlideCount": maximum,
        "declaredAspectRatio": declared_aspect,
        "observedAspectRatio": observed,
        "slideSizeEmu": package.get("slideSizeEmu"),
        "failures": failures,
    }


def verify_font_manifest(
    profile: dict[str, Any],
    font_dir: Path,
    observed_typefaces: Iterable[str] = (),
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    declared = {
        str(font.get("family", "")).casefold(): str(font.get("family", ""))
        for font in profile.get("fonts", [])
    }
    observed = sorted({str(name) for name in observed_typefaces if str(name)})
    undeclared = [name for name in observed if name.casefold() not in declared]
    for name in undeclared:
        failures.append(
            f"artifact render graph directly references undeclared typeface: {name}"
        )
    for font in profile.get("fonts", []):
        family = str(font.get("family", ""))
        required = bool(font.get("required"))
        files: list[dict[str, Any]] = []
        for filename in font.get("targetFiles", []):
            path = font_dir / str(filename)
            present = path.is_file() and not path.is_symlink()
            fact = {
                "name": str(filename),
                "path": str(path),
                "present": present,
                "sha256": sha256_file(path) if present else None,
            }
            files.append(fact)
            if required and not present:
                failures.append(
                    f"required font file missing for {family}: {filename}"
                )
        if required and not font.get("targetFiles"):
            failures.append(f"required font {family} has no targetFiles binding")
        results.append(
            {
                "family": family,
                "required": required,
                "embeddingPermission": font.get("embeddingPermission"),
                "files": files,
            }
        )
    return {
        "status": "PASS" if not failures else "FAIL",
        "fontDirectory": str(font_dir),
        "observedRenderExplicitTypefaces": observed,
        "undeclaredObservedTypefaces": undeclared,
        "fonts": results,
        "failures": failures,
    }
