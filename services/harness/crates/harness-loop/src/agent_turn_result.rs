//! A bounded, source-compatible no-Tool AgentTurnResult producer.
//! Original Python model.AgentTurnResult and AgentRunConclusion define the
//! output contract. The HTTP wire witness is evidence, not DomainSuccess.
use crate::native_loop::{ModelDecision, ProviderWireObservation};
use ordivon_harness_core::CanonicalDocument;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TurnResultError {
    NoVerifiedWire,
    InvalidSourceIdentity,
    UnqualifiedDecision,
    UnqualifiedModel,
    InvalidWireFinish,
}

fn txt(s: &str) -> CanonicalDocument {
    CanonicalDocument::string(s)
}
fn num(n: u64) -> CanonicalDocument {
    CanonicalDocument::integer_from_decimal(&n.to_string())
        .expect("u64 is exactly representable as a JSON integer")
}

/// Strictly no-Tool positive HTTP proposal, not proof of solving the Domain.
/// A distinct owner must later validate the Domain completion before any
/// AgentSolved declaration. A missing token observation remains an empty
/// usage object, never invented zero counters or an invoice.
///
/// Source identity model_call_id must come from the admitted Provider Call;
/// the builder does not invent identity, currentness, grant, or timestamps.
pub fn author_no_tool_turn_result(
    model_call_id: &str,
    requested_model: &str,
    decision: &ModelDecision,
    wire: Option<&ProviderWireObservation>,
) -> Result<CanonicalDocument, TurnResultError> {
    let wire = wire.ok_or(TurnResultError::NoVerifiedWire)?;
    let ModelDecision::ProposeCompletion(summary) = decision else {
        return Err(TurnResultError::UnqualifiedDecision);
    };
    if summary.is_empty()
        || summary.trim() != summary
        || summary.len() > 8000
        || model_call_id.is_empty()
        || model_call_id.trim() != model_call_id
        || model_call_id.len() > 300
        || requested_model.is_empty()
        || requested_model.trim() != requested_model
        || requested_model.len() > 300
    {
        return Err(TurnResultError::InvalidSourceIdentity);
    }
    if wire.finish_reason() != "stop"
        || wire.raw_response_bytes() == 0
        || !wire.raw_response_digest().starts_with("sha256:")
    {
        return Err(TurnResultError::InvalidWireFinish);
    }
    if wire
        .provider_reported_model()
        .is_some_and(|reported| reported != requested_model)
    {
        // Reject silent fallback to a different, possibly billable model until
        // a source-approved route/effective-model binding is implemented.
        return Err(TurnResultError::UnqualifiedModel);
    }
    let mut usage = Vec::<(String, CanonicalDocument)>::new();
    if let Some(tokens) = wire.reported_usage() {
        usage.extend([
            ("inputTokens".into(), num(tokens.input_tokens)),
            ("outputTokens".into(), num(tokens.output_tokens)),
            ("cacheReadTokens".into(), num(tokens.cache_read_tokens)),
            (
                "cacheCreationTokens".into(),
                num(tokens.cache_creation_tokens),
            ),
        ]);
    }
    let conclusion = CanonicalDocument::object(vec![
        ("status".into(), txt("candidate_completed")),
        ("summary".into(), txt(summary)),
        (
            "artifactRefs".into(),
            CanonicalDocument::array(vec![]).expect("empty array is canonical"),
        ),
        (
            "evidenceRefs".into(),
            CanonicalDocument::array(vec![]).expect("empty array is canonical"),
        ),
        (
            "unresolvedUnknowns".into(),
            CanonicalDocument::array(vec![]).expect("empty array is canonical"),
        ),
    ])
    .map_err(|_| TurnResultError::UnqualifiedDecision)?;
    CanonicalDocument::object(vec![
        ("schemaVersion".into(), num(1)),
        ("kind".into(), txt("ordivon.agent-turn-result")),
        ("modelCallId".into(), txt(model_call_id)),
        ("modelId".into(), txt(requested_model)),
        ("content".into(), txt(summary)),
        (
            "toolCalls".into(),
            CanonicalDocument::array(vec![]).expect("empty array is canonical"),
        ),
        ("conclusion".into(), conclusion),
        (
            "usage".into(),
            CanonicalDocument::object(usage).map_err(|_| TurnResultError::UnqualifiedDecision)?,
        ),
        ("finishReason".into(), txt(wire.finish_reason())),
        ("rawResponseDigest".into(), txt(wire.raw_response_digest())),
    ])
    .map_err(|_| TurnResultError::UnqualifiedDecision)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cc_usage::ProviderUsageObservation;
    use crate::native_loop::ProviderWireObservation;

    fn sample() -> ProviderWireObservation {
        ProviderWireObservation::from_validated_http(
            br#"{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"Hello"}}],"model":"model:verified"}"#,
            Some("model:verified"),
            Some(ProviderUsageObservation{
                input_tokens:9,output_tokens:4,cache_read_tokens:0,
                cache_creation_tokens:0,reported_model:Some("model:verified".into()),
            }),
            "stop",
        )
    }
    #[test]
    fn missing_usage_remains_unknown_not_a_fake_zero_bill() {
        let wire=ProviderWireObservation::from_validated_http(
            br#"{"choices":[{"finish_reason":"stop","message":{"role":"assistant","content":"Hi"}}]}"#,
            None,None,"stop",
        );
        let doc = author_no_tool_turn_result(
            "model-call:no-usage",
            "model:verified",
            &ModelDecision::ProposeCompletion("Hi".into()),
            Some(&wire),
        )
        .unwrap();
        assert_eq!(doc.field("usage").unwrap().object_len(), Some(0));
        assert_eq!(
            doc.field("rawResponseDigest").unwrap().as_str(),
            Some(wire.raw_response_digest())
        );
        let unsafe_finish =
            ProviderWireObservation::from_validated_http(b"partial", None, None, "length");
        assert!(matches!(
            author_no_tool_turn_result(
                "model-call:no-usage",
                "model:verified",
                &ModelDecision::ProposeCompletion("Hi".into()),
                Some(&unsafe_finish)
            ),
            Err(TurnResultError::InvalidWireFinish)
        ));
    }

    #[test]
    fn no_tool_positive_result_requires_wire_provenance() {
        let w = sample();
        let decision = ModelDecision::ProposeCompletion("Hello".into());
        let result =
            author_no_tool_turn_result("model-call:fixture", "model:verified", &decision, Some(&w))
                .unwrap();
        assert_eq!(
            result.field("rawResponseDigest").unwrap().as_str(),
            Some(w.raw_response_digest())
        );
        assert_eq!(
            result.field("kind").unwrap().as_str(),
            Some("ordivon.agent-turn-result")
        );
        assert!(author_no_tool_turn_result(
            "model-call:fixture",
            "model:verified",
            &decision,
            None
        )
        .is_err());
        assert!(author_no_tool_turn_result(
            "model-call:fixture",
            "model:other",
            &decision,
            Some(&w)
        )
        .is_err());
        assert!(author_no_tool_turn_result(
            "model-call:fixture",
            "model:verified",
            &ModelDecision::RequestInput,
            Some(&w)
        )
        .is_err());
    }
}
