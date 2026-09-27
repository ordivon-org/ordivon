# Human output contract

Render the ReviewRecord in three layers. The report is a decision instrument, not a database dump.

## L0 — System Judgment

One screen/page. 5–10 statements that materially change the reader's model of Ordivon.

Each statement should answer at least one:
- capability boundary/pressure changed?
- future reachability expanded or contracted?
- owner/authority/contract boundary changed?
- continuity/recovery standing changed?
- external capability became realizable/substitutable?
- a high-leverage sensitivity/tradeoff moved?
- delivery/recovery constraint became materially better/worse?

Routine refactors and low-impact cleanup do not appear here.

## L1 — Deep Review

Use these sections when material:

1. Review boundary & census confidence
2. Whole-system architecture evolution
3. Capability frontier — REALIZED / LATENT / BLOCKED / DEGRADED / RETIRED
4. Sensitivity points, tradeoffs, architectural risks/non-risks, systemic risk themes
5. Continuity, recovery & production readiness
6. Interfaces, V&V, and intent-vs-reality divergences
7. Evolution/delivery health
8. External substitution / custom-LEGO pressure
9. Next milestone chain — maximum 3, each with dependencies, entrance criteria, success criteria
10. Decisions needed from the user — only genuine stakeholder tradeoffs; include options, consequences, reversibility, and missing evidence

If a major area has no material change, say so briefly rather than manufacturing progress.

## L2 — Evidence Appendix

Include:
- review period and exact source revision/range;
- available owner surfaces and observation times;
- key evidence/receipt/test/contract locators;
- evidence freshness limitations;
- explicit UNKNOWNs;
- specialist reviews invoked and their scope.

Do not dump raw logs or every changed file.

## Writing rules

- Separate fact/evidence from inference and diagnosis.
- Prefer causal mechanisms and dependency chains over task lists.
- Risk themes describe systemic causes, not collections of TODOs.
- Do not use pseudo-precise architecture scores.
- Avoid declaring "healthy" when only code/tests were observed.
- User decisions should never be questions that more engineering investigation can answer without stakeholder preference.
