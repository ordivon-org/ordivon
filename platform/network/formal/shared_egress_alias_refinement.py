#!/usr/bin/env python3
"""Finite source-refinement proof for the Browserless -> Shared Egress Unit alias.
NOT proof of installed/loaded systemd, real DNS/VPN/UDP or app traffic.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import deque
from pathlib import Path

BASE = "8294059da75b6a363a27f83d552b9c18fed43681"
OLD = "network-v2-browserless.target"
NEW = "network-v2-shared-egress.target"
PREFIX = "platform/network"
UNITS = {
    "codex": ("network-v2-codex.target", "network-v2-codex-proxy.service", "network-v2-codex-relay.service"),
    "windows-real-chrome": ("network-v2-windows-real-chrome.target", "network-v2-windows-real-chrome-proxy.service", "network-v2-windows-real-chrome-relay.service"),
    "chat-ingress": ("network-v2-chat-ingress.target", "network-v2-chat-ingress-proxy.service", "network-v2-chat-ingress-relay.service"),
    "claude": ("network-v2-claude.target", "network-v2-claude-proxy.service", "network-v2-claude-relay.service", "network-v2-claude-client-netns.service"),
}
EDGES = {"After", "Requires", "Wants", "BindsTo", "Requisite", "PartOf", "Upholds"}

class NotProved(Exception):
    pass

def require(ok: bool, why: str) -> None:
    if not ok:
        raise NotProved(why)

def now(repo: Path, rel: str) -> str:
    p = repo / rel
    require(p.is_file() and not p.is_symlink(), f"missing or symlink: {rel}")
    return p.read_text(encoding="utf-8")

def before(repo: Path, rel: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), "show", f"{BASE}:{rel}"],
                       capture_output=True, text=True, check=False)
    require(p.returncode == 0, f"missing anchored baseline: {rel}")
    return p.stdout

def unit_edges(text: str) -> set[str]:
    section, pending = "", ""
    found: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        line = pending + line
        pending = ""
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if section != "Unit" or "=" not in line:
            continue
        key, val = (x.strip() for x in line.split("=", 1))
        require(key not in {"Before", "PropagatesStopTo", "StopPropagatedFrom", "Conflicts"},
                f"unmodeled coupling: {key}")
        if key in EDGES:
            require(bool(val), f"reset semantics unsupported: {key}")
            for target in val.split():
                require(target.endswith((".service", ".target", ".timer", ".socket", ".path")),
                        f"dynamic/unsupported unit: {target}")
                found.add(target)
    require(not pending, "unterminated continuation")
    return found

def reachable(graph: dict[str, set[str]], start: str) -> set[str]:
    visited: set[str] = set()
    queue = deque([start])
    while queue:
        u = queue.popleft()
        if u in visited:
            continue
        visited.add(u)
        queue.extend(v for v in graph.get(u, ()) if v not in visited)
    return visited

def prove(repo: Path) -> dict:
    target = f"{PREFIX}/substrates/shared-egress/systemd/{OLD}"
    previous, present = before(repo, target), now(repo, target)
    declaration = f"Alias={NEW}\n"
    require(present.count(declaration) == 1 and present.replace(declaration, "") == previous,
            "canonical target changed beyond exactly one alias declaration")
    require(not (repo / PREFIX / "substrates/shared-egress/systemd" / NEW).exists(),
            "competing physical target exists instead of one systemd alias")
    base: dict[str, set[str]] = {}
    projected: dict[str, set[str]] = {}
    for owner, units in UNITS.items():
        for unit in units:
            rel = f"{PREFIX}/consumers/{owner}/systemd/{unit}"
            old_text, new_text = before(repo, rel), now(repo, rel)
            require(NEW in new_text and OLD not in new_text, f"partial replacement: {rel}")
            require(new_text.replace(NEW, OLD) == old_text, f"extra Unit semantic delta: {rel}")
            require(unit not in base, f"duplicate unit: {unit}")
            base[unit] = unit_edges(old_text)
            projected[unit] = {OLD if dep == NEW else dep for dep in unit_edges(new_text)}
    provider_target = "network-v2-gluetun-owned.target"
    provider_rel = f"{PREFIX}/providers/gluetun/systemd/{provider_target}"
    provider_before, provider_after = before(repo, provider_rel), now(repo, provider_rel)
    require(NEW in provider_after and OLD not in provider_after,
            f"provider target not migrated: {provider_rel}")
    require(provider_after.replace(NEW, OLD) == provider_before,
            f"provider target has extra semantic delta: {provider_rel}")
    require(provider_target not in base, "provider target duplicate")
    base[provider_target] = unit_edges(provider_before)
    projected[provider_target] = {
        OLD if dep == NEW else dep for dep in unit_edges(provider_after)
    }
    for owner, config in (("chat-ingress", "egress.json"), ("claude", "authority.json")):
        rel = f"{PREFIX}/consumers/{owner}/config/{config}"
        old, new = json.loads(before(repo, rel)), json.loads(now(repo, rel))
        require(old["networkAuthority"]["serviceUnit"] == OLD and
                new["networkAuthority"]["serviceUnit"] == NEW,
                f"wrong semantic authority: {owner}")
        new["networkAuthority"]["serviceUnit"] = OLD
        require(new == old, f"extra authority delta: {owner}")
    require(base == projected, "edge-set inequality after canonicalization")
    nodes = set(base) | {v for deps in base.values() for v in deps}
    a = {n: base.get(n, set()) for n in nodes}
    b = {n: projected.get(n, set()) for n in nodes}
    for root in sorted(nodes):
        require(reachable(a, root) == reachable(b, root),
                f"dependency reachability counterexample: {root}")
    mutant = {k: set(v) for k, v in projected.items()}
    victim = sorted(mutant)[0]
    mutant[victim].add("ordivon-formal-rogue.target")
    require(reachable({**b, victim: mutant[victim]}, victim) != reachable(a, victim),
            "negative edge mutant escaped graph-refinement proof")
    provider_mutant = {name: set(deps) for name, deps in projected.items()}
    provider_mutant[provider_target].add("ordivon-formal-unapproved-provider.target")
    require(reachable({**b, provider_target: provider_mutant[provider_target]},
                      provider_target) != reachable(a, provider_target),
            "provider dependency mutation escaped proof")
    return {
        "kind": "ordivon.network.formal-shared-egress-alias-refinement",
        "standing": "SOURCE_REFINEMENT_PROVED",
        "method": "finite graph canonicalization and exhaustive transitive closure",
        "baseRevision": BASE,
        "consumerModules": len(UNITS),
        "providerTargets": 1,
        "unitFiles": len(base),
        "graphNodes": len(nodes),
        "aliasMapping": {NEW: OLD},
        "negativeControl": "consumer and provider extra dependencies change reachability",
        "unproved": ["installed and loaded systemd drop-ins", "process PID continuity",
                     "physical VPN/UDP/DNS/IPv6", "real iPad and other app traffic"],
    }

if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
    try:
        print(json.dumps(prove(root), sort_keys=True))
    except (NotProved, KeyError, OSError, ValueError) as exc:
        print(json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}), file=sys.stderr)
        sys.exit(1)
