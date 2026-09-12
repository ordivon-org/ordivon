# Capability Package Census Template

This is an operational checklist, not another framework.

## 1. Outcome boundary

- Package:
- Real outcome class:
- Current real consumer/task:
- Explicit non-goals:

## 2. Mature external ecosystem

Record only representative mature owners needed by the current task.

| Capability family | Standard / body of knowledge | Mature provider/tool/skill | Why relevant now |
|---|---|---|---|

Do not enumerate every tool in the world.

## 3. Local observed capability

Evidence-backed only.

| Capability | Provider / location | State | Evidence |
|---|---|---|---|
|  |  | PRESENT / PARTIAL / ABSENT / NOT_NEEDED |  |

Host-global PATH absence is not a capability gap when a reproducible project/container/API/skill provider already serves the task.

## 4. Gap classification

Classify before acting:

- `NEEDED_NOW` — blocks the current real task;
- `PARTIAL_NOW` — usable, but a concrete acceptance condition is missing;
- `ON_DEMAND` — mature capability exists but no current workload needs activation;
- `EXTERNAL_SERVICE` — consume through API/service when needed;
- `NOT_A_GAP` — another package/provider already owns it;
- `DO_NOT_BUILD` — mature external owner exists and local implementation would duplicate it.

## 5. Activation decision

For `NEEDED_NOW` only:

1. select the smallest mature provider;
2. pin/version when reproducibility or trust matters;
3. inspect security/network/credential effects;
4. activate task-locally when possible;
5. do not promote activation into permanent architecture without repeated evidence.

## 6. Real-task acceptance

Record:

- exact input / source revision;
- provider/version/digest where material;
- verification command/job;
- output identity/digest;
- semantic acceptance result;
- remaining limitations.

Acceptance asks whether the **real consumer outcome** is served, not merely whether a tool starts.

## 7. Stop condition

Stop package construction when the current real task can be completed and verified with mature knowledge plus available providers. Future gaps reopen only the missing capability family.
