package governance.overclaim

# ── Forbidden claim words (from claim-vocabulary.json) ──
forbidden_words := [
    "complete", "honest", "final", "safe", "verified", "guaranteed",
    "compliance", "production-ready", "production grade",
    "fully autonomous", "self-governing", "trustworthy", "secure", "foolproof",
]

# ── Overclaim patterns (from detect_overclaim.py) ──
overclaim_patterns := [
    "ready for production", "production ready", "fully tested",
    "fully verified", "fully validated", "no known issues", "zero risk",
]

# ── Receipt integrity HARD_FAILS (from checkers/receipt-integrity/run.py) ──
receipt_fails := [
    {"pattern": "Skipped Verification:\\s*None", "desc": "claims 'Skipped Verification: None' — verify was never run, not None skipped", "severity": "BLOCKING"},
    {"pattern": "Status:\\s*\\*?\\*?SEALED|FULLY SEALED", "desc": "claims 'FULLY SEALED' — not a governed closure status", "severity": "BLOCKING"},
    {"pattern": "clean working tree", "desc": "claims 'clean working tree' — should qualify if untracked residue exists", "severity": "WARN", "safe": "tracked working tree clean|tracked clean"},
    {"pattern": "Ruff\\s+clean", "desc": "claims 'Ruff clean' globally — should qualify with scope", "severity": "WARN", "safe": "DG\\s+scope\\s+clean|DG\\s+files\\s+clean|forbidden|anti.pattern"},
    {"pattern": "CandidateRule\\s+validated", "desc": "claims 'CandidateRule validated' — should say 'advisory' or 'supported by evidence'", "severity": "WARN", "safe": "advisory|not\\s+Policy|supported\\s+by\\s+evidence"},
]

# ── Document registry DANGEROUS claims (from checkers/document-registry/run.py) ──
dangerous_claims := [
    {"pattern": "active policy", "desc": "claims 'active policy' — policy activation NO-GO", "severity": "BLOCKING"},
    {"pattern": "live trading", "desc": "claims 'live trading' — Phase 8 DEFERRED", "severity": "BLOCKING"},
]

default allow := true

check_file(content, path) := findings if {
    lower_content := lower(content)
    fw := {w | w := forbidden_words[_]; contains(lower_content, w)}
    fw_findings := [{"severity": "WARN", "finding_id": "OC-FORBIDDEN-WORD", "description": sprintf("Forbidden word '%s' in %s", [w, path]), "affected_file": path} | w := fw[_]]
    
    op := {p | p := overclaim_patterns[_]; contains(lower_content, p)}
    op_findings := [{"severity": "BLOCKING", "finding_id": "OC-OVERCLAIM", "description": sprintf("Overclaim pattern '%s' in %s", [p, path]), "affected_file": path} | p := op[_]]

    rf := [r | r := receipt_fails[_]; contains(lower_content, r.pattern)]
    rf_findings := [{"severity": r.severity, "finding_id": "RECEIPT-INTEGRITY", "description": sprintf("%s in %s", [r.desc, path]), "affected_file": path} | r := rf[_]]

    dc := [d | d := dangerous_claims[_]; contains(lower_content, d.pattern)]
    dc_findings := [{"severity": d.severity, "finding_id": "DANGEROUS-CLAIM", "description": sprintf("%s in %s", [d.desc, path]), "affected_file": path} | d := dc[_]]

    findings := array.concat(fw_findings, array.concat(op_findings, array.concat(rf_findings, dc_findings)))
}

check_files(files) := all_findings if {
    all_findings := [f | file := files[_]; f := check_file(file.content, file.path)[_]]
}
