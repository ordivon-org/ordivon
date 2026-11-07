#!/usr/bin/env python3
"""Z3 inductive DNS cache/parallel-upstream safety model and native-source admission.

Scope: one cacheable A record key, two independent upstream liveness bits,
integer TTL, and one continuously running dnsproxy process. Models bounded
semantic transitions at unbounded logical time; Z3 checks an *arbitrary*
inductive step (not a hand-picked finite trace). Upstream response validity,
scheduler fairness, network transport, dnsproxy implementation refinement and
negative caching are outside this mathematical model. Native DNS fault
acceptance remains the independent implementation witness.
"""
from __future__ import annotations

import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

import z3

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SERVICE = ROOT / "systemd/network-v2-dnsproxy.service"
FAULT_ACCEPTANCE = ROOT / "acceptance/dns/upstream-resilience.sh"
UPSTREAMS = ("1.1.1.1:53", "8.8.8.8:53")
TTL_MAX = 2  # fixture local-ttl=2; model bound, NOT production TTL
IDLE, ANSWER, SERVFAIL = 0, 1, 2


class ContractViolation(RuntimeError):
    pass


def assert_source_admission() -> None:
    """Prove the *assumptions* have source references before SMT execution."""
    text = NATIVE_SERVICE.read_text(encoding="utf-8")
    starts = [s[len("ExecStart="):] for s in text.splitlines() if s.startswith("ExecStart=")]
    if len(starts) != 1:
        raise ContractViolation("DNS systemd start command missing/ambiguous")
    argv = shlex.split(starts[0])
    if not argv or argv[0] != "/usr/bin/dnsproxy":
        raise ContractViolation("DNS provider executable changed")
    tokens = [argv[n + 1] for n, x in enumerate(argv[:-1]) if x == "-u"]
    if sorted(tokens) != sorted(UPSTREAMS) or len(tokens) != 2:
        raise ContractViolation("unmodeled upstream count/addresses")
    if argv.count("--upstream-mode") != 1 or argv[argv.index("--upstream-mode") + 1] != "parallel":
        raise ContractViolation("parallel upstream selection not installed in source")
    if "--cache" not in argv or "--refuse-any" not in argv:
        raise ContractViolation("source cache or ANY-policy missing")
    if any(x == "--cache-optimistic" or x.startswith("--cache-optimistic=")
           or x.startswith("--cache-min-ttl") for x in argv):
        raise ContractViolation("stale-cache/TTL override requires a different formal model")
    if argv.count("--timeout") != 1:
        raise ContractViolation("unbounded DNS upstream timeouts")
    fixture = FAULT_ACCEPTANCE.read_text(encoding="utf-8")
    # The script constructs the two partial-failure labels dynamically;
    # match the semantically real command and response observations.
    if '--local-ttl=2' not in fixture:
        raise ContractViolation("DNS acceptance fixture TTL no longer matches model")
    if not all(x in fixture for x in ('--upstream-mode parallel', '--cache', 'systemctl stop "$UP"',
                                       'all_upstreams_down_uncached_servfail=PASS',
                                       'cache_expiry_fail_closed=PASS',
                                       'dns_upstream_recovery_without_dnsproxy_restart=PASS',
                                       'proxy_pid_after', 'proxy_pid_before')):
        raise ContractViolation("native fault acceptance missing source-side witness")
    if "--cache-optimistic" in fixture or "--cache-min-ttl" in fixture:
        raise ContractViolation("native fault acceptance semantics changed")


@dataclass(frozen=True)
class State:
    up0: z3.BoolRef
    up1: z3.BoolRef
    ttl: z3.ArithRef
    running: z3.BoolRef
    response: z3.ArithRef


def state(prefix: str) -> State:
    return State(
        up0=z3.Bool(f"{prefix}_up0"),
        up1=z3.Bool(f"{prefix}_up1"),
        ttl=z3.Int(f"{prefix}_ttl"),
        running=z3.Bool(f"{prefix}_running"),
        response=z3.Int(f"{prefix}_response"),
    )


def wellformed(s: State) -> z3.BoolRef:
    return z3.And(s.ttl >= 0, s.ttl <= TTL_MAX,
                  s.running, z3.Or(s.response == IDLE,
                                   s.response == ANSWER, s.response == SERVFAIL))


def preserved(s: State, t: State) -> z3.BoolRef:
    return z3.And(t.running == s.running)


def fail_upstream(s: State, t: State, which: int) -> z3.BoolRef:
    return z3.And(
        preserved(s, t), t.ttl == s.ttl, t.response == IDLE,
        t.up0 == (z3.BoolVal(False) if which == 0 else s.up0),
        t.up1 == (z3.BoolVal(False) if which == 1 else s.up1),
    )


def recover_upstream(s: State, t: State, which: int) -> z3.BoolRef:
    return z3.And(
        preserved(s, t), t.ttl == s.ttl, t.response == IDLE,
        t.up0 == (z3.BoolVal(True) if which == 0 else s.up0),
        t.up1 == (z3.BoolVal(True) if which == 1 else s.up1),
    )


