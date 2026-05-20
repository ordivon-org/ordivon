package governance.overclaim

# ── Forbidden claim words ──
forbidden_words := [
    "complete", "honest", "final", "safe", "verified", "guaranteed",
    "compliance", "production-ready", "production grade",
    "fully autonomous", "self-governing", "trustworthy", "secure", "foolproof",
]

# ── Negation phrases that cancel forbidden word matches ──
# If any of these appear within 80 chars of a forbidden word, skip the finding.
negation_phrases := [
    "does not mean", "does NOT mean", "not meant", "never",
    "is not", "are not", "may not", "must not", "cannot",
    "not: a system", "not: an authority", "not a",
]

# ── Overclaim patterns ──
overclaim_patterns := [
    "ready for production", "production ready", "fully tested",
    "fully verified", "fully validated", "no known issues", "zero risk",
]

# ── Receipt integrity HARD_FAILS ──
receipt_fails := [
    {"pattern": "Skipped Verification:\\s*None", "desc": "claims 'Skipped Verification: None'", "severity": "BLOCKING"},
    {"pattern": "Status:\\s*\\*?\\*?SEALED|FULLY SEALED", "desc": "claims 'FULLY SEALED'", "severity": "BLOCKING"},
]

# ── Helpers ──

# Check if any negation phrase appears near a word in the content
has_negation(content, word) := true if {
    lower_c := lower(content)
    lower_w := lower(word)
    word_idx := indexof(lower_c, lower_w)
    word_idx >= 0
    some phrase in negation_phrases
    lower_p := lower(phrase)
    phrase_idx := indexof(lower_c, lower_p)
    phrase_idx >= 0
    # Check if negation phrase is within 150 chars before or after the word
    abs(word_idx - phrase_idx) <= 150
}

default allow := true

check_file(content, path) := findings if {
    lower_content := lower(content)
    
    # Forbidden words (with negation context skip)
    fw := {w | w := forbidden_words[_]; contains(lower_content, w)}
    fw_filtered := {w | w := fw[_]; not has_negation(content, w)}
    fw_findings := [{"severity": "WARN", "finding_id": "OC-FORBIDDEN-WORD", "description": sprintf("Forbidden word '%s' in %s", [w, path]), "affected_file": path} | w := fw_filtered[_]]
    
    # Overclaim patterns
    op := {p | p := overclaim_patterns[_]; contains(lower_content, p)}
    op_findings := [{"severity": "BLOCKING", "finding_id": "OC-OVERCLAIM", "description": sprintf("Overclaim pattern '%s' in %s", [p, path]), "affected_file": path} | p := op[_]]

    # Receipt integrity
    rf := [r | r := receipt_fails[_]; contains(lower_content, r.pattern)]
    rf_findings := [{"severity": r.severity, "finding_id": "RECEIPT-INTEGRITY", "description": sprintf("%s in %s", [r.desc, path]), "affected_file": path} | r := rf[_]]

    findings := array.concat(fw_findings, array.concat(op_findings, rf_findings))
}

check_files(files) := all_findings if {
    all_findings := [f | file := files[_]; f := check_file(file.content, file.path)[_]]
}
