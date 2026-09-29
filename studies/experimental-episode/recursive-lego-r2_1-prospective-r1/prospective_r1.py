from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.model import AgentTurnRequest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
SKILL_PATH = ROOT / ".agents" / "skills" / "recursive-lego-calculus" / "SKILL.md"
EVIDENCE = HERE.parent / "evidence"
CALIBRATION_BANK_PATH = EVIDENCE / "design" / "calibration-bank.json"
INFERENTIAL_BANK_PATH = EVIDENCE / "design" / "inferential-bank.json"
PREREG_PATH = EVIDENCE / "preregistration" / "20260929-r1" / "preregistration.json"
PREFLIGHT_PATH = EVIDENCE / "preflight" / "20260929-r1" / "provider-preflight.json"
CALIBRATION_OUTPUT = EVIDENCE / "calibration" / "20260929-r1"
INFERENTIAL_OUTPUT = EVIDENCE / "inferential" / "20260929-r1"

EXPERIMENT_ID = "experiment:recursive-lego-r2_1-prospective-r1-20260929"
EXPECTED_SKILL_SHA256 = "1985dc2765bda250b1f2f76e1b85425141e6aadbb7e39ef5bd5b92d063f08c09"
REQUESTED_MODEL = "deepseek-flash"
ARMS = ("control", "r2_1")
FAMILIES = (
    "minimal_frontier",
    "verifier_bridge",
    "legal_program",
    "experimental_replication",
    "qualified_optimization",
    "semantic_completion",
)
CALIBRATION_VARIANTS_PER_FAMILY = 2
INFERENTIAL_VARIANTS_PER_FAMILY = 4
CALIBRATION_SEED = 20260929011
INFERENTIAL_SEED = 20260929012
MAX_OUTPUT_TOKENS = 512
CALL_TIMEOUT_SECONDS = 45.0

