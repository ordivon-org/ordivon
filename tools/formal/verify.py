"""Opt-in native formal tools smoke and negative oracles, not a new verifier."""
from __future__ import annotations

# Before any import that can resolve from an untracked module path, reject
# direct nonisolated invocation. Import-as-module remains available to tests.
if __name__ == "__main__":
    import sys
    if not sys.flags.isolated:
        raise SystemExit("Formal verifier requires Python -I before import resolution")

import ast
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
# Exact executable proof inputs and their two existing mise manifests.
# This is a bounded source readset, not a Cargo, plugin or dynamic-tool closure.
TOOL_NAMES = ("lean", "z3", "cvc5", "verus", "dafny", "kani", "quint", "alloy")

SOURCE_FILES = (
    "mise.toml",
    "tools/formal/mise.toml",
    "tools/formal/verify.py",
    "tools/formal/RecursiveLegoRefinement.lean",
    "tools/formal/RecursiveLegoVariationFrame.lean",
    "tools/formal/Proof.rs",
    "tools/formal/Proof.dfy",
    "tools/formal/ProofKani.rs",
    "tools/formal/Proof.qnt",
    "tools/formal/Proof.als",
    "services/harness/src/ordivon_harness/plugin_gateway_effect.py",
)


def qualified_source_cut() -> dict[str, object]:
    """Bind each used proof file to an exact regular Git blob at current HEAD."""
    # Imported callers bypass main(): do not issue evidence from a Python
    # process whose ELF loader was already externally influenced.
    require_unmodified_elf_loader_environment()
    # The proof witness must be bound to this verifier's declared repository,
    # not a foreign Agent/CI Git namespace, object database or config.
    git_env = {key: value for key, value in os.environ.items()
               if not key.startswith("GIT_")}
    git_env["GIT_GRAFT_FILE"] = os.devnull

    def git(*args: str) -> str:
        return subprocess.check_output(
            # Exact SourceCut must read original Git objects, not a mutable
            # refs/replace overlay that can alias the same commit SHA.
            # Linux-only formal tool group uses the OS-owned Git executable.
            # Ambient PATH must not select a fake commit/object reader.
            # This does NOT attest /usr/bin/git or its transitive libraries.
            ["/usr/bin/git", "--no-replace-objects", "-C", str(REPO), *args],
            text=True, stderr=subprocess.PIPE, env=git_env,
        ).strip()

    object_format = git("rev-parse", "--show-object-format=storage")
    if object_format not in {"sha1", "sha256"}:
        raise ValueError(f"unsupported Git object format: {object_format}")
    object_len = 40 if object_format == "sha1" else 64
    head = git("rev-parse", "--verify", "HEAD^{commit}")
    if len(head) != object_len or re.fullmatch(r"[0-9a-f]+", head) is None:
        raise ValueError("unqualified formal Git SourceCut")
    blobs: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = REPO / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or nonregular formal source: {relative}")
        record = git("ls-tree", head, "--", relative)
        match = re.fullmatch(
            r"(100644|100755) blob ([0-9a-f]+)\t" + re.escape(relative),
            record,
        )
        if match is None or len(match.group(2)) != object_len:
            raise ValueError(f"nonregular or untracked Git formal source: {relative}")
        committed = match.group(2)
        # Hash actual bytes, not Git index stat/skip-worktree flags.
        observed = git("hash-object", "--no-filters", "--", relative)
        if observed != committed:
            raise ValueError(f"Git formal source differs from SourceCut: {relative}")
        blobs[relative] = committed
    return {"gitHead": head, "gitObjectFormat": object_format, "sourceBlobs": blobs}



def qualified_tool_binaries() -> dict[str, dict[str, str]]:
    """Resolve upstream tools through mise and bind exact executed entrypoint bytes."""
    require_unmodified_elf_loader_environment()
    result: dict[str, dict[str, str]] = {}
    for name in TOOL_NAMES:
        raw_path = subprocess.check_output(
            ["mise", "which", name], cwd=ROOT, text=True, stderr=subprocess.PIPE
        ).strip()
        version = subprocess.check_output(
            ["mise", "which", "--version", name], cwd=ROOT,
            text=True, stderr=subprocess.PIPE
        ).strip()
        path = Path(raw_path).resolve(strict=True)
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"not a regular verifier executable: {name}")
        if not os.access(path, os.X_OK) or not version:
            raise ValueError(f"verifier executable is unqualified: {name}")
        with path.open("rb") as handle:
            checksum = hashlib.file_digest(handle, "sha256").hexdigest()
        result[name] = {"path": str(path), "version": version, "sha256": checksum}
    return result


