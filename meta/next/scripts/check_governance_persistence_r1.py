from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "planning" / "governance-persistence-ratchet-r1.json"
LENS_REGISTRY = ROOT / "knowledge" / "registries" / "lego-lens-registry-r1.json"
PROJECT_SCHEMA = ROOT / "schemas" / "project-lego-plan-r1.schema.json"

EXPECTED_DURABILITY = {
    "Task": "CONDITIONAL",
    "Workspace": "EPHEMERAL",
    "Evidence": "REFERENCE_FIRST",
    "Gate": "STATELESS",
    "Lens": "DEFINITION_ONLY",
    "Operator": "DEFINITION_ONLY",
    "Registry": "REBUILDABLE_BY_DEFAULT",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit() -> list[str]:
    problems: list[str] = []
    profile = load_json(PROFILE)
    roles = profile.get("roles", {})

    if set(roles) != set(EXPECTED_DURABILITY):
        problems.append(
            f"role set changed: observed={sorted(roles)} expected={sorted(EXPECTED_DURABILITY)}"
        )

    for name, expected in EXPECTED_DURABILITY.items():
        observed = roles.get(name, {}).get("durability")
        if observed != expected:
            problems.append(f"{name} durability={observed!r}, expected {expected!r}")

    sunset = profile.get("sunsetCondition", {})
    if sunset.get("kind") != "DELETE_RATCHET_WHEN_REDUNDANT":
        problems.append("ratchet must carry an explicit self-deletion condition")

    growth = profile.get("growthRatchets", {})
    lens_ceiling = growth.get("legoActiveLensCeiling")
    operator_ceiling = growth.get("legoOperatorCeiling")

    registry = load_json(LENS_REGISTRY)
    active_lenses = registry.get("activeLenses", [])
    operators = registry.get("operators", [])
    if len(active_lenses) > lens_ceiling:
        problems.append(
            f"active lens count grew additively: {len(active_lenses)} > {lens_ceiling}"
        )
    if len(operators) > operator_ceiling:
        problems.append(
            f"operator count grew additively: {len(operators)} > {operator_ceiling}"
        )

    schema = load_json(PROJECT_SCHEMA)
    forbidden = {x.lower() for x in growth["projectPlanForbiddenNewRequiredConcepts"]}
    required = {x.lower() for x in schema.get("required", [])}
    leaked = sorted(required & forbidden)
    if leaked:
        problems.append(
            "governance vocabulary became mandatory project truth: " + ", ".join(leaked)
        )

    node_required = {
        x.lower()
        for x in schema.get("properties", {})
        .get("nodes", {})
        .get("items", {})
        .get("required", [])
    }
    leaked_nodes = sorted(node_required & forbidden)
    if leaked_nodes:
        problems.append(
            "governance vocabulary became mandatory node truth: " + ", ".join(leaked_nodes)
        )

    return problems


def main() -> int:
    problems = audit()
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("PASS governance-persistence-ratchet-r1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
