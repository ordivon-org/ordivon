# Research Skill Expansion R1

Date: 2026-09-19
Status: **PASS — EXPAND BY FIVE AUDITED SKILLS; KEEP DEMAND-DRIVEN INTAKE**

## Why this changed

The 2026-09-13 local capability pack deliberately selected a minimal research surface. Paper-1 later exposed composition gaps between literature discovery, citation integrity, hypothesis/rival construction, evidence criticism, and pre-analysis data auditing. The correction is to consume mature Agent Skills directly rather than invent Paper-1-specific replacements or bulk-install an entire collection.

## Upstream subject

- Repository: `K-Dense-AI/scientific-agent-skills`
- Reviewed/install revision: `330c8e764435a731eff571e3efdda70b363d0792`
- Intake mode: exact-revision staging, package inspection, deterministic static checks, then explicit user-scope installation.
- SkillSpector: **unavailable locally during this intake**. No SkillSpector PASS is claimed.

## Promoted skills

| Skill | Package digest at intake | Research role |
| --- | --- | --- |
| `paper-lookup` | `sha256:f4409b44c4f87bf600a031c841b1f4993cd750880294f4f6b97608f2edc1aed0` | Reproducible scholarly discovery and citation/full-text lookup across supported scholarly APIs. |
| `citation-management` | `sha256:1c1984097dff712c29c7af9199ed850b7302033952e5f22b6a36a13547a53949` | DOI/metadata/BibTeX/reference-integrity work; external metadata remains untrusted until verified. |
| `hypothesis-generation` | `sha256:f5ec7e04d5557a7c3296aa331e468b9dfdf76791ea9f1918fb150c895ea4e962` | Evidence-bounded hypotheses, rival explanations, discriminating predictions, operationalization, and preregistration scaffolds. |
| `scientific-critical-thinking` | `sha256:ae68d60c997e2f2e2306d2aca4179f87ca7bb6327ea777d81dc5dddc172630db` | Bias, confound, construct, evidence-strength, and statistical-pitfall criticism before formal peer-review prose. |
| `exploratory-data-analysis` | `sha256:39b01db61eeed9329579b7bf48f67cf9247a0abe117045e9ca049b52d3cc3dc7` | Bounded local profiling, missingness/leakage checks, outlier and transformation sensitivity, and EDA report scaffolding. |

All staged Python files compiled successfully and no staged package contained a symlink. These checks are bounded supply-chain evidence, not a general safety certification or execution authorization.

## Deferred candidates

| Skill | Decision | Reason |
| --- | --- | --- |
| `research-lookup` | DEFER | Current package depends on Parallel CLI/API; neither `parallel-cli` nor `PARALLEL_API_KEY` is present. `paper-lookup` covers the immediate retrieval gap without adding that provider dependency. |
| `statistical-power` | DEFER | Current base Python lacks the principal SciPy/statsmodels/matplotlib stack and Paper-1 does not presently need a new power-analysis lane. Admit with a pinned analysis environment when a real planning task requires it. |
| `venue-templates` | DEFER | Generic venue assets do not provide an EMSE/Springer-specific authority. Current venue rules must continue to be checked against live official instructions. |

## Literature-review decision

Retain the current lightweight `msimchowitz/writing-skills` literature-review for now. The current K-Dense literature-review was not promoted because its present workflow makes Parallel a primary retrieval dependency, contains mandatory cross-skill AI-figure instructions, and documents an installer path using remote shell execution. The retained lightweight skill still has dependency debt around unavailable `paper-writing` / `general-writing`; that debt should be removed by a later literature-synthesis intake, not hidden.

## Resulting research composition

```text
paper-lookup
    ↓
citation-management
    ↓
literature review / evidence synthesis
    ↓
hypothesis-generation
    ↓
experimental-design
    ↓
exploratory-data-analysis
    ↓
statistical-analysis
    ↓
scientific-visualization
    ↓
scientific-writing
    ↓
scientific-critical-thinking + peer-review
```

This is a composition guide, not an obligatory linear workflow. Skills activate only when the research state needs them.

## Skill MCP bridge admission

The five promoted Codex user skills were added to the deployment `auditedSkillIds` after the bounded intake above. The live bridge preflight passed before restart, and the service restarted successfully.

Post-restart observations:

- catalog revision: `sha256:19c4ee8b0ab234f6cc666c14df8d0dea58bcae75741256fbd90fcda2c54dd096`
- model-visible snapshot revision: `sha256:b93a848140436a4f0056fd939357be62c54e25e090c04477de9a12974ea0dd8b`
- promoted skills are visible as `THIRD_PARTY_AUDITED`
- the deferred candidates were not added to the audited/model-visible set
- `scanState=WARN` remains visible; this intake does not reinterpret WARN as a clean scanner PASS

The bridge remains a temporary compatibility surface. This admission does not create an Ordivon-owned Skill registry, execution authority, or permanent trust oracle.

## Invariants

1. Do not bulk-install the 166-skill upstream catalog.
2. Pin external Skill revisions when trust/reproducibility matters.
3. A repository's reputation does not transfer approval to every Skill or future revision.
4. Network/API/script capability remains task-local execution authority, not instruction authority.
5. Prefer live venue/source authority over static templates.
6. Re-audit on upstream revision change.
