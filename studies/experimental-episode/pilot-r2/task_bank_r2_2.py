from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from anc_canonical import canonical_digest

FAMILIES = ("repository_repair", "edit_addressing", "edit_multiregion")
INFERENTIAL_VARIANTS_PER_FAMILY = 8
CALIBRATION_VARIANTS_PER_FAMILY = 2
REVISION = "r2.2"


def _sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class GeneratedTask:
    task_id: str
    family: str
    cohort: str
    variant_index: int
    files: dict[str, str]
    target_path: str
    visible_test_path: str
    oracle_source: str
    hidden_verifier_source: str
    known_invalid_sources: dict[str, str]
    known_invalid_expectations: dict[str, tuple[bool, bool]]
    objective: str
    structural_profile: dict[str, Any]
    sentinel: bool = False

    def definition(self) -> dict[str, Any]:
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-generated-evaluation-task",
            "taskId": self.task_id,
            "family": self.family,
            "cohort": self.cohort,
            "variantIndex": self.variant_index,
            "generatorRevision": REVISION,
            "objective": self.objective,
            "targetPath": self.target_path,
            "visibleTestPath": self.visible_test_path,
            "readPaths": sorted(self.files),
            "visibleFiles": [
                {"path": p, "digest": _sha_bytes(c.encode())}
                for p, c in sorted(self.files.items())
            ],
            "oracleDigest": _sha_bytes(self.oracle_source.encode()),
            "hiddenVerifierDigest": _sha_bytes(self.hidden_verifier_source.encode()),
            "structuralProfile": self.structural_profile,
            "sentinel": self.sentinel,
        }
        value["taskDigest"] = canonical_digest(value)
        return value


