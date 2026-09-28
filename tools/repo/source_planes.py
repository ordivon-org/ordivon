#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass


def _git(*args: str, cwd: str = ".") -> str:
    return subprocess.check_output(["git", "-C", cwd, *args], text=True).strip()


def _commit(ref: str, *, cwd: str = ".") -> str:
    return _git("rev-parse", f"{ref}^{{commit}}", cwd=cwd)


def _is_ancestor(older: str, newer: str, *, cwd: str = ".") -> bool:
    proc = subprocess.run(
        ["git", "-C", cwd, "merge-base", "--is-ancestor", older, newer],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git merge-base --is-ancestor failed: rc={proc.returncode}")
    return proc.returncode == 0


@dataclass(frozen=True)
class SourcePlaneProjection:
    schemaVersion: int
    kind: str
    truthRole: str
    localRevision: str
    providerRevision: str
    mergeBase: str
    localOnlyCount: int
    providerOnlyCount: int
    relationship: str
    reconciliationRequired: bool
    projectionDigest: str


def project(local_ref: str, provider_ref: str, *, cwd: str = ".") -> SourcePlaneProjection:
    local = _commit(local_ref, cwd=cwd)
    provider = _commit(provider_ref, cwd=cwd)
    merge_base = _git("merge-base", local, provider, cwd=cwd)
    local_only = int(_git("rev-list", "--count", f"{provider}..{local}", cwd=cwd))
    provider_only = int(_git("rev-list", "--count", f"{local}..{provider}", cwd=cwd))

    if local == provider:
        relationship = "SAME"
    elif _is_ancestor(provider, local, cwd=cwd):
        relationship = "LOCAL_AHEAD"
    elif _is_ancestor(local, provider, cwd=cwd):
        relationship = "PROVIDER_AHEAD"
    else:
        relationship = "DIVERGED"

    payload = {
        "localRevision": local,
        "providerRevision": provider,
        "mergeBase": merge_base,
        "localOnlyCount": local_only,
        "providerOnlyCount": provider_only,
        "relationship": relationship,
    }
    digest = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return SourcePlaneProjection(
        schemaVersion=1,
        kind="ordivon.repo-source-plane-projection",
        truthRole="git-source-plane-projection-not-provider-observation-or-publication-authority",
        localRevision=local,
        providerRevision=provider,
        mergeBase=merge_base,
        localOnlyCount=local_only,
        providerOnlyCount=provider_only,
        relationship=relationship,
        reconciliationRequired=relationship != "SAME",
        projectionDigest=digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify one local integration/source ref against one provider-observed Git revision."
    )
    parser.add_argument("--local", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--require-same", action="store_true")
    args = parser.parse_args()
    result = project(args.local, args.provider, cwd=args.repo)
    print(json.dumps(asdict(result), sort_keys=True))
    if args.require_same and result.relationship != "SAME":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
