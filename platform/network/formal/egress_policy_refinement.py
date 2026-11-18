#!/usr/bin/env python3
"""SMT refinement of the declared temporary OPEN TCP CONNECT routes.

Independent open-mode intent is represented in config/open-connectivity.json.
Actual sing-box source is a separate input.  For EVERY valid inbound, public
hostname and TCP port, the route must use the existing shared Carrier, except
the two explicit Finance public-direct listeners.  This is not proof of DNS,
TLS, UDP, actual consumer traffic, IP-literal semantics or device-side paths.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import z3

ROOT = Path(__file__).resolve().parents[1]
CARRIER = {"type": "http", "tag": "provider-carrier",
           "server": "10.252.246.2", "server_port": 19680}
DIRECT = {"type": "direct", "tag": "public-direct"}
CONFIG_NAMES = {
    "codex": "sing-box.json",
    "chat-ingress": "sing-box.json",
    "claude": "sing-box.json",
    "discord": "egress.json",
    "model-provider": "egress.json",
    "supply-chain": "egress.json",
    "x-reality": "egress.json",
    "finance": "egress.json",
    "windows-real-chrome": "sing-box.json",
}
FINANCE_DIRECT = frozenset({
    "finance-us-treasury-public", "finance-fred-public-csv",
})


class AdmissionError(RuntimeError):
    """Unsupported source configuration or non-refining network behavior."""


def require(ok: bool, why: str) -> None:
    if not ok:
        raise AdmissionError(why)


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: not a JSON object")
    return value


def read_independent_intent() -> dict:
    policy = read_json(ROOT / "config/open-connectivity.json")
    require(set(policy) == {
        "schemaVersion", "mode", "defaultOutbound", "consumers",
        "publicDirectInbounds",
    }, "open mode: unexpected independent policy fields")
    require(policy["schemaVersion"] == 1
            and policy["mode"] == "temporary-open-tcp-connect"
            and policy["defaultOutbound"] == "provider-carrier",
            "open mode: unsupported independent policy")
    require(set(policy["consumers"]) == set(CONFIG_NAMES)
            and len(policy["consumers"]) == len(CONFIG_NAMES),
            "open mode: incomplete consumer scope")
    require(policy["publicDirectInbounds"] == {
        "finance": sorted(FINANCE_DIRECT)
    }, "open mode: unexpected direct route exemptions")
    return policy


def admit(name: str, cfg: dict, policy: dict) -> tuple[str, ...]:
    require(set(cfg) <= {"$schema", "log", "inbounds", "outbounds", "route"},
            f"{name}: unexpected network stack or DNS override")
    inbound = cfg.get("inbounds")
    require(isinstance(inbound, list)
            and len(inbound) == (9 if name == "finance" else 1),
            f"{name}: listener count drift")
    tags = []
    for x in inbound:
        require(isinstance(x, dict) and x.get("type") in ("http", "mixed")
                and x.get("listen") == "127.0.0.1"
                and type(x.get("listen_port")) is int
                and 1 <= x["listen_port"] <= 65535
                and isinstance(x.get("tag"), str) and x["tag"],
                f"{name}: listener not bound to loopback / wrong protocol")
        if x["type"] == "mixed":
            require(name in ("chat-ingress", "windows-real-chrome"),
                    f"{name}: undeclared mixed listener")
        tags.append(x["tag"])
    require(len(tags) == len(set(tags)), f"{name}: duplicate listen tags")
    require(set(policy["publicDirectInbounds"].get(name, [])) <= set(tags),
            f"{name}: missing independently declared direct inbound")
    expected_out = [CARRIER, DIRECT] if name == "finance" else [CARRIER]
    require(cfg.get("outbounds") == expected_out, f"{name}: outbound carrier drift")
    route = cfg.get("route")
    require(isinstance(route, dict) and set(route) == {"rules", "final"}
            and route["final"] == policy["defaultOutbound"],
            f"{name}: open default Carrier not installed")
    rules = route["rules"]
    require(isinstance(rules, list), f"{name}: route rules malformed")
    direct_tags = policy["publicDirectInbounds"].get(name, [])
    require(len(rules) == len(direct_tags),
            f"{name}: undeclared narrower or wider routing exception")
    observed_direct = []
    for r in rules:
        require(isinstance(r, dict)
                and set(r) == {"inbound", "action", "outbound"}
                and r.get("action") == "route"
                and r.get("outbound") == "public-direct"
                and isinstance(r.get("inbound"), list)
                and len(r["inbound"]) == 1
                and r["inbound"][0] in direct_tags,
                f"{name}: unsupported direct exception / route operator")
        observed_direct.append(r["inbound"][0])
    require(sorted(observed_direct) == sorted(direct_tags),
            f"{name}: extra or missing public-direct exception")
    return tuple(tags)


def actual_route(cfg: dict, inbound: z3.SeqRef) -> z3.SeqRef:
    route = cfg["route"]
    decision = z3.StringVal(route["final"])
    for rule in reversed(route["rules"]):
        for tag in reversed(rule.get("inbound", [])):
            decision = z3.If(inbound == z3.StringVal(tag),
                             z3.StringVal(rule["outbound"]), decision)
    return decision


def intended_route(name: str, policy: dict, inbound: z3.SeqRef) -> z3.SeqRef:
    decision = z3.StringVal(policy["defaultOutbound"])
    for tag in policy["publicDirectInbounds"].get(name, []):
        decision = z3.If(inbound == z3.StringVal(tag),
                         z3.StringVal("public-direct"), decision)
    return decision


def mismatch(name: str, cfg: dict, policy: dict,
             tags: tuple[str, ...]) -> z3.CheckSatResult:
    # Host and port range are quantified by the counterexample search.
    # Their ABSENCE from native route expressions means no domain/port
    # allowlist is hidden inside the admitted rule grammar.
    host, port, inbound = (
        z3.String(f"{name}_host"),
        z3.Int(f"{name}_port"),
        z3.String(f"{name}_inbound"),
    )
    solver = z3.Solver()
    solver.set(timeout=5000)
    solver.add(z3.Or(*[inbound == z3.StringVal(tag) for tag in tags]))
    solver.add(z3.Length(host) >= 1, z3.Length(host) <= 253)
    solver.add(port >= 1, port <= 65535)
    solver.add(actual_route(cfg, inbound) != intended_route(name, policy, inbound))
    return solver.check()


def prove(name: str, cfg: dict, policy: dict) -> dict:
    tags = admit(name, cfg, policy)
    require(mismatch(name, cfg, policy, tags) == z3.unsat,
            f"{name}: Z3 found route counterexample or returned UNKNOWN")
    # Independent falsification: an unintended restrictive default MUST
    # generate a counterexample (unlike a vacuous model-only source check).
    reject_mutant = copy.deepcopy(cfg)
    reject_mutant["route"]["final"] = "reject"
    require(mismatch(name, reject_mutant, policy, tags) == z3.sat,
            f"{name}: restrictive mutation not refuted")
    if name == "finance":
        redirect_mutant = copy.deepcopy(cfg)
        redirect_mutant["route"]["rules"].append({
            "inbound": ["finance-okx"],
            "action": "route",
            "outbound": "public-direct",
        })
        require("finance-okx" in tags, "finance: unknown independent provider inbound")
        require(mismatch(name, redirect_mutant, policy, tags) == z3.sat,
                "finance: rogue direct escape not refuted")
    return {
        "consumer": name,
        "inbounds": len(tags),
        "standing": "SMT_REFINEMENT_UNSAT",
        "mutation": "OPEN_DEFAULT_REJECTED_BY_COUNTEREXAMPLE",
    }


def main() -> None:
    policy = read_independent_intent()
    results = [prove(name, read_json(ROOT / "consumers" / name / "config" / filename),
                     policy) for name, filename in CONFIG_NAMES.items()]
    print(json.dumps({
        "kind": "ordivon.network.formal-egress-policy-refinement",
        "model": "symbolic TCP CONNECT (inbound, arbitrary host, port): open Carrier except two Finance direct inbounds",
        "standing": "PROVED_WITHIN_MODEL",
        "solver": z3.get_version_string(),
        "consumerPolicies": len(results),
        "declaredLanes": sum(r["inbounds"] for r in results),
        "sourceOnly": True,
        "unproved": [
            "installed/loaded byte parity and running process",
            "actual application-origin traffic and external API authorization",
            "DNS, UDP, IPv6, tunneling, endpoint country and failover",
        ],
        "results": results,
    }, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except AdmissionError as exc:
        print(json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}),
              file=sys.stderr)
        raise SystemExit(1) from None
