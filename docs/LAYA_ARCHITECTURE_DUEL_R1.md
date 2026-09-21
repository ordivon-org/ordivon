# Laya Architecture Duel R1

## Question

Which architecture should own high-cardinality candidate selection after local Laya evidence showed
token-budget collapse, fixed-position attractors, and overconfident wrong listwise choices?

## Responsibility decomposition

1. Candidate generation: reduce the raw universe without losing the target.
2. Candidate representation: represent each candidate without sharing a shrinking token budget.
3. Query-candidate interaction: estimate relevance between the goal/state and each candidate.
4. Cross-candidate interaction: use interactions only when they are semantically necessary.
5. Ranking: order candidates under a query group.
6. Calibration/selective decision: decide whether the ranking is safe enough to act on.
7. Execution: freshness and mutation remain outside the ranking model.

## Local falsification result

The same exact Laya checkpoint was evaluated in two representations on a synthetic target-selection
task.

### Listwise single-sequence representation

All K options share one sequence and one head budget. Accuracy collapses at larger K; increasing
max_len/head_max_len removes the hard execution ceiling but does not restore reliable choice.

### Independent binary candidate scoring

Each candidate receives its own binary typed question and candidates are ranked by the resulting
true probability. No weights were changed.

Observed accuracy:

| K | Accuracy | Median latency |
|---:|---:|---:|
| 20 | 1.0000 | 59.843 ms |
| 50 | 1.0000 | 145.930 ms |
| 77 | 1.0000 | 235.295 ms |
| 100 | 0.8889 | 302.055 ms |
| 150 | 0.9000 | 469.433 ms |
| 200 | 1.0000 | 628.181 ms |

This synthetic result does not establish browser-task reliability. It does establish a strong
mechanistic signal: changing representation alone largely removes the observed cardinality
collapse and fixed-position attractor without retraining the encoder.

## External mature architecture candidates

### Bi-encoder retrieval

Owns candidate generation. Query and candidates receive reusable vector representations; similarity
search is cheap and may be backed by mature ANN infrastructure such as Faiss.

### Cross-encoder reranking

Owns high-quality query-candidate interaction. Each pair is jointly encoded and receives one score.
It avoids a shared option token budget and option-position competition, but cost scales with the
number of pairs.

### Retrieve then rerank

Primary candidate for Ordivon. A cheap deterministic/bi-encoder stage reduces the candidate set,
then a cross-encoder or independent Laya binary scorer reranks the surviving top-k.

### Late interaction

ColBERT-like systems independently encode query and candidate token representations, then use a
cheap fine-grained interaction. Valuable when collections are persistent and candidate
representations can be indexed/reused.

### Deep Sets / Set Transformer

Architecturally relevant where the result truly depends on interactions among an unordered set.
They directly model permutation invariance/equivariance. They are not the default first choice for
independent query-candidate relevance because retrieve/rerank has a much more mature IR ecosystem.

### Learning-to-rank

XGBoost/LambdaMART is relevant after stable candidate features exist. It can combine lexical,
semantic, DOM, provenance, visibility and policy features at query-group level, but it does not
replace semantic candidate representation.

## R1 standing

For browser-like target selection:

deterministic pruning -> retriever -> independent reranker -> calibration/selective gate

is the primary architecture to falsify next.

Set-specific architectures remain research alternatives, not the default implementation.

For Opportunity discovery over persistent corpora:

embedding/lexical retrieval -> ANN index -> reranker -> strong reasoning

is the stronger mature baseline.

Laya's original listwise dynamic-option head remains admissible only for small answer spaces until
new evidence changes that standing.
