"""Untrusted dual input must be bounded before materialization."""

import pytest

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.optimality_evidence import certify_canonical_gap
from ordivon_capital.portfolio.witness_repair import repair_canonical_witness


def contract():
    return MultistageProblem(
        2.0,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(1.125,),
                cash_gross=1.0,
                debt_gross=1.1,
                maintenance=(0.3,),
                terminal=True,
            ),
        ),
    )


class BoundedProbe:
    """Seven values suffice to disprove six-coordinate input."""

    def __init__(self):
        self.count = 0

    def __iter__(self):
        while True:
            self.count += 1
            if self.count > 7:
                raise AssertionError("consumed beyond expected dimension + 1")
            yield 0.0


def test_certifier_rejects_overlong_proposal_before_consuming_it():
    y = BoundedProbe()
    result = certify_canonical_gap(contract(), {"root": (0.5,)}, y, (0.0,), 0.0)
    assert result.reason == "MALFORMED_DUAL_PROPOSAL"
    assert result.certified_canonical_gap_upper is None
    assert y.count == 7


def test_repair_rejects_overlong_proposal_without_unbounded_freeze():
    y = BoundedProbe()
    result = repair_canonical_witness(
        contract(), {"root": (1.0000000000000002,)}, y, (0.0,), 0.0, max_change_r=2**-40
    )
    assert result.standing == "UNKNOWN"
    assert result.canonical_evidence is None
    assert y.count == 7


@pytest.mark.parametrize("bad", [(False,) * 6, ("0",) * 6, (float("nan"),) * 6, (0.0,) * 5])
def test_malformed_dual_coordinates_cannot_receive_certificate(bad):
    result = certify_canonical_gap(contract(), {"root": (0.5,)}, bad, (0.0,), 0.0)
    assert result.reason == "MALFORMED_DUAL_PROPOSAL"
    assert result.certified_canonical_gap_upper is None


@pytest.mark.parametrize(
    "bad", [bytes(6), bytearray(6), dict.fromkeys(range(6), 0.0), set(range(6))]
)
def test_noncoordinate_iterables_are_not_a_dual_vector(bad):
    result = certify_canonical_gap(contract(), {"root": (0.5,)}, bad, (0.0,), 0.0)
    assert result.reason == "MALFORMED_DUAL_PROPOSAL"


def test_exact_finite_iterators_are_replayed_without_changing_receipt():
    from ordivon_capital.portfolio.optimality_evidence import verify_canonical_gap_claim

    p = contract()
    raw = {"root": (0.5,)}
    baseline = certify_canonical_gap(p, raw, (0.0,) * 6, (0.0,), 0.0)
    observed = certify_canonical_gap(p, raw, (v for v in (0.0,) * 6), (v for v in (0.0,)), 0.0)
    assert observed == baseline
    assert verify_canonical_gap_claim(p, raw, observed)


def test_admission_dimension_matches_independent_sparse_compiler():
    from ordivon_capital.portfolio.constraint_compiler import compile_multistage_constraints
    from ordivon_capital.portfolio.optimality_evidence import proof_dual_dimensions

    # Cover varying asset counts, fanouts and decision depths, including
    # nonbinary trees. No assumption of a full binary tree in the budget.
    for assets in (1, 2, 4):
        for fanout, depth in ((1, 3), (2, 3), (3, 2), (3, 3), (2, 5)):
            nodes = [
                InformationNode(
                    "root",
                    None,
                    0,
                    1.0,
                    initial_margin=(0.8,) * assets,
                    turnover_cost=(0.001,) * assets,
                )
            ]
            level = ["root"]
            for t in range(1, depth + 1):
                nxt = []
                for parent in level:
                    for i in range(fanout):
                        key = f"{parent}:{i}"
                        term = t == depth
                        nodes.append(
                            InformationNode(
                                key,
                                parent,
                                t,
                                1.0 / fanout,
                                risky_gross=(1.01 + i * 0.01,) * assets,
                                cash_gross=1.0,
                                debt_gross=1.01,
                                maintenance=(0.3,) * assets,
                                initial_margin=() if term else (0.8,) * assets,
                                turnover_cost=() if term else (0.001,) * assets,
                                terminal=term,
                                observed_label=str(i),
                            )
                        )
                        nxt.append(key)
                level = nxt
            compiled = compile_multistage_constraints(MultistageProblem(2.0, tuple(nodes)))
            expected = (
                compiled.A_ub.shape[0] + compiled.W_arrival.shape[0] + compiled.W_leaf.shape[0],
                compiled.A_eq.shape[0],
            )
            assert proof_dual_dimensions(compiled.tree) == expected


def test_out_of_scope_repair_never_reads_dual_iterables():
    p = MultistageProblem(
        2.0,
        (
            InformationNode(
                "root", None, 0, 1.0, initial_margin=(1.0,) * 17, turnover_cost=(0.0,) * 17
            ),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(1.125,) * 17,
                cash_gross=1.0,
                debt_gross=1.1,
                maintenance=(0.3,) * 17,
                terminal=True,
            ),
        ),
    )

    class NoRead:
        def __iter__(self):
            raise AssertionError("out of scope must not inspect multipliers")

    x = repair_canonical_witness(
        p, {"root": (0.01,) * 17}, NoRead(), NoRead(), 0.0, max_change_r=1e-12
    )
    assert x.standing == "UNKNOWN"
    assert x.source_evidence.reason == "EXACT_WITNESS_RESOURCE_SCOPE"