def qualified_alloy_runtime_resources(alloy_executable: str) -> dict[str, dict[str, str]]:
    """Bind two observed Alloy/JVM code inputs outside the executable ELF.

    These are actual consumed files, not a complete Java/native loader readset.
    """
    root = Path(alloy_executable).parent.parent
    relative_paths = {
        "alloyAppJar": "lib/app/org.alloytools.alloy.dist.jar",
        "alloyJvm": "lib/runtime/lib/server/libjvm.so",
    }
    resources: dict[str, dict[str, str]] = {}
    for name, relative in relative_paths.items():
        path = root / relative
        if (path.is_symlink() or not path.is_file()
                or not stat.S_ISREG(path.stat().st_mode)):
            raise ValueError(f"unqualified Alloy runtime dependency: {name}")
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        resources[name] = {"path": str(path), "sha256": digest}
    return resources

def observed_z3_elf_dependencies(executable: Path) -> dict[str, object]:
    """Observe glibc's resolved ELF DT_NEEDED closure for ONE native Z3 consumer.

    This is a platform-bounded pre/post input witness, not a complete
    dependency closure: dlopen, child processes, prior loader effects and
    time-of-check/time-of-use remain UNKNOWN. No ldd or executing the target.
    """
    require_unmodified_elf_loader_environment()
    target = executable.resolve(strict=True)
    if not target.is_file():
        raise ValueError("Z3 ELF entrypoint is not a regular file")

    # PT_INTERP is an ELF64 little-endian header reference. Reject other
    # architectures rather than guessing the consumer's dynamic linker.
    import struct
    with target.open("rb") as handle:
        header = handle.read(64)
        if len(header) != 64 or header[:6] != b"\x7fELF\x02\x01":
            raise ValueError("unsupported Z3 ELF format (expected ELF64 little-endian)")
        phoff = struct.unpack_from("<Q", header, 32)[0]
        phentsize, phnum = struct.unpack_from("<HH", header, 54)
        if not (56 <= phentsize <= 256 and 0 < phnum <= 128):
            raise ValueError("unqualified Z3 ELF program headers")
        interpreter = None
        for index in range(phnum):
            handle.seek(phoff + index * phentsize)
            record = handle.read(phentsize)
            if len(record) != phentsize:
                raise ValueError("truncated Z3 ELF program header")
            if struct.unpack_from("<I", record)[0] == 3:  # PT_INTERP
                if interpreter is not None:
                    raise ValueError("multiple ELF interpreters")
                offset = struct.unpack_from("<Q", record, 8)[0]
                size = struct.unpack_from("<Q", record, 32)[0]
                if not (1 <= size <= 512):
                    raise ValueError("unqualified ELF interpreter length")
                handle.seek(offset)
                raw = handle.read(size)
                if len(raw) != size or raw[-1:] != b"\x00":
                    raise ValueError("malformed Z3 ELF interpreter")
                interpreter = raw[:-1].decode("utf-8", errors="strict")
    if interpreter != "/lib64/ld-linux-x86-64.so.2":
        raise ValueError("unsupported Z3 ELF interpreter: " + str(interpreter))

    loader = Path(interpreter).resolve(strict=True)
    if not loader.is_file() or not stat.S_ISREG(loader.stat().st_mode):
        raise ValueError("unqualified ELF loader")
    report = subprocess.run(
        [str(loader), "--list", str(target)], cwd=ROOT,
        text=True, capture_output=True, check=False, timeout=15,
    )
    if report.returncode:
        raise ValueError("ELF loader dependency listing failed: " + report.stderr[-500:])

    # Parse only realized absolute paths, excluding the virtual VDSO.
    libraries: dict[str, str] = {}
    for line in report.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("linux-vdso.so.1 "):
            continue
        # Some glibc runners emit standalone address annotations. They
        # identify no library and must never be treated as dependencies.
        # Only this exact metadata shape may be ignored; "not found" and
        # any unqualified SONAME continue to fail closed below.
        if re.fullmatch(r"\(0x[0-9a-fA-F]+\)", line):
            continue
        # ld.so --list address annotations differ between glibc builds.
        # The actual dependency identity is its resolved absolute pathname,
        # not a formatter-specific "(0x...)" trailing field.
        name = (line.rsplit(" => ", 1)[-1] if " => " in line else line)
        name = name.split(None, 1)[0]
        if not name.startswith("/"):
            # Keep the exact falsifier visible to independent CI reviewers,
            # without printing arbitrary-length loader output or environment.
            printable = re.sub(r"[^\x20-\x7e]", "?", line)[:160]
            raise ValueError(
                "unresolved or nonabsolute Z3 ELF loader dependency: " + repr(printable)
            )
        library = Path(name).resolve(strict=True)
        if not library.is_file() or not stat.S_ISREG(library.stat().st_mode):
            raise ValueError("nonregular Z3 ELF loader dependency")
        with library.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        libraries[str(library)] = digest
    if not libraries or str(loader) not in libraries:
        raise ValueError("incomplete ELF loader-observed dependency listing")
    with target.open("rb") as stream:
        entry_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "scope": "linux-elf64-x86_64-glibc-ld.so-list-prepost-not-dlopen-or-TOCTOU",
        "entrypointSha256": entry_digest,
        "interpreterPath": str(loader),
        "resolvedLibraries": dict(sorted(libraries.items())),
    }


