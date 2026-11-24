use super::super::super::RuntimeReleaseEffectBinding;

pub(super) fn release_effect_json_matches(
    value: &serde_json::Value,
    binding: &RuntimeReleaseEffectBinding,
) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    object.get("contract").and_then(|value| value.as_str()) == Some("runtime_release_v1")
        && object.get("effectId").and_then(|value| value.as_str())
            == Some(binding.effect_id.as_str())
        && object.get("requestDigest").and_then(|value| value.as_str())
            == Some(binding.request_digest.as_str())
        && object.get("commit").and_then(|value| value.as_str()) == Some(binding.commit.as_str())
        && object
            .get("candidateManifestDigest")
            .and_then(|value| value.as_str())
            == Some(binding.candidate_manifest_digest.as_str())
        && object
            .get("expectedToolCount")
            .and_then(|value| value.as_u64())
            == Some(u64::from(binding.expected_tool_count))
}
