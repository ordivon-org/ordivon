from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "planning" / "governance-persistence-ratchet-r1.json"

EXPECTED_DURABILITY = {
    "Task": "CONDITIONAL",
    "Workspace": "EPHEMERAL",
    "Evidence": "REFERENCE_FIRST",
    "Gate": "STATELESS",
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
    for relative in growth.get("forbiddenLocalMethodInfrastructure", []):
        if (ROOT / relative).exists():
            problems.append(
                f"retired local method infrastructure reappeared: {relative}"
            )

    forbidden_method_refs = growth.get("forbiddenMethodAdapterReferences", [])
    skills_root = ROOT / ".agents" / "skills"
    for skill_file in skills_root.glob("*/SKILL.md"):
        text = skill_file.read_text(encoding="utf-8")
        for forbidden_ref in forbidden_method_refs:
            if forbidden_ref in text:
                problems.append(
                    f"method adapter {skill_file.relative_to(ROOT)} retains retired local method reference: {forbidden_ref}"
                )

    for relative in growth.get("forbiddenLocalPlanningInfrastructure", []):
        if (ROOT / relative).exists():
            problems.append(
                f"retired local planning infrastructure reappeared: {relative}"
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