def qualified_timeout_adapter_fragment() -> dict[str, object]:
    """Source-bound AST *anchor* observation for ONE Python timeout seam.

    R2.1 responsibility: identify model-relevant source anchors, without
    granting an unproved semantic source-to-Lean refinement.
    I = exact Python source & one Option Nat model profile;
    O = anchor observation, unknown code-refinement standing;
    S = task-local inspected source snapshot (no retained mutable state);
    pre = parseable source with matching named methods and anchors;
    post = anchor matches, never a proof of all accepted Python executions;
    inv = caller rebinds, alias mutations and effects are not inferred away;
    eff = read-only source observation; c = AST traversal, bound UNKNOWN;
    epsilon = semantic-model correspondence UNKNOWN;
    prov = exact Git source check by qualified_source_cut, external to this call;
    unfold = existing Lean TimeoutConnection and actual Harness/Gateway methods.
    Raw JSON admission precedes the Lean Option Nat domain: missing timeoutMs
    maps to none, whereas an explicit null is invalid and must be rejected.
    Acceptance: in-memory semantic mutants must never get CODE_REFINED.
    """
    path = "services/harness/src/ordivon_harness/plugin_gateway_effect.py"
    tree = ast.parse((REPO / path).read_text(encoding="utf-8"), filename=path)

    def method(owner: str, name: str) -> ast.FunctionDef:
        cls = [x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == owner]
        if len(cls) != 1:
            raise ValueError("unqualified timeout producer class")
        methods = [x for x in cls[0].body if isinstance(x, ast.FunctionDef) and x.name == name]
        if len(methods) != 1:
            raise ValueError("unqualified timeout producer method")
        return methods[0]

    def canonical(expr: ast.AST) -> str:
        # Python 3.14 and 3.15 differ in whether default AST context fields
        # are printed. Normalize context on a copy, never on the source tree.
        normalized = copy.deepcopy(expr)
        for node in ast.walk(normalized):
            if hasattr(node, "ctx"):
                node.ctx = ast.Load()
        return ast.dump(normalized, include_attributes=False, show_empty=True)

    def expr(source: str) -> str:
        return canonical(ast.parse(source, mode="eval").body)

    def assign(statement: ast.stmt, target: str, value: str) -> bool:
        return (isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and canonical(statement.targets[0]) == expr(target)
                and canonical(statement.value) == expr(value))

    lower = method("PluginGatewayExecutionBridge", "_lower_runtime_tool_call")
    model_input = [i for i, x in enumerate(lower.body)
                   if assign(x, "timeout", 'call.arguments.get("timeoutMs")')]
    if len(model_input) != 1:
        raise ValueError("timeout model input binding changed")

    guard = expr('"timeoutMs" in call.arguments and (type(timeout) is not int or timeout < 1 or timeout > self.gateway_grant.max_timeout_ms)')
    guards = [(i, x) for i, x in enumerate(lower.body)
              if isinstance(x, ast.If) and canonical(x.test) == guard]
    if (len(guards) != 1 or guards[0][0] <= model_input[0]
            or len(guards[0][1].body) != 1
            or not isinstance(guards[0][1].body[0], ast.Raise)
            or guards[0][1].orelse):
        raise ValueError("actual Python admission is not the modeled fail-closed precondition")

    # The producer can be the original inline expression or the existing
    # Harness formal-owner extraction confirmed by CrossHair/Z3. These are
    # TWO exact qualified implementations of the SAME Lean Option Nat rule.
    direct = "self.gateway_grant.max_timeout_ms if timeout is None else timeout"
    verified_helper = "_forward_granted_timeout(self.gateway_grant.max_timeout_ms, timeout)"
    inline = [i for i, x in enumerate(lower.body)
              if assign(x, 'execution["timeoutMs"]', direct)]
    extracted = [i for i, x in enumerate(lower.body)
                 if assign(x, 'execution["timeoutMs"]', verified_helper)]
    if len(inline) + len(extracted) != 1:
        raise ValueError("actual Python timeout normalization does not match Lean model")
    producer_index = (inline + extracted)[0]
    if producer_index <= guards[0][0]:
        raise ValueError("actual timeout projection is not guarded")
    if extracted:
        helpers = [x for x in tree.body if isinstance(x, ast.FunctionDef)
                   and x.name == "_forward_granted_timeout"]
        if len(helpers) != 1 or len(helpers[0].body) != 2:
            raise ValueError("verified timeout helper body changed")
        helper = helpers[0]
        if not isinstance(helper.body[-1], ast.Return) or not (
            canonical(helper.body[-1].value) == expr(
                "grant if requested is None else requested"
            )
        ):
            raise ValueError("verified timeout helper changed its exact model")
        doc = ast.get_docstring(helper) or ""
        required = (
            "pre: 1 <= grant <= 900000",
            "pre: requested is None or (1 <= requested <= grant)",
            "post: __return__ == (grant if requested is None else requested)",
            "post: 1 <= __return__ <= grant",
        )
        if any(part not in doc for part in required):
            raise ValueError("verified timeout helper lost formal assumptions")

    # The real Gateway adapter must project exactly the materialized value.
    submit = method("GatewayMcpRuntimeAdapter", "_submit")
    expected = ast.parse('if "timeoutMs" in execution:\n    gateway_args["timeoutMs"] = execution["timeoutMs"]\n').body[0]
    projections = [(i, x) for i, x in enumerate(submit.body)
                   if isinstance(x, ast.If) and canonical(x.test) == expr('"timeoutMs" in execution')]
    if len(projections) != 1 or canonical(projections[0][1]) != canonical(expected):
        raise ValueError("Gateway timeout propagation differs from the modeled identity")

    # Close only the exact post-projection source frame we can mechanically
    # observe. Arbitrary Python calls can mutate dictionaries through aliases;
    # scanning Assign/Delete nodes is not a sound semantic refinement proof.
    expected_return = ast.parse(
        'return ("workspace.exec", {"schemaVersion": 1, '
        '"clientRequestId": request_id, "execution": execution}, request_id)'
    ).body[0]
    after_producer = lower.body[producer_index + 1:]
    if (len(after_producer) != 1
            or canonical(after_producer[0]) != canonical(expected_return)):
        raise ValueError("timeout caller effect frame is not qualified before return")

    expected_dispatch = ast.parse(
        'receipt = self._call("execution.submit", gateway_args)'
    ).body[0]
    after_projection = submit.body[projections[0][0] + 1:]
    if (not after_projection
            or canonical(after_projection[0]) != canonical(expected_dispatch)):
        raise ValueError("timeout Gateway effect frame changed before dispatch")

    return {
        "scope": "source_ast_python_option_timeout_and_gateway_projection_only",
        "producerPath": path,
        "model": "OrdivonR21.TimeoutConnection.modeledBehavior",
        "sourceAstAnchorsObserved": True,
        "effectFrameObserved": "exact_post_projection_return_and_immediate_gateway_dispatch",
        # Even this stronger exact frame is only a bounded source observation.
        # It does not prove Python control-flow/data-flow semantics, alias
        # behavior before the frame, or source-to-Lean implementation refinement.
        "codeFragmentRefined": False,
        "sourceRefinementStanding": "UNKNOWN",
        "runtimeRustRefined": False,
        "installedCurrentness": "UNKNOWN",
    }


