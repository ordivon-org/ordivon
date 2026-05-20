use crate::digest::sha256_digest;
use crate::governance_ops::{Debt, DebtState, Receipt, COMPARATOR_ISSUER};
use crate::observation::ObservedEvent;
use crate::types::{Obligation, ObservationStatus, OrderConstraint, Verdict};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ComparatorFinding {
    pub finding_type: String,
    pub detail: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ComparatorResult {
    pub verdict: Verdict,
    pub findings: Vec<ComparatorFinding>,
    pub receipt: Receipt,
    pub debts: Vec<Debt>,
}

pub fn compare_obligation(
    obligation: &Obligation,
    observed_events: &[ObservedEvent],
    issued_at: &str,
) -> ComparatorResult {
    match obligation.validate_at(issued_at) {
        Ok(()) => {}
        Err(err) => {
            return result_with_receipt(
                obligation,
                format!("receipt:{}", obligation.obligation_id),
                Verdict::DeclarationInvalid,
                vec![finding("DECLARATION_INVALID", err.to_string())],
                observed_event_refs(observed_events),
                issued_at,
            );
        }
    }

    let receipt_id = format!("receipt:{}", obligation.obligation_id);
    let mut findings = Vec::new();
    for event in observed_events {
        if let Err(err) = event.validate() {
            return result_with_receipt(
                obligation,
                receipt_id,
                Verdict::DeclarationInvalid,
                vec![finding("OBSERVED_EVENT_INVALID", err.to_string())],
                observed_event_refs(observed_events),
                issued_at,
            );
        }
        if event.status.is_unverifiable() {
            findings.push(finding(
                "UNVERIFIABLE",
                format!("{} has status {:?}", event.event_id, event.status),
            ));
        }
        if matches!(
            event.status,
            ObservationStatus::Partial | ObservationStatus::Failed
        ) {
            findings.push(finding(
                "OBSERVED_FAILURE",
                format!("{} has status {:?}", event.event_id, event.status),
            ));
        }
    }

    if observed_events.is_empty() {
        return result_with_receipt(
            obligation,
            receipt_id,
            Verdict::Unverifiable,
            vec![finding("UNVERIFIABLE", "no observed events available")],
            Vec::new(),
            issued_at,
        );
    }

    if findings
        .iter()
        .any(|item| item.finding_type == "UNVERIFIABLE")
    {
        return result_with_receipt(
            obligation,
            receipt_id,
            Verdict::Unverifiable,
            findings,
            observed_event_refs(observed_events),
            issued_at,
        );
    }

    let mut matched = vec![false; observed_events.len()];
    let mut missing = false;
    let mut extra = false;
    let mut mis = findings
        .iter()
        .any(|item| item.finding_type == "OBSERVED_FAILURE");
    let mut last_sequence = 0;

    for action in &obligation.declared_actions {
        let mut matches_for_action = Vec::new();
        for (index, event) in observed_events.iter().enumerate() {
            if event.action_class == action.action_class && event.target_ref == action.target_ref {
                matches_for_action.push((index, event));
            }
        }

        let count = matches_for_action.len() as u32;
        if count < action.cardinality.min {
            missing = true;
            findings.push(finding(
                "EXPECTED_ACTION_MISSING",
                format!("{:?}:{}", action.action_class, action.target_ref),
            ));
            continue;
        }
        if count > action.cardinality.max {
            extra = true;
            findings.push(finding(
                "ACTION_CARDINALITY_EXCEEDED",
                format!(
                    "{:?}:{} observed {} max {}",
                    action.action_class, action.target_ref, count, action.cardinality.max
                ),
            ));
        }

        for (index, event) in matches_for_action {
            matched[index] = true;
            if matches!(action.order_constraint, OrderConstraint::DeclaredOrder) {
                if event.observed_sequence < last_sequence {
                    mis = true;
                    findings.push(finding(
                        "ORDER_MISMATCH",
                        format!("{} observed out of declared order", event.event_id),
                    ));
                }
                last_sequence = event.observed_sequence;
            }
            if let Some(expected_key) = &action.idempotency_key {
                if &event.idempotency_key != expected_key {
                    mis = true;
                    findings.push(finding(
                        "IDEMPOTENCY_MISMATCH",
                        format!("{} expected {}", event.idempotency_key, expected_key),
                    ));
                }
            }
            if !action.authority_refs.is_empty()
                && !action.authority_refs.contains(&event.authority_ref)
            {
                mis = true;
                findings.push(finding(
                    "AUTHORITY_MISMATCH",
                    format!("{} not declared", event.authority_ref),
                ));
            }
            if let Some(expected_hash) = &action.expected_payload_hash {
                if &event.payload_hash != expected_hash {
                    mis = true;
                    findings.push(finding(
                        "PAYLOAD_DIGEST_MISMATCH",
                        format!("{} expected {}", event.payload_hash, expected_hash),
                    ));
                }
            }
            if !event.status.is_success_evidence() {
                mis = true;
                findings.push(finding(
                    "SUCCESS_PREDICATE_NOT_MET",
                    format!("{} status {:?}", event.event_id, event.status),
                ));
            }
        }
    }

    for (index, event) in observed_events.iter().enumerate() {
        if !matched[index] {
            extra = true;
            findings.push(finding(
                "UNDECLARED_ACTION_OBSERVED",
                format!("{:?}:{}", event.action_class, event.target_ref),
            ));
        }
    }

    let verdict = if mis || (missing && extra) {
        Verdict::Mis
    } else if extra {
        Verdict::Over
    } else if missing {
        Verdict::Under
    } else {
        Verdict::ExactMatch
    };

    result_with_receipt(
        obligation,
        receipt_id,
        verdict,
        findings,
        observed_event_refs(observed_events),
        issued_at,
    )
}

fn observed_event_refs(observed_events: &[ObservedEvent]) -> Vec<String> {
    observed_events
        .iter()
        .map(|event| event.event_id.clone())
        .collect()
}

fn result_with_receipt(
    obligation: &Obligation,
    receipt_id: String,
    verdict: Verdict,
    findings: Vec<ComparatorFinding>,
    observed_event_refs: Vec<String>,
    issued_at: &str,
) -> ComparatorResult {
    let comparator_digest = sha256_digest(&serde_json::json!({
        "obligationId": obligation.obligation_id,
        "verdict": verdict,
        "findings": findings.iter().map(|item| {
            serde_json::json!({"findingType": item.finding_type, "detail": item.detail})
        }).collect::<Vec<_>>()
    }))
    .unwrap_or_else(|_| "sha256:comparator-digest-error".to_string());
    let debt_refs = if verdict.is_blocking() {
        vec![format!("debt:{receipt_id}")]
    } else {
        Vec::new()
    };
    let root_cause_code = format!("{:?}", verdict).to_uppercase();
    let debts = debt_refs
        .iter()
        .map(|debt_id| Debt {
            debt_id: debt_id.clone(),
            debt_type: "receipt_mismatch".to_string(),
            severity: if matches!(
                verdict,
                Verdict::Over | Verdict::Mis | Verdict::DeclarationInvalid
            ) {
                "high".to_string()
            } else {
                "medium".to_string()
            },
            owner: "ordivon-core-maintainer".to_string(),
            due_at: "2026-05-23T00:00:00Z".to_string(),
            blocking_scope: "new-kernel-hardening".to_string(),
            introduced_by_receipt: receipt_id.clone(),
            root_cause_code: root_cause_code.clone(),
            root_cause_hypothesis: format!("Comparator issued {:?}", verdict),
            verification_receipt: None,
            state: DebtState::Open,
        })
        .collect();

    let receipt = Receipt {
        receipt_id,
        intent_id: obligation.intent_id.clone(),
        obligation_id: obligation.obligation_id.clone(),
        verdict: verdict.clone(),
        observed_event_refs,
        state_transitions: vec!["Receipt.Pending->Receipt.Issued".to_string()],
        debt_refs,
        issued_by: COMPARATOR_ISSUER.to_string(),
        issued_at: issued_at.to_string(),
        comparator_digest,
    };

    ComparatorResult {
        verdict,
        findings,
        receipt,
        debts,
    }
}

fn finding(finding_type: impl Into<String>, detail: impl Into<String>) -> ComparatorFinding {
    ComparatorFinding {
        finding_type: finding_type.into(),
        detail: detail.into(),
    }
}
