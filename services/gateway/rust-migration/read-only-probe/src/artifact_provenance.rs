//! R23: terminal owner evidence, then one bounded v1 artifact read.
//! Only the fixture ingress may construct the fixed identity. No Security grant.
use crate::{
    artifact_abi, artifact_descriptor,
    logic::parse_execution_ref,
    owner_resolution,
    owner_transport::{self, ReadRequest},
    principal_binding::{Binding, BindingFixture},
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{path::Path, time::Duration};

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct Request {
    operation_ref: String,
    artifact_id: String,
    #[serde(default)]
    offset: u64,
    #[serde(default = "default_max")]
    max_bytes: u64,
    request_id: String,
    capability: String,
}
fn default_max() -> u64 {
    1_048_576
}
fn nonblank(v: &Value) -> Option<&str> {
    v.as_str().filter(|s| !s.is_empty() && *s == s.trim())
}
fn rejected(reason: &'static str) -> Value {
    json!({"standing":"unobserved","reason":reason})
}
fn identity<'a>(
    job: &str,
    key: &str,
    inspection: &'a Value,
) -> Option<(&'a str, &'a str, &'a str, u64)> {
    let j = &inspection["job"];
    if inspection["schemaVersion"] != 2
        || inspection["migrationVersion"] != 0
        || j["jobId"].as_str() != Some(job)
        || j["clientRequestId"].as_str() != Some(key)
        || j["mechanicallyConverged"] != true
        || inspection["attemptsTruncated"] != false
    {
        return None;
    }
    let resolution = nonblank(&j["resolution"])?;
    let operation = nonblank(&j["operationDigest"])?;
    let attempts = inspection["attempts"].as_array()?;
    if attempts.len() != 1 {
        return None;
    }
    let a = &attempts[0];
    let attempt = nonblank(&a["attemptId"])?;
    let count = inspection["artifacts"]["count"].as_u64()?;
    if a["artifactCount"].as_u64() != Some(count) {
        return None;
    }
    Some((operation, attempt, resolution, count))
}
pub(crate) fn descriptor(
    job: &str,
    key: &str,
    artifact: &str,
    inspection: &Value,
    obs: &Value,
) -> Option<artifact_descriptor::Descriptor> {
    let (op, attempt, resolution, count) = identity(job, key, inspection)?;
    if obs["jobId"].as_str() != Some(job)
        || obs["operationDigest"].as_str() != Some(op)
        || obs["attemptId"].as_str() != Some(attempt)
        || obs["executionDisposition"].as_str() != Some(resolution)
        || obs["attemptState"] != inspection["attempts"][0]["state"]
        || nonblank(&obs["attemptState"]).is_none()
        || obs["executionTerminal"] != true
        || obs["deliveryDisposition"] != "committed"
        || obs["recoveryRequired"] != false
        || obs["artifactsAvailable"] != true
    {
        return None;
    }
    // Complete metadata only; same-attempt PG v1 fixture, no cross-attempt inference.
    let descriptors =
        artifact_descriptor::qualify(obs, &json!(count)).into_complete_descriptors()?;
    if descriptors.iter().any(|d| d.attempt_id() != attempt) {
        return None;
    }
    descriptors
        .into_iter()
        .find(|d| d.artifact_id() == artifact)
}
pub(crate) async fn read(
    endpoint: &str,
    credential: &Path,
    issuer: &str,
    principal: &str,
    legacy: bool,
    request: Request,
) -> Value {
    let r = &request;
    let Some(("runtime.linux", job)) = parse_execution_ref(&r.operation_ref) else {
        return rejected("invalid_operation_ref");
    };
    if r.artifact_id.is_empty()
        || r.artifact_id != r.artifact_id.trim()
        || !(1..=1_048_576).contains(&r.max_bytes)
        || r.offset.checked_add(r.max_bytes).is_none()
    {
        return rejected("invalid_cursor");
    }
    let Ok(binding) = serde_json::from_value::<BindingFixture>(
        json!({"issuer":issuer,"principal":principal,"capability":r.capability,"request_id":r.request_id,"operation_ref":r.operation_ref}),
    ) else {
        return rejected("invalid_binding");
    };
    let Some(key) = binding.scoped_key() else {
        return rejected("invalid_binding");
    };
    let Some(url) = owner_transport::fixture_endpoint(endpoint) else {
        return rejected("unqualified_fixture_endpoint");
    };
    let Ok(token) = crate::owner_credential::read_fixture_bearer(credential) else {
        return rejected("unqualified_fixture_credential");
    };
    let budget = Duration::from_secs(5);
    tokio::time::timeout(budget, async {
        let Ok(client) = owner_transport::connect(url, budget, legacy, Some(token)).await else {
            return rejected("owner_unobserved");
        };
        let result = async {
            let Ok(page) =
                owner_transport::call_read(&client, ReadRequest::Resolve { request_id: &key })
                    .await
            else {
                return rejected("owner_unobserved");
            };
            if binding.qualify(owner_resolution::project(&page, &key)) != Binding::Matched {
                return rejected("unqualified_operation_binding");
            }
            let Ok(inspection) =
                owner_transport::call_read(&client, ReadRequest::Inspect { job_id: job }).await
            else {
                return rejected("owner_unobserved");
            };
            // job.observe can dispatch an accepted job. Never use it for an unresolved job here.
            if identity(job, &key, &inspection).is_none() {
                return rejected("unqualified_terminal_inspection");
            }
            let Ok(obs) =
                owner_transport::call_read(&client, ReadRequest::Observe { job_id: job }).await
            else {
                return rejected("owner_unobserved");
            };
            let Some(d) = descriptor(job, &key, &r.artifact_id, &inspection, &obs) else {
                return rejected("unqualified_descriptor_provenance");
            };
            if r.offset > d.retained_bytes() {
                return rejected("invalid_cursor");
            }
            let n = r.max_bytes.min(128 * 1024);
            let Ok(v) = owner_transport::call_read(
                &client,
                ReadRequest::Artifact {
                    job_id: job,
                    artifact_id: &r.artifact_id,
                    offset: r.offset,
                    max_bytes: n,
                },
            )
            .await
            else {
                return rejected("owner_unobserved");
            };
            artifact_abi::project_bound(
                &r.operation_ref,
                &d,
                &json!({"artifactId":r.artifact_id,"offset":r.offset,"maxBytes":n}),
                &v,
            )
        }
        .await;
        let _ = client.cancel().await;
        result
    })
    .await
    .unwrap_or_else(|_| rejected("owner_deadline"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    fn fixture() -> (Value, Value) {
        let d = json!({"artifactId":"opaque","attemptId":"a","kind":"stdout","digest":format!("sha256:{}","a".repeat(64)),"retainedBytes":3,"truncated":false});
        (
            json!({"schemaVersion":2,"migrationVersion":0,"job":{"jobId":"j","clientRequestId":"k","operationDigest":"op","mechanicallyConverged":true,"resolution":"succeeded"},"attemptsTruncated":false,"attempts":[{"attemptId":"a","state":"succeeded","artifactCount":1}],"artifacts":{"count":1}}),
            json!({"jobId":"j","operationDigest":"op","attemptId":"a","attemptState":"succeeded","executionDisposition":"succeeded","executionTerminal":true,"deliveryDisposition":"committed","recoveryRequired":false,"artifactsAvailable":true,"artifacts":[d]}),
        )
    }
    #[test]
    fn provenance_exact_and_no_suffix_inference() {
        let (i, o) = fixture();
        assert_eq!(
            descriptor("j", "k", "opaque", &i, &o),
            artifact_descriptor::decode(&o["artifacts"][0])
        );
        assert!(descriptor("j", "k", "opaque.stdout", &i, &o).is_none());
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn reject_each_mismatched_witness(field in 0usize..20,foreign in "[a-z]{2,20}") {
            let (mut i,mut o)=fixture();
            match field {
                0=>i["job"]["jobId"]=json!(foreign),
                1=>i["job"]["clientRequestId"]=json!(foreign),
                2=>i["job"]["mechanicallyConverged"]=json!(false),
                3=>i["attemptsTruncated"]=json!(true),
                4=>i["attempts"][0]["artifactCount"]=json!(2),
                5=>o["jobId"]=json!(foreign),
                6=>o["operationDigest"]=json!(format!("foreign-{foreign}")),
                7=>o["attemptId"]=json!(foreign),
                8=>o["attemptState"]=json!(foreign),
                9=>o["executionDisposition"]=json!(foreign),
                10=>o["executionTerminal"]=json!(false),
                11=>o["deliveryDisposition"]=json!("unknown"),
                12=>o["recoveryRequired"]=Value::Null,
                13=>o["artifactsAvailable"]=Value::Null,
                14=>o["artifacts"][0]["attemptId"]=json!(foreign),
                15=>o["artifacts"][0]["digest"]=json!("invalid"),
                16=>o["artifacts"]=json!([o["artifacts"][0].clone(),o["artifacts"][0].clone()]),
                17=>i["migrationVersion"]=json!(1),
                18=>i["schemaVersion"]=json!(3),
                _=>i["attempts"]=json!([]),
            }
            prop_assert!(descriptor("j","k","opaque",&i,&o).is_none());
        }
    }
}
