from __future__ import annotations

from pathlib import Path
from typing import Any

from .cognition_sections import extract_learning
from .production_source_io import read_bound_bytes, read_bound_object, relative_child


def _production_learning_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    productions_root = root / "productions"
    if not productions_root.is_dir():
        return records
    for manifest_path in sorted(productions_root.glob("*/production.json")):
        production_root = manifest_path.parent
        production, _ = read_bound_object(manifest_path)
        production_id = str(production.get("id") or production_root.name)
        sources = production.get("sources")
        if not isinstance(sources, dict) or not isinstance(sources.get("cognition"), str):
            continue
        cognition_path = relative_child(production_root, sources["cognition"])
        if not cognition_path.is_file():
            continue
        cognition_bytes, cognition_digest = read_bound_bytes(cognition_path)
        learning = extract_learning(cognition_bytes.decode("utf-8"))
        if learning is None:
            continue
        outputs = production.get("outputs")
        profiles = []
        if isinstance(outputs, list):
            profiles = sorted({
                str(item["profile"])
                for item in outputs
                if isinstance(item, dict) and isinstance(item.get("profile"), str)
            })
        records.append({
            "productionId": production_id,
            "productionStatus": production.get("status"),
            "audiences": production.get("audiences", []),
            "outputProfiles": profiles,
            "learning": learning,
            "source": {
                "path": str(cognition_path.relative_to(root)),
                "digest": cognition_digest,
            },
        })
    return records


def build_learning_context(root: Path, *, current_production_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    expression_path = root / "research/expression/context.json"
    expression, expression_digest = read_bound_object(expression_path)
    creative = expression.get("creativeSystem")
    if not isinstance(creative, dict):
        raise TypeError("expression context must contain creativeSystem")
    observatory = creative.get("culturalObservatory")
    alpha = observatory.get("creativeAlphaResearch") if isinstance(observatory, dict) else None
    if not isinstance(alpha, dict):
        raise TypeError("expression context must contain creativeAlphaResearch")
    records = _production_learning_records(root)
    known_ids = {record["productionId"] for record in records}
    if current_production_id is not None and current_production_id not in known_ids:
        manifest = root / "productions" / current_production_id / "production.json"
        if not manifest.is_file():
            raise ValueError(f"unknown Production: {current_production_id}")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio.learning-context",
        "truthRole": "derived-read-only-projection",
        "currentProductionId": current_production_id,
        "promotionPath": list(creative.get("learningPromotion", [])),
        "twoSpeedBoundary": creative.get("twoSpeedLearning"),
        "researchValidity": {
            "authority": alpha.get("authority"),
            "institutions": list(alpha.get("researchInstitutions", [])),
            "oosDimensions": list(alpha.get("oosDimensions", [])),
            "boundary": alpha.get("boundary"),
        },
        "retainedLearning": records,
        "source": {
            "expressionContext": str(expression_path.relative_to(root)),
            "expressionContextDigest": expression_digest,
        },
        "consumptionRule": (
            "Retained Production learning is scoped source evidence for the next Agent, not automatic universal taste authority. "
            "Use it to alter the next production decision when applicable; broaden scope only through independent evidence and explicit OOS support."
        ),
        "humanBoundary": (
            "Human response is one typed evidence class. One observer is one observation; Human review is required only when the unresolved target claim itself depends on human response, culture, interpretation, or consequence."
        ),
        "escapeHatch": {
            "expressionContext": str(expression_path),
            "productionsRoot": str(root / "productions"),
        },
    }
