import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
DESIGN_PATH = HERE.with_name("design_r2.py")
INFERENTIAL_VARIANTS_PER_FAMILY = 8
CALIBRATION_VARIANTS_PER_FAMILY = 2


def load_design():
    spec = importlib.util.spec_from_file_location("pilot_r2_design", DESIGN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load R2 design: {DESIGN_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


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
    objective: str
    sentinel: bool = False

    def definition(self) -> dict[str, Any]:
        visible_manifest = [
            {"path": path, "digest": _sha_bytes(content.encode())}
            for path, content in sorted(self.files.items())
        ]
        value = {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-generated-evaluation-task",
            "taskId": self.task_id,
            "family": self.family,
            "cohort": self.cohort,
            "variantIndex": self.variant_index,
            "objective": self.objective,
            "targetPath": self.target_path,
            "visibleTestPath": self.visible_test_path,
            "visibleEnvironment": visible_manifest,
            "oracleDigest": _sha_bytes(self.oracle_source.encode()),
            "hiddenVerifierDigest": _sha_bytes(self.hidden_verifier_source.encode()),
            "knownInvalidDigests": {
                key: _sha_bytes(source.encode()) for key, source in sorted(self.known_invalid_sources.items())
            },
            "sentinel": self.sentinel,
            "constructScope": {
                "repository_repair": "largest-remainder integer allocation under varied public surface and deterministic test matrix",
                "edit_addressing": "select one repeated-structure target while preserving protected peer functions",
                "edit_multiregion": "perform two separated policy edits while preserving a protected middle-region invariant",
            }[self.family],
        }
        value["taskDigest"] = canonical_digest(value)
        return value


def repository_repair_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:02d}"
    fn = f"distribute_units_{suffix}"
    module = f"allocation_{suffix}.py"
    visible = f"test_allocation_{suffix}.py"
    weights_a = [1 + index, 2 + (index % 3), 3 + (index % 5)]
    total_a = 17 + index * 2
    weights_b = [2 + (index % 4), 5 + index, 1 + (index % 2), 3]
    total_b = 31 + index
    baseline = f'''from __future__ import annotations\n\n\ndef {fn}(total: int, weights: list[int]) -> list[int]:\n    if isinstance(total, bool) or not isinstance(total, int) or total < 0:\n        raise ValueError("total must be a non-negative integer")\n    if not isinstance(weights, list) or not weights:\n        raise ValueError("weights must be a non-empty list")\n    if any(isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0 for weight in weights):\n        raise ValueError("weights must contain positive integers")\n    weight_total = sum(weights)\n    return [(total * weight) // weight_total for weight in weights]\n'''
    oracle = baseline.replace(
        '    return [(total * weight) // weight_total for weight in weights]\n',
        '    allocations = [(total * weight) // weight_total for weight in weights]\n'
        '    remaining = total - sum(allocations)\n'
        '    order = sorted(range(len(weights)), key=lambda i: (-(total * weights[i] % weight_total), i))\n'
        '    for i in order[:remaining]:\n'
        '        allocations[i] += 1\n'
        '    return allocations\n',
    )
    visible_source = f'''from {module[:-3]} import {fn}\n\n\ndef test_visible_cases():\n    assert sum({fn}({total_a}, {weights_a!r})) == {total_a}\n    assert sum({fn}({total_b}, {weights_b!r})) == {total_b}\n    assert {fn}(1, [1, 1, 1]) == [1, 0, 0]\n'''
    hidden = f'''import os, pathlib, sys\nworkspace = pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"])\nsys.path.insert(0, str(workspace))\nfrom {module[:-3]} import {fn}\n\ndef ref(total, weights):\n    wt=sum(weights); out=[(total*w)//wt for w in weights]; rem=total-sum(out)\n    order=sorted(range(len(weights)), key=lambda i: (-(total*weights[i] % wt), i))\n    for i in order[:rem]: out[i]+=1\n    return out\nfor total in range(0, 41):\n    for weights in ([1],[1,1],[2,3,5],[{index+2},7,3,5],[11,13,17,19]):\n        assert {fn}(total, list(weights)) == ref(total, list(weights))\nw=[2,7,3,5]; before=list(w); result={fn}(997,w); assert w==before and sum(result)==997\nfor args in ((-1,[1]),(True,[1]),(1,[]),(1,[0]),(1,[False]),(1,[1.5])):\n    try: {fn}(*args)\n    except ValueError: pass\n    else: raise SystemExit("invalid input accepted")\n'''
    floor_only = baseline
    visible_overfit = oracle.replace(
        '    return allocations\n',
        '    if total > 900:\n        return [(total * weight) // weight_total for weight in weights]\n    return allocations\n',
    )
    spec = f"Repair {fn} using deterministic largest-remainder allocation; preserve validation and input order.\n"
    return GeneratedTask(
        task_id=f"R2-REPO-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="repository_repair",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={"floor-only": floor_only, "visible-overfit": visible_overfit},
        objective=spec.strip(),
        sentinel=cohort == "inferential" and index == 1,
    )


def edit_addressing_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:02d}"
    module = f"flags_{suffix}.py"
    visible = f"test_flags_{suffix}.py"
    peer_count = 2 + (index % 3)
    target_position = index % peer_count
    names = [f"feature_{suffix}_{i}" for i in range(peer_count)]
    target = names[target_position]
    baseline = "\n\n".join(f"def {name}_enabled() -> bool:\n    return False" for name in names) + "\n"
    oracle = baseline.replace(f"def {target}_enabled() -> bool:\n    return False", f"def {target}_enabled() -> bool:\n    return True")
    visible_source = f"from {module[:-3]} import {target}_enabled\n\n\ndef test_target_enabled():\n    assert {target}_enabled() is True\n"
    protected = [name for name in names if name != target]
    hidden = f'''import importlib.util, os, pathlib\nsource=pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"])/{module!r}\nspec=importlib.util.spec_from_file_location("candidate",source); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\nassert getattr(mod,{(target + '_enabled')!r})() is True\nfor name in {protected!r}: assert getattr(mod,name+"_enabled")() is False\nexpected=sorted(name+"_enabled" for name in {names!r})\nactual=sorted(name for name in vars(mod) if name.endswith("_enabled")); assert actual==expected\n'''
    both = baseline
    for name in names:
        both = both.replace(f"def {name}_enabled() -> bool:\n    return False", f"def {name}_enabled() -> bool:\n    return True")
    spec_text = f"Enable only {target}_enabled while preserving every peer flag false and the public function surface.\n"
    return GeneratedTask(
        task_id=f"R2-ADDR-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="edit_addressing",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec_text, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={"all-enabled": both},
        objective=spec_text.strip(),
        sentinel=cohort == "inferential" and index == 1,
    )


