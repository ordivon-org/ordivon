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

#[test]
fn readback_coherence_matches_independent_state_and_evidence_matrix() {
    let active = ["accepted", "starting", "running", "stopping", "recovering"];
    let terminal = [
        "succeeded",
        "failed",
        "timed_out",
        "cancelled",
        "lost",
        "orphaned",
    ];
    let invalid = ["", "RUNNING", " running", "completed", "succeeded "];
    let states = active.into_iter().chain(terminal).chain(invalid);
    let resolutions = [None]
        .into_iter()
        .chain(terminal.into_iter().map(Some))
        .chain([Some("running"), Some(""), Some("LOST")]);
    for state in states {
        for resolution in resolutions.clone() {
            for current in [None, Some("a"), Some("other")] {
                for reservation in ["active", "released", "held_orphaned", "", "unknown"] {
                    for result in [None, Some(""), Some("sha256:receipt")] {
                        for finished in [None, Some(-1), Some(0), Some(42)] {
                            let mut s = snapshot();
                            s.attempt_state = state.into();
                            s.resolution = resolution.map(str::to_owned);
                            s.current_attempt_id = current.map(str::to_owned);
                            s.reservation_state = reservation.into();
                            s.result_digest = result.map(str::to_owned);
                            s.finished_at_ms = finished;
                            let expected = match resolution {
                                None => {
                                    active.contains(&state)
                                        && current == Some("a")
                                        && reservation == "active"
                                        && result.is_none()
                                        && finished.is_none()
                                }
                                Some(r) => {
                                    terminal.contains(&r)
                                        && state == r
                                        && current.is_none()
                                        && result.is_some_and(|v| !v.is_empty())
                                        && finished.is_some_and(|v| v >= 0)
                                        && reservation
                                            == if r == "orphaned" {
                                                "held_orphaned"
                                            } else {
                                                "released"
                                            }
                                }
                            };
                            assert_eq!(s.lifecycle_coherent(), expected, "{s:?}");
                        }
                    }
                }
            }
        }
    }
    for bad in ["", "RUN", " run", "unknown"] {
        let mut s = snapshot();
        s.desired_state = bad.into();
        assert!(!s.lifecycle_coherent());
    }
    for bad in ["", "NATURAL", " natural", "unknown"] {
        let mut s = snapshot();
        s.termination_intent = bad.into();
        assert!(!s.lifecycle_coherent());
    }
    let mut s = snapshot();
    s.job_row_version = -1;
    assert!(!s.lifecycle_coherent());
    s.job_row_version = 0;
    s.attempt_row_version = -1;
    assert!(!s.lifecycle_coherent());
}
