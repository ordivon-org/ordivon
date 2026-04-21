# Capability Migration Plan

This is the minimal closure-oriented migration plan for the remaining mixed modules.

## Reports

- keep `reports` classified as a `view` capability
- keep report facts small: artifact id, title, path, created time
- do not expand report listing into analysis-domain semantics

## Audits

- keep `audits` classified as a `view` capability over persisted fact records
- if deeper audit semantics are needed later, add a dedicated domain-facing audit object instead of overloading the listing capability

## Validation

- current file remains a diagnostic capability because its primary product use is summary visibility
- if issue intake expands, split write paths into a dedicated workflow capability and keep summary reads diagnostic

## Compatibility Rule

- top-level `capabilities/*.py` modules stay as thin wrappers until downstream imports have migrated
- all new logic lands in classified subdirectories only
