//! Typed Runtime observation composition. No dispatch or domain verdict.
use crate::{artifact_descriptor, logic::parse_execution_ref};
use serde::Serialize;
use serde_json::Value;

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub(crate) enum Receipt<'a> {
    Unobserved {
        reason: &'static str,
    },
    Reported {
        owner: &'a str,
        native_id: &'a str,
        state: &'a str,
        attempt_state: Option<&'a str>,
        terminal: bool,
        delivery_disposition: Option<&'a str>,
        execution_disposition: Option<&'a str>,
        exit_code: Option<i32>,
        result_available: Option<bool>,
        recovery_required: Option<bool>,
        semantic_completion_evaluated: Option<bool>,
        artifacts_available: Option<bool>,
        artifacts: artifact_descriptor::Qualification,
    },
}
fn unknown(reason: &'static str) -> Receipt<'static> {
    Receipt::Unobserved { reason }
}
fn nonempty(v: &Value) -> Option<&str> {
    v.as_str().filter(|s| !s.is_empty())
}
fn optional_text<'a>(v: &'a Value, k: &str) -> Result<Option<&'a str>, ()> {
    match v.get(k) {
        None | Some(Value::Null) => Ok(None),
        Some(x) => nonempty(x).map(Some).ok_or(()),
    }
}
pub(crate) fn project<'a>(reference: &'a str, obs: &'a Value, inspection: &Value) -> Receipt<'a> {
    let Some((owner, native_id)) = parse_execution_ref(reference) else {
        return unknown("invalid_operation_ref");
    };
    if nonempty(&obs["jobId"]) != Some(native_id) {
        return unknown("mismatched_job_identity");
    }
    for k in ["status", "attemptState"] {
        if obs.get(k).is_some_and(|v| nonempty(v).is_none()) {
            return unknown("invalid_state");
        }
    }
    let state = nonempty(&obs["status"])
        .or_else(|| nonempty(&obs["attemptState"]))
        .unwrap_or("unknown");
    let Some(terminal) = obs["executionTerminal"].as_bool() else {
        return unknown("invalid_terminality");
    };
    let (Ok(delivery_disposition), Ok(execution_disposition)) = (
        optional_text(obs, "deliveryDisposition"),
        optional_text(obs, "executionDisposition"),
    ) else {
        return unknown("invalid_disposition");
    };
    let exit_code = if obs["exitCode"].is_null() {
        None
    } else {
        let Some(code) = obs["exitCode"].as_i64().and_then(|v| i32::try_from(v).ok()) else {
            return unknown("invalid_exit_code");
        };
        Some(code)
    };
    // Only the exact natural summary for this job can qualify coverage.
    let count = if inspection.is_null() {
        &Value::Null
    } else {
        if nonempty(&inspection["job"]["jobId"]) != Some(native_id) {
            return unknown("mismatched_inspection_identity");
        }
        &inspection["artifacts"]["count"]
    };
    Receipt::Reported {
        owner,
        native_id,
        state,
        attempt_state: nonempty(&obs["attemptState"]),
        terminal,
        delivery_disposition,
        execution_disposition,
        exit_code,
        result_available: obs["resultAvailable"].as_bool(),
        recovery_required: obs["recoveryRequired"].as_bool(),
        semantic_completion_evaluated: obs["semanticCompletionEvaluated"].as_bool(),
        artifacts_available: obs["artifactsAvailable"].as_bool(),
        artifacts: artifact_descriptor::qualify(obs, count),
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;
    #[test]
    fn independent_owner_dimensions() {
        let v = json!({"jobId":"job-a","status":"working","attemptState":"running","executionTerminal":false,"resultAvailable":false,"semanticCompletionEvaluated":false});
        let r = serde_json::to_value(project(
            "ordivon-exec:v1:runtime.linux:job-a",
            &v,
            &Value::Null,
        ))
        .unwrap();
        assert_eq!(r["state"], "working");
        assert_eq!(r["attempt_state"], "running");
        assert_eq!(r["terminal"], false);
        assert_eq!(r["result_available"], false);
        assert_eq!(r["semantic_completion_evaluated"], false);
        assert!(r["artifacts"]["metadata_complete"].is_null());
        assert_eq!(
            project(
                "ordivon-exec:v1:runtime.linux:job-a",
                &v,
                &json!({"job":{"jobId":"job-b"}})
            ),
            unknown("mismatched_inspection_identity")
        );
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn receipt_does_not_derive_domain_facts(status in "[a-z]{1,20}",attempt in "[a-z]{1,20}",terminal in any::<bool>(), result in prop::option::of(any::<bool>()), semantic in prop::option::of(any::<bool>()), recovery in prop::option::of(any::<bool>())){
            let v=json!({"jobId":"job-a","status":status,"attemptState":attempt,"executionTerminal":terminal,"resultAvailable":result,"semanticCompletionEvaluated":semantic,"recoveryRequired":recovery});
            let out=serde_json::to_value(project("ordivon-exec:v1:runtime.linux:job-a",&v,&Value::Null)).unwrap();
            prop_assert_eq!(&out["state"],&v["status"]);
            prop_assert_eq!(&out["attempt_state"],&v["attemptState"]);
            prop_assert_eq!(&out["terminal"],&v["executionTerminal"]);
            prop_assert_eq!(&out["result_available"],&v["resultAvailable"]);
            prop_assert_eq!(&out["semantic_completion_evaluated"],&v["semanticCompletionEvaluated"]);
            prop_assert_eq!(&out["recovery_required"],&v["recoveryRequired"]);
        }
    }
}
