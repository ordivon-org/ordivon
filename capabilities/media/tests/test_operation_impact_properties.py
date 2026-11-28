"""Generated physical-byte graphs, checked against independent reachability."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from hypothesis import example, given, settings
from hypothesis import strategies as st

from ordivon_studio.operation_impact import project_operation_impact


@st.composite
def graph_cases(draw):
    n = draw(st.integers(min_value=1, max_value=10))
    parents = [
        sorted(draw(st.sets(st.integers(min_value=0, max_value=i - 1))))
        if i else []
        for i in range(n)
    ]
    states = draw(st.lists(st.sampled_from(("match", "missing", "drift")), min_size=n, max_size=n))
    permutation = draw(st.permutations(tuple(range(n))))
    return parents, states, permutation


def reference_impact(parents, states, i):
    # Independent transitive closure, deliberately no topological evaluator
    # or production standing function.
    ancestors = {i}
    while True:
        expanded = ancestors | {p for node in ancestors for p in parents[node]}
        if expanded == ancestors:
            break
        ancestors = expanded
    if any(states[node] == "drift" for node in ancestors):
        return "REVALIDATE_REQUIRED"
    if any(states[node] == "missing" for node in ancestors):
        return "UNKNOWN_UPSTREAM"
    return "NO_BYTE_DRIFT_OBSERVED"


class OperationImpactProperties(unittest.TestCase):
    @settings(max_examples=120, deadline=None, derandomize=True, database=None)
    @given(graph_cases())
    @example(([[], [], [0, 1]], ["missing", "drift", "match"], (2, 1, 0)))
    @example(([[], [0], []], ["missing", "match", "match"], (1, 2, 0)))
    @example(([[], [0], [0], [1, 2]], ["drift", "match", "match", "match"], (3, 1, 2, 0)))
    def test_physical_graph_matches_independent_ancestor_oracle(self, case):
        parents, states, permutation = case
        n = len(parents)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            operations = []
            refs = []
            for i, state in enumerate(states):
                content = f"source bytes {i}".encode()
                source = f"source-{i}.bin"
                carrier = f"carrier-{i}.bin"
                expected = "sha256:" + hashlib.sha256(content).hexdigest()
                refs.append({"path": carrier, "digest": expected})
                (root / carrier).write_bytes(content)
                if state != "missing":
                    (root / source).write_bytes(content if state == "match" else b"changed")
                operations.append({
                    "id": f"step-{i}", "dependsOn": [f"step-{p}" for p in parents[i]],
                    "toolFamily": "fixture", "inputFiles": [
                        {"path": source, "digest": expected}, *[refs[p] for p in parents[i]],
                    ],
                    "retainedFile": refs[i], "outputIds": [],
                })
            production = {
                "id": "generated", "sources": {"sourceDocuments": ["operation-lineage.json"]},
                "outputs": [],
            }
            expected = {f"step-{i}": reference_impact(parents, states, i) for i in range(n)}
            projections = []
            for order in (range(n), permutation):
                manifest = {"schemaVersion": 1, "kind": "ordivon.media.operation-lineage",
                            "productionId": "generated",
                            "operations": [operations[i] for i in order]}
                raw = json.dumps(manifest).encode()
                (root / "operation-lineage.json").write_bytes(raw)
                result = project_operation_impact(root, production, [])
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result["sourceManifestSha256"], "sha256:" + hashlib.sha256(raw).hexdigest())
                rows = {row["stepId"]: row for row in result["steps"]}
                observed = {key: row["impactStanding"] for key, row in rows.items()}
                self.assertEqual(observed, expected)
                self.assertEqual(set(result["revalidateStepIds"]),
                                 {k for k, v in expected.items() if v == "REVALIDATE_REQUIRED"})
                self.assertEqual(set(result["unresolvedStepIds"]),
                                 {k for k, v in expected.items() if v == "UNKNOWN_UPSTREAM"})
                self.assertFalse(result["cacheReuseAuthorized"])
                self.assertFalse(result["executionOrPublicationAuthorized"])
                for row in rows.values():
                    self.assertFalse(row["cacheReuseAuthorized"])
                    self.assertIsNone(row["actionKey"])
                    self.assertEqual(row["toolAndEnvironmentQualification"], "UNKNOWN")
                projections.append(observed)
            self.assertEqual(projections[0], projections[1])