def repository_repair_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:03d}"
    fn = f"distribute_units_{suffix}"
    preview = f"preview_floor_{suffix}"
    module = f"allocation_{suffix}.py"
    visible = f"test_allocation_{suffix}.py"
    weights_a = [2 + index % 5, 3 + index % 7, 5 + index % 3, 7]
    total_a = 41 + index % 11
    weights_b = [1, 1, 1, 1, 1]
    total_b = 7 + index % 5
    validation = f"""def _validate_{suffix}(total: int, weights: list[int]) -> None:\n    if isinstance(total, bool) or not isinstance(total, int) or total < 0:\n        raise ValueError("total must be a non-negative integer")\n    if not isinstance(weights, list) or not weights:\n        raise ValueError("weights must be a non-empty list")\n    if any(isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0 for weight in weights):\n        raise ValueError("weights must contain positive integers")\n"""
    preview_body = f'''def {preview}(total: int, weights: list[int]) -> list[int]:\n    """Diagnostic floor allocation; intentionally not the repair target."""\n    _validate_{suffix}(total, weights)\n    weight_total = sum(weights)\n    return [(total * weight) // weight_total for weight in weights]\n'''
    target_body = f'''def {fn}(total: int, weights: list[int]) -> list[int]:\n    """Allocate exactly total units using stable largest remainders."""\n    _validate_{suffix}(total, weights)\n    weight_total = sum(weights)\n    return [(total * weight) // weight_total for weight in weights]\n'''
    baseline = (
        "from __future__ import annotations\n\n"
        + validation
        + "\n"
        + preview_body
        + "\n"
        + target_body
    )
    old = f'''def {fn}(total: int, weights: list[int]) -> list[int]:\n    """Allocate exactly total units using stable largest remainders."""\n    _validate_{suffix}(total, weights)\n    weight_total = sum(weights)\n    return [(total * weight) // weight_total for weight in weights]'''
    new = f'''def {fn}(total: int, weights: list[int]) -> list[int]:\n    """Allocate exactly total units using stable largest remainders."""\n    _validate_{suffix}(total, weights)\n    weight_total = sum(weights)\n    allocations = [(total * weight) // weight_total for weight in weights]\n    remaining = total - sum(allocations)\n    order = sorted(range(len(weights)), key=lambda i: (-(total * weights[i] % weight_total), i))\n    for i in order[:remaining]:\n        allocations[i] += 1\n    return allocations'''
    oracle = baseline.replace(old, new, 1)
    visible_source = f"""from {module[:-3]} import {fn}\n\ndef test_visible_contract():\n    assert sum({fn}({total_a}, {weights_a!r})) == {total_a}\n    assert sum({fn}({total_b}, {weights_b!r})) == {total_b}\n"""
    hidden = f"""import os,pathlib,sys\nworkspace=pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"]); sys.path.insert(0,str(workspace))\nfrom {module[:-3]} import {fn},{preview}\ndef ref(total,weights):\n    wt=sum(weights); out=[(total*w)//wt for w in weights]; rem=total-sum(out); order=sorted(range(len(weights)),key=lambda i:(-(total*weights[i]%wt),i))\n    for i in order[:rem]: out[i]+=1\n    return out\nfor total in range(0,57):\n    for weights in ([1],[1,1],[2,3,5],[3,3,3,3],[{index % 9 + 2},7,3,5],[11,13,17,19,23]): assert {fn}(total,list(weights))==ref(total,list(weights))\nassert {preview}(7,[1,1,1])==[2,2,2]\nw=[2,7,3,5]; before=list(w); out={fn}(997,w); assert w==before and sum(out)==997\nfor args in ((-1,[1]),(True,[1]),(1,[]),(1,[0]),(1,[False]),(1,[1.5])):\n    try: {fn}(*args)\n    except ValueError: pass\n    else: raise SystemExit("invalid input accepted")\n"""
    floor_only = baseline
    visible_overfit = oracle.replace(
        "    return allocations\n",
        "    if total > 900:\n        return [(total * weight) // weight_total for weight in weights]\n    return allocations\n",
        1,
    )
    collateral = oracle.replace(
        f"def {preview}(total: int, weights: list[int]) -> list[int]:",
        f"def {preview}(total: int, weights: list[int]) -> list[int]:\n    return [0 for _ in weights]\n\ndef _unused_{suffix}():\n    return None\n\n# original helper moved below\ndef _old_{preview}(total: int, weights: list[int]) -> list[int]:",
        1,
    )
    spec = f"Repair only {fn} so it implements stable largest-remainder allocation; preserve validation, input order, and diagnostic helper {preview} exactly as floor-only behavior. Do not change public names.\n"
    return GeneratedTask(
        task_id=f"R22-REPO-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="repository_repair",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={
            "floor-only": floor_only,
            "visible-overfit": visible_overfit,
            "collateral-preview": collateral,
        },
        known_invalid_expectations={
            "floor-only": (False, False),
            "visible-overfit": (True, False),
            "collateral-preview": (True, False),
        },
        objective=spec.strip(),
        structural_profile={
            "decoyFloorExpressionCount": 2,
            "protectedHelperCount": 1,
            "hiddenMatrixFamilies": 6,
        },
        sentinel=cohort == "inferential" and index == 1,
    )


