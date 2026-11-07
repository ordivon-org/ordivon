#!/usr/bin/env python3
"""Finite SMT proof: Ordivon management units do not depend on tested Network v2.

Scope: checked-in Linux systemd [Unit] relationships only. This does NOT prove
deployed drop-ins, alias expansion, external network-online.target,
ExecStart program effects, network reachability, or management availability.
"""

from __future__ import annotations

import json
import re
import sys
from collections import deque
from pathlib import Path

import z3

REPO = Path(__file__).resolve().parents[3]
NETWORK = REPO / "platform/network"
CONTROL_SOURCES = {
    "ordivon-runtime.service": REPO / "services/runtime/packaging/systemd/ordivon-runtime.service",
    "ordivon-host-v2.service": REPO / "services/host/packaging/systemd/ordivon-host-v2.service",
    "ordivon-gateway.service": REPO / "services/gateway/systemd/ordivon-gateway.service",
}
# Includes weak start edges and pure ordering edges, intentionally stronger
# than checking Requires= alone. PartOf= is a stop/restart coupling, not start.
COUPLING = frozenset(("Requires", "Wants", "Requisite", "BindsTo", "Upholds", "PartOf", "After"))
UNIT_NAME = re.compile(r"^[A-Za-z0-9@_.:-]+\.(?:service|target)$")


class UnsupportedSource(RuntimeError):
    pass


def unit_dependencies(source: Path) -> set[str]:
    if not source.is_file():
        raise UnsupportedSource(f"missing Unit source {source}")
    section = ""
    deps: set[str] = set()
    logical_lines: list[str] = []
    pending = ""
    for original in source.read_text(encoding="utf-8").splitlines():
        line = original.strip()
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        logical_lines.append(pending + line)
        pending = ""
    if pending:
        raise UnsupportedSource(f"unterminated continuation: {source}")
    for line in logical_lines:
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if section != "Unit":
            continue
        if "=" not in line:
            raise UnsupportedSource(f"unparsed Unit directive: {source}: {line}")
        key, value = (x.strip() for x in line.split("=", 1))
        if key not in COUPLING:
            continue
        if not value:
            # systemd permits resetting dependencies with an empty directive;
            # without full native merge semantics, reject rather than misprove.
            raise UnsupportedSource(f"reset {key}= requires native systemd merge: {source}")
        for name in value.split():
            if not UNIT_NAME.fullmatch(name):
                raise UnsupportedSource(f"unsupported dynamic unit reference {name}: {source}")
            deps.add(name)
    return deps


def source_graph() -> tuple[dict[str, set[str]], list[str], int]:
    files = list(NETWORK.rglob("*.service")) + list(NETWORK.rglob("*.target"))
    # Quadlet's native .container -> generated .service identity is an
    # upstream Podman convention. Model its declared [Unit] dependencies,
    # but do not claim the generator or installed generation was checked.
    generated = list(NETWORK.rglob("*.container"))
    entries = [(p.name, p) for p in files] + [(p.stem + ".service", p) for p in generated]
    sources: dict[str, Path] = dict(CONTROL_SOURCES)
    for name, path in entries:
        if name in sources:
            raise UnsupportedSource(f"duplicate Unit name {name}: {sources[name]} / {path}")
        sources[name] = path
    data = sorted(name for name in sources if name.startswith("network-v2-"))
    if len(data) < 20:
        raise UnsupportedSource("Network v2 source coverage unexpectedly small")
    graph = {name: unit_dependencies(file) for name, file in sources.items()}
    missing_network = sorted({
        name for deps in graph.values() for name in deps
        if name.startswith("network-v2-") and name not in graph
    })
    if missing_network:
        raise UnsupportedSource(f"unresolved Network v2 source units: {missing_network}")
    return graph, data, len(entries)


def symbolic_crossing(graph: dict[str, set[str]], roots: set[str],
                      targets: set[str]) -> z3.CheckSatResult:
    """Exact finite transitive-closure model, including cycles.

    A path in an N-node graph has a simple path of length at most N-1.
    Equations for 0..N stages reach every such path; a satisfying solver
    assignment is an actual crossing, not a sampled execution.
    """
    nodes = sorted(graph)
    incoming: dict[str, list[str]] = {n: [] for n in nodes}
    for source, targets_for_source in graph.items():
        for destination in targets_for_source:
            if destination in incoming:
                incoming[destination].append(source)
    solver = z3.Solver()
    prev = {n: z3.BoolVal(n in roots) for n in nodes}
    for step in range(len(nodes)):
        now = {n: z3.Bool(f"reach_{step}_{i}") for i, n in enumerate(nodes)}
        for n in nodes:
            solver.add(now[n] == z3.Or(prev[n], *[prev[src] for src in incoming[n]]))
        prev = now
    solver.add(z3.Or(*[prev[n] for n in targets]))
    return solver.check()


def concrete_path(graph: dict[str, set[str]], roots: set[str], targets: set[str]) -> list[str]:
    queue = deque((root, [root]) for root in sorted(roots))
    visited: set[str] = set()
    while queue:
        node, path = queue.popleft()
        if node in targets:
            return path
        if node in visited:
            continue
        visited.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt in graph and nxt not in visited:
                queue.append((nxt, path + [nxt]))
    return []


def proof() -> dict[str, object]:
    graph, data, count = source_graph()
    control = set(CONTROL_SOURCES)
    data_set = set(data)
    result = symbolic_crossing(graph, control, data_set)
    if result != z3.unsat:
        raise UnsupportedSource(
            f"management -> data-plane crossing (or solver UNKNOWN): "
            f"{result}, path={concrete_path(graph, control, data_set)}"
        )
    # Mutate the mathematical graph, not actual service files. Show the same
    # verifier rejects exactly the forbidden coupling it is supposed to catch.
    mutant = {k: set(v) for k, v in graph.items()}
    mutant["ordivon-runtime.service"].add("network-v2-r0.target")
    negative = symbolic_crossing(mutant, control, data_set)
    if negative != z3.sat:
        raise UnsupportedSource(f"negative dependency mutant not falsified: {negative}")
    return {
        "kind": "ordivon.network.control-plane-independence",
        "standing": "PROVED_WITHIN_SOURCE_GRAPH",
        "solver": z3.get_version_string(),
        "sourceUnitFiles": len(graph),
        "networkSourceFiles": count,
        "networkTargets": len(data),
        "managementRoots": sorted(control),
        "checkedCouplingDirectives": sorted(COUPLING),
        "proof": "UNSAT: no management-to-Network-v2 path in finite source graph",
        "negativeControl": "SAT: adding Runtime Wants=network-v2-r0.target",
        "unproved": [
            "deployed systemd unit and drop-in parity",
            "external network-online.target dependencies or native alias expansion",
            "ExecStart and runtime process network effects",
            "Windows services and active user processes",
            "physical management availability during provider failure",
        ],
    }


def main() -> None:
    print(json.dumps(proof(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except UnsupportedSource as exc:
        print(json.dumps({"standing": "NOT_PROVED", "reason": str(exc)}), file=sys.stderr)
        raise SystemExit(1)
