//! Scheduling projection from already committed original PostgreSQL Job facts.
use super::failure_policy::decode_accepted_candidate;
use super::policy::scheduling_readback;
use super::{io, PgRuntime, RuntimeResult, SCHEDULING_READBACK_SQL};

impl PgRuntime {
    pub fn annotate_scheduling(
        &self,
        mut value: serde_json::Value,
    ) -> RuntimeResult<serde_json::Value> {
        let id = value.get("jobId").and_then(|v| v.as_str()).or_else(|| {
            value
                .get("job")
                .and_then(|j| j.get("jobId"))
                .and_then(|v| v.as_str())
        });
        let Some(id) = id.map(str::to_string) else {
            return Ok(value);
        };
        let mut db = self.store()?;
        let row = db
            .client
            .query_one(SCHEDULING_READBACK_SQL, &[&id])
            .map_err(io)?;
        // Corruption of one committed Job plan is an invalid Job record, not
        // PostgreSQL transport unavailability. Until the public Scheduling
        // schema can represent an unknown frozen request, fail visibly with
        // the existing typed error rather than fabricating a default budget.
        let plan = decode_accepted_candidate(&row.get::<_, String>(0))?;
        let spec = self.scheduling_contract(&plan)?;
        let attempt_state: Option<String> = row.get(1);
        let allocated: bool = row.get(2);
        let desired: String = row.get(3);
        let resolution: Option<String> = row.get(4);
        let has_issue: bool = row.get(5);
        let mut projection = scheduling_readback(
            spec,
            attempt_state.as_deref(),
            &desired,
            resolution.as_deref(),
            allocated,
        );
        // The existing public schema only offers cause_unobserved. When a
        // persisted Job event has a concrete failure, do not mislabel it as
        // an unobserved resource wait; clients can inspect exact job.get events.
        // Observe the issue and selected Attempt in the same SQL snapshot.
        // A later event must not be mixed into an earlier pending projection.
        if projection["state"] == "pending" && has_issue {
            projection["pendingReason"] = serde_json::Value::Null;
        }
        // The durable allocation is not a Runner start. The extra observation
        // must identify the same Attempt as the enclosing Job result; a
        // changed selection between readback statements remains UNKNOWN.
        let selected: Option<String> = row.get(6);
        let acquired: Option<i64> = row.get(7);
        let released: Option<i64> = row.get(8);
        if let Some(observation) =
            allocation_observation(&value, selected.as_deref(), acquired, released)
        {
            projection["allocationObservation"] = observation;
        }
        value["scheduling"] = projection;
        Ok(value)
    }
}

// The timestamp is the committed PG allocation-row value. It neither measures
// the wait for the advisory lock nor asserts that the native payload started.
fn allocation_observation(
    value: &serde_json::Value,
    attempt: Option<&str>,
    acquired: Option<i64>,
    released: Option<i64>,
) -> Option<serde_json::Value> {
    let attempt = attempt?;
    let observed = value.get("attemptId").and_then(|v| v.as_str()).or_else(|| {
        let attempts = value.get("attempts")?.as_array()?;
        if attempts.len() == 1 {
            attempts[0].get("attemptId")?.as_str()
        } else {
            None
        }
    });
    if observed != Some(attempt) {
        return None;
    }
    let acquired = u64::try_from(acquired?).ok()?;
    // Do not make a negative/corrupt timestamp into zero or a measured time.
    let released = released.and_then(|ms| u64::try_from(ms).ok());
    Some(serde_json::json!({
        "attemptId": attempt,
        "acquiredAtMs": acquired,
        "releasedAtMs": released,
    }))
}

#[cfg(test)]
mod tests {
    use super::allocation_observation;
    use serde_json::json;

    #[test]
    fn allocation_observation_is_exact_attempt_not_native_start() {
        let direct = json!({"attemptId":"a"});
        let get = json!({"attempts":[{"attemptId":"a"}]});
        for value in [direct, get] {
            assert_eq!(
                allocation_observation(&value, Some("a"), Some(100), Some(150)),
                Some(json!({"attemptId":"a","acquiredAtMs":100,"releasedAtMs":150}))
            );
            assert_eq!(
                allocation_observation(&value, Some("a"), Some(100), None),
                Some(json!({"attemptId":"a","acquiredAtMs":100,"releasedAtMs":null}))
            );
            assert!(allocation_observation(&value, Some("other"), Some(100), None).is_none());
            assert!(allocation_observation(&value, Some("a"), None, None).is_none());
            assert!(allocation_observation(&value, Some("a"), Some(-1), None).is_none());
        }
        assert!(allocation_observation(&json!({}), Some("a"), Some(100), None).is_none());
        assert!(allocation_observation(
            &json!({"attempts":[{"attemptId":"a"},{"attemptId":"b"}]}),
            Some("a"),
            Some(100),
            None
        )
        .is_none());
    }
}