CONTROL_SYSTEM = (
    "You are a fresh Agent solving one frozen evaluation task. Use only the supplied facts. "
    "Do not invent missing evidence. Preserve UNKNOWN when the evidence does not establish PASS or FAIL. "
    "Choose exactly one listed option and return exactly one JSON object of the form "
    '{"choice":"OPTION_ID"} with no markdown or additional prose.'
)


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def journal_append(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def skill_contract() -> str:
    raw = SKILL_PATH.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SKILL_SHA256:
        raise RuntimeError(f"canonical R2.1 Skill digest differs: {actual}")
    return raw.decode("utf-8")


def option_rows(correct: str, distractors: list[str], *, seed: int) -> tuple[list[dict[str, str]], str]:
    texts = [correct, *distractors]
    rng = random.Random(seed)
    rng.shuffle(texts)
    labels = [f"OPT_{index}" for index in range(1, len(texts) + 1)]
    rows = [{"id": label, "text": text} for label, text in zip(labels, texts, strict=True)]
    gold = next(row["id"] for row in rows if row["text"] == correct)
    return rows, gold


def _frontier_task(index: int, cohort: str) -> dict[str, Any]:
    a, b, c, d = [f"L{index}{letter}" for letter in "ABCD"]
    scenario = (
        f"A system has four diagnostic loci. Evidence directly invalidates {a}'s interface contract and independently "
        f"invalidates {c}'s authority assumption. {b} is a downstream symptom whose only dependency is {a}; {d} is a "
        f"downstream symptom whose only dependency is {c}. No evidence independently invalidates {b} or {d}. "
        "Which repair frontier is minimally supported by the evidence?"
    )
    correct = f"Repair exactly {{{a}, {c}}}; preserve the downstream loci until re-verification."
    distractors = [
        f"Repair only {a}, because an earliest single broken layer must always exist.",
        f"Repair {{{b}, {d}}}, because symptoms are the observed failures.",
        f"Restart and rebuild {{{a}, {b}, {c}, {d}}} to eliminate uncertainty.",
    ]
    options, gold = option_rows(correct, distractors, seed=1000 + index)
    return _task("minimal_frontier", index, cohort, scenario, options, gold)


def _bridge_task(index: int, cohort: str) -> dict[str, Any]:
    bridged = index % 2 == 0
    if bridged:
        scenario = (
            "A checker returned PASS for predicate psi. The frozen problem specification is phi. A separately frozen and "
            "accepted theorem establishes psi => phi under assumptions A1 and A2, and both A1 and A2 are observed true "
            "for this exact instance. What problem-level verdict is justified?"
        )
        correct = "PASS for phi is justified by the checked psi plus the valid bridge and satisfied assumptions."
        distractors = [
            "UNKNOWN for phi because a verifier can never support a problem specification.",
            "FAIL for phi because psi and phi have different names.",
            "PASS for phi solely because the checker process exited zero; the bridge is irrelevant.",
        ]
    else:
        scenario = (
            "A checker returned PASS for predicate psi='serialized rows satisfy schema'. The frozen problem specification "
            "phi is 'all rows represent the correct real-world entities'. No identity or implication from psi to phi has "
            "been established, and no real-world entity check was observed. What problem-level verdict is justified?"
        )
        correct = "UNKNOWN for phi; PASS on psi does not establish phi without a justified bridge."
        distractors = [
            "PASS for phi because any formal checker PASS transfers to the enclosing problem.",
            "FAIL for phi because lack of a bridge is proof that phi is false.",
            "Rerun the same psi checker and declare PASS for phi if it passes twice.",
        ]
    options, gold = option_rows(correct, distractors, seed=2000 + index)
    return _task("verifier_bridge", index, cohort, scenario, options, gold)


def _legal_program_task(index: int, cohort: str) -> dict[str, Any]:
    token = f"K{index}"
    scenario = (
        f"Initial state: fetched=false, validated=false, published=false, token={token}. Actions: "
        "FETCH has precondition not fetched and effect fetched=true; VALIDATE has precondition fetched and effect "
        "validated=true; PUBLISH has precondition validated and effect published=true; RESET has precondition published "
        "and effect fetched=false, validated=false, published=false. Goal: published=true. Which proposed program is legal "
        "at every intermediate state and reaches the goal?"
    )
    correct = "FETCH -> VALIDATE -> PUBLISH"
    distractors = [
        "VALIDATE -> FETCH -> PUBLISH",
        "FETCH -> PUBLISH -> VALIDATE",
        "PUBLISH -> RESET -> FETCH",
    ]
    options, gold = option_rows(correct, distractors, seed=3000 + index)
    return _task("legal_program", index, cohort, scenario, options, gold)


def _replication_task(index: int, cohort: str) -> dict[str, Any]:
    tasks = 3 + (index % 4)
    repeats = 4 + (index % 3)
    scenario = (
        f"A workflow treatment is assigned once to each of {tasks} independently generated task instances. For noise "
        f"diagnosis, the Provider is then called {repeats} times on each same task under that assigned treatment. The study "
        "wants to estimate the treatment effect across tasks. What is the independent replication count and how should the "
        "repeated Provider calls be treated?"
    )
    correct = f"Independent n={tasks}; the {repeats} repeated calls per task are nested stochasticity measurements, not additional independent task replicates."
    distractors = [
        f"Independent n={tasks * repeats}; every Provider call is a new replicate.",
        f"Independent n={repeats}; the task instances are repeated measurements.",
        "There is no independent unit because model outputs are stochastic.",
    ]
    options, gold = option_rows(correct, distractors, seed=4000 + index)
    return _task("experimental_replication", index, cohort, scenario, options, gold)


def _optimization_task(index: int, cohort: str) -> dict[str, Any]:
    rows = [
        (f"A{index}", 100 + index, False),
        (f"B{index}", 92 + index, True),
        (f"C{index}", 88 + index, True),
        (f"D{index}", 80 + index, False),
    ]
    if index % 2 == 0:
        rows = [
            (f"A{index}", 100 + index, True),
            (f"B{index}", 99 + index, True),
            (f"C{index}", 110 + index, False),
            (f"D{index}", 70 + index, False),
        ]
    feasible = [row for row in rows if row[2]]
    best = max(feasible, key=lambda row: row[1])
    table = "; ".join(f"{name}: objective={score}, hardFeasible={str(ok).lower()}" for name, score, ok in rows)
    scenario = (
        f"A frozen optimization has a hard feasibility contract that may not be violated. Candidates: {table}. "
        "Which candidate may be accepted as the objective optimum under the qualified feasible region?"
    )
    correct = f"Choose {best[0]}, the highest-objective candidate among hard-feasible candidates."
    distractors = [
        f"Choose {max(rows, key=lambda row: row[1])[0]}, because objective value dominates hard constraints.",
        "Choose no candidate; optimization is forbidden whenever any candidate is infeasible.",
        "Temporarily accept the infeasible maximum and re-qualify after deployment.",
    ]
    options, gold = option_rows(correct, distractors, seed=5000 + index)
    return _task("qualified_optimization", index, cohort, scenario, options, gold)


def _semantic_task(index: int, cohort: str) -> dict[str, Any]:
    bridged = index % 2 == 0
    if bridged:
        scenario = (
            "A Runtime Job exited zero and delivery is committed. A domain verifier then checked the frozen acceptance "
            "predicate for the exact produced artifact and returned PASS; the verifier target is identical to the task's "
            "semantic completion predicate. What semantic completion standing is justified?"
        )
        correct = "PASS semantic completion is justified for the frozen predicate; execution evidence and domain verification are both present."
        distractors = [
            "UNKNOWN because Runtime can never contribute any evidence to semantic completion.",
            "FAIL because process exit zero is not semantic truth.",
            "PASS solely from process exit zero; the domain verifier adds nothing.",
        ]
    else:
        scenario = (
            "A Runtime Job exited zero, delivery is committed, and stdout contains the expected filename. No domain verifier "
            "has checked the file contents and the task's semantic acceptance predicate is not otherwise observed. What "
            "semantic completion standing is justified?"
        )
        correct = "UNKNOWN semantic completion; mechanical execution success does not establish the unverified domain predicate."
        distractors = [
            "PASS semantic completion because exit code zero and expected stdout are sufficient.",
            "FAIL semantic completion because absence of verification proves the artifact is wrong.",
            "PASS after replaying the same successful Runtime Job once more.",
        ]
    options, gold = option_rows(correct, distractors, seed=6000 + index)
    return _task("semantic_completion", index, cohort, scenario, options, gold)


def _task(family: str, index: int, cohort: str, scenario: str, options: list[dict[str, str]], gold: str) -> dict[str, Any]:
    task_id = f"LEGO-R21-{cohort[:3].upper()}-{family.upper().replace('_', '-')}-{index:02d}"
    visible = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-task",
        "taskId": task_id,
        "family": family,
        "cohort": cohort,
        "scenario": scenario,
        "options": options,
        "responseContract": {"type": "object", "required": ["choice"], "choiceMustBeOneListedOptionId": True},
    }
    return {
        "visible": visible,
        "goldChoice": gold,
        "taskDigest": canonical_digest(visible),
        "goldDigest": canonical_digest({"taskId": task_id, "goldChoice": gold}),
    }