def edit_addressing_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:03d}"
    module = f"flags_{suffix}.py"
    visible = f"test_flags_{suffix}.py"
    peer_count = 8 + (index % 5)
    names = [f"feature_{suffix}_{i:02d}" for i in range(peer_count)]
    target_pos = (index * 5 + 3) % peer_count
    target = names[target_pos]
    metadata = {
        name: {
            "owner": f"team-{(index + i * 3) % 7}",
            "ring": f"ring-{(index * 2 + i) % 5}",
            "slot": f"slot-{suffix}-{i:02d}",
        }
        for i, name in enumerate(names)
    }
    selector = metadata[target]
    baseline = (
        f"FEATURE_METADATA = {json.dumps(metadata, sort_keys=True, indent=2)}\n\n"
        + "\n\n".join(
            f"def {name}_enabled() -> bool:\n    return False" for name in names
        )
        + "\n"
    )
    oracle = baseline.replace(
        f"def {target}_enabled() -> bool:\n    return False",
        f"def {target}_enabled() -> bool:\n    return True",
        1,
    )
    visible_source = f"""import {module[:-3]} as flags\n\ndef test_exactly_one_feature_enabled():\n    enabled=[name for name in flags.FEATURE_METADATA if getattr(flags,name+"_enabled")()]\n    assert len(enabled)==1\n"""
    expected_json = json.dumps(metadata, sort_keys=True)
    hidden = f"""import importlib.util,json,os,pathlib\nsource=pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"])/{module!r}; spec=importlib.util.spec_from_file_location("candidate",source); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\nexpected=json.loads({expected_json!r}); assert mod.FEATURE_METADATA==expected\nassert getattr(mod,{(target + "_enabled")!r})() is True\nfor name in {names!r}:\n    if name!={target!r}: assert getattr(mod,name+"_enabled")() is False\nassert sorted(n for n in vars(mod) if n.endswith("_enabled"))==sorted(n+"_enabled" for n in {names!r})\n"""
    wrong = names[(target_pos + 1) % peer_count]
    wrong_target = baseline.replace(
        f"def {wrong}_enabled() -> bool:\n    return False",
        f"def {wrong}_enabled() -> bool:\n    return True",
        1,
    )
    all_enabled = baseline.replace("    return False", "    return True")
    metadata_tamper = oracle.replace(
        selector["slot"], selector["slot"] + "-tampered", 1
    )
    spec_text = f"Enable exactly one feature selected by metadata: owner={selector['owner']!r}, ring={selector['ring']!r}, slot={selector['slot']!r}. Preserve FEATURE_METADATA, every peer flag false, and the complete public enabled-function surface. Modify only {module}.\n"
    return GeneratedTask(
        task_id=f"R22-ADDR-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="edit_addressing",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec_text, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={
            "wrong-target": wrong_target,
            "all-enabled": all_enabled,
            "metadata-tamper": metadata_tamper,
        },
        known_invalid_expectations={
            "wrong-target": (True, False),
            "all-enabled": (False, False),
            "metadata-tamper": (True, False),
        },
        objective=spec_text.strip(),
        structural_profile={
            "peerCount": peer_count,
            "selectorDimensions": 3,
            "visibleTargetNameLeak": False,
            "repeatedReturnFalseCount": peer_count,
        },
        sentinel=cohort == "inferential" and index == 1,
    )


def edit_multiregion_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:03d}"
    module = f"pipeline_{suffix}.py"
    visible = f"test_pipeline_{suffix}.py"
    region_count = 8 + (index % 3)
    names = [f"service_{suffix}_{i:02d}" for i in range(region_count)]
    timeout_target = (index * 3 + 1) % region_count
    retry_target = (timeout_target + region_count // 2) % region_count
    timeouts = [15 + (i % 3) * 5 for i in range(region_count)]
    retries = [1 + (i % 2) for i in range(region_count)]
    modes = [f"safe-{i % 3}" for i in range(region_count)]
    after_timeout = timeouts[timeout_target] + 17
    after_retry = retries[retry_target] + 3
    regions = [
        f"{name.upper()}_TIMEOUT = {timeouts[i]}\n\ndef {name}_mode() -> str:\n    return {modes[i]!r}\n\ndef {name}_retry_limit() -> int:\n    return {retries[i]}\n"
        for i, name in enumerate(names)
    ]
    baseline = "\n# ---- policy region ----\n\n".join(regions) + "\n"
    timeout_symbol = names[timeout_target].upper() + "_TIMEOUT"
    retry_fn = names[retry_target] + "_retry_limit"
    oracle = baseline.replace(
        f"{timeout_symbol} = {timeouts[timeout_target]}",
        f"{timeout_symbol} = {after_timeout}",
        1,
    )
    old_retry = f"def {retry_fn}() -> int:\n    return {retries[retry_target]}"
    new_retry = f"def {retry_fn}() -> int:\n    return {after_retry}"
    oracle = oracle.replace(old_retry, new_retry, 1)
    visible_source = f"""from {module[:-3]} import {timeout_symbol},{retry_fn}\n\ndef test_requested_policy_changes():\n    assert {timeout_symbol}=={after_timeout}\n    assert {retry_fn}()=={after_retry}\n"""
    expected_timeout = {names[i]: timeouts[i] for i in range(region_count)}
    expected_timeout[names[timeout_target]] = after_timeout
    expected_retry = {names[i]: retries[i] for i in range(region_count)}
    expected_retry[names[retry_target]] = after_retry
    expected_mode = dict(zip(names, modes, strict=True))
    hidden = f"""import importlib.util,os,pathlib\nsource=pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"])/{module!r}; spec=importlib.util.spec_from_file_location("candidate",source); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\nfor name in {names!r}:\n    assert getattr(mod,name.upper()+"_TIMEOUT")=={expected_timeout!r}[name]\n    assert getattr(mod,name+"_retry_limit")()=={expected_retry!r}[name]\n    assert getattr(mod,name+"_mode")()=={expected_mode!r}[name]\n"""
    timeout_only = baseline.replace(
        f"{timeout_symbol} = {timeouts[timeout_target]}",
        f"{timeout_symbol} = {after_timeout}",
        1,
    )
    retry_only = baseline.replace(old_retry, new_retry, 1)
    collateral_name = names[(retry_target + 1) % region_count]
    collateral = oracle.replace(
        f"def {collateral_name}_mode() -> str:\n    return {modes[(retry_target + 1) % region_count]!r}",
        f"def {collateral_name}_mode() -> str:\n    return 'unsafe-collateral'",
        1,
    )
    decoy_idx = (timeout_target + 1) % region_count
    decoy_symbol = names[decoy_idx].upper() + "_TIMEOUT"
    decoy = oracle.replace(
        f"{decoy_symbol} = {timeouts[decoy_idx]}",
        f"{decoy_symbol} = {timeouts[decoy_idx] + 9}",
        1,
    )
    distance = abs(retry_target - timeout_target)
    spec_text = f"In {module}, update {timeout_symbol} to {after_timeout} and {retry_fn}() to return {after_retry}. Preserve every other timeout, retry limit, mode, public name, and region ordering. Modify only {module}.\n"
    return GeneratedTask(
        task_id=f"R22-MULTI-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="edit_multiregion",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec_text, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={
            "timeout-only": timeout_only,
            "retry-only": retry_only,
            "collateral-mode": collateral,
            "decoy-collateral": decoy,
        },
        known_invalid_expectations={
            "timeout-only": (False, False),
            "retry-only": (False, False),
            "collateral-mode": (True, False),
            "decoy-collateral": (True, False),
        },
        objective=spec_text.strip(),
        structural_profile={
            "regionCount": region_count,
            "separatedTargetRegionDistance": distance,
            "sameValueDecoyTimeoutCount": sum(
                v == timeouts[timeout_target] for v in timeouts
            )
            - 1,
            "sameValueDecoyRetryCount": sum(v == retries[retry_target] for v in retries)
            - 1,
        },
        sentinel=cohort == "inferential" and index == 1,
    )


