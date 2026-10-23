# SkillSpector integration contract

Upstream: https://github.com/NVIDIA/SkillSpector

Checked: 2026-09-17.

## Stable integration surface used here

SkillSpector documents `skillspector scan` exit status plus JSON as an automation interface:

- 0: completed under the default threshold/gates;
- 1: completed but risk or an enabled gate failed;
- 2: input/internal error.

Default exit status intentionally does not distinguish SAFE from CAUTION. Integrations therefore read the JSON report as well.

Expected single-Skill JSON evidence includes a risk assessment, issue details, component/metadata information, suppression information, and analysis completeness in current releases. The adapter must tolerate additive schema evolution and fail clearly when the payload cannot support the requested claim.

## Local policy

SkillSpector is evidence, not authority.

A local gate considers:

1. process exit status;
2. parse success;
3. analysis completeness when represented;
4. active issue severity, especially HIGH/CRITICAL;
5. aggregate risk/recommendation;
6. requested analyzer mode and failures.

No single aggregate score can downgrade a more severe concrete finding. An incomplete scan is not equivalent to a clean scan.

## Known integration caveats considered

GitHub issue history in 2026 documented cases around analysis-completeness/exit-code semantics and reduced detail in recursive JSON output. Current upstream adds explicit strict gates, but Ordivon still consumes the richer report rather than assuming a zero exit code proves full coverage.

For this reason Ordivon admission evidence should prefer one Skill package at a time when per-issue detail matters.
