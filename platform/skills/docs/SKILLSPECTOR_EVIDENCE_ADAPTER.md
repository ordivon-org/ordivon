# SkillSpector Evidence Adapter

The Harness SkillSpector adapter is an **explicit single-Skill evidence producer**, not a catalog trust engine.

`ordivon_skills.skillspector_adapter.run_skillspector_scan()` runs a locally approved SkillSpector executable against one exact filesystem-backed Skill package using `--no-llm --format json`, binds the result to the package revision, and normalizes scanner output into one bounded evidence record.

The normalized `evidenceState` is one of:

- `CLEAN_EVIDENCE` — completed scan with no material finding under the normalized checks;
- `CAUTION` — completed scan with non-blocking findings or non-clean aggregate evidence;
- `BLOCK_SIGNAL` — high/critical issue or `DO_NOT_INSTALL` signal;
- `INCOMPLETE` — scanner transport succeeded but required completeness was not established;
- `SCANNER_ERROR` — execution, transport, parse, or package-revision failure.

This adapter deliberately does **not** write `TrustState`, authorize tools/effects, or run during ordinary Skill catalog refresh. The normal Harness scanner, source trust, invocation policy, package/snapshot fences, and higher-level authorization remain independent owners.

A typical operator/runtime call is equivalent to:

```python
from ordivon_skills.skillspector_adapter import run_skillspector_scan

evidence = run_skillspector_scan(
    "/path/to/one-skill",
    "/approved/path/to/skillspector",
    expected_package_revision="sha256:...",
)
```

The expected package revision is optional but recommended when the caller already resolved the Skill through the catalog; a changed package fails explicitly rather than transferring historical scanner evidence to new bytes.