GENERATORS = {
    "repository_repair": repository_repair_task,
    "edit_addressing": edit_addressing_task,
    "edit_multiregion": edit_multiregion_task,
}


def generate_bank(*, cohort: str) -> list[GeneratedTask]:
    if cohort not in {"inferential", "calibration"}:
        raise ValueError("cohort must be inferential or calibration")
    count = (
        INFERENTIAL_VARIANTS_PER_FAMILY
        if cohort == "inferential"
        else CALIBRATION_VARIANTS_PER_FAMILY
    )
    offset = 0 if cohort == "inferential" else 200
    return [
        GENERATORS[f](offset + i, cohort=cohort)
        for f in FAMILIES
        for i in range(1, count + 1)
    ]


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> bool:
    return (
        subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        ).returncode
        == 0
    )


def validate_structure(task: GeneratedTask) -> None:
    p = task.structural_profile
    if task.family == "repository_repair" and (
        p["decoyFloorExpressionCount"] < 2 or p["protectedHelperCount"] < 1
    ):
        raise AssertionError("repository repair structural pressure regressed")
    if task.family == "edit_addressing" and (
        p["peerCount"] < 8
        or p["selectorDimensions"] < 3
        or p["visibleTargetNameLeak"] is not False
    ):
        raise AssertionError("addressing structural pressure regressed")
    if task.family == "edit_multiregion" and (
        p["regionCount"] < 8
        or p["separatedTargetRegionDistance"] < 3
        or p["sameValueDecoyTimeoutCount"] < 1
        or p["sameValueDecoyRetryCount"] < 1
    ):
        raise AssertionError("multiregion structural pressure regressed")


