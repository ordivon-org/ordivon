package governance.rules

# ── Finance boundary (from checkers/finance-boundary) ──
finance_dangerous := [
    "live trade", "live trading", "live order",
    "place_live_order", "live broker", "live execution",
    "phase 8 ready", "phase 8 active", "phase 8 start",
    "broker write", "can_place_live_order",
]
finance_safe := ["NO-GO", "DEFERRED", "BLOCKED", "not live", "paper.only", "Phase 8 DEFERRED", "never live", "not auth"]

# ── Ownership manifest (from checkers/ownership-manifest) ──
ownership_dangerous := [
    "authorizes", "authorized", "authorization",
    "approved for merge", "approved for release", "approved for deploy",
    "approved for publication", "approved for trading", "approved for external action",
    "release approval",
]
ownership_safe := ["not", "no", "does not", "must not", "without", "evidence, not"]

# ── Protected paths (from checkers/protected-paths) ──
protected_patterns := [
    ".env", "secrets", "secret", "private_key", "private key",
    "credentials",
    "pyproject.toml", "uv.lock", "pnpm-lock", "package-lock",
    "state/db/migrations/runner.py",
]
path_safe := ["NO-GO", "not allowed", "protected", "governed", "forbidden", "FORBIDDEN", "boundary", "explicit justification", "explicitly allowed"]

# ── EGB-3 violation patterns (from checkers/egb3-operating-governance) ──
# Keywords+danger pair detection — both must appear near each other
egb3_patterns := [
    {"id": "reviewer_approver_confusion", "keywords": ["reviewer", "reviewers"], "danger": ["approve", "approves", "approved", "approval"], "desc": "Reviewer-approver confusion"},
    {"id": "ownerless_approval", "keywords": ["approval", "approved", "approver"], "danger": ["without owner", "missing owner", "no owner"], "desc": "Ownerless approval"},
    {"id": "shadow_hard_laundering", "keywords": ["shadow-tested", "shadow checker", "shadow tested", "shadow checkers"], "danger": ["hard gate", "pr-fast", "blocking", "blocks PR", "must pass for merge"], "desc": "Shadow-hard laundering"},
    {"id": "freeze_authorization", "keywords": ["freeze protocol", "freeze state"], "danger": ["authorizes", "approves", "permits", "allows"], "desc": "Freeze authorization overreach"},
    {"id": "trust_budget_expansion", "keywords": ["trust budget"], "danger": ["spent", "exceeded", "negative"], "extra": ["continue", "expand", "new scope", "ship", "release"], "desc": "Trust budget expansion"},
]

# ── Agentic patterns (from scripts/detect_agentic_patterns.py) ──
# READY overclaim: "READY" used as execution authorization
ready_danger_context := ["authorize execution", "authorises execution", "authorized execution", "approved for merge", "approved for deploy", "approved for execution", "approved for action", "approved for production"]

# CandidateRule premature promotion
candidate_rule_danger := ["binding policy", "active policy", "enforced rule"]

default allow := true

# ── Check rules against content ──

check_file(content, path) := findings if {
    lower_content := lower(content)

    # Finance boundary
    f_matched := {kw | kw := finance_dangerous[_]; contains(lower_content, lower(kw))}
    f_safe := {s | s := finance_safe[_]; contains(lower_content, lower(s))}
    has_safe_context := count(f_safe) > 0
    f_findings := [{"severity": "BLOCKING", "finding_id": "FINANCE-BOUNDARY", "description": sprintf("Dangerous finance language '%s' in %s", [kw, path]), "affected_file": path} | kw := f_matched[_]; not has_safe_context]

    # Ownership manifest
    o_matched := {kw | kw := ownership_dangerous[_]; contains(lower_content, lower(kw))}
    o_safe := {s | s := ownership_safe[_]; contains(lower_content, lower(s))}
    o_has_safe := count(o_safe) > 0
    o_findings := [{"severity": "BLOCKING", "finding_id": "OWNERSHIP-APPROVAL", "description": sprintf("Dangerous approval language '%s' in %s", [kw, path]), "affected_file": path} | kw := o_matched[_]; not o_has_safe]

    # Protected paths
    p_matched := {pat | pat := protected_patterns[_]; contains(lower_content, lower(pat))}
    p_safe := {s | s := path_safe[_]; contains(lower_content, lower(s))}
    p_has_safe := count(p_safe) > 0
    p_findings := [{"severity": "WARN", "finding_id": "PROTECTED-PATH", "description": sprintf("Unprotected reference to '%s' in %s", [pat, path]), "affected_file": path} | pat := p_matched[_]; not p_has_safe]

    # EGB-3 violations
    e_findings := [{"severity": "WARN", "finding_id": r.id, "description": sprintf("%s in %s", [r.desc, path]), "affected_file": path} | r := egb3_patterns[_]; kw := r.keywords[_]; dw := r.danger[_]; contains(lower_content, lower(kw)); contains(lower_content, lower(dw))]

    # READY overclaim — both "ready" + authorization context must appear
    r_words := {w | w := ready_danger_context[_]; contains(lower_content, lower(w))}
    has_ready := contains(lower_content, "ready")
    r_findings := [{"severity": "BLOCKING", "finding_id": "READY-OVERCLAIM", "description": sprintf("READY used as authorization in %s", [path]), "affected_file": path} | has_ready; count(r_words) > 0]

    # CandidateRule premature promotion
    cr_words := {w | w := candidate_rule_danger[_]; contains(lower_content, lower(w))}
    has_cr := contains(lower_content, "candidaterule")
    c_findings := [{"severity": "BLOCKING", "finding_id": "CANDIDATE-RULE-PROMOTION", "description": sprintf("CandidateRule treated as binding in %s", [path]), "affected_file": path} | has_cr; count(cr_words) > 0]

    findings := array.concat(f_findings, array.concat(o_findings, array.concat(p_findings, array.concat(e_findings, array.concat(r_findings, c_findings)))))
}

check_files(files) := all_findings if {
    all_findings := [f | file := files[_]; f := check_file(file.content, file.path)[_]]
}
