# Schema and numerical primitives qualification R1 — 2026-09-21

## JSON Schema

jsonschema 4.26.0 remains the implementation owner for the two active Draft 2020-12
validation contracts.

The schemas are not mere flat type checks. Together they exercise strict additional-property
control, required properties, constants, enums, string patterns/minimum lengths, allOf,
conditional if/then behavior, and not constraints. A local replacement would therefore be a
partial JSON Schema engine rather than thin domain glue.

Decision: retain jsonschema. Ordivon owns the domain documents and the extra unique-ID
invariant; jsonschema owns standard schema evaluation.

## NumPy

NumPy 2.5.3 is used for ndarray conversion and vector arithmetic, differences, sample
variance, quantiles, means, absolute values, correlation, residual arithmetic, and interval
statistics.

Individual formulas could be recreated, but NumPy is also the common numerical substrate of
SciPy and scikit-learn. Rewriting isolated primitives would neither remove the dependency nor
reduce the trusted surface.

Decision: retain NumPy as the numerical-array primitive owner.

## SciPy

SciPy 1.18.1 owns three active statistical mechanics:

- linregress summaries in dependence observation;
- two-sample KS statistic/p-value mechanics;
- Wasserstein distances.

A local implementation of one regression formula is not contract-equivalent to the active
KS and Wasserstein surface, and SciPy remains a required dependency of scikit-learn.

Decision: retain SciPy as the statistical-primitives owner.

## scikit-learn

scikit-learn 1.9.1 owns:

- LinearRegression;
- HuberRegressor as a robust challenger;
- TimeSeriesSplit including walk-forward/gap mechanics.

A small local ordinary-least-squares formula cannot replace robust Huber optimization and
split semantics. The project has a current CPython 3.14 wheel and PyPI provenance attestation.

Decision: retain scikit-learn as the estimator/validation mechanics owner. Ordivon continues
to own chronology, sample alignment, evidence interpretation, model-use restrictions, and
governance standing.

## Ownership boundary

None of these libraries owns:

- portfolio limits;
- investment recommendation;
- model approval;
- causal interpretation;
- external-write admission;
- provider truth.

They own mechanics only.
