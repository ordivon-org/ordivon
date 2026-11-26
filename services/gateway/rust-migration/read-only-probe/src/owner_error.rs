//! Safe, typed error evidence; no arbitrary upstream message or automatic retry.
use serde::Serialize;
use serde_json::Value;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum CommitState {
    Committed,
    NotCommitted,
    Unknown,
}

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub(crate) enum QualifiedError {
    Runtime {
        commit_state: CommitState,
        retryable: bool,
    },
    RuntimeArtifact {
        action: &'static str,
    },
    Host,
    HostCursor {
        requested: u64,
        observed: u64,
    },
}

// The Python source caps its JSON encoding including separator spaces.
// Restrict this receiver to integral JSON values; floats in arbitrary extension
// fields remain opaque, avoiding cross-language float formatting ambiguity.
fn bounded(v: &Value) -> bool {
    fn size(v: &Value) -> Option<usize> {
        match v {
            Value::Number(n) if !n.is_i64() && !n.is_u64() => None,
            Value::Array(rows) => {
                let mut n = 2usize;
                for (i, r) in rows.iter().enumerate() {
                    n = n
                        .checked_add(size(r)?)?
                        .checked_add(if i == 0 { 0 } else { 2 })?;
                    if n > 8192 {
                        return None;
                    }
                }
                Some(n)
            }
            Value::Object(rows) => {
                let mut n = 2usize;
                for (i, (k, r)) in rows.iter().enumerate() {
                    n = n
                        .checked_add(serde_json::to_string(k).ok()?.len())?
                        .checked_add(2)?
                        .checked_add(size(r)?)?
                        .checked_add(if i == 0 { 0 } else { 2 })?;
                    if n > 8192 {
                        return None;
                    }
                }
                Some(n)
            }
            _ => Some(serde_json::to_string(v).ok()?.len()),
        }
    }
    v.is_object() && size(v).is_some_and(|n| n <= 8192)
}

fn runtime(owner: &str) -> bool {
    matches!(
        owner,
        "runtime.linux" | "runtime.windows" | "runtime.harness"
    )
}

fn qualify(error: &Value, owner: &str, tool: &str) -> Option<QualifiedError> {
    if !bounded(error) {
        return None;
    }
    if runtime(owner) {
        if error["origin"] != "runtime_core"
            || !["code", "commitState", "message", "retryClass"]
                .iter()
                .all(|k| error[*k].as_str().is_some_and(|s| !s.is_empty()))
            || error.get("field").is_some_and(|v| !v.is_string())
        {
            return None;
        }
        let retryable = error["retryable"].as_bool()?;
        let commit_state = match error["commitState"].as_str()? {
            "committed" => CommitState::Committed,
            "not_committed" => CommitState::NotCommitted,
            "unknown" => CommitState::Unknown,
            _ => return None,
        };
        if owner == "runtime.linux"
            && tool == "artifact.read"
            && !retryable
            && commit_state == CommitState::NotCommitted
            && error["retryClass"] == "never"
            && error["field"] == "artifactId"
        {
            let action = match error["code"].as_str()? {
                "ARTIFACT_NOT_UTF8" => Some("authorized-binary-owner-path"),
                "ARTIFACT_NOT_FOUND" => Some("reobserve-original-operation"),
                "ARTIFACT_IDENTITY_CONFLICT" => Some("stop-consumption"),
                _ => None,
            };
            if let Some(action) = action {
                return Some(QualifiedError::RuntimeArtifact { action });
            }
        }
        Some(QualifiedError::Runtime {
            commit_state,
            retryable,
        })
    } else if matches!(owner, "host" | "host.read") {
        if error["kind"] != "ordivon.host-domain-error"
            || error["schemaVersion"].as_i64() != Some(1)
            || !error["code"]
                .as_str()
                .is_some_and(|s| (1..=96).contains(&s.chars().count()))
            || error
                .get("retryable")
                .is_some_and(|v| !v.is_null() && !v.is_boolean())
        {
            return None;
        }
        if owner == "host"
            && tool == "topic.resume"
            && error["code"] == "CONFLICT"
            && error["reason"] == "topic_resume_cursor_ahead"
            && error["resourceKind"] == "topic"
            && error["retryable"].as_bool() == Some(false)
            && error["suggestedAction"] == "reread-topic-horizon-and-check-cursor-domain"
            && let (Some(requested), Some(observed)) = (
                error["requestedAfterSequence"].as_u64(),
                error["observedTopicHighSequence"].as_u64(),
            )
            && observed < requested
            && requested <= i64::MAX as u64
        {
            return Some(QualifiedError::HostCursor {
                requested,
                observed,
            });
        }
        Some(QualifiedError::Host)
    } else {
        None
    }
}

