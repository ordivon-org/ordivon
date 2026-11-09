#!/usr/bin/env python3
"""Network-specific source refinement plus bounded SMT safety proof.

The accepted consumer contract is anchored to an immutable published Git
commit. Candidate manifests are untrusted. This is a *source* check, not a
tool-effect permission, a domain acceptance record or a proof of physical VPN
behavior. GitHub protected-branch checks/review must protect this checker.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    "platform/network/acceptance/lifecycle/shared-forward-reload-circuit-r1.json"
)
ACCEPTED_CUT = "b7d64d103cf67242cbd1609e5c7df729fc187d45"
REQUIRED = frozenset(
    {"gate:forward-source-installed", "gate:loaded-unit-native-effect"}
)
SEAM_FIELDS = (
    "producerStageId",
    "consumerStageId",
    "assumption",
    "guarantee",
    "verifierOwnerId",
    "supportScope",
    "required",
)


class ContractNotRefined(ValueError):
    """Source candidate cannot be shown to retain accepted consumer duties."""


def _git(*args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(REPO), *args],
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ContractNotRefined(
            "accepted immutable Git SourceCut unavailable"
        ) from exc


def accepted_manifest() -> dict[str, Any]:
    """Read original accepted regular Git blob, never candidate/worktree bytes."""
    if _git("cat-file", "-t", ACCEPTED_CUT).strip() != b"commit":
        raise ContractNotRefined("accepted SourceCut must be a commit")
    try:
        _git("merge-base", "--is-ancestor", ACCEPTED_CUT, "HEAD")
    except ContractNotRefined as exc:
        raise ContractNotRefined(
            "frozen pilot cut is not in candidate history"
        ) from exc
    entries = [
        part
        for part in _git("ls-tree", "-z", ACCEPTED_CUT, "--", CONTRACT_PATH).split(
            b"\x00"
        )
        if part
    ]
    if len(entries) != 1:
        raise ContractNotRefined("expected one immutable contract blob")
    try:
        mode_type_blob, path = entries[0].split(b"\t", 1)
        mode, kind, _blob = mode_type_blob.split(b" ", 2)
    except ValueError as exc:
        raise ContractNotRefined("unexpected Git contract tree entry") from exc
    if (
        mode not in {b"100644", b"100755"}
        or kind != b"blob"
        or path.decode() != CONTRACT_PATH
    ):
        raise ContractNotRefined("accepted contract must be a regular Git blob")
    try:
        baseline = json.loads(
            _git("cat-file", "blob", ACCEPTED_CUT + ":" + CONTRACT_PATH)
        )
    except (ValueError, UnicodeDecodeError) as exc:
        raise ContractNotRefined("invalid accepted JSON contract") from exc
    return baseline


def required_gates(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("gateRequirements")
    if not isinstance(rows, list):
        raise ContractNotRefined("gateRequirements must be a list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ContractNotRefined("invalid candidate Gate")
        if row["id"] in result:
            raise ContractNotRefined("duplicate Gate identity")
        result[row["id"]] = row
    return {name: row for name, row in result.items() if row.get("required") is True}


def assert_consumer_refinement(
    accepted: dict[str, Any], candidate: dict[str, Any]
) -> tuple[str, ...]:
    """Preserve original required duties; extensions may add independent duties.

    This task-local rule is deliberately strict: modifying inherited
    assumptions/guarantees requires a separately adopted successor contract.
    """
    before, after = required_gates(accepted), required_gates(candidate)
    if frozenset(before) != REQUIRED:
        raise ContractNotRefined(
            "original accepted consumer Gate set unexpectedly changed"
        )
    if not set(before).issubset(after):
        raise ContractNotRefined("candidate removed or made optional an accepted Gate")
    for name, original in before.items():
        new = after[name]
        if any(original.get(field) != new.get(field) for field in SEAM_FIELDS):
            raise ContractNotRefined(
                "candidate changed accepted Gate contract: " + name
            )
    if accepted.get("circuitId") != candidate.get("circuitId"):
        raise ContractNotRefined("candidate changed accepted circuit identity")
    return tuple(sorted(before))


def _smt_and(parts: list[str]) -> str:
    return "(and " + " ".join(parts) + ")" if parts else "true"


def _z3_check(lines: list[str]) -> str:
    """Run the centrally pinned, existing Z3 5.3.2 CLI; never download a solver."""
    mise = shutil.which("mise")
    if not mise:
        raise ContractNotRefined("mise unavailable for pinned upstream Z3")
    try:
        binary = subprocess.check_output(
            [mise, "-C", str(REPO / "tools/formal"), "which", "z3"],
            text=True,
            stderr=subprocess.PIPE,
            timeout=12,
        ).strip()
        process = subprocess.run(
            [binary, "-in", "-smt2"],
            input="\n".join(lines + ["(check-sat)"]) + "\n",
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ContractNotRefined("pinned native Z3 executable unavailable") from exc
    results = process.stdout.strip().splitlines()
    if process.returncode or results not in (["sat"], ["unsat"]):
        raise ContractNotRefined(
            f"Z3 did not return one unambiguous satisfiability result: "
            f"{process.stdout[-200:]!r} {process.stderr[-200:]!r}"
        )
    return results[0]


def _prove_abstract_acceptance_law(names: tuple[str, ...]) -> dict[str, Any]:
    """Exhaustive symbolic finite obligation law with independent negative controls.

    Only the read model is proved. The candidate manifest is checked against
    a frozen Git source independently and existing Composition APIs are tested
    separately. Neither is an installed-effect/domain-acceptance theorem.
    """
    if not names:
        raise ContractNotRefined("nonvacuous consumer obligation set required")
    declared = ["(declare-const consumed Bool)"]
    atoms: list[str] = []
    for i, _name in enumerate(names):
        declared += [
            f"(declare-const included_{i} Bool)",
            f"(declare-const status_{i} Int)",  # 0 UNKNOWN, 1 UNSAT, 2 SAT
            f"(declare-const fresh_{i} Bool)",
            f"(declare-const owner_{i} Bool)",
            f"(declare-const scope_{i} Bool)",
            f"(assert (and (<= 0 status_{i}) (<= status_{i} 2)))",
        ]
        atoms.append(
            _smt_and(
                [
                    f"included_{i}",
                    f"(= status_{i} 2)",
                    f"fresh_{i}",
                    f"owner_{i}",
                    f"scope_{i}",
                ]
            )
        )

    independent = _smt_and(["consumed", *atoms])
    failure = (
        "(or " + " ".join(["(not consumed)", *[f"(not {a})" for a in atoms]]) + ")"
    )
    if (
        _z3_check([*declared, f"(assert {independent})", f"(assert {failure})"])
        != "unsat"
    ):
        raise ContractNotRefined("independent consumer safety property not established")

    # A candidate that drops one required Gate can mechanically pass its
    # reduced gate list, but cannot satisfy the frozen consumer obligations.
    removed = 0
    positive_conditions = ["(assert consumed)", "(assert (not included_0))"]
    for i in range(len(names)):
        positive_conditions += [
            f"(assert (= status_{i} 2))",
            f"(assert fresh_{i})",
            f"(assert owner_{i})",
            f"(assert scope_{i})",
        ]
        if i != removed:
            positive_conditions.append(f"(assert included_{i})")
    weak_candidate = _smt_and(
        ["consumed"]
        + [
            f"(=> included_{i} {_smt_and([f'(= status_{i} 2)', f'fresh_{i}', f'owner_{i}', f'scope_{i}'])})"
            for i in range(len(names))
        ]
    )
    if (
        _z3_check(
            [
                *declared,
                *positive_conditions,
                f"(assert {weak_candidate})",
                f"(assert (not {independent}))",
            ]
        )
        != "sat"
    ):
        raise ContractNotRefined(
            "removed-Gate false-acceptance negative control unreachable"
        )

    # UNKNOWN, wrong verifier owner or stale evidence each independently
    # prevent the full originally required consumer acceptance.
    for field, assertion in (
        ("unknown", "(assert (= status_0 0))"),
        ("wrong-owner", "(assert (not owner_0))"),
        ("stale-evidence", "(assert (not fresh_0))"),
        ("widened-scope", "(assert (not scope_0))"),
    ):
        if _z3_check([*declared, assertion, f"(assert {independent})"]) != "unsat":
            raise ContractNotRefined("unsafe abstract acceptance with " + field)
    return {
        "standing": "BOUNDED_ABSTRACT_SAFETY_PROVED",
        "acceptedGateCount": len(names),
        "removedGateCounterexample": "REACHABLE",
        "unknownWrongOwnerStaleScopeCounterexamples": "REJECTED",
        "domainAcceptanceEstablished": False,
        "nonClaims": [
            "SMT proves the named predicate under finite typed Gate identities only.",
            "Immutable original Git bytes are a source baseline, not independent approval.",
            "Source refinement, live installed provider, and consumer acceptance are separate.",
        ],
    }


def prove(
    accepted: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    original = accepted if accepted is not None else accepted_manifest()
    proposed = (
        candidate
        if candidate is not None
        else json.loads((REPO / CONTRACT_PATH).read_text(encoding="utf-8"))
    )
    names = assert_consumer_refinement(original, proposed)
    result = _prove_abstract_acceptance_law(names)
    return {
        "kind": "ordivon.network.outcome-contract-refinement",
        "truthRole": "source-and-bounded-model-only-not-domain-acceptance",
        "acceptedGitCut": ACCEPTED_CUT,
        "contractPath": CONTRACT_PATH,
        **result,
    }


def negative_controls() -> None:
    original = accepted_manifest()
    assert_consumer_refinement(original, original)
    for mutation in ("remove", "optional", "owner", "scope", "guarantee", "identity"):
        altered = copy.deepcopy(original)
        row = altered["gateRequirements"][0]
        if mutation == "remove":
            altered["gateRequirements"].pop(0)
        elif mutation == "optional":
            row["required"] = False
        elif mutation == "owner":
            row["verifierOwnerId"] = "harness"
        elif mutation == "scope":
            row["supportScope"] = "all-network-consumers"
        elif mutation == "guarantee":
            row["guarantee"] = "some systemd process exists"
        else:
            altered["circuitId"] = "circuit:wrong-subject"
        try:
            assert_consumer_refinement(original, altered)
        except ContractNotRefined:
            continue
        raise ContractNotRefined("negative control escaped acceptance: " + mutation)


def main() -> int:
    try:
        result = prove()
        negative_controls()
    except (OSError, ValueError) as exc:
        print(
            json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}), file=sys.stderr
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
