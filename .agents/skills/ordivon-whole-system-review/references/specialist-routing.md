# Specialist routing

The Whole-System Review is a meta-review and synthesis Skill. It should activate a specialist method only when current evidence creates a concrete question that the specialist can resolve.

| Trigger | Route | What it must return |
| --- | --- | --- |
| system boundary / external actor / lifecycle ownership unclear | `systems-engineering` | boundary, interfaces, lifecycle-sensitive concerns |
| decomposition has hubs/cycles/suspicious coupling | `design-structure-matrix` | structural dependency/coupling evidence |
| replacement or independent composition depends on assumptions/guarantees | `compositional-contracts` | compatibility/replacement obligations |
| concrete component/process failure propagation matters | `fmea-fta` | failure modes/top events/mitigations |
| unacceptable loss may occur despite locally correct components | `stpa` | unsafe control interactions/constraints |
| authority/data/evidence may cross boundaries incorrectly | `information-flow-analysis` | flow/boundary violations and controls |
| subsystem must be reduced to transferable kernel | `project-kernel-decomposition` | owner/state/flow/protocol/failure decomposition |
| security trust boundary materially changed | repository-grounded threat-model method | assets, boundaries, abuse paths, mitigations |
| major implementation/release candidate changed | SHA-bounded independent code review | findings tied to exact base/head and requirements |
| real incident / response-loss / reconciliation fracture | incident/postmortem/root-cause workflow | timeline, causal mechanism, contributing factors, corrective controls |
| custom-vs-external substitution decision | bounded external research | current primary contracts, alternatives, adoption consequences |

## Routing rules

1. Do not route merely because a method name sounds relevant.
2. State the question each specialist must answer and its stop condition.
3. Prefer one specialist; add another only if it answers a materially different question.
4. Keep evidence boundaries intact. A threat model does not prove runtime failure; a code review does not prove deployment; an external provider document does not prove adoption.
5. Synthesize returned findings into the ReviewRecord; do not copy entire specialist reports into the weekly human briefing.
6. If a specialist Skill is unavailable, mark the question unresolved rather than improvising a weaker method and presenting it as equivalent.