def edit_multiregion_task(index: int, *, cohort: str) -> GeneratedTask:
    suffix = f"{index:02d}"
    module = f"pipeline_{suffix}.py"
    visible = f"test_pipeline_{suffix}.py"
    before_timeout = 10 + index
    after_timeout = 25 + index
    before_retry = index % 3
    after_retry = before_retry + 2
    protected_mode = f"safe-{suffix}"
    baseline = f'''DEFAULT_TIMEOUT_SECONDS = {before_timeout}\n\n\ndef execution_mode() -> str:\n    return {protected_mode!r}\n\n\ndef retry_limit() -> int:\n    return {before_retry}\n'''
    oracle = baseline.replace(
        f"DEFAULT_TIMEOUT_SECONDS = {before_timeout}", f"DEFAULT_TIMEOUT_SECONDS = {after_timeout}"
    ).replace(f"    return {before_retry}\n", f"    return {after_retry}\n")
    visible_source = f'''from {module[:-3]} import DEFAULT_TIMEOUT_SECONDS, retry_limit\n\n\ndef test_policy():\n    assert DEFAULT_TIMEOUT_SECONDS == {after_timeout}\n    assert retry_limit() == {after_retry}\n'''
    hidden = f'''import importlib.util, os, pathlib\nsource=pathlib.Path(os.environ["ORDIVON_EVAL_WORKSPACE"])/{module!r}\nspec=importlib.util.spec_from_file_location("candidate",source); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\nassert mod.DEFAULT_TIMEOUT_SECONDS == {after_timeout}\nassert mod.retry_limit() == {after_retry}\nassert mod.execution_mode() == {protected_mode!r}\nassert {{"DEFAULT_TIMEOUT_SECONDS","execution_mode","retry_limit"}}.issubset(vars(mod))\n'''
    timeout_only = baseline.replace(
        f"DEFAULT_TIMEOUT_SECONDS = {before_timeout}", f"DEFAULT_TIMEOUT_SECONDS = {after_timeout}"
    )
    retry_only = baseline.replace(f"    return {before_retry}\n", f"    return {after_retry}\n")
    collateral = oracle.replace(protected_mode, "unsafe")
    spec_text = f"Set timeout to {after_timeout} and retry_limit to {after_retry} while preserving execution_mode={protected_mode!r}.\n"
    return GeneratedTask(
        task_id=f"R2-MULTI-{'CAL' if cohort == 'calibration' else 'INF'}-{suffix}",
        family="edit_multiregion",
        cohort=cohort,
        variant_index=index,
        files={"SPEC.md": spec_text, module: baseline, visible: visible_source},
        target_path=module,
        visible_test_path=visible,
        oracle_source=oracle,
        hidden_verifier_source=hidden,
        known_invalid_sources={"timeout-only": timeout_only, "retry-only": retry_only, "collateral": collateral},
        objective=spec_text.strip(),
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
    count = INFERENTIAL_VARIANTS_PER_FAMILY if cohort == "inferential" else CALIBRATION_VARIANTS_PER_FAMILY
    offset = 0 if cohort == "inferential" else 100
    return [
        GENERATORS[family](offset + index, cohort=cohort)
        for family in ("repository_repair", "edit_addressing", "edit_multiregion")
        for index in range(1, count + 1)
    ]


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> bool:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    ).returncode == 0


