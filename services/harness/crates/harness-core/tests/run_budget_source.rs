use num_bigint::BigUint;
use ordivon_harness_core::{
    loads_strict,
    run_budget::{restore_run_budget, MaterializedRunLimits, RestoreError},
};

#[test]
#[ignore = "requires locked Python Harness environment via HARNESS_PYTHON"]
fn current_resume_budget_source_oracle() {
    let python = std::env::var_os("HARNESS_PYTHON").expect("locked Python interpreter");
    // Execute the actual inline Python recovery arithmetic, without starting
    // a Provider or treating this isolated arithmetic as the entire Run.
    let script = r#"
import ast, inspect, json, random
from types import SimpleNamespace
from ordivon_harness.ordivon import loop
from ordivon_harness.ordivon.run_contract import RunBudget
tree = ast.parse(inspect.getsource(loop))
def target(node, name):
    return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
blocks = [n.body for n in ast.walk(tree) if isinstance(getattr(n, "body", None), list)]
blocks += [n.orelse for n in ast.walk(tree) if isinstance(getattr(n, "orelse", None), list)]
matches = [(b, i) for b in blocks for i, n in enumerate(b) if target(n, "remaining") and ast.unparse(n.value) == "state.remaining_budget"]
assert len(matches) == 1
block, start = matches[0]
end = next(i for i in range(start, len(block)) if target(block[i], "remaining_wall_time_ms"))
usage = next(i for i in range(end, len(block)) if target(block[i], "reported_history_tokens"))
assert target(block[usage + 1], "total_tokens")
code = compile(ast.Module(body=block[start:end+1]+block[usage:usage+2], type_ignores=[]), "<current Resume budget>", "exec")
keys = ["modelCalls","toolCalls","observationBytes","wallTimeMs","totalTokens","modelRetries","toolCorrections","conclusionCorrections","observationOnlyTurns","noProgressTurns"]
attrs = ["model_calls","tool_calls","observation_bytes","prior_elapsed_ms","total_tokens","model_retries","tool_corrections","conclusion_corrections","observation_only_turns","no_progress_turns","provider_attempts","remaining_wall_time_ms"]
rng = random.Random(20261128)
out = []
for i in range(1024):
    budget = RunBudget(rng.randint(1,10),rng.randint(0,10),rng.randint(1,1000),rng.randint(1,1000),rng.randint(1,1000),rng.randint(0,10),rng.randint(0,10),rng.randint(0,10),rng.randint(0,10),rng.randint(0,10))
    limits = budget.to_contract_dict()
    maxima = {k:limits["max"+k[0].upper()+k[1:]] for k in keys}
    remaining = {k:rng.randint(0,maxima[k]) for k in keys if k in keys[:4] or rng.choice([True,False])}
    elapsed = None if rng.choice([True,False]) else rng.randint(0,maxima["wallTimeMs"]*2)
    if elapsed is not None:
        remaining["wallTimeMs"] = max(0,maxima["wallTimeMs"]-elapsed)
    reset = bool(i%2)
    reports = [{}, {"total_tokens":0}, {"prompt_tokens":90,"output_tokens":60}, {"inputTokens":2**70,"outputTokens":2**70}, {"totalTokens":5,"input_tokens":8,"output_tokens":9}]
    reports = rng.sample(reports, rng.randint(0,len(reports)))
    # Alternate invalid cases; isolate the observed reset-before-bound-check
    # difference from ordinary valid-state parity.
    defect = None
    if i%8 == 0:
        k = keys[(i//8)%len(keys)]
        remaining[k] = maxima[k]+1
        defect = "reset_progress" if reset and k in keys[-2:] else "bounds"
    elif i%8 == 1:
        k = keys[(i//8)%len(keys)]
        remaining[k] = False
        defect = "type"
    elif i%8 == 2:
        remaining["unexpected"] = 0
        defect = "extra"
    elif i%8 == 3:
        remaining.pop(keys[(i//8)%4],None)
        defect = "missing"
    if i%64 == 5:
        remaining["noProgressTurns"] = maxima["noProgressTurns"]+1
        defect = "reset_progress"
    env = dict(self=SimpleNamespace(budget=budget,working_view_projector=None),
        state=SimpleNamespace(remaining_budget=remaining,active_elapsed_ms=elapsed),
        initial_messages=[{}] if reset else [],projected_caller_input=[],
        provider_usage=reports,_usage_total_tokens=loop._usage_total_tokens)
    try:
        exec(code, env)
        expected = [str(env[a]) for a in attrs]
        expected.append(str(sum(loop._usage_total_tokens(r) is None for r in reports)))
    except ValueError:
        expected = None
    out.append([json.dumps(limits),json.dumps(remaining),None if elapsed is None else str(elapsed),
                json.dumps(reports),reset,expected,defect=="reset_progress"])
print(json.dumps(out,separators=(",",":")))
"#;
    let result = std::process::Command::new(python)
        .args(["-c", script])
        .output()
        .expect("execute current source oracle");
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    type Row = (
        String,
        String,
        Option<String>,
        String,
        bool,
        Option<Vec<String>>,
        bool,
    );
    let cases: Vec<Row> = serde_json::from_slice(&result.stdout).unwrap();
    assert_eq!(cases.len(), 1024);
    let mut strict_reset = 0;
    for (limits, remaining, elapsed, usage, reset, expected, strict_difference) in cases {
        let limits = MaterializedRunLimits::from_document(&loads_strict(&limits).unwrap()).unwrap();
        let elapsed = elapsed.map(|n| n.parse::<BigUint>().unwrap());
        let result = restore_run_budget(
            &limits,
            &loads_strict(&remaining).unwrap(),
            elapsed.as_ref(),
            loads_strict(&usage).unwrap().as_borrowed(),
            reset,
        );
        if strict_difference {
            assert!(expected.is_some());
            assert!(matches!(
                result,
                Err(RestoreError::ExceedsLimit("noProgressTurns"))
            ));
            strict_reset += 1;
            continue;
        }
        let actual = result.ok().map(|r| {
            vec![
                r.model_calls.to_string(),
                r.tool_calls.to_string(),
                r.observation_bytes.to_string(),
                r.prior_elapsed_ms.to_string(),
                r.total_tokens.to_string(),
                r.model_retries.to_string(),
                r.tool_corrections.to_string(),
                r.conclusion_corrections.to_string(),
                r.observation_only_turns.to_string(),
                r.no_progress_turns.to_string(),
                r.provider_attempts.to_string(),
                r.remaining_wall_time_ms.to_string(),
                r.unknown_provider_usage_rows.to_string(),
            ]
        });
        assert_eq!(actual, expected, "remaining={remaining}, reset={reset}");
    }
    assert_eq!(strict_reset, 16);
    println!("Current Python Resume arithmetic: 1008 matching cases; 16 deliberately stricter native reset rejections");
}
