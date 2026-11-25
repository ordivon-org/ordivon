"""Differential oracle for the shared CRRA power mean, independent of SciPy."""
from decimal import Decimal, localcontext

import pytest

from ordivon_capital.portfolio.crra_numeric import certainty_equivalent
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError


def _oracle(wealth, probabilities, gamma):
    with localcontext() as context:
        context.prec = 100
        w = [Decimal.from_float(float(x)) for x in wealth]
        p = [Decimal.from_float(float(x)) for x in probabilities]
        a = 1 - Decimal.from_float(float(gamma))
        total = sum(p)
        if a == 0:
            return float((sum(q * x.ln() for q, x in zip(p, w, strict=True)) / total).exp())
        moment = sum(q * (a * x.ln()).exp() for q, x in zip(p, w, strict=True)) / total
        return float((moment.ln() / a).exp())


@pytest.mark.parametrize("gamma", (
    0.01, .5, .9999999999999999, 1., 1.0000000000000002, 1+1e-12, 2., 100., 1000.,
))
@pytest.mark.parametrize(("wealth", "probabilities"), (
    ((.1, 1.5), (.4, .6)),
    ((1e-200, 1e200), (.2, .8)),
    ((.5, .5), (.50000000002, .5)),
    ((.1, 1.5, 3.), (.1, .3, .60000000002)),
))
def test_certainty_equivalent_matches_high_precision_power_mean(wealth, probabilities, gamma):
    result = certainty_equivalent(wealth, probabilities, gamma)
    reference = _oracle(wealth, probabilities, gamma)
    assert min(wealth) <= result <= max(wealth)
    assert result == pytest.approx(reference, rel=2e-12, abs=0)


@pytest.mark.parametrize(("wealth", "probabilities", "gamma"), (
    ((0., 1.), (.5, .5), 1.),
    ((float("inf"), 1.), (.5, .5), 1.),
    ((1., 2.), (.5, float("nan")), 1.),
    ((1., 2.), (.5, .4), 1.),
    ((1.,), (1.00000000001,), 1.),
    ((1., 2.), (.5, .5), True),
))
def test_invalid_power_mean_fails_as_domain_error(wealth, probabilities, gamma):
    with pytest.raises(AlgebraicPolicyError):
        certainty_equivalent(wealth, probabilities, gamma)