GENERATORS = {
    "minimal_frontier": _frontier_task,
    "verifier_bridge": _bridge_task,
    "legal_program": _legal_program_task,
    "experimental_replication": _replication_task,
    "qualified_optimization": _optimization_task,
    "semantic_completion": _semantic_task,
}


def build_bank(cohort: str) -> dict[str, Any]:
    if cohort not in {"calibration", "inferential"}:
        raise ValueError(cohort)
    count = CALIBRATION_VARIANTS_PER_FAMILY if cohort == "calibration" else INFERENTIAL_VARIANTS_PER_FAMILY
    offset = 100 if cohort == "calibration" else 0
    tasks = [GENERATORS[family](offset + i, cohort) for family in FAMILIES for i in range(1, count + 1)]
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-task-bank",
        "experimentId": EXPERIMENT_ID,
        "cohort": cohort,
        "families": list(FAMILIES),
        "taskCount": len(tasks),
        "tasks": tasks,
        "generationContract": {
            "generatorDigest": file_digest(HERE),
            "calibrationDisjointFromInferential": True,
            "independentUnit": "task-instance",
        },
        "nonClaims": [
            "These synthetic tasks probe six R2.1 reasoning seams and are not a general task population.",
            "Hidden gold is runner-side only and is never included in Provider messages.",
        ],
    }
    value["bankDigest"] = canonical_digest(value)
    return value


