# Ordivon Authority Transition Policies — OPA Rego v1
package ordivon.authority
import rego.v1

# ═══════════════════════════════════════════════════════════════════════════
# Transition tables (explicit from→to pairs)
# ═══════════════════════════════════════════════════════════════════════════

valid_evidence_transitions contains {"from": "missing", "to": "partial"}
valid_evidence_transitions contains {"from": "missing", "to": "missing"}
valid_evidence_transitions contains {"from": "partial", "to": "partial"}
valid_evidence_transitions contains {"from": "partial", "to": "sufficient"}
valid_evidence_transitions contains {"from": "partial", "to": "contradicted"}
valid_evidence_transitions contains {"from": "sufficient", "to": "sufficient"}
valid_evidence_transitions contains {"from": "sufficient", "to": "contradicted"}
valid_evidence_transitions contains {"from": "contradicted", "to": "contradicted"}
valid_evidence_transitions contains {"from": "contradicted", "to": "partial"}

valid_authorization_transitions contains {"from": "not_requested", "to": "not_requested"}
valid_authorization_transitions contains {"from": "not_requested", "to": "requested"}
valid_authorization_transitions contains {"from": "requested", "to": "requested"}
valid_authorization_transitions contains {"from": "requested", "to": "approved"}
valid_authorization_transitions contains {"from": "requested", "to": "rejected"}
valid_authorization_transitions contains {"from": "requested", "to": "expired"}
valid_authorization_transitions contains {"from": "approved", "to": "approved"}
valid_authorization_transitions contains {"from": "approved", "to": "expired"}
valid_authorization_transitions contains {"from": "rejected", "to": "rejected"}
valid_authorization_transitions contains {"from": "rejected", "to": "requested"}
valid_authorization_transitions contains {"from": "expired", "to": "expired"}
valid_authorization_transitions contains {"from": "expired", "to": "requested"}

valid_policy_transitions contains {"from": "candidate", "to": "candidate"}
valid_policy_transitions contains {"from": "candidate", "to": "experimental"}
valid_policy_transitions contains {"from": "experimental", "to": "experimental"}
valid_policy_transitions contains {"from": "experimental", "to": "adopted"}
valid_policy_transitions contains {"from": "experimental", "to": "deprecated"}
valid_policy_transitions contains {"from": "adopted", "to": "adopted"}
valid_policy_transitions contains {"from": "adopted", "to": "deprecated"}
valid_policy_transitions contains {"from": "adopted", "to": "revoked"}
valid_policy_transitions contains {"from": "deprecated", "to": "deprecated"}
valid_policy_transitions contains {"from": "deprecated", "to": "revoked"}
# revoked is terminal — no transitions out, not even self

# ═══════════════════════════════════════════════════════════════════════════
# Validation — all boolean rules use := true / default := false pattern
# ═══════════════════════════════════════════════════════════════════════════

default evidence_allowed := false
evidence_allowed := true if {
    input.target.evidence
    input.target.evidence != ""
    some i
    valid_evidence_transitions[i] == {"from": input.state.evidence, "to": input.target.evidence}
}
evidence_allowed := true if { not input.target.evidence }
evidence_allowed := true if { input.target.evidence = "" }

default authorization_allowed := false
authorization_allowed := true if {
    input.target.authorization
    input.target.authorization != ""
    some i
    valid_authorization_transitions[i] == {"from": input.state.authorization, "to": input.target.authorization}
}
authorization_allowed := true if { not input.target.authorization }
authorization_allowed := true if { input.target.authorization = "" }

default policy_allowed := false
policy_allowed := true if {
    input.target.policy
    input.target.policy != ""
    some i
    valid_policy_transitions[i] == {"from": input.state.policy, "to": input.target.policy}
}
policy_allowed := true if { not input.target.policy }
policy_allowed := true if { input.target.policy = "" }

default all_allowed := false
all_allowed := true if {
    evidence_allowed
    authorization_allowed
    policy_allowed
}

# ── Safety predicates ──────────────────────────────────────────────────────

default safe_to_proceed := false
safe_to_proceed := true if {
    input.state.evidence = "sufficient"
    input.state.readiness != "not_ready"
    input.state.authorization != "rejected"
    input.state.policy != "revoked"
}

default requires_human_approval := false
requires_human_approval := true if { input.state.authorization = "requested" }
requires_human_approval := true if { input.state.authorization = "approved" }
requires_human_approval := true if { input.state.policy = "adopted" }

default has_authority_confusion := false
has_authority_confusion := true if { input.state.authorization = "approved" }
has_authority_confusion := true if {
    input.state.policy = "adopted"
    input.state.evidence != "sufficient"
}

# ── Blocked reasons ────────────────────────────────────────────────────────

blocked_reasons contains "evidence_transition_blocked" if {
    input.target.evidence
    input.target.evidence != ""
    not evidence_allowed
}
blocked_reasons contains "authorization_transition_blocked" if {
    input.target.authorization
    input.target.authorization != ""
    not authorization_allowed
}
blocked_reasons contains "policy_transition_blocked" if {
    input.target.policy
    input.target.policy != ""
    not policy_allowed
}

# ── Full validation result ─────────────────────────────────────────────────

validate_transition := {
    "evidence_valid": evidence_allowed,
    "authorization_valid": authorization_allowed,
    "policy_valid": policy_allowed,
    "all_valid": all_allowed,
    "safe_to_proceed": safe_to_proceed,
    "requires_human_approval": requires_human_approval,
    "has_authority_confusion": has_authority_confusion,
    "blocked_reasons": blocked_reasons,
}
