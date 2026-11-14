//! OpenAI-compatible Chat Completion SSE to the existing strict non-stream
//! decoder. Framing is reused verbatim from CC-Switch v5.11.1 (MIT).
//! This is a model *proposal*, never a ToolGrant or committed Provider result.
use crate::cc_sse::{append_utf8_safe, strip_sse_field, take_sse_block};
use serde_json::{json, Value};
use std::collections::BTreeMap;

#[derive(Default)]
struct ToolParts {
    id: Option<String>,
    kind: Option<String>,
    name: Option<String>,
    arguments: String,
}

fn same_or_first(slot: &mut Option<String>, value: &Value) -> Option<()> {
    let actual = value.as_str()?;
    match slot {
        Some(previous) if previous != actual => None,
        Some(_) => Some(()),
        None => {
            *slot = Some(actual.to_owned());
            Some(())
        }
    }
}

/// Decode only complete, single-choice OpenAI-compatible ChatCompletion SSE.
/// Not Responses/Anthropic SSE. Incomplete, malformed or ambiguous frames
/// intentionally return None; the Provider journal must retain UNKNOWN.
pub(crate) fn decode_chat_completion_sse(bytes: &[u8]) -> Option<Value> {
    // Strictly reject invalid UTF-8; the exact CC-Switch helper then keeps
    // legitimate multibyte characters intact across transport-sized chunks.
    std::str::from_utf8(bytes).ok()?;
    let mut buffer = String::new();
    let mut remainder = Vec::new();
    for chunk in bytes.chunks(4096) {
        append_utf8_safe(&mut buffer, &mut remainder, chunk);
    }
    if !remainder.is_empty() {
        return None;
    }
    let mut content = String::new();
    let mut tools: BTreeMap<usize, ToolParts> = BTreeMap::new();
    let mut finish: Option<String> = None;
    let mut done = false;
    let mut saw_choice = false;
    let mut usage: Option<Value> = None;

    while let Some(block) = take_sse_block(&mut buffer) {
        if block.is_empty() {
            continue;
        }
        let mut data_lines = Vec::new();
        for raw_line in block.lines() {
            let line = raw_line.trim_end_matches('\r');
            if line.is_empty() || line.starts_with(':') {
                continue;
            }
            if let Some(data) = strip_sse_field(line, "data") {
                data_lines.push(data);
            } else if line.starts_with("event:")
                || line.starts_with("id:")
                || line.starts_with("retry:")
            {
                // SSE metadata is not authority for a ChatCompletion decision.
            } else {
                return None;
            }
        }
        if data_lines.is_empty() {
            continue;
        }
        let payload = data_lines.join("\n");
        if payload == "[DONE]" {
            done = true;
            break;
        }
        let frame: Value = serde_json::from_str(&payload).ok()?;
        let choices = frame.get("choices")?.as_array()?;
        if choices.is_empty() {
            // OpenAI stream_options.include_usage may append a usage-only frame.
            if finish.is_some()
                && usage.is_none()
                && frame.get("usage").is_some_and(Value::is_object)
            {
                usage = frame.get("usage").cloned();
                continue;
            }
            return None;
        }
        if finish.is_some() || choices.len() != 1 {
            return None;
        }
        let choice = &choices[0];
        if choice.get("index").and_then(Value::as_u64) != Some(0) {
            return None;
        }
        let delta = choice.get("delta")?.as_object()?;
        saw_choice = true;
        if let Some(role) = delta.get("role") {
            if role.as_str() != Some("assistant") {
                return None;
            }
        }
        if let Some(fragment) = delta.get("content") {
            if !fragment.is_null() {
                content.push_str(fragment.as_str()?);
            }
        }
        if let Some(chunks) = delta.get("tool_calls") {
            for chunk in chunks.as_array()? {
                let index = usize::try_from(chunk.get("index")?.as_u64()?).ok()?;
                if index > 255 {
                    return None;
                }
                let tool = tools.entry(index).or_default();
                if let Some(id) = chunk.get("id") {
                    same_or_first(&mut tool.id, id)?;
                }
                if let Some(kind) = chunk.get("type") {
                    same_or_first(&mut tool.kind, kind)?;
                }
                if let Some(function) = chunk.get("function") {
                    let function = function.as_object()?;
                    if let Some(name) = function.get("name") {
                        same_or_first(&mut tool.name, name)?;
                    }
                    if let Some(arguments) = function.get("arguments") {
                        tool.arguments.push_str(arguments.as_str()?);
                    }
                }
            }
        }
        let reason = choice.get("finish_reason")?;
        if !reason.is_null() {
            finish = Some(reason.as_str()?.to_owned());
        }
    }

    // A visible sentence, finish marker, or HTTP 200 alone is NOT completion.
    if !done || !buffer.trim().is_empty() || !saw_choice {
        return None;
    }
    let finish = finish?;
    if !matches!(finish.as_str(), "stop" | "tool_calls") {
        return None;
    }
    let tool_calls: Option<Vec<Value>> = if tools.is_empty() {
        None
    } else {
        let mut out = Vec::new();
        for (expected_index, (index, parts)) in tools.into_iter().enumerate() {
            if expected_index != index {
                return None;
            }
            out.push(json!({
                "id": parts.id?,
                "type": parts.kind?,
                "function": {
                    "name": parts.name?,
                    "arguments": parts.arguments
                }
            }));
        }
        Some(out)
    };
    let message = match tool_calls {
        Some(calls) => json!({
            "role": "assistant",
            "content": if content.is_empty() { Value::Null } else { json!(content) },
            "tool_calls": calls
        }),
        None => json!({"role": "assistant", "content": content}),
    };
    let mut reply = json!({"choices":[{"finish_reason":finish,"message":message}]});
    if let Some(usage) = usage {
        reply["usage"] = usage;
    }
    Some(reply)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn frames(parts: &[Value], include_done: bool) -> Vec<u8> {
        let mut out = String::new();
        for part in parts {
            out.push_str("data: ");
            out.push_str(&part.to_string());
            out.push_str("\n\n");
        }
        if include_done {
            out.push_str("data: [DONE]\n\n");
        }
        out.into_bytes()
    }
    #[test]
    fn complete_text_requires_finish_and_done() {
        let p = [
            json!({"choices":[{"index":0,"delta":{"role":"assistant","content":"Hel"},"finish_reason":null}]}),
            json!({"choices":[{"index":0,"delta":{"content":"lo"},"finish_reason":null}]}),
            json!({"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}),
        ];
        let good = decode_chat_completion_sse(&frames(&p, true)).unwrap();
        assert_eq!(
            good.pointer("/choices/0/message/content")
                .and_then(Value::as_str),
            Some("Hello")
        );
        assert!(decode_chat_completion_sse(&frames(&p, false)).is_none());
        assert!(decode_chat_completion_sse(&frames(&p[..2], true)).is_none());
    }
    #[test]
    fn complete_tool_arguments_are_reassembled_not_granted() {
        let p = [
            json!({"choices":[{"index":0,"delta":{"role":"assistant","tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"search","arguments":"{\"q\":"}}]},"finish_reason":null}]}),
            json!({"choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\"cat\"}"}}]},"finish_reason":null}]}),
            json!({"choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}]}),
        ];
        let v = decode_chat_completion_sse(&frames(&p, true)).unwrap();
        assert_eq!(
            v.pointer("/choices/0/message/tool_calls/0/function/arguments")
                .and_then(Value::as_str),
            Some("{\"q\":\"cat\"}")
        );
    }
    #[test]
    fn rejects_partial_mutation_and_multiple_choices() {
        let base = [
            json!({"choices":[{"index":0,"delta":{"content":"unsafe"},"finish_reason":"length"}]}),
        ];
        assert!(decode_chat_completion_sse(&frames(&base, true)).is_none());
        let duplicate = [
            json!({"choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":"stop"}]}),
            json!({"choices":[{"index":0,"delta":{"content":"late"},"finish_reason":null}]}),
        ];
        assert!(decode_chat_completion_sse(&frames(&duplicate, true)).is_none());
        let multiple = [
            json!({"choices":[{"index":0,"delta":{"content":"A"},"finish_reason":"stop"},{"index":1,"delta":{"content":"B"},"finish_reason":"stop"}]}),
        ];
        assert!(decode_chat_completion_sse(&frames(&multiple, true)).is_none());
        assert!(decode_chat_completion_sse(b"data: [DONE]\n\n").is_none());
        assert!(decode_chat_completion_sse(b"data: \xff\n\n").is_none());
    }
    #[test]
    fn every_truncated_prefix_refuses_a_confirmed_model_decision() {
        let p = [
            json!({"choices":[{"index":0,"delta":{"content":"complete answer"},"finish_reason":null}]}),
            json!({"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}),
        ];
        let full = frames(&p, true);
        assert!(decode_chat_completion_sse(&full).is_some());
        for end in 0..full.len() {
            assert!(
                decode_chat_completion_sse(&full[..end]).is_none(),
                "strict prefix length {end} falsely completed Provider response"
            );
        }
    }

    #[test]
    fn preserves_utf8_when_real_provider_chunks_split_inside_character() {
        let mk = |s: String| {
            frames(
                &[
                    json!({"choices":[{"index":0,"delta":{"content":s},"finish_reason":null}]}),
                    json!({"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}),
                ],
                true,
            )
        };
        let first = mk("你".into());
        let pos = first
            .windows("你".len())
            .position(|w| w == "你".as_bytes())
            .unwrap();
        let pad = (4095 + 4096 - (pos % 4096)) % 4096;
        let expected = format!("{}你", "x".repeat(pad));
        let source = mk(expected.clone());
        let char_pos = source
            .windows(3)
            .position(|w| w == "你".as_bytes())
            .unwrap();
        assert_eq!(char_pos % 4096, 4095);
        let decoded = decode_chat_completion_sse(&source).unwrap();
        assert_eq!(
            decoded
                .pointer("/choices/0/message/content")
                .and_then(Value::as_str),
            Some(expected.as_str())
        );
    }

    #[test]
    fn sse_usage_is_not_zero_when_unreported_and_is_released_only_with_done() {
        use crate::cc_usage::observe_chat_usage;
        let p = [
            json!({"choices":[{"index":0,"delta":{"content":"yes"},"finish_reason":"stop"}]}),
            json!({"choices":[],"usage":{"prompt_tokens":100,"completion_tokens":7,
                "prompt_tokens_details":{"cached_tokens":40}}}),
        ];
        let full = frames(&p, true);
        let reply = decode_chat_completion_sse(&full).unwrap();
        let usage = observe_chat_usage(&reply).unwrap();
        assert_eq!(usage.input_tokens, 100);
        assert_eq!(usage.cache_read_tokens, 40);
        assert!(decode_chat_completion_sse(&frames(&p, false)).is_none());
        let p_without = [p[0].clone()];
        let without = decode_chat_completion_sse(&frames(&p_without, true)).unwrap();
        assert!(observe_chat_usage(&without).is_none());
    }

    #[test]
    fn duplicated_or_premature_usage_frame_is_not_admitted() {
        let end =
            json!({"choices":[{"index":0,"delta":{"content":"answer"},"finish_reason":"stop"}]});
        let usage = json!({"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":2}});
        assert!(decode_chat_completion_sse(&frames(&[usage.clone(), end.clone()], true)).is_none());
        assert!(decode_chat_completion_sse(&frames(&[end, usage.clone(), usage], true)).is_none());
    }

    #[test]
    fn tolerates_usage_after_finished_choice() {
        let p = [
            json!({"choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":"stop"}]}),
            json!({"choices":[],"usage":{"prompt_tokens":2,"completion_tokens":1}}),
        ];
        assert!(decode_chat_completion_sse(&frames(&p, true)).is_some());
    }
}
