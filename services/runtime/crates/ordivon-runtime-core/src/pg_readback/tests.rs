use super::types::PgJobSnapshot;

fn snapshot() -> PgJobSnapshot {
    PgJobSnapshot {
        job_id: "j".into(),
        desired_state: "run".into(),
        resolution: None,
        current_attempt_id: Some("a".into()),
        attempt_id: "a".into(),
        attempt_state: "accepted".into(),
        termination_intent: "natural".into(),
        reservation_state: "active".into(),
        result_digest: None,
        started_at_ms: None,
        finished_at_ms: None,
        job_row_version: 0,
        attempt_row_version: 0,
    }
}

#[test]
fn accepted_and_cancel_requested_are_nonterminal_without_false_effect_claim() {
    let mut s = snapshot();
    assert!(s.lifecycle_coherent());
    s.desired_state = "cancelled".into();
    s.termination_intent = "stop_requested".into();
    assert!(s.lifecycle_coherent());
    s.attempt_state = "stopping".into();
    assert!(s.lifecycle_coherent());
    s.current_attempt_id = None;
    assert!(!s.lifecycle_coherent());
}

#[test]
fn terminal_requires_corresponding_attempt_evidence_and_released_capacity() {
    let mut s = snapshot();
    s.resolution = Some("succeeded".into());
    s.current_attempt_id = None;
    s.attempt_state = "succeeded".into();
    s.reservation_state = "released".into();
    s.result_digest = Some("sha256:result".into());
    s.finished_at_ms = Some(20);
    assert!(s.lifecycle_coherent());
    s.result_digest = None;
    assert!(!s.lifecycle_coherent());
    s.result_digest = Some("sha256:result".into());
    s.reservation_state = "active".into();
    assert!(!s.lifecycle_coherent());
    s.reservation_state = "released".into();
    s.attempt_state = "running".into();
    assert!(!s.lifecycle_coherent());
}

#[test]
fn orphan_never_projects_as_released_capacity() {
    let mut s = snapshot();
    s.resolution = Some("orphaned".into());
    s.current_attempt_id = None;
    s.attempt_state = "orphaned".into();
    s.reservation_state = "held_orphaned".into();
    s.result_digest = Some("sha256:orphan".into());
    s.finished_at_ms = Some(9);
    assert!(s.lifecycle_coherent());
    s.reservation_state = "released".into();
    assert!(!s.lifecycle_coherent());
}

#[test]
fn unfinished_attempt_with_terminal_artifacts_is_inconclusive() {
    let mut s = snapshot();
    s.result_digest = Some("sha256:premature".into());
    assert!(!s.lifecycle_coherent());
    s.result_digest = None;
    s.finished_at_ms = Some(12);
    assert!(!s.lifecycle_coherent());
}