def tick(s: State, t: State, elapsed: z3.ArithRef) -> z3.BoolRef:
    return z3.And(
        elapsed > 0, preserved(s, t), t.up0 == s.up0, t.up1 == s.up1,
        t.ttl == z3.If(s.ttl > elapsed, s.ttl - elapsed, 0),
        t.response == IDLE,
    )


def query(s: State, t: State, cached_key: z3.BoolRef,
          *, mutant_stale: bool = False) -> z3.BoolRef:
    available = z3.Or(s.up0, s.up1)
    cache_hit = z3.And(cached_key, (s.ttl >= 0 if mutant_stale else s.ttl > 0))
    success = z3.Or(available, cache_hit)
    return z3.And(
        preserved(s, t), t.up0 == s.up0, t.up1 == s.up1,
        t.ttl == z3.If(z3.And(available, z3.Not(cache_hit)), TTL_MAX, s.ttl),
        t.response == z3.If(success, ANSWER, SERVFAIL),
    )


def prove(name: str, assumptions: list[z3.BoolRef], bad: z3.BoolRef,
          *, expected: z3.CheckSatResult = z3.unsat) -> None:
    solver = z3.Solver()
    solver.set(timeout=12000)
    solver.add(*assumptions, bad)
    outcome = solver.check()
    if outcome != expected:
        if outcome == z3.sat:
            raise ContractViolation(f"{name}: unexpected SAT, counterexample: {solver.model()}")
        raise ContractViolation(f"{name}: expected {expected}, returned {outcome}")
    if expected == z3.sat:
        # SAT is a necessary negative mutation control proving not vacuous.
        print(f"REFUTATION={name}:SAT")


def main() -> None:
    assert_source_admission()
    s, t = state("s"), state("t")
    alive = z3.Or(s.up0, s.up1)
    key = z3.Bool("key_cached")
    elapsed = z3.Int("elapsed")
    moves = [
        fail_upstream(s, t, 0), fail_upstream(s, t, 1),
        recover_upstream(s, t, 0), recover_upstream(s, t, 1),
        tick(s, t, elapsed),
        query(s, t, key),
    ]
    # Inductive invariant: arbitrary pre-state, all transition cases,
    # no proxy restart or negative TTL introduced by any transition.
    for i, move in enumerate(moves):
        prove(f"inductive_{i}", [wellformed(s), move], z3.Not(wellformed(t)))

    no_up = z3.And(z3.Not(s.up0), z3.Not(s.up1))
    for cached in (True, False):
        # Post-outage expired cache MUST NOT serve even when querying old key.
        prove(f"expired_offline_{cached}", [
            wellformed(s), no_up, s.ttl == 0,
            query(s, t, z3.BoolVal(cached)),
        ], t.response == ANSWER)

    # A still-valid cache may serve while both providers are offline.
    prove("fresh_cache_offline",
          [wellformed(s), no_up, s.ttl > 0,
           query(s, t, z3.BoolVal(True))],
          t.response != ANSWER)

    # Cold query must succeed if any upstream is available.
    prove("partial_failure_survival",
          [wellformed(s), alive,
           query(s, t, z3.BoolVal(False))],
          t.response != ANSWER)

    # On recovery, a new query succeeds without changing daemon identity.
    for which in (0, 1):
        mid = state(f"mid{which}")
        prove(f"recover_without_restart_{which}",
              [wellformed(s), no_up, recover_upstream(s, mid, which),
               query(mid, t, z3.BoolVal(False))],
              z3.Or(t.response != ANSWER, t.running != s.running))

    # Deliberately broken optimistic stale-cache behavior is detected by
    # exactly the same offline-expiry proof property, not separate sample tests.
    prove("stale_mutant",
          [wellformed(s), no_up, s.ttl == 0,
           query(s, t, z3.BoolVal(True), mutant_stale=True)],
          t.response == ANSWER, expected=z3.sat)

    print(json.dumps({
        "kind": "ordivon.network.dns-cache-upstream-formal",
        "standing": "PROVED_WITHIN_ABSTRACTION",
        "tool": "Z3",
        "version": z3.get_version_string(),
        "inductionCases": len(moves),
        "propertyClasses": [
            "nonnegative-ttl-and-process-preservation",
            "all-upstream-outage-expired-cache-no-serve",
            "valid-cache-partial-failure-allowed",
            "single-upstream-survival",
            "post-recovery-new-query-no-proxy-restart",
        ],
        "mutation": "stale-response SAT counterexample",
        "sourceBound": ["network-v2-dnsproxy.service", "acceptance/dns/upstream-resilience.sh"],
        "assumptions": [
            "two independent upstream liveness booleans",
            "one cacheable known A query with TTL=2 in acceptance fixture",
            "upstream replies truthful when reachable",
            "request executes fairly after recovery",
            "cache-optimistic disabled; no stale-cache serving",
        ],
        "unproved": [
            "physical dnsproxy implementation semantics",
            "external DNS provider reliability or confidentiality",
            "IPv6/UDP/DoH direct escape",
            "arbitrary negative DNS caching and multiproxy races",
        ],
    }, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except ContractViolation as exc:
        print(json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(1) from exc
