# Engineering Re-Entry Prompt

Use this prompt when assigning an engineering task to an AI coding agent.

## Task

[Describe the task here]

## Execution Frame (from ordivon-core-method P2)

- **Intent:** What is the goal?
- **Scope:** What is included? What files/systems?
- **Non-Goals:** What is explicitly NOT being done this round?
- **Tools:** What tools are needed? (annotate with M0-M5)
- **Authority:** Who can approve? AI may propose, not authorize.
- **Verification:** How will we know it's done correctly?
- **Seal Condition:** What must be true to declare this task complete?

## Receipt Required

After execution, produce an R2 Engineering Receipt with:
- Actions taken (with evidence: diffs, test outputs, commands run)
- Verification results
- Remaining debt (what is NOT resolved)
- Status: PASS / DEGRADED / BLOCKED
- Draft: true (receipt is draft until reviewed)

## Hard Boundaries

- Do not expand scope beyond what is declared.
- Do not self-close without receipt.
- Do not treat test-pass as task-complete.
- Separate execution from sealing.
