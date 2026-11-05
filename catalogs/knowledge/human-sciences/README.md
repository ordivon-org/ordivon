# Human Sciences — reusable domain map R1

**SourceCut:** `edc1a81f82a4e0bc46b2f26a796a217af62edf1e` · **Evidence boundary:** 2026-11-05 · **Standing:** curated question/construct map, **not** an admitted Study or validated causal model.

This catalog serves cross-disciplinary questions about physiology, motor control, perception, body ownership, cognition, affect, intimacy, social norms and autonomous consent. It represents **research constructs**, not interchangeable parts of a person. Cross-level links are hypotheses, not proven causal edges. A biological explanation never by itself establishes psychological motives, consent or social meaning.

The machine-readable source is [construct-map-r1.json](construct-map-r1.json), with **11 constructs, 8 candidate bridges, 6 scoped research questions, 8 official method/source references**. Each question records method candidates, rival explanations, and how participant contact would have to be evaluated. No participant data are collected or stored here.

## Contract and separation of responsibility

| Layer | Canonical owner | Role |
| --- | --- | --- |
| Knowledge representation | `catalogs/knowledge/` (this repository) | Concepts, boundaries, question candidates, standards and source pointers |
| Study policy and admission | Independent `ordivon-research-v2` Study Birth | Legitimate study identity, protocol, sources, evidence and scientific acceptance |
| Study-specific materials/data | The admitted Study | Input datasets, observations, analysis and provenance |
| Generic execution | Ordivon Runtime | Job/Workspace/Artifact mechanical truth |
| Coordination | Ordivon Host | Work, Space, Topic; not scientific truth |

### Scientific method routing

- **NIMH RDoC:** multiple units of analysis for constructs in emotion, cognition, motivation, perception and social functioning. Do not convert its domain matrix into an exhaustive human ontology.
- **WHO ICF:** functioning, activities and participation in environmental context. Preserve disability-inclusive, non-deficit descriptions.
- **APA JARS:** reporting guidance for actual quantitative, qualitative or mixed-method studies.
- **BIDS:** apply only to compatible neuroimaging/behavioral/physiological datasets; not a universal directory rule.
- **FAIR:** ensure that source and data provenance supports findability, interoperability and reuse.
- **W3C PROV-O / RO-Crate:** bind these only to a real scientific provenance interchange or Study packaging consumer.
- **Belmont:** any human-participant proposal must respect informed consent, independent ethics review as applicable and an uncompromised right to withdraw. Studying coercion **must not** introduce real coercion.

Read the catalog without importing custom software:

```bash
python3 -c 'import json; from pathlib import Path; d=json.loads(Path("catalogs/knowledge/human-sciences/construct-map-r1.json").read_text()); print([(q["id"], q["constructIds"]) for q in d["questions"]])'
```

## Method for a new question

1. **Bound the construct:** choose a population, setting, time horizon and relevant dimensions; distinguish subjective report, body state, observed behavior and social power.
2. **Separate evidence types:** descriptive vs associational vs causal vs mechanistic. Preserve competing explanations and measurement validity.
3. **Choose mature research methods:** literature synthesis, permitted de-identified secondary data, or ethics-reviewed low-risk voluntary studies. A fictional adult vignette measures responses to scenarios, not reactions to experienced violence.
4. **Admit any actual Study with the existing Research owner.** Reuse available hypothesis-generation, experimental-design, literature-review and causal methods Skills rather than introducing another orchestration/registry/ontology implementation.
5. **Record failures and unknowns:** a plausible mechanism is not a finding; a voluntary public act is not equivalent to pressured behavior; a physiological response is never consent.

## Data hygiene and retirement

The 2026-11-05 initial inspection found no dedicated human-sciences tracked corpus in the monorepo or Research-v2. Research-v2 `HUMAN_*` records concerned human decisions/submission handoffs, not this research topic. There was therefore **no justified topical deletion**. Leave old paper and scientific provenance carriers under their existing Owners. Delete a future generated derivative/cache when its real consumer is gone and exact source reconstruction is possible; retain source data and obligations until their disposition is established. Git history is sufficient for superseded explanatory drafts, but **not** a substitute for unique unpublished research data.

Do not spin up a human-sciences executor, independent LEGO registry or universal theory engine. The first consumer is the research question, and the scientific evidence remains at its natural source.
