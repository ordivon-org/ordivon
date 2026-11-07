#!/usr/bin/env python3
"""SMT refinement of source-declared scoped HTTP CONNECT authorities to sing-box routes.

Finite policy artifacts are inputs; (inbound, hostname, destination port) are
symbolic. The proof assumes the HTTP proxy supplies a normalized DNS hostname
and TCP CONNECT, matching the selected restricted sing-box grammar. Loaded
bytes, IP literal handling, DNS, UDP and actual Carrier flows require the
existing independent native consumer witnesses.
"""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import z3

ROOT = Path(__file__).resolve().parents[1]
CONFIG_NAMES = {
    "claude": "sing-box.json",
    "discord": "egress.json",
    "model-provider": "egress.json",
    "supply-chain": "egress.json",
    "x-reality": "egress.json",
    "finance": "egress.json",
}
ROUTE_FIELDS = frozenset({"inbound", "domain", "domain_suffix", "port", "network", "action", "outbound"})
ALLOW = {"provider-carrier", "public-direct"}
EXACT_NONFINANCE = frozenset(CONFIG_NAMES) - {"finance"}


class AdmissionError(RuntimeError):
    """Unsupported or contradictory source representation; no proof admitted."""


@dataclass(frozen=True)
class AuthorizedLane:
    inbound: str
    host: str
    port: int
    outbound: str
    suffix: bool = False


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise AdmissionError(message)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: not an object")
    return value


def scalar_list(value: Any, kind: type, description: str) -> list[Any]:
    values = value if isinstance(value, list) else [value]
    require(bool(values) and all(type(v) is kind for v in values),
            f"bad {description}: {value!r}")
    return values


def hostname(value: str) -> str:
    require(bool(value) and value == value.lower() and not value.startswith(".")
            and not value.endswith(".") and ".." not in value,
            f"unsupported hostname {value!r}; normalized ASCII DNS inputs assumed")
    require(all(0 < len(label) <= 63 for label in value.split(".")), f"invalid DNS labels {value!r}")
    require(len(value) <= 253 and all(all(c.isascii() and (c.isalnum() or c == "-") for c in part)
                                  for part in value.split(".")), f"unsupported IDN representation: {value!r}")
    return value


