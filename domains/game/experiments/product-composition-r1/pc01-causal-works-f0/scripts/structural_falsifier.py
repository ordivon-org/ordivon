#!/usr/bin/env python3
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "design.json").read_text())
ARCH = tuple(D["architectureModes"])
DIAGS = tuple(D["diagnostics"])
CYCLES = D["cycles"]
DIAG_COST = float(D["diagnosticCost"])
SWITCH_COST = float(D["switchCost"])


def observation(diag: str, cause: str) -> str:
    if diag == "none":
        return "none"
    return "fault" if diag == cause else "ok"


def solve(*, allow_diagnostics: bool, switch_cost: float):
    @lru_cache(maxsize=None)
    def value(i: int, previous: str | None):
        if i == len(CYCLES):
            return 0.0, None
        cycle = CYCLES[i]
        choices = DIAGS if allow_diagnostics else ("none",)
        best_value = float("-inf")
        best_policy = None
        for diag in choices:
            groups: dict[str, list[tuple[str, float]]] = {}
            for cause, prior in cycle["causePrior"].items():
                groups.setdefault(observation(diag, cause), []).append((cause, float(prior)))

            total = -DIAG_COST if diag != "none" else 0.0
            action_by_observation = {}
            for obs, members in groups.items():
                p_obs = sum(p for _, p in members)
                candidate_values = []
                for architecture in ARCH:
                    immediate = sum(
                        (p / p_obs) * float(cycle["rewardByCauseAndArchitecture"][cause][architecture])
                        for cause, p in members
                    )
                    if previous is not None and architecture != previous:
                        immediate -= switch_cost
                    future, _ = value(i + 1, architecture)
                    candidate_values.append((immediate + future, architecture))
                branch_value, branch_arch = max(candidate_values)
                total += p_obs * branch_value
                action_by_observation[obs] = branch_arch

            if total > best_value:
                best_value = total
                best_policy = {"diagnostic": diag, "architectureByObservation": action_by_observation}
        return best_value, best_policy

    return value


with_diag = solve(allow_diagnostics=True, switch_cost=SWITCH_COST)
without_diag = solve(allow_diagnostics=False, switch_cost=SWITCH_COST)
zero_switch = solve(allow_diagnostics=True, switch_cost=0.0)

with_value, first_policy = with_diag(0, None)
without_value, _ = without_diag(0, None)
zero_switch_value, _ = zero_switch(0, None)

policies = []
preferred_diags = set()
persistence_changes = []
for i, cycle in enumerate(CYCLES):
    for previous in (None,) + ARCH:
        _, p = with_diag(i, previous)
        _, p0 = zero_switch(i, previous)
        preferred_diags.add(p["diagnostic"])
        if p != p0:
            persistence_changes.append({"cycle": cycle["id"], "previous": previous, "withSwitchCost": p, "zeroSwitchCost": p0})
        policies.append({"cycle": cycle["id"], "previousArchitecture": previous, "policy": p})

no_scan_choices = []
for i, cycle in enumerate(CYCLES):
    _, p = without_diag(i, None)
    no_scan_choices.append(p["architectureByObservation"]["none"])

ambiguous_negative = True
for cycle in CYCLES:
    causes = tuple(cycle["causePrior"].keys())
    for diag in (d for d in DIAGS if d != "none"):
        negative = [cause for cause in causes if observation(diag, cause) == "ok"]
        ambiguous_negative &= len(negative) >= 2

unique_best = True
for cycle in CYCLES:
    for cause, row in cycle["rewardByCauseAndArchitecture"].items():
        top = max(row.values())
        unique_best &= sum(1 for v in row.values() if v == top) == 1

checks = {
    "diagnosisAddsExpectedValue": (with_value - without_value) >= float(D["predeclaredChecks"]["diagnosisAddsExpectedValueMin"]),
    "distinctPreferredDiagnostics": len(preferred_diags) >= int(D["predeclaredChecks"]["distinctPreferredDiagnosticsMin"]),
    "distinctNoScanArchitectureChoicesAcrossCycles": len(set(no_scan_choices)) >= int(D["predeclaredChecks"]["distinctNoScanArchitectureChoicesAcrossCyclesMin"]),
    "persistenceChangesAtLeastOneDecision": bool(persistence_changes),
    "negativeDiagnosticObservationRemainsAmbiguous": ambiguous_negative,
    "uniqueBestArchitecturePerCause": unique_best
}

standing = "SURVIVES_PC01_F0_STRUCTURAL_COMPOSITION" if all(checks.values()) else "FAILS_PC01_F0_STRUCTURAL_COMPOSITION"
out = {
    "schemaVersion": 1,
    "kind": "pc01-causal-works-f0-structural-falsifier",
    "standing": standing,
    "mechanismLibraryModified": False,
    "metrics": {
        "expectedValueWithDiagnostics": with_value,
        "expectedValueWithoutDiagnostics": without_value,
        "diagnosisExpectedValueUplift": with_value - without_value,
        "expectedValueWithZeroSwitchCost": zero_switch_value,
        "preferredDiagnosticsAcrossState": sorted(preferred_diags),
        "noScanArchitectureChoicesAcrossCycles": no_scan_choices,
        "persistenceDecisionChangeCount": len(persistence_changes)
    },
    "firstPolicy": first_policy,
    "checks": checks,
    "persistenceExamples": persistence_changes[:8],
    "policies": policies,
    "boundary": D["boundary"]
}
(ROOT / "evidence").mkdir(parents=True, exist_ok=True)
(ROOT / "evidence" / "structural-falsifier-r1.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
raise SystemExit(0 if standing.startswith("SURVIVES") else 3)