def build_schedule(bank: dict[str, Any], *, seed: int) -> dict[str, Any]:
    trials = []
    for task in bank["tasks"]:
        for arm in ARMS:
            trials.append({
                "taskId": task["visible"]["taskId"],
                "family": task["visible"]["family"],
                "arm": arm,
                "independentTaskBlock": task["visible"]["taskId"],
            })
    rng = random.Random(seed)
    rng.shuffle(trials)
    for ordinal, row in enumerate(trials, 1):
        row["ordinal"] = ordinal
        row["trialId"] = f"trial:lego-r21:{bank['cohort'][:3]}:{ordinal:03d}"
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-paired-schedule",
        "experimentId": EXPERIMENT_ID,
        "cohort": bank["cohort"],
        "assignmentSeed": seed,
        "bankDigest": bank["bankDigest"],
        "independentTaskBlockCount": bank["taskCount"],
        "trialCount": len(trials),
        "arms": list(ARMS),
        "replicationLaw": "task-instance-is-independent; paired arm calls within one task are not additional independent task replicates",
        "trials": trials,
    }
    value["scheduleDigest"] = canonical_digest(value)
    return value


def load_bank(path: Path, cohort: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("kind") != "ordivon.recursive-lego-prospective-task-bank" or value.get("cohort") != cohort:
        raise RuntimeError(f"task bank kind/cohort differs: {path}")
    expected = canonical_digest({key: item for key, item in value.items() if key != "bankDigest"})
    if value.get("bankDigest") != expected:
        raise RuntimeError(f"task bank digest mismatch: {path}")
    return value


def generate_banks() -> None:
    json_write(CALIBRATION_BANK_PATH, build_bank("calibration"))
    json_write(INFERENTIAL_BANK_PATH, build_bank("inferential"))


def build_preregistration(source_revision: str) -> dict[str, Any]:
    subprocess.run(["git", "merge-base", "--is-ancestor", source_revision, "HEAD"], cwd=ROOT, check=True)
    calibration = load_bank(CALIBRATION_BANK_PATH, "calibration")
    inferential = load_bank(INFERENTIAL_BANK_PATH, "inferential")
    skill_contract()
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-r2_1-prospective-preregistration",
        "experimentId": EXPERIMENT_ID,
        "sourceRevision": source_revision,
        "runnerBinding": {"path": str(HERE.relative_to(ROOT)), "digest": file_digest(HERE)},
        "skillBinding": {"path": str(SKILL_PATH.relative_to(ROOT)), "digest": "sha256:" + EXPECTED_SKILL_SHA256},
        "provider": {"name": "deepseek", "requestedModelId": REQUESTED_MODEL, "maxOutputTokens": MAX_OUTPUT_TOKENS, "timeoutMs": int(CALL_TIMEOUT_SECONDS * 1000)},
        "arms": {
            "control": {"contractDigest": sha256_bytes(CONTROL_SYSTEM.encode()), "description": "generic evidence-bounded problem solving"},
            "r2_1": {"contractDigest": canonical_digest([CONTROL_SYSTEM, skill_contract()]), "description": "same control contract plus exact canonical R2.1 Skill bytes"},
        },
        "calibration": {"bankDigest": calibration["bankDigest"], "schedule": build_schedule(calibration, seed=CALIBRATION_SEED)},
        "inferential": {"bankDigest": inferential["bankDigest"], "schedule": build_schedule(inferential, seed=INFERENTIAL_SEED)},
        "primaryEndpoint": {
            "name": "exactChoiceCorrect",
            "estimand": "mean paired task-level correctness difference R2.1 minus control over the frozen inferential task bank",
            "test": "two-sided exact McNemar conditional binomial test over discordant task pairs",
        },
        "secondaryDiagnostics": ["jsonParseValid", "effectiveModelIdentity", "promptTokens", "completionTokens", "totalTokens", "latencyMs"],
        "calibrationGate": {"minimumSuccessesInclusive": 4, "maximumSuccessesInclusive": 20, "minimumMixedTasks": 2, "minimumMixedFamilies": 2},
        "stopRules": [
            "No Provider call before provider preflight is frozen.",
            "An unmatched trial_started stops the cohort until explicitly reconciled; no blind retry.",
            "Effective-model drift or Provider exception stops before the next trial.",
            "Calibration tasks never enter inferential estimates.",
            "A failed calibration gate closes this task-bank revision and forbids inferential execution.",
        ],
        "nonClaims": [
            "R1 tests the method-contract treatment without live domain Tools or Runtime effects.",
            "A positive result is bounded to this model, prompt carrier and frozen synthetic task families.",
            "No weighted overall-intelligence score is defined.",
        ],
    }
    value["preregistrationDigest"] = canonical_digest(value)
    return value


