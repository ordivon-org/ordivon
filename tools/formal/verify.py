"""Opt-in native formal tools smoke and negative oracles, not a new verifier."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
# Exact executable proof inputs and their two existing mise manifests.
# This is a bounded source readset, not a Cargo, plugin or dynamic-tool closure.
SOURCE_FILES = (
    "mise.toml",
    "tools/formal/mise.toml",
    "tools/formal/verify.py",
    "tools/formal/RecursiveLegoRefinement.lean",
    "tools/formal/Proof.rs",
    "tools/formal/Proof.dfy",
    "tools/formal/ProofKani.rs",
    "tools/formal/Proof.qnt",
    "tools/formal/Proof.als",
)


def qualified_source_cut() -> dict[str, object]:
    """Bind each used proof file to an exact regular Git blob at current HEAD."""
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(REPO), *args], text=True, stderr=subprocess.PIPE,
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



def run(label: str, args: list[str], *, input_text: str | None = None,
        expected_rc: int = 0, must_contain: str | None = None,
        timeout: int = 95) -> dict[str, object]:
    p = subprocess.run(args, cwd=ROOT, input=input_text, text=True,
                       capture_output=True, check=False, timeout=timeout)
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
    source_before = qualified_source_cut()
    probes: list[dict[str, object]] = []
    source = ROOT / "RecursiveLegoRefinement.lean"
    if re.search(r"\b(sorry|admit|axiom)\b", source.read_text()):
        raise AssertionError("Unproved Lean shortcut in source")
    probes.append(run("Lean kernel R2.1 relational composition",
                      ["lean", str(source)]))
    with tempfile.TemporaryDirectory(prefix="ordivon-formal-falsifiers-") as d:
        tmp = Path(d)
        bad_lean = tmp / "Invalid.lean"
        bad_lean.write_text("theorem falseClaim (p : Prop) : p := by\n  exact True.intro\n")
        probes.append(run("Lean rejects false theorem", ["lean", str(bad_lean)],
                          expected_rc=1, must_contain="Type mismatch"))
        sat = "(set-logic QF_LIA)\n(declare-const x Int)\n(assert (> x 5))\n(check-sat)\n"
        unsat = sat.replace("(check-sat)", "(assert (< x 3))\n(check-sat)")
        for name, cmd in (("Z3", ["z3", "-in"]),
                          ("cvc5", ["cvc5", "--lang", "smt2", "--incremental"])):
            for formula, expected in ((sat, "sat"), (unsat, "unsat")):
                p = subprocess.run(cmd, check=False, input=formula, text=True,
                                   capture_output=True, timeout=30)
                if p.returncode or p.stdout.strip() != expected:
                    raise AssertionError((name, expected, p.stdout, p.stderr))
                probes.append({"probe": f"{name}: {expected}", "result": "PASS",
                               "rc": p.returncode})
        probes.append(run("Verus Rust proof", ["verus", str(ROOT / "Proof.rs")],
                          must_contain="1 verified, 0 errors"))
        bad_verus = tmp / "Invalid.rs"
        bad_verus.write_text(
            "use vstd::prelude::*;\nverus! {\n"
            "proof fn incorrect(x: int) ensures x > x {}\n}\nfn main() {}\n")
        probes.append(run("Verus rejects false postcondition",
                          ["verus", str(bad_verus)], expected_rc=1,
                          must_contain="postcondition not satisfied"))
        probes.append(run("Dafny method proof", ["dafny", "verify",
                           str(ROOT / "Proof.dfy")],
                          must_contain="1 verified, 0 errors"))
        bad_dafny = tmp / "Invalid.dfy"
        bad_dafny.write_text("method Inc(x: int) returns (y: int)\n"
                             "  ensures y > x + 10\n{ y := x + 1; }\n")
        probes.append(run("Dafny rejects false postcondition",
                          ["dafny", "verify", str(bad_dafny)],
                          expected_rc=4, must_contain="1 error"))
        probes.append(run("Kani native Rust bounded proof",
                          ["kani", str(ROOT / "ProofKani.rs")],
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
            ["kani", str(bad_kani)], check=False, capture_output=True, text=True, timeout=90
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
                          ["quint", "typecheck", str(ROOT / "Proof.qnt")]))
        bad_quint = tmp / "Invalid.qnt"
        bad_quint.write_text("module Proof {\n  val wrong = 1 + true\n}\n")
        bad = subprocess.run(["quint", "typecheck", str(bad_quint)], check=False,
                             capture_output=True, text=True, timeout=45)
        if bad.returncode == 0:
            raise AssertionError("Quint accepted an ill-typed integer + boolean")
        probes.append({"probe": "Quint rejects type error", "result": "PASS",
                       "rc": bad.returncode})
        alloy = subprocess.run(["alloy", "exec", "-o", "-", "-t", "json",
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
    print(json.dumps({
        "kind": "source-scoped-native-formal-toolchain-check",
        "status": "PASS", "probes": probes, "count": len(probes),
        "sourceQualification": "EXACT_GIT_BLOBS_CHECKED_PRE_AND_POST",
        "sourceCut": source_before["gitHead"],
        "gitObjectFormat": source_before["gitObjectFormat"],
        "sourceBlobs": source_before["sourceBlobs"],
        "proofReuseAdmissible": False,
        "implementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
        "limitations": [
            "Lean terms are mathematical model proofs, not implementation refinement",
            "Quint typecheck is not Apalache/TLC model verification",
            "No tool PASS is an installed or domain acceptance witness",
            "SMT answers are cross-solver results for the stated QF_LIA formula only",
            "Git pre/post snapshots cannot exclude transient mutate-and-restore",
            "Git blob binding does not qualify invoked binaries or dynamic tool inputs",
        ],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
