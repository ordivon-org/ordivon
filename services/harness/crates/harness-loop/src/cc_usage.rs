//! OpenAI-compatible usage observation, derived from pinned CC-Switch v5.11.1
//! src-tauri/src/proxy/usage/parser.rs (MIT, SaladDay commit 7a860510).
//!
//! This is a *reported* token count, NOT a bill, priced charge, durable PG
//! Provider receipt, or evidence that an ambiguous request was not billed.
//! The upstream parser narrows u64 counters with `as u32`, which can wrap;
//! Harness retains source meaning without numeric truncation.
use serde_json::Value;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProviderUsageObservation {
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_read_tokens: u64,
    pub cache_creation_tokens: u64,
    pub reported_model: Option<String>,
}
impl ProviderUsageObservation {
    /// Preserve CC's cache-bucket semantics: all-cache requests may still
    /// represent billable work, but pricing and settlement are external.
    pub fn has_reported_tokens(&self) -> bool {
        self.input_tokens > 0
            || self.output_tokens > 0
            || self.cache_read_tokens > 0
            || self.cache_creation_tokens > 0
    }
}

fn optional_count(usage: &Value, names: &[&str]) -> Option<u64> {
    // Like CC-Switch, use the first present key, but do not silently turn an
    // invalid present field into zero or truncate valid 64-bit counters.
    for name in names {
        if let Some(v) = usage.pointer(name) {
            return v.as_u64();
        }
    }
    Some(0)
}

/// The OpenAI Chat Completion / OpenRouter usage projection from CC-Switch:
/// prompt_tokens/completion_tokens + either standard or vendor cache buckets.
/// On malformed or absent token counts, retain None (unobserved, not 0).
pub fn observe_chat_usage(reply: &Value) -> Option<ProviderUsageObservation> {
    let usage = reply.get("usage")?;
    if !usage.is_object() {
        return None;
    }
    Some(ProviderUsageObservation {
        input_tokens: usage.get("prompt_tokens")?.as_u64()?,
        output_tokens: usage.get("completion_tokens")?.as_u64()?,
        cache_read_tokens: optional_count(
            usage,
            &[
                "/cache_read_input_tokens",
                "/input_tokens_details/cached_tokens",
                "/prompt_tokens_details/cached_tokens",
            ],
        )?,
        cache_creation_tokens: optional_count(
            usage,
            &[
                "/cache_creation_input_tokens",
                "/input_tokens_details/cache_write_tokens",
                "/prompt_tokens_details/cache_write_tokens",
            ],
        )?,
        reported_model: reply
            .get("model")
            .and_then(Value::as_str)
            .map(str::to_owned),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn openai_and_openrouter_cache_paths_preserved() {
        let reply = json!({"model":"model:reported","usage":{
            "prompt_tokens":100,"completion_tokens":20,
            "prompt_tokens_details":{"cached_tokens":50,"cache_write_tokens":4}
        }});
        let usage = observe_chat_usage(&reply).unwrap();
        assert_eq!((usage.input_tokens, usage.output_tokens), (100, 20));
        assert_eq!(
            (usage.cache_read_tokens, usage.cache_creation_tokens),
            (50, 4)
        );
        assert_eq!(usage.reported_model.as_deref(), Some("model:reported"));
    }

    #[test]
    fn vendor_buckets_take_priority_without_truncation() {
        let big = u64::from(u32::MAX) + 17;
        let reply = json!({"usage":{
            "prompt_tokens":big,"completion_tokens":0,
            "cache_read_input_tokens":big,
            "prompt_tokens_details":{"cached_tokens":1}
        }});
        let usage = observe_chat_usage(&reply).unwrap();
        assert_eq!(usage.input_tokens, big);
        assert_eq!(usage.cache_read_tokens, big);
        assert!(usage.has_reported_tokens());
    }

    #[test]
    fn zero_is_not_the_same_as_missing_or_invalid() {
        assert!(observe_chat_usage(&json!({"choices":[]})).is_none());
        assert!(observe_chat_usage(&json!({"usage":{
            "prompt_tokens":5,"completion_tokens":null
        }}))
        .is_none());
        assert!(observe_chat_usage(&json!({"usage":{
            "prompt_tokens":5,"completion_tokens":2,
            "cache_read_input_tokens":"garbage"
        }}))
        .is_none());
        let zero = observe_chat_usage(&json!({"usage":{
            "prompt_tokens":0,"completion_tokens":0
        }}))
        .unwrap();
        assert!(!zero.has_reported_tokens());
    }

    #[test]
    fn invalid_signed_decimal_or_fraction_is_not_usage() {
        for value in [json!(-1), json!(1.5), json!("10")] {
            assert!(observe_chat_usage(&json!({"usage":{
                "prompt_tokens":value,"completion_tokens":3
            }}))
            .is_none());
        }
    }
}