def check_policy_shape(name: str, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    route = cfg.get("route")
    require(isinstance(route, dict), f"{name}: missing route")
    require(set(cfg) <= {"$schema", "log", "inbounds", "outbounds", "route"},
            f"{name}: unsupported top-level egress/DNS configuration")
    require(set(route) == {"rules"}, f"{name}: unexpected route fields or default bypass")
    rules = route["rules"]
    require(isinstance(rules, list) and len(rules) > 1, f"{name}: invalid rules")
    require(rules[-1] == {"action": "reject"}, f"{name}: terminal default must reject")
    inbound = cfg.get("inbounds")
    require(isinstance(inbound, list) and bool(inbound), f"{name}: no inbounds")
    inbound_tags = set()
    for listener in inbound:
        require(listener.get("type") == "http" and listener.get("tag"), f"{name}: only TCP HTTP inbound modeled")
        require(listener["tag"] not in inbound_tags, f"{name}: duplicate inbound")
        inbound_tags.add(listener["tag"])
    outgoing = cfg.get("outbounds")
    require(isinstance(outgoing, list), f"{name}: no outbounds")
    tags = {}
    for out in outgoing:
        tag = out.get("tag")
        require(tag not in tags and tag in ALLOW, f"{name}: unknown outbound {tag}")
        if tag == "provider-carrier":
            require(out == {"type": "http", "tag": tag, "server": "10.252.246.2", "server_port": 19680},
                    f"{name}: unexpected physical carrier")
        else:
            require(name == "finance" and out == {"type": "direct", "tag": "public-direct"},
                    f"{name}: undeclared direct lane")
        tags[tag] = out
    require("provider-carrier" in tags, f"{name}: provider missing")
    for r in rules[:-1]:
        require(set(r) <= ROUTE_FIELDS and r.get("action") == "route",
                f"{name}: unsupported rule operator or field: {r}")
        require(r.get("outbound") in tags, f"{name}: undeclared outgoing tag")
        ib = scalar_list(r.get("inbound"), str, "inbound")
        require(set(ib) <= inbound_tags, f"{name}: unknown inbound")
        require("domain" in r or "domain_suffix" in r, f"{name}: unbounded destination")
        for key in ("domain", "domain_suffix"):
            if key in r:
                for domain in scalar_list(r[key], str, key):
                    hostname(domain)
        for p in scalar_list(r.get("port"), int, "port"):
            require(1 <= p <= 65535, f"{name}: invalid port {p}")
        if "network" in r:
            require(scalar_list(r["network"], str, "network") == ["tcp"],
                    f"{name}: unsupported non-TCP rule")
    return rules


def declared_lanes(name: str, cfg: dict[str, Any]) -> list[AuthorizedLane]:
    config = ROOT / "consumers" / name / "config"
    tags = {v["tag"]: v for v in cfg["inbounds"]}
    declared: list[AuthorizedLane] = []
    if name in EXACT_NONFINANCE:
        authority = read_json(config / "authority.json")
        require(authority.get("directFallback") is False, f"{name}: fallback enabled")
        listener = authority.get("listen", {})
        require(listener.get("protocol") == "http", f"{name}: authority protocol mismatch")
        require(len(tags) == 1, f"{name}: multiple source listener authorities")
        inbound, physical = next(iter(tags.items()))
        # Claude deliberately has a host-visible relay on 19481 feeding a
        # namespace-local sing-box listener on 19480; they are distinct
        # source contracts. The live relay bridge is independently verified.
        if name == "claude":
            require(listener == {"host": "127.0.0.1", "port": 19481, "protocol": "http"}
                    and physical["listen"] == "127.0.0.1"
                    and physical["listen_port"] == 19480,
                    f"{name}: declared relay / namespace boundary changed")
        else:
            require(physical["listen_port"] == listener["port"]
                    and physical["listen"] == listener["host"],
                    f"{name}: listener binding drift")
        for dom in authority.get("allowedHttpsDomains", []):
            declared.append(AuthorizedLane(inbound, hostname(dom), 443, "provider-carrier"))
        for dom in authority.get("allowedHttpsDomainSuffixes", []):
            declared.append(AuthorizedLane(inbound, hostname(dom), 443, "provider-carrier", suffix=True))
    else:
        authority_files = sorted(config.glob("*authority.json"))
        require(len(authority_files) == len(tags), "finance: missing or duplicate source lane declaration")
        for file in authority_files:
            a = read_json(file)
            require(a.get("directFallback") is False, f"{file}: fallback enabled")
            tag = a.get("profile")
            require(tag in tags, f"finance: unknown inbound in {file}")
            require(tags[tag]["listen"] == a.get("listenHost")
                    and tags[tag]["listen_port"] == a.get("listenPort"),
                    f"{file}: proxy listener drift")
            dest = a.get("destination")
            require(isinstance(dest, dict) and hostname(dest.get("host", "")), f"{file}: invalid host")
            ports = a.get("allowedTcpPorts")
            require(isinstance(ports, list) and ports == [dest.get("port")],
                    f"{file}: port authority mismatch")
            expected = "provider-carrier" if "networkAuthority" in a else "public-direct"
            if expected == "public-direct":
                require(tag in {"finance-us-treasury-public", "finance-fred-public-csv"},
                        f"{file}: unexpected direct authority")
            declared.append(AuthorizedLane(tag, dest["host"], dest["port"], expected))
    require(bool(declared), f"{name}: empty admissible policy")
    require(len({(x.inbound, x.host, x.port, x.suffix) for x in declared}) == len(declared),
            f"{name}: duplicated declaration")
    require({x.inbound for x in declared} == set(tags), f"{name}: unmatched consumer listeners")
    return declared


def member(host: z3.SeqRef, exact: str, suffix: bool) -> z3.BoolRef:
    at = host == z3.StringVal(exact)
    if suffix:
        return z3.Or(at, z3.SuffixOf(z3.StringVal("." + exact), host))
    return at


def lane_condition(
    name: str, host: z3.SeqRef, port: z3.ArithRef, inbound: z3.SeqRef,
    source: dict[str, Any] | AuthorizedLane,
) -> z3.BoolRef:
    if isinstance(source, AuthorizedLane):
        return z3.And(inbound == z3.StringVal(source.inbound),
                      port == source.port, member(host, source.host, source.suffix))
    clauses: list[z3.BoolRef] = []
    for key, sym in (("inbound", inbound), ("port", port)):
        values = scalar_list(source.get(key), str if key == "inbound" else int, key)
        clauses.append(z3.Or(*[sym == (z3.StringVal(v) if key == "inbound" else v) for v in values]))
    # The scoped HTTP inbound only offers TCP CONNECT; the optional rule
    # network field was already restricted to either omitted or ["tcp"].
    domains = [member(host, d, False) for d in scalar_list(source["domain"], str, "domain")] if "domain" in source else []
    suff = [member(host, d, True) for d in scalar_list(source["domain_suffix"], str, "domain_suffix")] if "domain_suffix" in source else []
    clauses.append(z3.Or(*domains, *suff))
    return z3.And(*clauses)


def actual_route(name: str, rules: list[dict[str, Any]], host: z3.SeqRef,
                 port: z3.ArithRef, inbound: z3.SeqRef) -> z3.SeqRef:
    result: z3.SeqRef = z3.StringVal("reject")
    for rule in reversed(rules[:-1]):
        result = z3.If(lane_condition(name, host, port, inbound, rule),
                       z3.StringVal(rule["outbound"]), result)
    return result


def specified_route(lanes: list[AuthorizedLane], host: z3.SeqRef,
                    port: z3.ArithRef, inbound: z3.SeqRef) -> z3.SeqRef:
    out: z3.SeqRef = z3.StringVal("reject")
    for lane in reversed(lanes):
        out = z3.If(lane_condition("spec", host, port, inbound, lane),
                    z3.StringVal(lane.outbound), out)
    return out


def validate_refinement(name: str, cfg: dict[str, Any], lanes: list[AuthorizedLane]) -> int:
    rules = check_policy_shape(name, cfg)
    host, port, inbound = z3.String(f"{name}_host"), z3.Int(f"{name}_port"), z3.String(f"{name}_inbound")
    expected = specified_route(lanes, host, port, inbound)
    actual = actual_route(name, rules, host, port, inbound)
    scope = z3.And(port >= 1, port <= 65535, z3.Length(host) >= 1, z3.Length(host) <= 253)
    solver = z3.Solver()
    solver.add(scope, actual != expected)
    status = solver.check()
    if status == z3.sat:
        model = solver.model()
        raise AdmissionError(f"{name}: SMT refinement counterexample "
                             f"{model.eval(inbound)}, {model.eval(host)}, {model.eval(port)}; "
                             f"source={model.eval(actual)} declared={model.eval(expected)}")
    require(status == z3.unsat, f"{name}: SMT solver returned UNKNOWN")
    # Rule non-vacuity: each independently declared concrete authorized origin
    # must be admitted by actual policy, including one non-root suffix child.
    for lane in lanes:
        concrete = ("subdomain." + lane.host) if lane.suffix else lane.host
        reach = z3.Solver()
        reach.add(host == z3.StringVal(concrete), port == lane.port,
                  inbound == z3.StringVal(lane.inbound),
                  actual == z3.StringVal(lane.outbound))
        require(reach.check() == z3.sat, f"{name}: declared origin unreachable {lane}")
    return len(lanes)


def falsify_source_policy(name: str, cfg: dict[str, Any], lanes: list[AuthorizedLane]) -> None:
    # Negative mutation is not a duplicate example-based policy test: the
    # very same quantified SMT refinement must admit a counterexample.
    bad = copy.deepcopy(cfg)
    r = bad["route"]["rules"]
    r.insert(-1, {"inbound": [lanes[0].inbound], "domain": ["rogue.example.invalid"],
                  "port": lanes[0].port, "action": "route", "outbound": "provider-carrier"})
    try:
        validate_refinement(name, bad, lanes)
    except AdmissionError as exc:
        require("counterexample" in str(exc), "mutant not rejected by SMT refutation")
    else:
        raise AdmissionError(f"{name}: rogue destination mutation falsely proven safe")


def main() -> None:
    summary = []
    for name, source in CONFIG_NAMES.items():
        cfg = read_json(ROOT / "consumers" / name / "config" / source)
        lanes = declared_lanes(name, cfg)
        n = validate_refinement(name, cfg, lanes)
        falsify_source_policy(name, cfg, lanes)
        summary.append({"consumer": name, "declaredLanes": n, "standing": "SMT_REFINEMENT_UNSAT",
                        "mutation": "ROGUE_ORIGIN_COUNTEREXAMPLE"})
    print(json.dumps({
        "kind": "ordivon.network.formal-egress-policy-refinement",
        "model": "symbolic TCP HTTP CONNECT inbound/domain/port; source vs independent authority",
        "standing": "PROVED_WITHIN_MODEL",
        "solver": z3.get_version_string(),
        "consumerPolicies": len(summary),
        "declaredLanes": sum(x["declaredLanes"] for x in summary),
        "sourceOnly": True,
        "unproved": ["installed/loaded byte parity", "actual application process routing",
                     "DNS/DoH/UDP/IPv6 and IP-literal interactions", "sing-box native runtime effects"],
        "results": summary
    }, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except AdmissionError as exc:
        print(json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}), file=sys.stderr)
        sys.exit(1)
