#!/usr/bin/env python3
"""Finite SMT proof: Ordivon management units do not depend on tested Network v2.

Scope: checked-in Linux systemd [Unit] relationships only. This does NOT prove
deployed drop-ins, alias symlink installation, external network-online.target,
ExecStart program effects, network reachability, or management availability.
"""

from __future__ import annotations

import json
import re
import sys
from collections import deque
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
import tomllib

import z3

REPO = Path(__file__).resolve().parents[3]
NETWORK = REPO / "platform/network"
# Exactly three intended management contracts; physical Owner paths remain
# task-local evidence and cannot silently create cross-Owner source seams.
EXPECTED_MANAGEMENT = {
    "ordivon-runtime.service": "runtime",
    "ordivon-host-v2.service": "host",
    "ordivon-gateway.service": "gateway",
}
BINDING_PATH = NETWORK / "formal/fixtures/control-plane-source-bindings.json"
OWNER_MANIFEST = REPO / "tools/repo/owners.toml"
# Includes weak start edges and pure ordering edges, intentionally stronger
# than checking Requires= alone. PartOf= is a stop/restart coupling, not start.
COUPLING = frozenset(("Requires", "Wants", "Requisite", "BindsTo", "Upholds", "PartOf", "After"))
UNIT_NAME = re.compile(r"^[A-Za-z0-9@_.:-]+\.(?:service|target|timer|socket|path|mount|automount)$")


class UnsupportedSource(RuntimeError):
    pass


def management_source_bindings() -> dict[str, Path]:
    """Admit one task-local source binding against canonical Owner roots.

    Physical repository locations are proof inputs, never runtime dependencies
    between Network and the verified managers. Reject stale/escaped bindings.
    """
    try:
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        manifest = tomllib.loads(OWNER_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UnsupportedSource(f"management source binding unavailable: {exc}") from exc
    if (not isinstance(binding, dict)
            or set(binding) != {"schemaVersion", "kind", "truthRole", "managementUnits"}
            or binding["schemaVersion"] != 1
            or binding["kind"] != "ordivon.network.formal-control-plane-source-binding"
            or binding["truthRole"] != "task-local-proof-input-not-owner-truth"):
        raise UnsupportedSource("management binding schema/authority role changed")
    rows = binding["managementUnits"]
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_MANAGEMENT):
        raise UnsupportedSource("unexpected management unit binding count")
    owner_roots = {o["name"]: o["root"] for o in manifest.get("owners", [])}
    sources: dict[str, Path] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"unit", "owner", "sourcePath"}:
            raise UnsupportedSource("unsupported management binding entry")
        unit, owner, source_path = row["unit"], row["owner"], row["sourcePath"]
        if (not isinstance(unit, str) or EXPECTED_MANAGEMENT.get(unit) != owner
                or not isinstance(source_path, str) or not source_path
                or not isinstance(owner_roots.get(owner), str)):
            raise UnsupportedSource("binding does not match the three canonical management owners")
        repo_relative = PurePosixPath(source_path)
        if (repo_relative.is_absolute() or ".." in repo_relative.parts
                or chr(92) in source_path
                or repo_relative.as_posix() != source_path):
            raise UnsupportedSource("noncanonical management source binding path")
        candidate = REPO.joinpath(*repo_relative.parts)
        owner_root = (REPO / owner_roots[owner]).resolve(strict=True)
        if (unit in sources or candidate.name != unit or not candidate.is_file()
                or candidate.is_symlink()
                or not candidate.resolve(strict=True).is_relative_to(owner_root)):
            raise UnsupportedSource("duplicate, missing or escaping management source binding")
        sources[unit] = candidate
    if set(sources) != set(EXPECTED_MANAGEMENT):
        raise UnsupportedSource("management source binding is incomplete")
    return sources


CONTROL_SOURCES = management_source_bindings()


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
        # Reverse or mutual coupling has different semantics. Do not silently
        # produce a "proof" if such new source directives are introduced.
        if key in {"Before", "PropagatesStopTo", "StopPropagatedFrom", "Conflicts"}:
            raise UnsupportedSource(f"unmodeled coupling directive {key}: {source}")
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



def source_aliases(unit_name: str, source: Path) -> set[str]:
    """Parse native systemd [Install] aliases; fail closed on unsupported names."""
    section = ""
    result: set[str] = set()
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if section != "Install" or not line.startswith("Alias="):
            continue
        names = line.partition("=")[2].split()
        if not names:
            raise UnsupportedSource(f"empty or reset Alias directive: {source}")
        for alias in names:
            if (not UNIT_NAME.fullmatch(alias) or alias == unit_name
                    or alias.rsplit(".", 1)[-1] != unit_name.rsplit(".", 1)[-1]
                    or "@" in alias or "@" in unit_name
                    or alias in result):
                raise UnsupportedSource(f"unmodeled or duplicate systemd Alias={alias}: {source}")
            result.add(alias)
    return result

def source_graph() -> tuple[dict[str, set[str]], list[str], int]:
    files = [p for suffix in (".service", ".target", ".timer", ".socket", ".path")
             for p in NETWORK.rglob("*" + suffix)]
    # Podman Quadlet generator convention: .container -> .service and
    # .network -> -network.service. This models authored [Unit] text only,
    # not whether the installed generator emitted or loaded these units.
    containers = list(NETWORK.rglob("*.container"))
    networks = list(NETWORK.rglob("*.network"))
    entries = ([(p.name, p) for p in files]
               + [(p.stem + ".service", p) for p in containers]
               + [(p.stem + "-network.service", p) for p in networks])
    sources: dict[str, Path] = dict(CONTROL_SOURCES)
    for name, path in entries:
        if name in sources:
            raise UnsupportedSource(f"duplicate Unit name {name}: {sources[name]} / {path}")
        sources[name] = path
    data = sorted(name for name in sources if name.startswith("network-v2-"))
    if len(data) < 20:
        raise UnsupportedSource("Network v2 source coverage unexpectedly small")
    # systemd Alias= is a source-declared name for the SAME canonical Unit,
    # not an additional process or graph node. Installed symlink is checked
    # separately by native systemctl; here we prove source graph semantics.
    aliases: dict[str, str] = {}
    for canonical, file in sources.items():
        for alias in source_aliases(canonical, file):
            if alias in sources or alias in aliases:
                raise UnsupportedSource(f"conflicting systemd Alias name: {alias}")
            aliases[alias] = canonical
    graph = {
        name: {aliases.get(dep, dep) for dep in unit_dependencies(file)}
        for name, file in sources.items()
    }
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
    # Falsify the entire source-parser-to-SMT path, not only the solver:
    # temporarily inject a genuine systemd Wants= declaration into a copy.
    # No installed or repository Unit is changed.
    with TemporaryDirectory(prefix="ordivon-network-unit-falsification-") as temp:
        original = CONTROL_SOURCES["ordivon-runtime.service"]
        mutated = Path(temp) / original.name
        mutated.write_text(
            original.read_text(encoding="utf-8")
            + "\n[Unit]\nWants=network-v2-r0.target\n",
            encoding="utf-8",
        )
        mutant = {k: set(v) for k, v in graph.items()}
        mutant["ordivon-runtime.service"] = unit_dependencies(mutated)
        if "network-v2-r0.target" not in mutant["ordivon-runtime.service"]:
            raise UnsupportedSource("source parser did not admit injected dependency")
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
            "external network-online.target dependencies and actual installed Alias symlinks",
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
