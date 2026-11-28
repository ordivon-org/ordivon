use ordivon_harness_core::{loads_strict, token_usage::total_tokens};

fn debit(input: &str) -> Option<String> {
    total_tokens(loads_strict(input).unwrap().as_borrowed()).map(|n| n.to_string())
}

#[test]
fn source_counter_families_are_not_mixed() {
    assert_eq!(debit(r#"{"prompt_tokens":90,"output_tokens":60}"#), None);
    assert_eq!(
        debit(r#"{"prompt_tokens":90,"completionTokens":1,"input_tokens":1,"outputTokens":60}"#),
        Some("91".into())
    );
    assert_eq!(
        debit(r#"{"inputTokens":90,"outputTokens":60,"totalTokens":0}"#),
        Some("150".into())
    );
    assert_eq!(debit(r#"{"totalTokens":false,"promptTokens":4}"#), None);
    assert_eq!(
        debit(r#"{"inputTokens":0,"outputTokens":0}"#),
        Some("0".into())
    );
    assert_eq!(
        debit(r#"{"totalTokens":-1,"inputTokens":"5","outputTokens":0,"reasoning_tokens":9}"#),
        None
    );
    assert_eq!(
        debit(r#"{"inputTokens":18446744073709551616,"outputTokens":18446744073709551616}"#),
        Some("36893488147419103232".into())
    );
}

#[test]
#[ignore = "requires locked Python Harness environment via HARNESS_PYTHON"]
fn current_source_oracle() {
    let python = std::env::var_os("HARNESS_PYTHON").expect("locked Python interpreter");
    let script = r#"
import itertools, json, random
from ordivon_harness.ordivon.loop import _usage_total_tokens
keys = ("total_tokens", "totalTokens", "prompt_tokens", "promptTokens",
        "completion_tokens", "completionTokens", "input_tokens", "inputTokens",
        "output_tokens", "outputTokens")
cases = [
    {key: 17 + i * 7 for i, (key, yes) in enumerate(zip(keys, presence)) if yes}
    for presence in itertools.product((False, True), repeat=len(keys))
]
rng = random.Random(20261128)
values = [None, False, True, -1, 0, 1, 99, 2**64, 10**100, "7", {}, [], ["x"]]
for _ in range(1024):
    cases.append({k: rng.choice(values)
                  for k in (*keys, "cache_tokens", "reasoning_tokens") if rng.randrange(3)})
out = []
for usage in cases:
    value = _usage_total_tokens(usage)
    out.append([json.dumps(usage, separators=(",", ":")),
                None if value is None else str(value)])
print(json.dumps(out, separators=(",", ":")))
"#;
    let result = std::process::Command::new(python)
        .args(["-c", script])
        .output()
        .expect("execute source oracle");
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let cases: Vec<(String, Option<String>)> = serde_json::from_slice(&result.stdout).unwrap();
    assert_eq!(cases.len(), 2048);
    for (input, expected) in &cases {
        assert_eq!(&debit(input), expected, "{input}");
    }
    println!(
        "actual Python/Rust token usage parity: {} cases",
        cases.len()
    );
}
