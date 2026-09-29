# Framework stack

The Whole-System Review combines mature methods only where each answers a different question. It is not a blended proprietary methodology and no external framework becomes Ordivon authority.

## SEI ATAM / QAW — architecture consequences

Use for: quality-attribute scenarios, architectural approaches, sensitivity points, tradeoff points, risks/non-risks, and risk themes.

Core question: **Which architectural decisions most strongly affect important quality attributes, and where do attributes conflict?**

Apply scenarios rather than generic checklists. Prefer concrete stimulus/environment/artifact/response/response-measure statements when a measurable response matters. Use normal-use, growth, and exploratory/stress scenarios to expose different risks.

Official references:
- https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/
- https://www.sei.cmu.edu/library/sei-architecture-analysis-techniques-and-when-to-use-them/

## NASA systems engineering — recursive decomposition, interfaces, V&V

Use for: system-of-interest framing, requirement allocation, interface management, technical risk, technical assessment, decision analysis, verification, validation, and milestone entrance/success criteria.

Core question: **Can the whole-system outcome be traced through allocated responsibilities and interfaces to verified implementation and intended-use validation?**

Keep verification and validation separate:
- verification: did the implementation meet the specified contract/requirement?
- validation: does the integrated result accomplish the intended purpose in the intended environment?

Official reference:
- https://www.nasa.gov/reference/systems-engineering-handbook/

## Google SRE Production Readiness / Launch Review — operational reality

Use for: dependencies, monitoring/instrumentation, emergency response, capacity, change management, reliability/performance, failure modes, rollout/rollback, incident/postmortem follow-up, and toil.

Core question: **If this system must be operated and recovered now, what would an on-call owner need to trust, observe, and control?**

For Ordivon, extend this to durable Job identity, response-loss reconciliation, external-effect ambiguity, checkpoint/resume, semantic-completion receipts, and cross-OS authority handoff.

Official references:
- https://sre.google/sre-book/evolving-sre-engagement-model/
- https://sre.google/sre-book/reliable-product-launches/
- https://sre.google/sre-book/launch-checklist/

## DORA — delivery evolution trend

Use for: longitudinal delivery throughput and instability signals, not architecture quality scores.

Core question: **Is the mechanism for safely changing Ordivon becoming faster and more stable over time?**

Current delivery metrics include change lead time, deployment frequency, failed deployment recovery time, change fail rate, and deployment rework rate. Compare Ordivon primarily with its own prior baseline; context matters more than benchmark labels.

Official reference:
- https://dora.dev/guides/dora-metrics/

## C4-style multiscale representation — navigation

Use for: keeping a large system review navigable from system context to macro owner/container and only then to critical components/contracts.

Core question: **At what level must we look to understand this decision without drowning in implementation detail?**

C4 is a representation aid, not architectural truth or a mandatory diagram format.

Reference:
- https://c4model.com/

## Evolutionary architecture fitness functions — continuous guardrails

Use for: converting repeatedly reviewed architectural characteristics into executable feedback mechanisms.

Core question: **Which architectural property can be continuously checked so humans do not have to rediscover the same regression?**

A fitness function should be objective enough to detect drift while remaining narrow enough not to become a universal score.

Reference:
- https://www.thoughtworks.com/insights/books/building-evolutionary-architectures-second-edition

## Ordivon-native synthesis

External methods are subordinate to Ordivon's existing owner/authority/evidence law:

- natural owner remains authoritative for its own state;
- co-location does not merge authority;
- control state, execution state, external effect, observation, evidence, and semantic completion stay distinct;
- reusable method Skills are advisory;
- mature external substrates are preferred over custom replicas;
- UNKNOWN is a valid result when the available evidence cannot establish current truth.
