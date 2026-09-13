# Atlas retrieval application retirement

Date: 2026-09-14

Harness no longer carries a current Atlas research-start application or Atlas multilingual dogfood script. The actual packaged Atlas runtime bridge had already been retired on 2026-09-09; the remaining scripts were standalone, uninstalled experimental/application surfaces with no Harness package API, CLI, README, or Quickstart exposure.

Atlas `first-look` provided bounded lexical substring/path matching over generated projections and curated synthesis. It did not provide semantic retrieval, translation, query expansion, novelty adjudication, or research admission. Maintaining a dedicated federated-currentness owner solely to preserve that application would duplicate generic source search/retrieval and the current Research capability's mature literature/evidence stack.

Historical Atlas/Harness experiments remain recoverable in Git. For current work, use owner-native repositories plus generic source search for local prior work, and `ordivon-research-v2` with its mature literature/evidence providers for scientific prior art. Reintroduce a specialized retrieval adapter only when a real workload proves a gap that generic search and current Research tooling cannot satisfy.
