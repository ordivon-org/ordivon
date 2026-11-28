"""Evolving proof graphs: independent relational oracle, not production worklist."""

from copy import deepcopy

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from ordivon_composition.verification_impact import select_impacted_obligations

ROOTS = ("source:a", "source:b")
PROOFS = ("proof:a", "proof:b", "proof:c", "proof:d")
NODES = ROOTS + PROOFS
OUTSIDE = "source:unindexed"
RANK = ("REUSE_CANDIDATE", "UNKNOWN", "RECHECK_REQUIRED")
DIGESTS = (None, "sha256:" + "1" * 64, "sha256:" + "2" * 64)


def oracle(before, after, changed, unknown):
    """Relational composition over a finite universe; no DFS/SCC/worklist."""
    roots = set(after["authorityRefs"])
    claims = {row["id"]: row for row in after["obligations"]}
    prev_roots = set(before["authorityRefs"])
    prev_claims = {row["id"]: row for row in before["obligations"]}
    nodes = roots | claims.keys()
    previous_nodes = prev_roots | prev_claims.keys()

    def relation(row):
        return None if row is None else (frozenset(row["dependsOn"]), row["dependenciesComplete"])

    relations = roots ^ prev_roots
    contracts = set()
    for key in claims.keys() | prev_claims.keys():
        a, b = prev_claims.get(key), claims.get(key)
        if relation(a) != relation(b):
            relations.add(key)
        if (a or {}).get("obligationDigest") != (b or {}).get("obligationDigest"):
            contracts.add(key)
    changed = set(changed) | relations | contracts
    unknown = set(unknown)
    unindexed = ((changed - (previous_nodes - nodes)) | unknown) - nodes

    reach = {(key, dep) for key, row in claims.items() for dep in row["dependsOn"]}
    for k in sorted(nodes):
        reach |= {(i, j) for i, m in reach for n, j in reach if m == k == n}
    cycles = {key for key in claims if (key, key) in reach}
    incomplete = {key for key, row in claims.items() if not row["dependenciesComplete"]}
    result = {}
    for key in claims:
        dependencies = {key} | {dep for src, dep in reach if src == key}
        result[key] = RANK[
            2
            if dependencies & changed
            else 1
            if unindexed or dependencies & (unknown | incomplete | cycles)
            else 0
        ]
    return result, sorted(cycles), sorted(unindexed), sorted(relations), sorted(contracts)


def snapshot(roots, claims):
    return {
        "authorityRefs": sorted(roots),
        "obligations": [deepcopy(claims[key]) for key in sorted(claims)],
    }


def assert_projection(before, after, changed=(), unknown=()):
    kwargs = dict(
        authority_refs=after["authorityRefs"],
        obligations=after["obligations"],
        previous_graph=before,
        changed_refs=sorted(set(changed)),
        unknown_refs=sorted(set(unknown)),
    )
    actual = select_impacted_obligations(**kwargs)
    expected, cyclic, unindexed, relations, contracts = oracle(before, after, changed, unknown)
    assert {row["id"]: row["standing"] for row in actual["standingByObligation"]} == expected
    assert actual["cyclicObligationIds"] == cyclic
    assert actual["unindexedChangeRefs"] == unindexed
    assert actual["derivedRelationChangedRefs"] == relations
    assert actual["derivedContractChangedRefs"] == contracts
    assert actual["derivedChangedRefs"] == sorted(set(relations) | set(contracts))
    assert actual["proofReuseAdmissible"] is False
    assert actual["proofAcceptanceEstablished"] is False

    # Permutation is semantics-preserving for every set-like input.
    def reversed_graph(graph):
        result = deepcopy(graph)
        result["authorityRefs"].reverse()
        result["obligations"].reverse()
        for row in result["obligations"]:
            row["dependsOn"].reverse()
        return result

    rev = reversed_graph(after)
    assert actual == select_impacted_obligations(
        authority_refs=rev["authorityRefs"],
        obligations=rev["obligations"],
        previous_graph=reversed_graph(before),
        changed_refs=list(reversed(kwargs["changed_refs"])),
        unknown_refs=list(reversed(kwargs["unknown_refs"])),
    )
    return actual