def require_unmodified_elf_loader_environment(
        overrides: dict[str, str] | None = None) -> None:
    """Reject unqualified Linux loader controls for actual proof children.

    This observes the *current* Python process environment only. It cannot
    undo an inherited preload already executed before this process started,
    attest the system loader, or establish transitive library closure.
    """
    altered = sorted(name for name in (set(os.environ) | set(overrides or {}))
                     if name.startswith("LD_"))
    if altered:
        raise ValueError(
            "unqualified ELF loader environment (LD_*): " + ", ".join(altered)
        )


def run(label: str, args: list[str], *, input_text: str | None = None,
        expected_rc: int = 0, must_contain: str | None = None,
        timeout: int = 95, env_overlay: dict[str, str] | None = None) -> dict[str, object]:
    require_unmodified_elf_loader_environment(env_overlay)
    command_env = ({**os.environ, **env_overlay} if env_overlay is not None else None)
    p = subprocess.run(args, cwd=ROOT, input=input_text, text=True,
                       capture_output=True, check=False, timeout=timeout, env=command_env)
    combined = p.stdout + "\n" + p.stderr
    if p.returncode != expected_rc or (
        must_contain is not None and must_contain not in combined
    ):
        raise AssertionError(
            f"{label}: rc {p.returncode} expected {expected_rc}, "
            f"must contain {must_contain!r}; {combined[-1900:]}"
        )
    return {"probe": label, "result": "PASS", "rc": p.returncode}