pub(crate) fn decode(result: &Value, owner: &str, tool: &str) -> Option<QualifiedError> {
    if result["isError"].as_bool() != Some(true) {
        return None;
    }
    if let Some(q) = qualify(&result["structuredContent"]["error"], owner, tool) {
        return Some(q);
    }
    let prefix = format!("Error executing tool {tool}: ");
    for item in result["content"].as_array()? {
        if item["type"] != "text" {
            continue;
        }
        let Some(raw) = item["text"].as_str().filter(|s| s.len() <= 8192) else {
            continue;
        };
        let candidate = if runtime(owner) {
            raw.strip_prefix(&prefix).unwrap_or(raw)
        } else if matches!(owner, "host" | "host.read") {
            let Some(s) = raw.strip_prefix(&prefix) else {
                continue;
            };
            s
        } else {
            return None;
        };
        let Ok(value) = serde_json::from_str::<Value>(candidate) else {
            continue;
        };
        let error = if runtime(owner) {
            if value
                .as_object()
                .is_none_or(|m| m.len() != 1 || !m.contains_key("error"))
            {
                continue;
            }
            &value["error"]
        } else {
            &value
        };
        if let Some(q) = qualify(error, owner, tool) {
            return Some(q);
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;
    #[test]
    fn safe_typed_results_never_echo_detail() {
        let e = json!({"origin":"runtime_core","code":"ARTIFACT_NOT_UTF8","commitState":"not_committed","message":"SECRET","retryClass":"never","retryable":false,"field":"artifactId"});
        let r = json!({"isError":true,"structuredContent":{"error":e}});
        assert_eq!(
            decode(&r, "runtime.linux", "artifact.read"),
            Some(QualifiedError::RuntimeArtifact {
                action: "authorized-binary-owner-path"
            })
        );
        assert_eq!(
            decode(&r, "runtime.linux", "job.list"),
            Some(QualifiedError::Runtime {
                commit_state: CommitState::NotCommitted,
                retryable: false
            })
        );
        assert_eq!(decode(&r, "host", "topic.resume"), None);
        let mut false_result = r.clone();
        false_result["isError"] = json!(false);
        assert_eq!(
            decode(&false_result, "runtime.linux", "artifact.read"),
            None
        );
        assert!(
            !serde_json::to_string(&decode(&r, "runtime.linux", "artifact.read"))
                .unwrap()
                .contains("SECRET")
        );
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn cursor_recovery_requires_exact_geometry(requested in any::<u64>(),observed in any::<u64>(),wrong in any::<bool>()) {
            let e=json!({"kind":"ordivon.host-domain-error","schemaVersion":1,"code":"CONFLICT","reason":"topic_resume_cursor_ahead","resourceKind":"topic","retryable":false,"suggestedAction":"reread-topic-horizon-and-check-cursor-domain","requestedAfterSequence":requested,"observedTopicHighSequence":observed,"detail":"SECRET"});
            let r=json!({"isError":true,"structuredContent":{"error":e}});
            let expected=if !wrong && observed<requested && requested<=i64::MAX as u64 {QualifiedError::HostCursor{requested,observed}}else{QualifiedError::Host};
            prop_assert_eq!(decode(&r,"host",if wrong {"work.get"}else{"topic.resume"}),Some(expected));
        }
    }
}
