#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_ROLES = {
    "LENS",
    "DOMAIN_METHOD",
    "OPERATOR",
    "INFORMATIVE_ONLY",
    "DEFERRED",
    "REJECTED",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(registry: dict, ledger: dict) -> dict:
    if ledger.get("schemaVersion") != 1:
        raise ValueError("unsupported ledger schemaVersion")

    lens_ids = {item["id"] for item in registry.get("lenses", [])}
    operators = set(registry.get("operators", []))

    summary = {
        "caseCount": 0,
        "maxSelectedLensCount": 0,
        "casesOverThreeLenses": [],
        "domainMethodUses": 0,
        "operatorUses": 0,
        "roleCounts": {role: 0 for role in sorted(VALID_ROLES)},
        "contractions": [],
    }

    for case in ledger.get("cases", []):
        case_id = case.get("id")
        if not case_id:
            raise ValueError("case missing id")

        methods = case.get("methods", [])
        ids = [m.get("id") for m in methods]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{case_id}: duplicate method id")

        selected_lenses = 0
        for method in methods:
            method_id = method.get("id")
            role = method.get("role")
            if role not in VALID_ROLES:
                raise ValueError(f"{case_id}: invalid role {role!r}")
            if not method_id:
                raise ValueError(f"{case_id}: method missing id")

            summary["roleCounts"][role] += 1

            if role == "LENS":
                if method_id not in lens_ids and not method.get("candidate", False):
                    raise ValueError(f"{case_id}: unknown registry lens {method_id}")
                if method.get("selected", False):
                    selected_lenses += 1
            elif role == "OPERATOR":
                if method_id not in operators:
                    raise ValueError(f"{case_id}: unknown operator {method_id}")
                summary["operatorUses"] += 1
            elif role == "DOMAIN_METHOD":
                summary["domainMethodUses"] += 1

        if selected_lenses > 3 and not case.get("exceptionalLensCountJustification"):
            raise ValueError(
                f"{case_id}: {selected_lenses} selected lenses requires exceptionalLensCountJustification"
            )

        summary["caseCount"] += 1
        summary["maxSelectedLensCount"] = max(summary["maxSelectedLensCount"], selected_lenses)
        if selected_lenses > 3:
            summary["casesOverThreeLenses"].append(case_id)

        original = case.get("originalActiveCount")
        if isinstance(original, int) and original > selected_lenses:
            summary["contractions"].append(
                {
                    "case": case_id,
                    "from": original,
                    "to": selected_lenses,
                }
            )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()

    summary = audit(load(args.registry), load(args.ledger))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