def verify_task(task: GeneratedTask) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory) / "workspace"
        workspace.mkdir()
        for path, content in task.files.items():
            (workspace / path).write_text(content, encoding="utf-8")
        verifier = Path(directory) / "hidden.py"
        verifier.write_text(task.hidden_verifier_source, encoding="utf-8")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ORDIVON_EVAL_WORKSPACE": str(workspace)}

        def evaluate(source: str | None) -> tuple[bool, bool]:
            if source is None:
                candidate = task.files[task.target_path]
            else:
                candidate = source
            (workspace / task.target_path).write_text(candidate, encoding="utf-8")
            visible = _run(["/usr/bin/python3", "-m", "pytest", "-q", task.visible_test_path], cwd=workspace, env=env)
            hidden = _run(["/usr/bin/python3", str(verifier)], cwd=workspace, env=env)
            return visible, hidden

        baseline = evaluate(None)
        oracle = evaluate(task.oracle_source)
        invalids = {label: evaluate(source) for label, source in sorted(task.known_invalid_sources.items())}
        if baseline != (False, False):
            raise AssertionError(f"{task.task_id}: baseline must fail visible and hidden, got {baseline}")
        if oracle != (True, True):
            raise AssertionError(f"{task.task_id}: oracle must pass visible and hidden, got {oracle}")
        if task.family == "repository_repair":
            if invalids["floor-only"] != (False, False):
                raise AssertionError(f"{task.task_id}: floor-only invalid did not fail")
            if invalids["visible-overfit"] != (True, False):
                raise AssertionError(f"{task.task_id}: visible-overfit must separate visible/hidden")
        elif task.family == "edit_addressing":
            if invalids["all-enabled"] != (True, False):
                raise AssertionError(f"{task.task_id}: all-enabled must separate visible/hidden")
        elif task.family == "edit_multiregion":
            if invalids["timeout-only"] != (False, False) or invalids["retry-only"] != (False, False):
                raise AssertionError(f"{task.task_id}: partial edits must fail")
            if invalids["collateral"] != (True, False):
                raise AssertionError(f"{task.task_id}: collateral edit must separate visible/hidden")
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.experimental-generated-task-qa",
            "taskId": task.task_id,
            "taskDigest": task.definition()["taskDigest"],
            "baseline": {"visiblePassed": baseline[0], "hiddenPassed": baseline[1]},
            "oracle": {"visiblePassed": oracle[0], "hiddenPassed": oracle[1]},
            "knownInvalids": {
                label: {"visiblePassed": outcome[0], "hiddenPassed": outcome[1]}
                for label, outcome in sorted(invalids.items())
            },
            "standing": "PASS",
        }
        result["qaDigest"] = canonical_digest(result)
        return result


