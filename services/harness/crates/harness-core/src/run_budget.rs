//! Pure reconstruction of spent Run resources from an original retained state.
//!
//! This is an in-process semantic port, not a Store, dispatcher, or permission
//! to start a Provider call. Limits are already materialized by the Run Contract
//! consumer; no legacy-default policy or clock is introduced here.

use crate::{token_usage::total_tokens, CanonicalDocument, CanonicalRef};
use num_bigint::BigUint;

struct Field {
    remaining: &'static str,
    limit: &'static str,
    required: bool,
    positive: bool,
}

const FIELDS: [Field; 10] = [
    Field {
        remaining: "modelCalls",
        limit: "maxModelCalls",
        required: true,
        positive: true,
    },
    Field {
        remaining: "toolCalls",
        limit: "maxToolCalls",
        required: true,
        positive: false,
    },
    Field {
        remaining: "observationBytes",
        limit: "maxObservationBytes",
        required: true,
        positive: true,
    },
    Field {
        remaining: "wallTimeMs",
        limit: "maxWallTimeMs",
        required: true,
        positive: true,
    },
    Field {
        remaining: "totalTokens",
        limit: "maxTotalTokens",
        required: false,
        positive: true,
    },
    Field {
        remaining: "modelRetries",
        limit: "maxModelRetries",
        required: false,
        positive: false,
    },
    Field {
        remaining: "toolCorrections",
        limit: "maxToolCorrections",
        required: false,
        positive: false,
    },
    Field {
        remaining: "conclusionCorrections",
        limit: "maxConclusionCorrections",
        required: false,
        positive: false,
    },
    Field {
        remaining: "observationOnlyTurns",
        limit: "maxObservationOnlyTurns",
        required: false,
        positive: false,
    },
    Field {
        remaining: "noProgressTurns",
        limit: "maxNoProgressTurns",
        required: false,
        positive: false,
    },
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RestoreError {
    InvalidMaterializedLimits,
    InvalidRetainedBudget,
    ExceedsLimit(&'static str),
    WallTimeMismatch,
    InvalidProviderUsage,
}

fn natural(value: CanonicalRef<'_>) -> Option<BigUint> {
    let text = value.integer_text()?;
    if !text.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    text.parse().ok()
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct MaterializedRunLimits([BigUint; 10]);

impl MaterializedRunLimits {
    /// Consume the complete original RunBudget.to_contract_dict projection.
    /// Partial legacy Contracts must first be materialized by their owner.
    pub fn from_document(doc: &CanonicalDocument) -> Result<Self, RestoreError> {
        if doc.object_len() != Some(FIELDS.len() + 1) {
            return Err(RestoreError::InvalidMaterializedLimits);
        }
        let zero = BigUint::default();
        let mut values = std::array::from_fn(|_| BigUint::default());
        for (index, field) in FIELDS.iter().enumerate() {
            let value = doc
                .field(field.limit)
                .and_then(natural)
                .ok_or(RestoreError::InvalidMaterializedLimits)?;
            if field.positive && value == zero {
                return Err(RestoreError::InvalidMaterializedLimits);
            }
            values[index] = value;
        }
        if doc
            .field("maxModelObservationBytes")
            .and_then(natural)
            .is_none_or(|v| v == zero)
        {
            return Err(RestoreError::InvalidMaterializedLimits);
        }
        Ok(Self(values))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RestoredRunBudget {
    pub model_calls: BigUint,
    pub tool_calls: BigUint,
    pub observation_bytes: BigUint,
    pub prior_elapsed_ms: BigUint,
    /// Conservative lower bound, not proof of complete Provider billing.
    pub total_tokens: BigUint,
    pub model_retries: BigUint,
    pub tool_corrections: BigUint,
    pub conclusion_corrections: BigUint,
    pub observation_only_turns: BigUint,
    pub no_progress_turns: BigUint,
    pub provider_attempts: BigUint,
    pub remaining_wall_time_ms: BigUint,
    /// Keep unknown reports distinguishable from measured zero.
    pub unknown_provider_usage_rows: usize,
}

/// Reconstruct counters from the verified retained state. Validate before any
/// caller-requested reset. Explicit elapsed time may exceed the wall limit, but
/// only when remaining wall time is zero. No truncation to machine integers.
pub fn restore_run_budget(
    limits: &MaterializedRunLimits,
    remaining: &CanonicalDocument,
    active_elapsed_ms: Option<&BigUint>,
    provider_usage: CanonicalRef<'_>,
    reset_progress: bool,
) -> Result<RestoredRunBudget, RestoreError> {
    let mut supplied: [Option<BigUint>; 10] = std::array::from_fn(|_| None);
    let fields = remaining
        .object_entries()
        .ok_or(RestoreError::InvalidRetainedBudget)?;
    for (key, value) in fields {
        let i = FIELDS
            .iter()
            .position(|f| f.remaining == key)
            .ok_or(RestoreError::InvalidRetainedBudget)?;
        supplied[i] = Some(natural(value).ok_or(RestoreError::InvalidRetainedBudget)?);
    }
    let mut spent = std::array::from_fn(|_| BigUint::default());
    let mut wall = BigUint::default();
    for (i, field) in FIELDS.iter().enumerate() {
        let remaining = match &supplied[i] {
            Some(value) => value,
            None if !field.required => &limits.0[i],
            None => return Err(RestoreError::InvalidRetainedBudget),
        };
        let limit = &limits.0[i];
        if i == 3 {
            wall = remaining.clone();
            if let Some(elapsed) = active_elapsed_ms {
                let expected = if elapsed >= limit {
                    BigUint::default()
                } else {
                    limit - elapsed
                };
                if wall != expected {
                    return Err(RestoreError::WallTimeMismatch);
                }
                spent[i] = elapsed.clone();
                continue;
            }
        }
        if remaining > limit {
            return Err(RestoreError::ExceedsLimit(field.remaining));
        }
        spent[i] = limit - remaining;
    }
    let [model_calls, tool_calls, observation_bytes, prior_elapsed_ms, retained_tokens, model_retries, tool_corrections, conclusion_corrections, observation_only_turns, no_progress_turns] =
        spent;
    let mut history = BigUint::default();
    let mut unknown_provider_usage_rows = 0;
    let len = provider_usage
        .array_len()
        .ok_or(RestoreError::InvalidProviderUsage)?;
    for index in 0..len {
        let row = provider_usage
            .index(index)
            .ok_or(RestoreError::InvalidProviderUsage)?;
        if row.object_len().is_none() {
            return Err(RestoreError::InvalidProviderUsage);
        }
        match total_tokens(row) {
            Some(count) => history += count,
            None => unknown_provider_usage_rows += 1,
        }
    }
    let provider_attempts = &model_calls + &model_retries;
    Ok(RestoredRunBudget {
        model_calls,
        tool_calls,
        observation_bytes,
        prior_elapsed_ms,
        total_tokens: retained_tokens.max(history),
        model_retries,
        tool_corrections,
        conclusion_corrections,
        observation_only_turns: if reset_progress {
            BigUint::default()
        } else {
            observation_only_turns
        },
        no_progress_turns: if reset_progress {
            BigUint::default()
        } else {
            no_progress_turns
        },
        provider_attempts,
        remaining_wall_time_ms: wall,
        unknown_provider_usage_rows,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::loads_strict;
    use serde_json::{json, Value};

    fn limits() -> MaterializedRunLimits {
        MaterializedRunLimits::from_document(
            &loads_strict(
                r#"{
            "maxModelCalls":8,"maxToolCalls":9,"maxObservationBytes":1000,
            "maxWallTimeMs":500,"maxTotalTokens":50,"maxModelRetries":2,
            "maxToolCorrections":3,"maxConclusionCorrections":3,
            "maxObservationOnlyTurns":6,"maxNoProgressTurns":3,
            "maxModelObservationBytes":32768}"#,
            )
            .unwrap(),
        )
        .unwrap()
    }

    #[test]
    fn exact_recovery_resets_only_progress_and_conserves_known_usage() {
        let retained = loads_strict(
            r#"{"modelCalls":6,"toolCalls":6,
            "observationBytes":920,"wallTimeMs":460,"totalTokens":45,
            "modelRetries":1,"observationOnlyTurns":4,"noProgressTurns":2}"#,
        )
        .unwrap();
        let usage = loads_strict(r#"[{"total_tokens":1,"input_tokens":30,"outputTokens":25},{"inputTokens":3},{"totalTokens":0},{"prompt_tokens":90,"output_tokens":60}]"#).unwrap();
        for reset in [false, true] {
            let state = restore_run_budget(
                &limits(),
                &retained,
                Some(&40u32.into()),
                usage.as_borrowed(),
                reset,
            )
            .unwrap();
            assert_eq!(state.model_calls, 2u32.into());
            assert_eq!(state.tool_calls, 3u32.into());
            assert_eq!(state.observation_bytes, 80u32.into());
            assert_eq!(state.total_tokens, 55u32.into());
            assert_eq!(state.provider_attempts, 3u32.into());
            assert_eq!(
                state.observation_only_turns,
                (if reset { 0u32 } else { 2u32 }).into()
            );
            assert_eq!(
                state.no_progress_turns,
                (if reset { 0u32 } else { 1u32 }).into()
            );
            assert_eq!(state.unknown_provider_usage_rows, 2);
        }
    }

    #[test]
    fn rejects_invalid_retained_counters_even_with_reset() {
        let original =
            json!({"modelCalls":8,"toolCalls":9,"observationBytes":1000,"wallTimeMs":500});
        for field in &FIELDS {
            let mut retained = original.clone();
            retained[field.remaining] = json!(999999);
            let doc = loads_strict(&retained.to_string()).unwrap();
            assert!(restore_run_budget(
                &limits(),
                &doc,
                None,
                loads_strict("[]").unwrap().as_borrowed(),
                true
            )
            .is_err());
        }
        for value in [json!(false), json!(-1), json!("3"), Value::Null] {
            let mut retained = original.clone();
            retained["noProgressTurns"] = value;
            assert!(restore_run_budget(
                &limits(),
                &loads_strict(&retained.to_string()).unwrap(),
                None,
                loads_strict("[]").unwrap().as_borrowed(),
                true
            )
            .is_err());
        }
    }

    #[test]
    fn elapsed_overrun_is_retained_and_known_usage_is_not_saturated() {
        let retained = loads_strict(
            r#"{"modelCalls":8,"toolCalls":9,"observationBytes":1000,"wallTimeMs":0}"#,
        )
        .unwrap();
        let usage = loads_strict(
            r#"[{"inputTokens":18446744073709551616,"outputTokens":18446744073709551616}]"#,
        )
        .unwrap();
        let state = restore_run_budget(
            &limits(),
            &retained,
            Some(&501u32.into()),
            usage.as_borrowed(),
            false,
        )
        .unwrap();
        assert_eq!(state.prior_elapsed_ms, 501u32.into());
        assert_eq!(state.remaining_wall_time_ms, 0u32.into());
        assert_eq!(state.total_tokens.to_string(), "36893488147419103232");
        assert!(restore_run_budget(
            &limits(),
            &retained,
            Some(&499u32.into()),
            loads_strict("[]").unwrap().as_borrowed(),
            false
        )
        .is_err());
    }
}
