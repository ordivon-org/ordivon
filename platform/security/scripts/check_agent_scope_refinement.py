#!/usr/bin/env python3
"""Bounded Rego ↔ real TypeScript GrantStore ↔ independent path-spec refinement.

This is a *finite source-consumer check*, not a theorem about every resource
identity or a deployed Owner PEP. All providers must execute successfully.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

OWNER = Path(__file__).resolve().parents[1]
LAB = OWNER / "labs" / "agent-admission-rs"
POLICIES = OWNER / "policies"

# The source-bound v1 profile defines canonical absolute resource paths.
# Values with URL-decoding ambiguities or path traversal aliases are invalid.
def canonical_path(value: str) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("/")
        and "//" not in value
        and not any(ch in value for ch in ("\\", "%", "?", "#"))
        and not any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
        and all(seg not in (".", "..") for seg in value.split("/"))
    )


def expected_scope(prefix: str, resource: str) -> bool:
    if not (canonical_path(prefix) and canonical_path(resource)):
        return False
    return resource == prefix or resource.startswith(
        prefix if prefix.endswith("/") else prefix + "/"
    )


# Independent named falsifiers are assertions, not derived from the implementation.
MUST_DENY = [
    ("/comments", "/comments-evil"),
    ("/comments/", "/comments/../account/recovery"),
    ("/comments/", "/comments/%2e%2e/account"),
    ("/comments/", "/comments/./article-42"),
    ("/comments/", "/comments//article-42"),
    ("/comments/", "/comments/.."),
    ("/comments/", "/comments/a?admin=true"),
    ("/comments/", "/comments/a#private"),
    ("/comments/", "/comments\\..\\secret"),
    ("/comments/", "/comments/\nadmin"),
    ("/comments/../", "/comments/article-42"),
    ("comments/", "/comments/article-42"),
    ("/comments%", "/comments/article-42"),
    ("/comments//", "/comments/article-42"),
]
MUST_ALLOW = [
    ("/comments", "/comments"),
    ("/comments", "/comments/article-42"),
    ("/comments/", "/comments/article-42"),
    ("/comments/article-42", "/comments/article-42"),
    ("/", "/comments/article-42"),
    ("/文档/", "/文档/研究"),
]
assert all(not expected_scope(*case) for case in MUST_DENY)
assert all(expected_scope(*case) for case in MUST_ALLOW)

prefixes = [
    "/", "/comments", "/comments/", "/comments/a", "/comments/a/",
    "/site", "/site/", "/文档/", "/a", "/a/", "/ab", "/a.b",
    "/a/../", "/a//", "/a%", "/a?x", "/a#f", "a", "",
]
resources = [
    "/", "/comments", "/comments/", "/comments/a", "/comments/a/", "/comments/ab",
    "/comments-evil", "/comments.article", "/comments/../secret",
    "/comments/%2e%2e/secret", "/comments/./article", "/comments//article",
    "/comments\\..\\secret", "/comments/article?admin", "/comments/a#f",
    "/comments/\nadmin", "/site", "/site/", "/site/probe",
    "/site-effect", "/文档/研究", "/文档/研究二", "/a", "/a/", "/ab",
    "/a.b", "/a/b", "/a/../b", "/a/%2f", "/a//b", "a/b", "",
]
pairs = list(dict.fromkeys(MUST_DENY + MUST_ALLOW + [
    (prefix, resource) for prefix in prefixes for resource in resources
]))
cases = [
    {"id": str(i), "prefix": prefix, "resource": resource}
    for i, (prefix, resource) in enumerate(pairs)
]
input_bytes = json.dumps({"cases": cases}, ensure_ascii=False).encode("utf-8")

env = dict(os.environ)
env["MISE_OFFLINE"] = "1"
env["MISE_AUTO_INSTALL"] = "false"

def invoke(args: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        args,
        input=input_bytes,
        cwd=cwd,
        capture_output=True,
        timeout=65,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"provider failed: {args[:4]!r} exit={completed.returncode} "
            + completed.stderr.decode("utf-8", errors="replace")[:3500]
        )
    return completed.stdout.decode("utf-8")

# One OPA invocation evaluates every concrete boundary from current native Rego.
rego_query = (
    "[entry.id | some entry in input.cases; "
    "data.ordivon.security.v2.agent_admission.scope_contains("
    "entry.prefix, entry.resource)]"
)
opa_ids = json.loads(
    invoke(
        ["mise", "exec", "--", "opa", "eval", "--stdin-input", "-f", "raw",
         "-d", str(POLICIES), rego_query],
        cwd=OWNER,
    )
)

# Exercise the *actual* GrantStore contract, rather than copying TS matching
# logic into a fixture or a new Python implementation.
node_source = '''
import { readFileSync } from "node:fs";
import { GrantStore } from "./src/grant-store.ts";
const cases = JSON.parse(readFileSync(0, "utf8")).cases;
const allowed = [];
for (const c of cases) {
  const store = new GrantStore(":memory:");
  try {
    store.createGrant({
      grantId: "grant:case", principalId: "principal:proof",
      agentId: "agent:proof", audience: "https://example.invalid",
      allowedActions: ["read"], resourcePrefixes: [c.prefix],
      expiresAtEpochSeconds: 2000000000, maxRiskClass: "R1",
      stepUpAtOrAbove: "R4", remainingEffects: 1,
    });
    try {
      store.resolveUniqueGrant(
        "agent:proof", "https://example.invalid", "read", c.resource, 1800000000
      );
      allowed.push(c.id);
    } catch { /* denial */ }
  } catch { /* malformed grant is not allowed */ }
  finally { store.close(); }
}
process.stdout.write(JSON.stringify(allowed));
'''
ts_ids = json.loads(
    invoke(["mise", "exec", "--", "node", "--input-type=module",
            "--eval", node_source], cwd=LAB)
)
assert isinstance(opa_ids, list) and isinstance(ts_ids, list), "invalid native provider output"
expected_ids = {
    str(i) for i, (prefix, resource) in enumerate(pairs)
    if expected_scope(prefix, resource)
}
# Restriction monotonicity over the bounded sample space: the new check cannot
# admit an action rejected by the old raw startswith rule.
old_allow_ids = {
    str(i) for i, (prefix, resource) in enumerate(pairs)
    if resource.startswith(prefix)
}
assert expected_ids <= old_allow_ids, "resource-scope change widened authority"
rego_ids, lab_ids = set(opa_ids), set(ts_ids)
for name, actual in (("OPA", rego_ids), ("TypeScript GrantStore", lab_ids)):
    if actual != expected_ids:
        false_allows = sorted(actual - expected_ids)[:12]
        false_denies = sorted(expected_ids - actual)[:12]
        raise AssertionError(
            f"{name} disagrees with canonical segment specification; "
            f"falseAllows={false_allows}, falseDenies={false_denies}"
        )
if rego_ids != lab_ids:
    raise AssertionError("OPA and TypeScript GrantStore scope semantics diverged")
print(
    "SECURITY_AGENT_SCOPE_REFINEMENT PASS: "
    f"cases={len(cases)}, allowed={len(expected_ids)}, "
    "providers=OPA+native-TypeScript-GrantStore, no_widening=true, source_only=true"
)
