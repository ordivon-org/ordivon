//! Pure Provider usage accounting over the existing canonical Run representation.
//! Unknown usage is not a measured zero. Counter families must be complete.
use crate::CanonicalRef;
use num_bigint::BigUint;

/// Match the source Loop's conservative maximum of reported total and complete
/// same-family input/output counters. Cache/reasoning fields are not extra totals.
/// This is a debit projection, not an invoice or admission decision.
pub fn total_tokens(usage: CanonicalRef<'_>) -> Option<BigUint> {
    fn greatest(usage: CanonicalRef<'_>, aliases: &[&str]) -> Option<BigUint> {
        aliases
            .iter()
            .filter_map(|name| {
                let raw = usage.field(name)?.integer_text()?;
                if !raw.bytes().all(|b| b.is_ascii_digit()) {
                    return None;
                }
                raw.parse::<BigUint>().ok()
            })
            .max()
    }
    let mut result = greatest(usage, &["total_tokens", "totalTokens"]);
    for (inputs, outputs) in [
        (
            ["prompt_tokens", "promptTokens"],
            ["completion_tokens", "completionTokens"],
        ),
        (
            ["input_tokens", "inputTokens"],
            ["output_tokens", "outputTokens"],
        ),
    ] {
        if let (Some(a), Some(b)) = (greatest(usage, &inputs), greatest(usage, &outputs)) {
            let candidate = a + b;
            result = Some(match result {
                Some(old) => old.max(candidate),
                None => candidate,
            });
        }
    }
    result
}