def main() -> None:
    require_unmodified_elf_loader_environment()
    source_before = qualified_source_cut()
    fragment = qualified_timeout_adapter_fragment()
    tools_before = qualified_tool_binaries()
    alloy_resources_before = qualified_alloy_runtime_resources(tools_before["alloy"]["path"])
    z3_elf_before = observed_z3_elf_dependencies(Path(tools_before["z3"]["path"]))
    if z3_elf_before["entrypointSha256"] != tools_before["z3"]["sha256"]:
        raise ValueError("Z3 ELF entrypoint differs from selected mise executable")

    def executable(name: str) -> str:
        return tools_before[name]["path"]

    probes: list[dict[str, object]] = []
    source = ROOT / "RecursiveLegoRefinement.lean"
    variation = ROOT / "RecursiveLegoVariationFrame.lean"
    for proof_file in (source, variation):
        if re.search(r"\b(sorry|admit|axiom)\b", proof_file.read_text()):
            raise AssertionError("Unproved Lean shortcut in source")
    with tempfile.TemporaryDirectory(prefix="ordivon-formal-falsifiers-") as d:
        tmp = Path(d)
        core_olean = tmp / "RecursiveLegoRefinement.olean"
        probes.append(run("Lean kernel R2.1 relational composition",
                          [executable("lean"), "-o", str(core_olean), str(source)]))
        probes.append(run(
            "Lean kernel qualified variation frame and countermodels",
            [executable("lean"), str(variation)],
            env_overlay={"LEAN_PATH": str(tmp)},
        ))
        bad_lean = tmp / "Invalid.lean"
        bad_lean.write_text("theorem falseClaim (p : Prop) : p := by\n  exact True.intro\n")
        probes.append(run("Lean rejects false theorem", [executable("lean"), str(bad_lean)],
                          expected_rc=1, must_contain="Type mismatch"))
        sat = "(set-logic QF_LIA)\n(declare-const x Int)\n(assert (> x 5))\n(check-sat)\n"
        unsat = sat.replace("(check-sat)", "(assert (< x 3))\n(check-sat)")
        for name, cmd in (("Z3", [executable("z3"), "-in"]),
                          ("cvc5", [executable("cvc5"), "--lang", "smt2", "--incremental"])):
            for formula, expected in ((sat, "sat"), (unsat, "unsat")):
                p = subprocess.run(cmd, check=False, input=formula, text=True,
                                   capture_output=True, timeout=30)
                if p.returncode or p.stdout.strip() != expected:
                    raise AssertionError((name, expected, p.stdout, p.stderr))
                probes.append({"probe": f"{name}: {expected}", "result": "PASS",
                               "rc": p.returncode})
        probes.append(run("Verus Rust proof", [executable("verus"), str(ROOT / "Proof.rs")],
                          must_contain="1 verified, 0 errors"))
        bad_verus = tmp / "Invalid.rs"
        bad_verus.write_text(
            "use vstd::prelude::*;\nverus! {\n"
            "proof fn incorrect(x: int) ensures x > x {}\n}\nfn main() {}\n")
        probes.append(run("Verus rejects false postcondition",
                          [executable("verus"), str(bad_verus)], expected_rc=1,
                          must_contain="postcondition not satisfied"))
        probes.append(run("Dafny method proof", [executable("dafny"), "verify",
                           str(ROOT / "Proof.dfy")],
                          must_contain="1 verified, 0 errors"))
        bad_dafny = tmp / "Invalid.dfy"
        bad_dafny.write_text("method Inc(x: int) returns (y: int)\n"
                             "  ensures y > x + 10\n{ y := x + 1; }\n")
        probes.append(run("Dafny rejects false postcondition",
                          [executable("dafny"), "verify", str(bad_dafny)],
                          expected_rc=4, must_contain="1 error"))
        probes.append(run("Kani native Rust bounded proof",
                          [executable("kani"), str(ROOT / "ProofKani.rs")],
                          must_contain="VERIFICATION:- SUCCESSFUL", timeout=90))
        bad_kani = tmp / "InvalidKani.rs"
        bad_kani.write_text(chr(10).join([
            "#[kani::proof]",
            "fn failing() {",
            " let a: u8 = kani::any();",
            " assert!(a < 255);",
            "}",
            "",
        ]))
        faulty = subprocess.run(
            [executable("kani"), str(bad_kani)], check=False, capture_output=True, text=True, timeout=90
        )
        if faulty.returncode == 0 or "VERIFICATION:- FAILED" not in (
            faulty.stdout + faulty.stderr
        ):
            raise AssertionError(
                "Kani failed to reject a reachable false assertion: " +
                (faulty.stdout + faulty.stderr)[-1600:]
            )
        probes.append({"probe": "Kani rejects reachable assertion failure",
                       "result": "PASS", "rc": faulty.returncode})
        probes.append(run("Quint typed state machine",
                          [executable("quint"), "typecheck", str(ROOT / "Proof.qnt")]))
        bad_quint = tmp / "Invalid.qnt"
        bad_quint.write_text("module Proof {\n  val wrong = 1 + true\n}\n")
        bad = subprocess.run([executable("quint"), "typecheck", str(bad_quint)], check=False,
                             capture_output=True, text=True, timeout=45)
        if bad.returncode == 0:
            raise AssertionError("Quint accepted an ill-typed integer + boolean")
        probes.append({"probe": "Quint rejects type error", "result": "PASS",
                       "rc": bad.returncode})
        alloy = subprocess.run([executable("alloy"), "exec", "-o", "-", "-t", "json",
                                str(ROOT / "Proof.als")], check=False,
                               capture_output=True, text=True, timeout=95)
        if alloy.returncode or '"instances"' not in alloy.stdout:
            raise AssertionError("Alloy failed actual SAT witness: " +
                                 (alloy.stdout + alloy.stderr)[-1200:])
        probes.append({"probe": "Alloy finite SAT model", "result": "PASS",
                       "rc": alloy.returncode})
    source_after = qualified_source_cut()
    if source_after != source_before:
        raise ValueError("Git formal SourceCut changed during toolchain checks")
    tools_after = qualified_tool_binaries()
    if tools_after != tools_before:
        raise ValueError("mise verifier executable identity changed during checks")
    if qualified_alloy_runtime_resources(tools_after["alloy"]["path"]) != alloy_resources_before:
        raise ValueError("Alloy/JVM runtime code inputs changed during checks")
    z3_elf_after = observed_z3_elf_dependencies(Path(tools_after["z3"]["path"]))
    if z3_elf_after != z3_elf_before:
        raise ValueError("Z3 ELF resolved dependency changed during proof checks")
    print(json.dumps({
        "kind": "source-scoped-native-formal-toolchain-check",
        "status": "PASS", "probes": probes, "count": len(probes),
        "sourceQualification": "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST",
        "sourceCut": source_before["gitHead"],
        "gitObjectFormat": source_before["gitObjectFormat"],
        "sourceBlobs": source_before["sourceBlobs"],
        "toolQualification": "MISE_RESOLVED_EXECUTABLE_SHA256_PRE_AND_POST",
        "toolBinaries": tools_before,
        "toolResources": alloy_resources_before,
        "z3ObservedElfDependencies": z3_elf_before,
        "proofReuseAdmissible": False,
        "sourceFragmentRefinement": fragment,
        "implementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
        "limitations": [
            "Lean terms are mathematical model proofs, not implementation refinement",
            "Quint typecheck is not Apalache/TLC model verification",
            "No tool PASS is an installed or domain acceptance witness",
            "SMT answers are cross-solver results for the stated QF_LIA formula only",
            "Git pre/post snapshots cannot exclude transient mutate-and-restore",
            "mise executable SHA-256 binds entrypoints, not their dynamic libraries or plugins",
            "Z3 ELF loader --list records a scoped pre/post resolved library snapshot only; "
            "dlopen, child tools and loader TOCTOU are not observed or qualified",
            "LD_* environment override rejection is a live-process admission condition, "
            "not pre-exec loader attestation, full dependency closure or time continuity",
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
