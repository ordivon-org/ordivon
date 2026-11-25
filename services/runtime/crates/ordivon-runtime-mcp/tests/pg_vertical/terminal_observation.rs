//! Test consumer only. A bounded MCP response is not a terminal assertion.
//! No submit operation is available through this driver.
use super::{committed_40001_job_id, rpc_with_timeout};
use serde_json::{json, Value};
use std::time::{Duration, Instant};

#[derive(Default, Debug)]
struct Identity {
    job: Option<String>,
    attempt: Option<String>,
    operation: Option<String>,
}

fn bind(slot: &mut Option<String>, value: &str, name: &str) -> Result<(), String> {
    if value.is_empty() || slot.as_deref().is_some_and(|old| old != value) {
        return Err(format!("invalid or foreign {name}: {value}"));
    }
    if slot.is_none() {
        *slot = Some(value.to_owned());
    }
    Ok(())
}

impl Identity {
    // Return true only for a structurally terminal response, independent
    // of domain success. The calling test asserts the actual disposition.
    fn accept(&mut self, receipt: &Value) -> Result<bool, String> {
        if receipt["isError"] == true {
            let job = committed_40001_job_id(receipt).ok_or("unqualified observation error")?;
            bind(&mut self.job, job, "Job")?;
            return Ok(false);
        }
        let p = &receipt["structuredContent"];
        let job = p["jobId"].as_str().ok_or("missing Job")?;
        let attempt = p["attemptId"].as_str().ok_or("missing Attempt")?;
        let operation = p["operationDigest"].as_str().ok_or("missing Operation")?;
        if !job.starts_with("job-")
            || !attempt.starts_with("attempt-")
            || !operation.starts_with("sha256:")
        {
            return Err("malformed observation identity".into());
        }
        bind(&mut self.job, job, "Job")?;
        bind(&mut self.attempt, attempt, "Attempt")?;
        bind(&mut self.operation, operation, "Operation")?;
        let terminal = p["executionTerminal"]
            .as_bool()
            .ok_or("missing terminal predicate")?;
        let disposition = &p["executionDisposition"];
        if (terminal
            && !matches!(
                disposition.as_str(),
                Some("succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned")
            ))
            || (!terminal && !disposition.is_null())
        {
            return Err("terminal/disposition disagreement".into());
        }
        Ok(terminal)
    }
}

// A finite, independently injectable observation budget. Its clock is
// monotonic at the real boundary; tests can exhaust it without sleeping.
fn drive(
    mut receipt: Value,
    mut remaining: impl FnMut() -> Duration,
    mut observe: impl FnMut(&str, Duration) -> Value,
) -> Result<Value, String> {
    let mut identity = Identity::default();
    loop {
        if identity
            .accept(&receipt)
            .map_err(|error| format!("{error}; last receipt: {receipt}"))?
        {
            return Ok(receipt);
        }
        let budget = remaining();
        if budget.is_zero() {
            return Err(format!(
                "terminal observation budget exhausted; last exact receipt: {receipt}"
            ));
        }
        receipt = observe(
            identity.job.as_deref().unwrap(),
            budget.min(Duration::from_secs(1)),
        );
    }
}

