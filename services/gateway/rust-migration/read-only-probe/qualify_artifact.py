"""Bounded differential for the native pure Artifact inventory receiver."""

from __future__ import annotations

import ast
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def add_artifact_cases(add):
    # The existing receiver's nested pure functions are the source oracle.
    # No calls to job.observe (which may dispatch) are made by this qualifier.
    source = ROOT / "src/ordivon_gateway/capabilities/execution/observations.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    names = {"artifact_ids", "identities_complete"}
    functions = [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert len(functions) == len(names)
    scope = {"Any": Any}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), scope)
    artifact_ids, identities_complete = (scope[n] for n in ("artifact_ids", "identities_complete"))

    def case(payload, count):
        ids, qualified = artifact_ids(payload)
        # The native JSON integer domain is u64, not arbitrary Python ints.
        complete = (
            identities_complete(ids, count, qualified)
            if type(count) is int and 0 <= count <= 2**64 - 1
            else None
        )
        add(
            "artifact_inventory",
            {"payload": payload, "count": count},
            {"ids": ids, "qualified": qualified, "complete": complete},
        )

    rng = random.Random(20261126)
    rows = [
        None,
        False,
        {},
        [],
        *(
            {"artifactId": v}
            for v in (
                None,
                1,
                "",
                " \u001c\u001f",
                "\u0085",
                "\u2003",
                "\u200b",
                "a",
                " a ",
                "汉字",
                "é",
                "e\u0301",
                "b",
            )
        ),
    ]
    counts = [None, True, False, 0, 1, 2, 3, 4, 8, 16, -1, 0.0, "0", 2**64 - 1, 2**64]
    for payload in (
        {},
        {"artifacts": None},
        {"artifacts": {}},
        {"artifacts": []},
        {"artifacts": [{"artifactId": "a"}, {"artifactId": "a"}]},
    ):
        for count in counts:
            case(payload, count)
    for _ in range(2000):
        case(
            {"artifacts": [rng.choice(rows) for _ in range(rng.randrange(16))]},
            rng.choice(counts),
        )
    # Synthetic shape of the native producer's five common descriptors.
    case(
        {
            "artifacts": [
                {"artifactId": f"attempt-id.{k}"}
                for k in (
                    "resource-receipt",
                    "result",
                    "stderr",
                    "stdout",
                    "workspace-source-observation",
                )
            ]
        },
        5,
    )
