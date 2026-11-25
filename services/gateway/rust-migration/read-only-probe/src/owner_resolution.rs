//! A single principal-scoped Owner page is a readback, not an execution permit.
use crate::logic::parse_execution_ref;
use crate::owner_transport::{ReadRequest, protected_read};
use serde::Serialize;
use serde_json::Value;
use std::{path::Path, time::Duration};

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "resolution", rename_all = "snake_case")]
pub enum Resolution {
    Found {
        operation_ref: String,
        native_id: String,
        workspace_id: String,
    },
    Absent,
    Ambiguous,
    Unobserved {
        reason: &'static str,
    },
}

fn unknown(reason: &'static str) -> Resolution {
    Resolution::Unobserved { reason }
}

pub fn project(page: &Value, request_id: &str) -> Resolution {
    if request_id.is_empty() {
        return unknown("invalid_request_identity");
    }
    let Some(rows) = page.get("jobs").and_then(Value::as_array) else {
        return unknown("invalid_job_page");
    };
    // Limit two suffices for uniqueness; never infer absence from a bad page.
    if rows.len() > 2 {
        return unknown("invalid_job_page");
    }
    let mut ids = std::collections::BTreeSet::new();
    for row in rows {
        if row.get("clientRequestId").and_then(Value::as_str) != Some(request_id) {
            return unknown("mismatched_request_identity");
        }
        let Some(id) = row
            .get("jobId")
            .and_then(Value::as_str)
            .filter(|s| !s.is_empty() && !s.contains(':'))
        else {
            return unknown("invalid_job_identity");
        };
        if !ids.insert(id)
            || row
                .get("workspaceId")
                .and_then(Value::as_str)
                .is_none_or(|s| s.trim().is_empty())
        {
            return unknown("invalid_job_identity");
        }
    }
    // Legacy producer omits absent cursor, PG emits null. A continuing page
    // must be full and its cursor must name the final row's exact coordinates.
    if let Some(cursor) = page.get("nextCursor").filter(|v| !v.is_null()) {
        if rows.len() != 2
            || cursor.get("jobId").and_then(Value::as_str) != rows[1]["jobId"].as_str()
            || cursor.get("createdAtMs").and_then(Value::as_u64).is_none()
            || cursor["createdAtMs"].as_u64() != rows[1]["createdAtMs"].as_u64()
        {
            return unknown("invalid_job_cursor");
        }
        return Resolution::Ambiguous;
    }
    match rows.as_slice() {
        [] => Resolution::Absent,
        [row] => {
            let native_id = row["jobId"].as_str().expect("qualified identity");
            let operation_ref = format!("ordivon-exec:v1:runtime.linux:{native_id}");
            if parse_execution_ref(&operation_ref) != Some(("runtime.linux", native_id)) {
                return unknown("invalid_job_identity");
            }
            Resolution::Found {
                operation_ref,
                native_id: native_id.to_owned(),
                workspace_id: row["workspaceId"]
                    .as_str()
                    .expect("qualified identity")
                    .to_owned(),
            }
        }
        _ => Resolution::Ambiguous,
    }
}

pub async fn resolve_protected_fixture(
    endpoint: &str,
    credential: &Path,
    request_id: &str,
    legacy: bool,
) -> Resolution {
    if request_id.is_empty() {
        return unknown("invalid_request_identity");
    }
    match protected_read(
        endpoint,
        credential,
        Duration::from_secs(3),
        legacy,
        ReadRequest::Resolve { request_id },
    )
    .await
    {
        Ok(page) => project(&page, request_id),
        Err(reason) => unknown(reason),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;
    fn row(id: &str, request: &str, at: u64) -> Value {
        json!({"jobId":id,"clientRequestId":request,"workspaceId":"ws-test","createdAtMs":at})
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(256))]
        #[test]
        fn independent_page_cardinality_and_identity(
            request in "[a-z0-9]{1,32}",id in "[a-z0-9]{1,32}",
            size in 0usize..4, continuation in any::<bool>(),
        ){
            let rows:Vec<_>=(0..size).map(|i|row(&format!("{id}-{i}"),&request,100-i as u64)).collect();
            let cursor=if continuation && size>0 {json!({"jobId":format!("{id}-{}",size-1),"createdAtMs":101-size as u64})}else if continuation {json!({})}else{Value::Null};
            let expected=match (size,continuation) {
                (0,false)=>Resolution::Absent,
                (1,false)=>Resolution::Found{operation_ref:format!("ordivon-exec:v1:runtime.linux:{id}-0"),native_id:format!("{id}-0"),workspace_id:"ws-test".into()},
                (2,_)=>Resolution::Ambiguous,
                (3,_)=>unknown("invalid_job_page"),
                _=>unknown("invalid_job_cursor"),
            };
            prop_assert_eq!(project(&json!({"jobs":rows,"nextCursor":cursor}),&request),expected);
        }
        #[test]
        fn foreign_or_corrupt_identity_never_resolves(
            request in "[a-z]{1,20}", id in "[a-z]{1,20}", field in 0u8..5,
        ){
            let mut good=row(&id,&request,5);
            let mut bad=row("sibling",&request,4);
            match field {
                0=>bad["clientRequestId"]=json!(format!("{request}-other")),
                1=>bad["jobId"]=json!(id),
                2=>bad["workspaceId"]=json!(false),
                3=>bad["jobId"]=json!("not:roundtrip"),
                _=>{good["workspaceId"]=json!(" ");}
            }
            let result=project(&json!({"jobs":[good,bad]}),&request);
            prop_assert!(matches!(result,Resolution::Unobserved{..}), "foreign or corrupt row must remain unobserved");
        }
        #[test]
        fn independent_trace_does_not_reuse_previous_resolution(
            actions in prop::collection::vec(0u8..5,1..32),
        ){
            for action in actions {
                let (page,expected)=match action {
                    0=>(json!({"jobs":[]}),Resolution::Absent),
                    1=>(json!({"jobs":[row("a","r",1)]}),Resolution::Found{operation_ref:"ordivon-exec:v1:runtime.linux:a".into(),native_id:"a".into(),workspace_id:"ws-test".into()}),
                    2=>(json!({"jobs":[row("a","r",2),row("b","r",1)]}),Resolution::Ambiguous),
                    3=>(json!({"jobs":[row("a","other",1)]}),unknown("mismatched_request_identity")),
                    _=>(json!({"jobs":[],"nextCursor":{}}),unknown("invalid_job_cursor")),
                };
                prop_assert_eq!(project(&page,"r"),expected);
            }
        }
    }
}
