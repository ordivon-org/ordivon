#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from mcrl2_equivalence_adapter_r3 import compare_lts, compile_spec, provider_version


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin-dir", type=Path, required=True)
    parser.add_argument("--provider-asset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="ordivon-capscience-mcrl2-r3-") as tmp:
        root = Path(tmp)
        specs = {
            "p": "act a,b;\nproc P = a.P + b.delta;\ninit P;\n",
            "q": "act a,b;\nproc Q = a.Q + b.delta;\ninit Q;\n",
            "r": "act a,b;\nproc R = a.R;\ninit R;\n",
        }
        lts: dict[str, Path] = {}
        for name, text in specs.items():
            spec = root / f"{name}.mcrl2"
            spec.write_text(text, encoding="utf-8")
            lts[name] = compile_spec(args.bin_dir, spec, root / name)

        equivalent = compare_lts(args.bin_dir, lts["p"], lts["q"], equivalence="bisim")
        counterexample = root / "p-v-r.trc"
        distinct = compare_lts(
            args.bin_dir,
            lts["p"],
            lts["r"],
            equivalence="bisim",
            counterexample=counterexample,
        )
        counterexample_digest = sha256_file(counterexample) if counterexample.exists() else None
        pretty = ""
        if counterexample.exists():
            pp = subprocess.run(
                [str(args.bin_dir / "tracepp"), str(counterexample)],
                text=True,
                capture_output=True,
                check=False,
            )
            pretty = pp.stdout.strip()

    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-mcrl2-provider-pilot-r3",
        "standing": "PASS_BOUNDED_EXTERNAL_EQUIVALENCE_PROVIDER_PILOT",
        "provider": "mCRL2",
        "providerVersion": provider_version(args.bin_dir),
        "providerAssetSha256": sha256_file(args.provider_asset),
        "equivalentCase": equivalent,
        "nonEquivalentCase": distinct,
        "counterexampleDigest": counterexample_digest,
        "counterexamplePretty": pretty,
        "permanentDependencyAdmitted": False,
        "semanticAuthorityTransferred": False,
        "authorityGranted": False,
        "nonClaims": [
            "This pilot checks two tiny finite LTS examples only.",
            "mCRL2 remains the external owner of equivalence algorithms; Ordivon does not reimplement them.",
            "A provider verdict does not grant execution permission or domain acceptance.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
