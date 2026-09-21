# Monorepo Source Migration Standing

| Wave | Scope | Standing |
| --- | --- | --- |
| M1 | Next / Security / Network | ACCEPTED_SOURCE_ONLY |
| M2 | Workstation / Media / Artifact | ACCEPTED_SOURCE_ONLY |
| Wave 3 | Game / Capital / Host | ACCEPTED_SOURCE_ONLY |
| Harness | identity-preserving current-source supersession | ACCEPTED_SOURCE_ONLY |
| Skills bridge | extracted from Harness into platform/skills; source/package/artifact owner boundaries accepted; live service cutover pending M7 | ACCEPTED_SOURCE_ONLY |
| Host | exact current source tree; legacy rewritten import bridged to original a95a8e11 identity | ACCEPTED_SOURCE_ONLY |
| Next | legacy-rewritten import bridged to identity-preserving current-source supersession at `5e556869` | ACCEPTED_SOURCE_ONLY |
| Runtime | converged current source at `af67ed76` after `d3613c2e` supersession; repeatable identity-preserving update accepted | ACCEPTED_SOURCE_ONLY |
| Media | standalone main aligned ff-only to accepted `30f6d122`; Media-hosted Creative Library remains an intentional monorepo-only projection overlay | ACCEPTED_SOURCE_ONLY |
| Capital | standalone main aligned ff-only to accepted `918fd86a`; exact standalone and monorepo owner trees now match | ACCEPTED_SOURCE_ONLY |
| Security | legacy rewritten import normalized to exact source tree; original `f5db8508` identity attached | ACCEPTED_SOURCE_ONLY |
| Network | standalone main aligned ff-only to accepted `9aec70bb`; original source identity attached | ACCEPTED_SOURCE_ONLY |
| Distribution | optional effect-safety/profile source | ACCEPTED_SOURCE_ONLY |
| Preservation | standard-native local preservation profile | ACCEPTED_SOURCE_ONLY |
| Creative Library | Media-hosted cross-domain catalog/presentation projection; owner-native work/source truth preserved | ACCEPTED_SOURCE_ONLY |
| workstation-lab | historical Git carrier only; active/current responsibilities drained; exact revision lookup retained in place | ARCHIVED_IN_PLACE |
| Research shared layer | composition profile / method-authority binding, no Research runtime owner | PROFILE_ONLY_NO_CODE_IMPORT |
| Paper1 frozen | frozen Research-v2 worktree/ref; archive in place | ARCHIVED_IN_PLACE |
| Paper2 | active independent scientific authority | KEEP_INDEPENDENT_ACTIVE |
| Paper3 | integrated study state inside Research-v2; no dedicated frozen authority ref yet | HOLD_EXTRACTION_UNTIL_FREEZE |

These standings cover source/history relocation and owner-native behavior only. Deployment, external effects, durable state, scientific standing, and old-repository retirement require separate evidence and gates.