class EvolvingProofGraph(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.roots = set(ROOTS)
        self.claims = {
            key: {"id": key, "dependsOn": [], "dependenciesComplete": True} for key in PROOFS
        }
        self.before = snapshot(self.roots, self.claims)
        self.changed = set()
        self.unknown = set()

    def begin(self):
        self.before = snapshot(self.roots, self.claims)
        self.changed.clear()
        self.unknown.clear()

    @rule(root=st.sampled_from(ROOTS))
    def toggle_root(self, root):
        self.begin()
        if root in self.roots:
            self.roots.remove(root)
            for row in self.claims.values():
                row["dependsOn"] = [dep for dep in row["dependsOn"] if dep != root]
        else:
            self.roots.add(root)

    @rule(proof=st.sampled_from(PROOFS))
    def toggle_proof(self, proof):
        self.begin()
        if proof in self.claims:
            del self.claims[proof]
            for row in self.claims.values():
                row["dependsOn"] = [dep for dep in row["dependsOn"] if dep != proof]
        else:
            self.claims[proof] = {"id": proof, "dependsOn": [], "dependenciesComplete": True}

    @rule(proof=st.sampled_from(PROOFS), dep=st.sampled_from(NODES))
    def toggle_dependency(self, proof, dep):
        self.begin()
        if proof in self.claims and dep in (self.roots | self.claims.keys()):
            deps = set(self.claims[proof]["dependsOn"])
            self.claims[proof]["dependsOn"] = sorted(deps ^ {dep})

    @rule(proof=st.sampled_from(PROOFS), complete=st.booleans(), digest=st.sampled_from(DIGESTS))
    def edit_contract(self, proof, complete, digest):
        self.begin()
        if proof in self.claims:
            row = self.claims[proof]
            row["dependenciesComplete"] = complete
            if digest is None:
                row.pop("obligationDigest", None)
            else:
                row["obligationDigest"] = digest

    @rule(
        changed=st.sets(st.sampled_from(NODES + (OUTSIDE,))),
        unknown=st.sets(st.sampled_from(NODES + (OUTSIDE,))),
    )
    def observe(self, changed, unknown):
        # Keep the actual prior transition: explicit unknown may name a retired node.
        self.changed = changed
        self.unknown = unknown

    @invariant()
    def exact_projection(self):
        assert_projection(
            self.before, snapshot(self.roots, self.claims), self.changed, self.unknown
        )


TestEvolvingProofGraph = EvolvingProofGraph.TestCase
TestEvolvingProofGraph.settings = settings(
    max_examples=100, stateful_step_count=30, deadline=None, derandomize=True
)


@given(
    st.sets(st.sampled_from(NODES)),
    st.sets(st.sampled_from(NODES)),
    st.lists(st.sets(st.sampled_from(NODES)), min_size=4, max_size=4),
)
@settings(max_examples=200, deadline=None, derandomize=True)
def test_more_uncertainty_or_changes_never_reduce_standing(changed, unknown, dependencies):
    graph = {
        "authorityRefs": list(ROOTS),
        "obligations": [
            {"id": proof, "dependsOn": sorted(deps), "dependenciesComplete": True}
            for proof, deps in zip(PROOFS, dependencies, strict=True)
        ],
    }
    before = assert_projection(graph, graph)
    after = assert_projection(graph, graph, changed, unknown)
    for a, b in zip(before["standingByObligation"], after["standingByObligation"], strict=True):
        assert a["id"] == b["id"]
        assert RANK.index(a["standing"]) <= RANK.index(b["standing"])


def test_retired_reference_unknown_is_not_silenced():
    before = {
        "authorityRefs": list(ROOTS),
        "obligations": [
            {"id": "proof:a", "dependsOn": [], "dependenciesComplete": True},
        ],
    }
    after = {**before, "authorityRefs": ["source:a"]}
    assert (
        assert_projection(before, after)["standingByObligation"][0]["standing"] == "REUSE_CANDIDATE"
    )
    assert (
        assert_projection(before, after, unknown=["source:b"])["standingByObligation"][0][
            "standing"
        ]
        == "UNKNOWN"
    )