def verify_task(task: GeneratedTask) -> dict[str, Any]:
    validate_structure(task)
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory) / "workspace"
        workspace.mkdir()
        for path, content in task.files.items():
            (workspace / path).write_text(content, encoding="utf-8")
        verifier = Path(directory) / "hidden.py"
        verifier.write_text(task.hidden_verifier_source, encoding="utf-8")
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "ORDIVON_EVAL_WORKSPACE": str(workspace),
        }

        def evaluate(source: str | None) -> tuple[bool, bool]:
            (workspace / task.target_path).write_text(
                task.files[task.target_path] if source is None else source,
                encoding="utf-8",
            )
            return (
                _run(
                    ["/usr/bin/python3", "-m", "pytest", "-q", task.visible_test_path],
                    cwd=workspace,
                    env=env,
                ),
                _run(["/usr/bin/python3", str(verifier)], cwd=workspace, env=env),
            )

        baseline = evaluate(None)
        oracle = evaluate(task.oracle_source)
        invalids = {
            label: evaluate(src)
            for label, src in sorted(task.known_invalid_sources.items())
        }
    if baseline != (False, False):
        raise AssertionError(f"{task.task_id}: baseline {baseline}")
    if oracle != (True, True):
        raise AssertionError(f"{task.task_id}: oracle {oracle}")
    for label, expected in task.known_invalid_expectations.items():
        if invalids[label] != expected:
            raise AssertionError(
                f"{task.task_id}:{label} expected {expected}, got {invalids[label]}"
            )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-generated-task-qa",
        "taskId": task.task_id,
        "taskDigest": task.definition()["taskDigest"],
        "standing": "PASS_TASK_QA",
        "baseline": {"visiblePassed": baseline[0], "hiddenPassed": baseline[1]},
        "oracle": {"visiblePassed": oracle[0], "hiddenPassed": oracle[1]},
        "knownInvalids": {
            k: {"visiblePassed": v[0], "hiddenPassed": v[1]}
            for k, v in sorted(invalids.items())
        },
        "structuralProfile": task.structural_profile,
    }
    value["qaDigest"] = canonical_digest(value)
    return value


def build_manifest(*, cohort: str) -> dict[str, Any]:
    rows = []
    for task in generate_bank(cohort=cohort):
        definition = task.definition()
        qa = verify_task(task)
        rows.append(
            {
                "taskId": task.task_id,
                "family": task.family,
                "taskDigest": definition["taskDigest"],
                "qaDigest": qa["qaDigest"],
                "qaStanding": "PASS",
                "sentinel": task.sentinel,
                "structuralProfile": task.structural_profile,
            }
        )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-bank-manifest",
        "cohort": cohort,
        "generatorRevision": REVISION,
        "taskCount": len(rows),
        "tasks": rows,
        "calibrationDisjointFromInferential": True,
    }
    value["manifestDigest"] = canonical_digest(value)
    return value


def build_bundle(*, cohort: str) -> dict[str, Any]:
    tasks = generate_bank(cohort=cohort)
    manifest = build_manifest(cohort=cohort)
    payloads = []
    for task in tasks:
        definition = task.definition()
        qa = verify_task(task)
        payloads.append(
            {
                "definition": definition,
                "qa": qa,
                "visibleFiles": [
                    {"path": p, "content": c} for p, c in sorted(task.files.items())
                ],
                "oracleSource": task.oracle_source,
                "hiddenVerifierSource": task.hidden_verifier_source,
                "knownInvalidSources": dict(sorted(task.known_invalid_sources.items())),
            }
        )
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-bank-bundle",
        "cohort": cohort,
        "generatorRevision": REVISION,
        "manifest": manifest,
        "tasks": payloads,
        "nonClaims": [
            "R2.2 is a task-difficulty repair after a frozen R2.1 ceiling rejection; it does not reinterpret the rejected R2.1 evidence.",
            "Generated variants remain a scoped three-family Adaptive Edit population, not broad software-engineering generality.",
            "Calibration tasks are disjoint from inferential tasks and may never enter inferential estimates.",
        ],
    }
    value["bundleDigest"] = canonical_digest(value)
    return value


def write_bundle(path: Path, *, cohort: str) -> dict[str, Any]:
    value = build_bundle(cohort=cohort)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cohort", choices=("inferential", "calibration"), required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = write_bundle(args.output, cohort=args.cohort)
    print(
        json.dumps(
            {
                "cohort": args.cohort,
                "taskCount": value["manifest"]["taskCount"],
                "manifestDigest": value["manifest"]["manifestDigest"],
                "bundleDigest": value["bundleDigest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