def write_preregistration(source_revision: str) -> None:
    if PREREG_PATH.exists():
        raise RuntimeError("preregistration already exists; create a new experiment revision instead of rewriting")
    json_write(PREREG_PATH, build_preregistration(source_revision))


def load_preregistration() -> dict[str, Any]:
    value = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    expected = canonical_digest({key: item for key, item in value.items() if key != "preregistrationDigest"})
    if value.get("preregistrationDigest") != expected:
        raise RuntimeError("preregistration digest mismatch")
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source = value.get("sourceRevision")
    if not isinstance(source, str):
        raise RuntimeError("preregistration sourceRevision missing")
    subprocess.run(["git", "merge-base", "--is-ancestor", source, current], cwd=ROOT, check=True)
    if value["runnerBinding"]["digest"] != file_digest(HERE):
        raise RuntimeError("runner changed after preregistration")
    if value["skillBinding"]["digest"] != file_digest(SKILL_PATH):
        raise RuntimeError("Skill changed after preregistration")
    return value


def _request(messages: list[dict[str, str]], *, run_id: str, ordinal: int) -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id=run_id,
        turn_id=f"turn:{run_id}:{ordinal}",
        sequence=1,
        assignment_id=f"assignment:{run_id}:{ordinal}",
        context_digest=canonical_digest(messages),
        tool_catalog_digest=canonical_digest([]),
        messages=tuple(messages),
        tools=(),
        remaining_budget={"modelCalls": 1, "modelRetries": 0, "toolCalls": 0, "wallTimeMs": int(CALL_TIMEOUT_SECONDS * 1000), "observationOnlyTurns": 0, "noProgressTurns": 1},
    )


def _settings() -> DeepSeekSettings:
    settings = DeepSeekSettings.from_secret_file(timeout_seconds=CALL_TIMEOUT_SECONDS, max_output_tokens=MAX_OUTPUT_TOKENS)
    if settings.model != REQUESTED_MODEL:
        raise RuntimeError(f"configured Provider model differs: {settings.model} != {REQUESTED_MODEL}")
    return settings


def run_preflight() -> dict[str, Any]:
    prereg = load_preregistration()
    settings = _settings()
    adapter = DeepSeekTurnAdapter(settings)
    rows = []
    for ordinal in (1, 2):
        messages = [
            {"role": "system", "content": "Provider identity preflight. Return the token READY and no other text."},
            {"role": "user", "content": "READY"},
        ]
        result = adapter.invoke(_request(messages, run_id="lego-r21-preflight", ordinal=ordinal))
        rows.append({
            "ordinal": ordinal,
            "requestedModelId": settings.model,
            "effectiveModelId": result.effective_model_id,
            "modelId": result.model_id,
            "rawResponseDigest": result.raw_response_digest,
            "usage": result.usage,
        })
    effective = sorted({row["effectiveModelId"] for row in rows})
    standing = "PASS_EFFECTIVE_IDENTITY" if effective == [REQUESTED_MODEL] else "FAIL_EFFECTIVE_IDENTITY_DRIFT"
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-provider-preflight",
        "experimentId": EXPERIMENT_ID,
        "preregistrationDigest": prereg["preregistrationDigest"],
        "provider": "deepseek",
        "requestedModelId": REQUESTED_MODEL,
        "credentialScopeId": settings.credential_scope_id,
        "toolAuthority": {"control": [], "r2_1": [], "equivalent": True},
        "rows": rows,
        "effectiveModelIds": effective,
        "standing": standing,
    }
    value["preflightDigest"] = canonical_digest(value)
    json_write(PREFLIGHT_PATH, value)
    return value


