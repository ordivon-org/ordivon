"""Bounded Rego / real WebStore / Lab GrantStore scope refinement.

This validates current native consumers, not a copied TypeScript matcher.
It proves agreement over the stated finite counterexample corpus only.
"""
from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT.parents[1] / "apps" / "web"
LAB = ROOT / "labs" / "agent-admission-rs"

PREFIXES = (
    "/", "/comments", "/comments/", "/comments/a", "/comments/a/",
    "/site", "/site/", "/文档/", "/a", "/a/", "/ab", "/a.b",
    "/a/../", "/a//", "/a%", "/a?x", "/a#f", "a", "",
)
RESOURCES = (
    "/", "/comments", "/comments/", "/comments/a", "/comments/a/",
    "/comments/ab", "/comments-evil", "/comments.article",
    "/comments/../secret", "/comments/%2e%2e/secret",
    "/comments/./article", "/comments//article",
    "/comments\\..\\secret", "/comments/article?admin",
    "/comments/a#f", "/comments/\\nadmin", "/site", "/site/",
    "/site/probe", "/site-effect", "/文档/研究", "/文档/研究二",
    "/a", "/a/", "/ab", "/a.b", "/a/b", "/a/../b",
    "/a/%2f", "/a//b", "a/b", "",
)

# Independent finite oracle, not imported from a provider implementation.
def canonical_path(value: str) -> bool:
    return (
        value.startswith("/")
        and "//" not in value
        and not any(c in value for c in ("\\", "%", "?", "#"))
        and all(segment not in (".", "..") for segment in value.split("/"))
        and not any(ord(char) < 32 or ord(char) == 127 for char in value)
    )


def expected_scope(prefix: str, resource: str) -> bool:
    return canonical_path(prefix) and canonical_path(resource) and (
        resource == prefix or resource.startswith(
            prefix if prefix.endswith("/") else prefix + "/"
        )
    )


def invoke(args: list[str], cwd: Path, input_bytes: bytes) -> str:
    env = dict(os.environ)
    env.update(MISE_OFFLINE="1", MISE_AUTO_INSTALL="false")
    result = subprocess.run(
        args, cwd=cwd, input=input_bytes, capture_output=True,
        timeout=85, check=False, env=env,
    )
    if result.returncode:
        raise AssertionError(
            f"{args[:4]} failed ({result.returncode}): "
            + result.stderr.decode("utf8", "replace")[:1800]
        )
    return result.stdout.decode("utf8")


# The same case corpus is passed to real native stores; no shadow matcher.
WEB_SOURCE = """
import { readFileSync } from "node:fs";
import { WebStore } from "./src/store.ts";
const cases = JSON.parse(readFileSync(0, "utf8")).cases;
const accepted = [];
const grouped = Map.groupBy(cases, (c) => c.prefix);
for (const [prefix, entries] of grouped) {
  const store = new WebStore(":memory:");
  try {
    store.ensurePrincipal("principal:proof", "proof-user", "Proof User", 1800000000);
    try {
      store.createAgentGrant({
        grantId: "grant:proof", principalId: "principal:proof", agentId: "agent:proof",
        audience: "https://example.invalid", allowedActions: ["read"],
        resourcePrefixes: [prefix], expiresAtEpochSeconds: 2000000000,
        maxRiskClass: "R1", stepUpAtOrAbove: "R4", remainingEffects: 1,
      }, 1800000000);
    } catch { continue; }
    for (const c of entries) {
      try {
        store.resolveAgentGrant("agent:proof", "https://example.invalid", "read",
          c.resource, 1800000000);
        accepted.push(c.id);
      } catch { /* expected deny */ }
    }
  } finally { store.close(); }
}
process.stdout.write(JSON.stringify(accepted));
"""

LAB_SOURCE = """
import { readFileSync } from "node:fs";
import { GrantStore } from "./src/grant-store.ts";
const cases = JSON.parse(readFileSync(0, "utf8")).cases;
const accepted = [];
const grouped = Map.groupBy(cases, (c) => c.prefix);
for (const [prefix, entries] of grouped) {
  const store = new GrantStore(":memory:");
  try {
    try {
      store.createGrant({
        grantId: "grant:proof", principalId: "principal:proof", agentId: "agent:proof",
        audience: "https://example.invalid", allowedActions: ["read"],
        resourcePrefixes: [prefix], expiresAtEpochSeconds: 2000000000,
        maxRiskClass: "R1", stepUpAtOrAbove: "R4", remainingEffects: 1,
      });
    } catch { continue; }
    for (const c of entries) {
      try {
        store.resolveUniqueGrant("agent:proof", "https://example.invalid", "read",
          c.resource, 1800000000);
        accepted.push(c.id);
      } catch { /* expected deny */ }
    }
  } finally { store.close(); }
}
process.stdout.write(JSON.stringify(accepted));
"""


class ScopeRefinementTests(unittest.TestCase):
    def test_policy_and_both_real_typescript_consumers_agree(self) -> None:
        pairs = [(prefix, resource) for prefix in PREFIXES for resource in RESOURCES]
        cases = [
            {"id": str(i), "prefix": prefix, "resource": resource}
            for i, (prefix, resource) in enumerate(pairs)
        ]
        payload = json.dumps({"cases": cases}, ensure_ascii=False).encode("utf8")
        expected = {
            str(i) for i, pair in enumerate(pairs) if expected_scope(*pair)
        }
        old_allows = {
            str(i) for i, (prefix, resource) in enumerate(pairs)
            if resource.startswith(prefix)
        }
        self.assertTrue(expected <= old_allows, "scope would widen old authority")

        query = (
            "[entry.id | some entry in input.cases; "
            "data.ordivon.security.v2.agent_admission.scope_contains("
            "entry.prefix, entry.resource)]"
        )
        opa = json.loads(invoke(
            ["mise", "exec", "--", "opa", "eval", "--stdin-input",
             "--format", "raw", "--data", str(ROOT / "policies"), query],
            ROOT, payload,
        ))
        web = json.loads(invoke(
            ["mise", "exec", "--", "node", "--input-type=module",
             "--eval", WEB_SOURCE], WEB, payload,
        ))
        lab = json.loads(invoke(
            ["mise", "exec", "--", "node", "--input-type=module",
             "--eval", LAB_SOURCE], LAB, payload,
        ))
        for provider, actual in (("Rego", opa), ("WebStore", web), ("Lab GrantStore", lab)):
            actual = set(actual)
            self.assertEqual(
                actual, expected,
                f"{provider}: false_allow={sorted(actual - expected)[:8]}, "
                f"false_deny={sorted(expected - actual)[:8]}",
            )
        print(f"SCOPE_REFINEMENT PASS pairs={len(pairs)} "
              f"allowed={len(expected)} providers=OPA/WebStore/LabGrantStore")


if __name__ == "__main__":
    unittest.main()
