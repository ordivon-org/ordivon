//! Artifact byte-window refinement. Full-window hash is not domain acceptance.
use crate::{artifact_descriptor, logic::parse_execution_ref};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Request<'a> {
    artifact_id: &'a str,
    offset: u64,
    max_bytes: u64,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct OwnerWindow<'a> {
    job_id: &'a str,
    artifact_id: &'a str,
    content: &'a str,
    offset: u64,
    next_offset: u64,
    eof: bool,
    digest: &'a str,
}
#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub(crate) enum Window<'a> {
    Unobserved {
        reason: &'static str,
    },
    Qualified {
        owner: &'a str,
        native_id: &'a str,
        artifact_id: &'a str,
        digest: &'a str,
        offset: u64,
        next_offset: u64,
        eof: bool,
        content: &'a str,
        // None is an incomplete-window witness, not a negative digest result.
        full_digest_verified: Option<bool>,
    },
}
fn unknown(reason: &'static str) -> Window<'static> {
    Window::Unobserved { reason }
}
pub(crate) fn qualify<'a>(
    reference: &'a str,
    descriptor: &Value,
    request: &'a Value,
    response: &'a Value,
) -> Window<'a> {
    if parse_execution_ref(reference).is_none() {
        return unknown("invalid_operation_ref");
    }
    let Some(d) = artifact_descriptor::decode(descriptor) else {
        return unknown("unqualified_descriptor");
    };
    qualify_bound(reference, &d, request, response)
}

pub(crate) fn qualify_bound<'a>(
    reference: &'a str,
    d: &artifact_descriptor::Descriptor,
    request: &'a Value,
    response: &'a Value,
) -> Window<'a> {
    let Some((owner, native_id)) = parse_execution_ref(reference) else {
        return unknown("invalid_operation_ref");
    };
    let Ok(r) = Request::deserialize(request) else {
        return unknown("invalid_request");
    };
    if r.artifact_id != d.artifact_id()
        || !(1..=1_048_576).contains(&r.max_bytes)
        || r.offset > d.retained_bytes()
    {
        return unknown("invalid_request");
    }
    let Some(limit) = r.offset.checked_add(r.max_bytes) else {
        return unknown("invalid_request");
    };
    let Ok(v) = OwnerWindow::deserialize(response) else {
        return unknown("invalid_window");
    };
    if v.job_id != native_id || v.artifact_id != r.artifact_id || v.digest != d.digest() {
        return unknown("mismatched_window_identity");
    }
    if v.offset != r.offset
        || v.next_offset < v.offset
        || v.next_offset > limit
        || v.next_offset > d.retained_bytes()
    {
        return unknown("invalid_range");
    }
    if v.eof != (v.next_offset == d.retained_bytes()) || (!v.eof && v.next_offset == v.offset) {
        return unknown("invalid_progress_or_eof");
    }
    if v.content.len() as u64 != v.next_offset - v.offset {
        return unknown("invalid_byte_length");
    }
    let full_digest_verified = if v.offset == 0 && v.eof {
        let digest = Sha256::digest(v.content.as_bytes());
        let hex: String = digest.iter().map(|b| format!("{b:02x}")).collect();
        if !v.digest.strip_prefix("sha256:").is_some_and(|s| s == hex) {
            return unknown("full_digest_mismatch");
        }
        Some(true)
    } else {
        None
    };
    Window::Qualified {
        owner,
        native_id,
        artifact_id: v.artifact_id,
        digest: v.digest,
        offset: v.offset,
        next_offset: v.next_offset,
        eof: v.eof,
        content: v.content,
        full_digest_verified,
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;
    const REF: &str = "ordivon-exec:v1:runtime.linux:job-a";
    fn fixture(text: &str) -> (Value, Value, Value) {
        let digest = format!(
            "sha256:{}",
            Sha256::digest(text.as_bytes())
                .iter()
                .map(|b| format!("{b:02x}"))
                .collect::<String>()
        );
        (
            json!({"artifactId":"a","attemptId":"opaque","kind":"stdout","digest":digest,"retainedBytes":text.len(),"truncated":false}),
            json!({"artifactId":"a","offset":0,"maxBytes":1048576}),
            json!({"jobId":"job-a","artifactId":"a","offset":0,"nextOffset":text.len(),"eof":true,"digest":digest,"content":text}),
        )
    }
    #[test]
    fn partial_window_does_not_claim_full_digest() {
        let (d, mut r, mut v) = fixture("中文🙂");
        r["maxBytes"] = json!(3);
        v["nextOffset"] = json!(3);
        v["content"] = json!("中");
        v["eof"] = json!(false);
        assert!(matches!(
            qualify(REF, &d, &r, &v),
            Window::Qualified {
                full_digest_verified: None,
                ..
            }
        ));
        v["eof"] = json!(true);
        assert_eq!(qualify(REF, &d, &r, &v), unknown("invalid_progress_or_eof"));
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn unicode_full_window_and_same_length_corruption(text in ".{1,64}",field in 0u8..7){
            let (d,r,mut v)=fixture(&text);
            prop_assert!(matches!(qualify(REF,&d,&r,&v),Window::Qualified{full_digest_verified:Some(true),..}), "full window must verify");
            match field{
                0=>v["jobId"]=json!("other"),
                1=>v["artifactId"]=json!("other"),
                2=>v["nextOffset"]=json!(text.len()+1),
                3=>v["eof"]=json!(false),
                4=>v["offset"]=json!(1),
                5=>v["digest"]=json!(format!("sha256:{}", "z".repeat(64))),
                _=>v["content"]=json!(if text.bytes().all(|b|b==b'x'){"y".repeat(text.len())}else{"x".repeat(text.len())}),
            }
            let bad=qualify(REF,&d,&r,&v);
            let rejected=matches!(bad,Window::Unobserved{..});
            prop_assert!(rejected,"corrupt window accepted");
        }
    }
}