def load_preflight(prereg: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    expected = canonical_digest({key: item for key, item in value.items() if key != "preflightDigest"})
    if value.get("preflightDigest") != expected:
        raise RuntimeError("provider preflight digest mismatch")
    if value.get("preregistrationDigest") != prereg["preregistrationDigest"]:
        raise RuntimeError("provider preflight targets a different preregistration")
    if value.get("standing") != "PASS_EFFECTIVE_IDENTITY":
        raise RuntimeError("provider preflight did not pass")
    return value


def _task_prompt(task: dict[str, Any]) -> str:
    visible = task["visible"]
    return (
        "Frozen task follows. Hidden evaluator gold is not shown.\n"
        + json.dumps(visible, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )


def _messages(task: dict[str, Any], arm: str) -> list[dict[str, str]]:
    system = CONTROL_SYSTEM
    if arm == "r2_1":
        system += "\n\nApply this exact advisory method contract when solving the task:\n---BEGIN R2.1---\n" + skill_contract() + "\n---END R2.1---"
    elif arm != "control":
        raise ValueError(arm)
    return [{"role": "system", "content": system}, {"role": "user", "content": _task_prompt(task)}]


def parse_choice(content: str, option_ids: set[str]) -> tuple[bool, str | None]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return False, None
    if not isinstance(value, dict) or set(value) != {"choice"} or not isinstance(value.get("choice"), str):
        return False, None
    choice = value["choice"]
    return (choice in option_ids), choice if choice in option_ids else None


def _journal_state(path: Path) -> tuple[set[str], set[str]]:
    started: set[str] = set()
    completed: set[str] = set()
    if not path.exists():
        return started, completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") == "trial_started":
            started.add(row["trialId"])
        elif row.get("event") == "trial_completed":
            completed.add(row["trialId"])
    return started, completed


def _run_cohort(cohort: str, output_dir: Path) -> list[dict[str, Any]]:
    prereg = load_preregistration()
    preflight = load_preflight(prereg)
    bank_path = CALIBRATION_BANK_PATH if cohort == "calibration" else INFERENTIAL_BANK_PATH
    bank = load_bank(bank_path, cohort)
    schedule = prereg[cohort]["schedule"]
    if schedule["bankDigest"] != bank["bankDigest"]:
        raise RuntimeError("schedule/bank digest mismatch")
    task_by_id = {row["visible"]["taskId"]: row for row in bank["tasks"]}
    journal = output_dir / "journal.jsonl"
    started, completed = _journal_state(journal)
    uncertain = sorted(started - completed)
    if uncertain:
        raise RuntimeError(f"unmatched trial_started requires reconciliation before dispatch: {uncertain}")
    settings = _settings()
    adapter = DeepSeekTurnAdapter(settings)
    records = []
    for trial in schedule["trials"]:
        path = output_dir / "trials" / f"{trial['trialId'].replace(':', '-')}.json"
        if trial["trialId"] in completed:
            records.append(json.loads(path.read_text(encoding="utf-8")))
            continue
        task = task_by_id[trial["taskId"]]
        messages = _messages(task, trial["arm"])
        journal_append(journal, {"event": "trial_started", "trialId": trial["trialId"], "ordinal": trial["ordinal"], "observedAtUnixMs": int(time.time() * 1000)})
        started_at = time.monotonic()
        try:
            result = adapter.invoke(_request(messages, run_id=f"lego-r21-{cohort}-{trial['arm']}", ordinal=trial["ordinal"]))
            latency = int(round((time.monotonic() - started_at) * 1000))
        except Exception as exc:
            error_record = {
                "schemaVersion": 1,
                "kind": "ordivon.recursive-lego-prospective-trial-error",
                **trial,
                "errorType": type(exc).__name__,
                "error": str(exc)[:1000],
                "preregistrationDigest": prereg["preregistrationDigest"],
                "preflightDigest": preflight["preflightDigest"],
            }
            error_record["recordDigest"] = canonical_digest(error_record)
            json_write(path, error_record)
            journal_append(journal, {"event": "trial_completed", "trialId": trial["trialId"], "recordDigest": error_record["recordDigest"], "status": "provider_error", "observedAtUnixMs": int(time.time() * 1000)})
            raise RuntimeError(f"Provider exception stops cohort at {trial['trialId']}: {exc}") from exc
        if result.effective_model_id != REQUESTED_MODEL:
            raise RuntimeError(f"effective model drift at {trial['trialId']}: {result.effective_model_id}")
        option_ids = {row["id"] for row in task["visible"]["options"]}
        parse_valid, choice = parse_choice(result.content, option_ids)
        correct = parse_valid and choice == task["goldChoice"]
        record = {
            "schemaVersion": 1,
            "kind": "ordivon.recursive-lego-prospective-trial",
            "experimentId": EXPERIMENT_ID,
            "cohort": cohort,
            **trial,
            "taskDigest": task["taskDigest"],
            "goldDigest": task["goldDigest"],
            "preregistrationDigest": prereg["preregistrationDigest"],
            "preflightDigest": preflight["preflightDigest"],
            "requestedModelId": REQUESTED_MODEL,
            "effectiveModelId": result.effective_model_id,
            "rawResponseDigest": result.raw_response_digest,
            "jsonParseValid": parse_valid,
            "choice": choice,
            "exactChoiceCorrect": bool(correct),
            "latencyMs": latency,
            "usage": result.usage,
            "responseDigest": sha256_bytes(result.content.encode()),
            "response": result.content,
        }
        record["recordDigest"] = canonical_digest(record)
        json_write(path, record)
        journal_append(journal, {"event": "trial_completed", "trialId": trial["trialId"], "recordDigest": record["recordDigest"], "status": "completed", "observedAtUnixMs": int(time.time() * 1000)})
        records.append(record)
        print(json.dumps({"trial": trial["trialId"], "family": trial["family"], "arm": trial["arm"], "correct": correct, "parse": parse_valid, "tokens": result.usage.get("total_tokens") if isinstance(result.usage, dict) else None}, sort_keys=True), flush=True)
    return records


def calibration_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 24 or len({row["trialId"] for row in records}) != 24:
        raise RuntimeError("calibration requires 24 unique completed trials")
    if any(row.get("kind") != "ordivon.recursive-lego-prospective-trial" for row in records):
        raise RuntimeError("calibration contains non-completed trial records")
    successes = sum(bool(row["exactChoiceCorrect"]) for row in records)
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        by_task.setdefault(row["taskId"], []).append(row)
    mixed = []
    families = set()
    for task_id, rows in sorted(by_task.items()):
        if len(rows) != 2 or {row["arm"] for row in rows} != set(ARMS):
            raise RuntimeError(f"calibration paired block incomplete: {task_id}")
        outcomes = {bool(row["exactChoiceCorrect"]) for row in rows}
        if len(outcomes) == 2:
            mixed.append(task_id)
            families.add(rows[0]["family"])
    passed = 4 <= successes <= 20 and len(mixed) >= 2 and len(families) >= 2
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-calibration-gate",
        "experimentId": EXPERIMENT_ID,
        "standing": "PASS_CALIBRATION_DIFFICULTY" if passed else "REJECT_TASK_BANK_DIFFICULTY",
        "trialCount": 24,
        "successCount": successes,
        "failureCount": 24 - successes,
        "mixedTaskCount": len(mixed),
        "mixedTaskIds": mixed,
        "mixedFamilyCount": len(families),
        "mixedFamilies": sorted(families),
        "thresholds": {"minimumSuccessesInclusive": 4, "maximumSuccessesInclusive": 20, "minimumMixedTasks": 2, "minimumMixedFamilies": 2},
        "nonClaims": ["Calibration does not enter the inferential effect estimate.", "Passing does not establish treatment efficacy."],
    }
    value["gateDigest"] = canonical_digest(value)
    return value


def finalize_calibration() -> dict[str, Any]:
    prereg = load_preregistration()
    records = _run_cohort("calibration", CALIBRATION_OUTPUT)
    gate = calibration_gate(records)
    gate["preregistrationDigest"] = prereg["preregistrationDigest"]
    gate["preflightDigest"] = load_preflight(prereg)["preflightDigest"]
    gate["receiptDigest"] = canonical_digest(gate)
    json_write(CALIBRATION_OUTPUT / "gate.json", gate)
    return gate


def _rational(numerator: int, denominator: int) -> dict[str, int]:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    divisor = math.gcd(numerator, denominator)
    return {"numerator": numerator // divisor, "denominator": denominator // divisor}


def _binomial_two_sided(n10: int, n01: int) -> dict[str, int]:
    n = n10 + n01
    if n == 0:
        return _rational(1, 1)
    k = min(n10, n01)
    numerator = 2 * sum(math.comb(n, i) for i in range(k + 1))
    denominator = 2 ** n
    if numerator >= denominator:
        return _rational(1, 1)
    return _rational(numerator, denominator)


def analyze_inferential(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != 48 or len({row["trialId"] for row in records}) != 48:
        raise RuntimeError("inferential analysis requires 48 unique completed trials")
    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for row in records:
        by_task.setdefault(row["taskId"], {})[row["arm"]] = row
    if len(by_task) != 24 or any(set(pair) != set(ARMS) for pair in by_task.values()):
        raise RuntimeError("inferential paired blocks incomplete")
    n10 = n01 = both_correct = both_wrong = 0
    per_task = []
    for task_id in sorted(by_task):
        pair = by_task[task_id]
        c = bool(pair["control"]["exactChoiceCorrect"])
        t = bool(pair["r2_1"]["exactChoiceCorrect"])
        if t and not c:
            n10 += 1
        elif c and not t:
            n01 += 1
        elif c and t:
            both_correct += 1
        else:
            both_wrong += 1
        per_task.append({"taskId": task_id, "family": pair["control"]["family"], "controlCorrect": c, "r2_1Correct": t, "pairedDifference": int(t) - int(c)})
    effect = _rational(n10 - n01, 24)
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.recursive-lego-prospective-inferential-analysis",
        "experimentId": EXPERIMENT_ID,
        "independentTaskBlockCount": 24,
        "r2_1MinusControlAccuracyDifference": effect,
        "discordant": {"r2_1OnlyCorrect": n10, "controlOnlyCorrect": n01},
        "concordant": {"bothCorrect": both_correct, "bothWrong": both_wrong},
        "mcnemarExactTwoSidedP": _binomial_two_sided(n10, n01),
        "perTask": per_task,
        "nonClaims": ["The p-value is conditional on the frozen 24-task bank and does not create a broader task population.", "Resource diagnostics are secondary and not part of a weighted score."],
    }
    value["analysisDigest"] = canonical_digest(value)
    return value


def run_inferential() -> dict[str, Any]:
    gate = json.loads((CALIBRATION_OUTPUT / "gate.json").read_text(encoding="utf-8"))
    if gate.get("standing") != "PASS_CALIBRATION_DIFFICULTY":
        raise RuntimeError("inferential execution forbidden: calibration did not pass")
    records = _run_cohort("inferential", INFERENTIAL_OUTPUT)
    analysis = analyze_inferential(records)
    analysis["calibrationGateDigest"] = gate["receiptDigest"]
    analysis["analysisReceiptDigest"] = canonical_digest(analysis)
    json_write(INFERENTIAL_OUTPUT / "analysis.json", analysis)
    return analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--generate-banks", action="store_true")
    action.add_argument("--preregister", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--run-calibration", action="store_true")
    action.add_argument("--run-inferential", action="store_true")
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    if args.generate_banks:
        generate_banks()
        print("GENERATED_TASK_BANKS")
        return 0
    if args.preregister:
        if not args.source_revision:
            raise SystemExit("--source-revision is required with --preregister")
        write_preregistration(args.source_revision)
        print("PREREGISTRATION=" + json.dumps(json.loads(PREREG_PATH.read_text()), sort_keys=True))
        return 0
    if args.preflight:
        value = run_preflight()
        print("PREFLIGHT=" + json.dumps(value, sort_keys=True))
        return 0 if value["standing"] == "PASS_EFFECTIVE_IDENTITY" else 2
    if args.run_calibration:
        gate = finalize_calibration()
        print("CALIBRATION_GATE=" + json.dumps(gate, sort_keys=True))
        return 0 if gate["standing"] == "PASS_CALIBRATION_DIFFICULTY" else 3
    analysis = run_inferential()
    print("INFERENTIAL_ANALYSIS=" + json.dumps(analysis, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