pub(super) fn await_terminal(url: &str, receipt: Value, budget: Duration) -> Value {
    let deadline = Instant::now() + budget;
    drive(
        receipt,
        || deadline.saturating_duration_since(Instant::now()),
        |job, wait| {
            // Only reconciliation of the original Job; never another submit.
            let transport_budget = deadline.saturating_duration_since(Instant::now());
            assert!(
                !transport_budget.is_zero(),
                "observation budget exhausted before transport"
            );
            let result = rpc_with_timeout(
                url,
                "tools/call",
                json!({"name":"job.observe","arguments":{
                    "jobId":job,"waitMs":wait.min(transport_budget).as_millis() as u64,
                    "waitUntil":"terminal","stdoutTailBytes":8192,"stderrTailBytes":8192
                }}),
                Some(transport_budget),
            );
            if result["structuredContent"]["executionTerminal"] != true {
                std::thread::sleep(
                    Duration::from_millis(20)
                        .min(deadline.saturating_duration_since(Instant::now())),
                );
            }
            result
        },
    )
    .unwrap_or_else(|error| panic!("{error}"))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn row(terminal: bool) -> Value {
        json!({"isError":false,"structuredContent":{
            "jobId":"job-original","attemptId":"attempt-original","operationDigest":"sha256:original",
            "executionTerminal":terminal,"executionDisposition":if terminal {Some("failed")} else {None}
        }})
    }
    fn committed() -> Value {
        json!({"isError":true,"structuredContent":{"error":{
            "commitState":"committed","retryClass":"reconcile_first","code":"REGISTRY_BUSY",
            "operationId":"job-original","message":"PostgreSQL: SqlState(E40001)"
        }}})
    }
    #[test]
    fn same_identity_pending_then_failed_is_not_resubmission() {
        let mut history = [committed(), row(false), row(true)].into_iter();
        let mut observed = 0;
        let terminal = drive(
            row(false),
            || Duration::from_secs(2),
            |job, wait| {
                assert_eq!(job, "job-original");
                assert_eq!(wait, Duration::from_secs(1));
                observed += 1;
                history.next().expect("finite exact observations")
            },
        )
        .unwrap();
        assert_eq!(observed, 3);
        assert_eq!(terminal, row(true));
    }
    #[test]
    fn committed_error_binds_job_before_attempt_is_known() {
        assert_eq!(
            drive(
                committed(),
                || Duration::from_secs(1),
                |job, _| {
                    assert_eq!(job, "job-original");
                    row(true)
                }
            )
            .unwrap(),
            row(true)
        );
    }
    #[test]
    fn reject_foreign_attempt_job_operation_and_false_terminal() {
        for (key, value, expected) in [
            ("jobId", json!("job-foreign"), "foreign Job"),
            ("attemptId", json!("attempt-foreign"), "foreign Attempt"),
            (
                "operationDigest",
                json!("sha256:foreign"),
                "foreign Operation",
            ),
            (
                "executionDisposition",
                Value::Null,
                "terminal/disposition disagreement",
            ),
            (
                "executionDisposition",
                json!("not_a_resolution"),
                "terminal/disposition disagreement",
            ),
            (
                "executionTerminal",
                json!(false),
                "terminal/disposition disagreement",
            ),
            (
                "executionTerminal",
                json!("true"),
                "missing terminal predicate",
            ),
        ] {
            let mut bad = row(true);
            bad["structuredContent"][key] = value;
            let mut ticks = [Duration::from_secs(1), Duration::ZERO].into_iter();
            let error = drive(
                row(false),
                || ticks.next().unwrap_or(Duration::ZERO),
                |_, _| bad.clone(),
            )
            .unwrap_err();
            assert!(error.contains(expected), "{key}: {error}");
        }
    }
    #[test]
    fn terminal_is_not_necessarily_success_and_needs_no_new_observation() {
        for disposition in [
            "succeeded",
            "failed",
            "timed_out",
            "cancelled",
            "lost",
            "orphaned",
        ] {
            let mut terminal = row(true);
            terminal["structuredContent"]["executionDisposition"] = json!(disposition);
            let actual = drive(
                terminal.clone(),
                || Duration::ZERO,
                |_, _| panic!("already terminal"),
            )
            .unwrap();
            assert_eq!(actual, terminal);
        }
    }
    #[test]
    fn reject_foreign_committed_error_and_missing_identity() {
        let mut error = committed();
        error["structuredContent"]["error"]["operationId"] = json!("job-foreign");
        let mut ticks = [Duration::from_secs(1), Duration::ZERO].into_iter();
        let actual = drive(
            row(false),
            || ticks.next().unwrap_or(Duration::ZERO),
            |_, _| error.clone(),
        )
        .unwrap_err();
        assert!(actual.contains("foreign Job"), "{actual}");
        for key in ["jobId", "attemptId", "operationDigest"] {
            let mut missing = row(true);
            missing["structuredContent"]
                .as_object_mut()
                .unwrap()
                .remove(key);
            let actual = drive(
                missing,
                || Duration::ZERO,
                |_, _| panic!("missing identity"),
            )
            .unwrap_err();
            assert!(actual.contains("missing"), "{actual}");
        }
    }
    #[test]
    fn no_unqualified_error_observation_or_vacuous_timeout() {
        let mut bad = committed();
        bad["structuredContent"]["error"]["commitState"] = json!("not_committed");
        assert!(drive(
            bad,
            || Duration::from_secs(1),
            |_, _| panic!("must not observe")
        )
        .is_err());
        let mut remaining = [Duration::from_millis(30), Duration::ZERO].into_iter();
        let error = drive(
            row(false),
            || remaining.next().unwrap(),
            |job, wait| {
                assert_eq!(job, "job-original");
                assert_eq!(wait, Duration::from_millis(30));
                row(false)
            },
        )
        .unwrap_err();
        assert!(error.contains("budget exhausted") && error.contains("job-original"));
    }
}