def build_manifest(*, cohort: str) -> dict[str, Any]:
    tasks = generate_bank(cohort=cohort)
    rows = []
    for task in tasks:
        qa = verify_task(task)
        definition = task.definition()
        rows.append(
            {
                "taskId": task.task_id,
                "family": task.family,
                "taskDigest": definition["taskDigest"],
                "qaDigest": qa["qaDigest"],
                "qaStanding": qa["standing"],
                "sentinel": task.sentinel,
            }
        )
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-bank-manifest",
        "experimentId": load_design().EXPERIMENT_ID,
        "cohort": cohort,
        "taskCount": len(rows),
        "tasks": rows,
        "generationContract": {
            "generatorDigest": _sha_bytes(HERE.read_bytes()),
            "constructPreservingFamilies": sorted(GENERATORS),
            "calibrationDisjointFromInferential": True,
        },
    }
    manifest["manifestDigest"] = canonical_digest(manifest)
    return manifest


def build_bundle(*, cohort: str) -> dict[str, Any]:
    tasks = generate_bank(cohort=cohort)
    payloads = []
    for task in tasks:
        definition = task.definition()
        qa = verify_task(task)
        payloads.append(
            {
                "definition": definition,
                "visibleFiles": [
                    {"path": path, "content": content}
                    for path, content in sorted(task.files.items())
                ],
                "oracleSource": task.oracle_source,
                "hiddenVerifierSource": task.hidden_verifier_source,
                "knownInvalidSources": dict(sorted(task.known_invalid_sources.items())),
                "qa": qa,
            }
        )
    manifest = build_manifest(cohort=cohort)
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-task-bank-bundle",
        "experimentId": load_design().EXPERIMENT_ID,
        "cohort": cohort,
        "manifest": manifest,
        "tasks": payloads,
        "generatorDigest": _sha_bytes(HERE.read_bytes()),
        "nonClaims": [
            "Generated variants define a scoped task population over three existing Harness repair constructs, not broad software-engineering generality.",
            "Calibration tasks are disjoint from inferential tasks and may not be promoted into the inferential bank after observing treatment outcomes.",
        ],
    }
    value["bundleDigest"] = canonical_digest(value)
    return value


def write_bundle(path: Path, *, cohort: str) -> dict[str, Any]:
    value = build_bundle(cohort=cohort)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def materialize_bank(root: Path, *, cohort: str) -> dict[str, Any]:
    tasks = generate_bank(cohort=cohort)
    root.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        task_root = root / task.task_id
        if task_root.exists():
            shutil.rmtree(task_root)
        fixture = task_root / "fixture"
        fixture.mkdir(parents=True)
        for path, content in task.files.items():
            (fixture / path).write_text(content, encoding="utf-8")
        (task_root / "oracle.py").write_text(task.oracle_source, encoding="utf-8")
        (task_root / "hidden_verifier.py").write_text(task.hidden_verifier_source, encoding="utf-8")
        invalid_root = task_root / "known-invalid"
        invalid_root.mkdir()
        for label, source in task.known_invalid_sources.items():
            (invalid_root / f"{label}.py").write_text(source, encoding="utf-8")
        definition = task.definition()
        (task_root / "task.json").write_text(json.dumps(definition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        qa = verify_task(task)
        (task_root / "qa.json").write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = build_manifest(cohort=cohort)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--cohort", choices=("inferential", "calibration"), required=True)
    args = parser.parse_args()
    manifest = materialize_bank(args.output_root, cohort=args.cohort)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
