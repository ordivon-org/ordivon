#!/usr/bin/env python3
"""Fail closed before a Network install could erase existing live monitoring bytes.

Three existing Owner files are compared as exact immutable source-cut values.
The check is deliberately stricter than YAML semantic equivalence: intended
changes require a separately qualified migration, never a silent overwrite.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

from monitoring_graph import prometheus_projection as _prometheus_projection, verify_active_targets

CONFIGS = ("blackbox/blackbox.yml", "prometheus/prometheus.yml", "prometheus/consumer.rules.yml")
SCRAPE_GLOB = "consumers/*.yml"  # Prometheus' native optional-owner fragment contract


def _fragment_paths(root: Path) -> list[Path]:
    """Use only upstream native scrape_config_files, not a custom registry."""
    prometheus = _read_owner_yaml(root / CONFIGS[1])
    patterns = prometheus.get("scrape_config_files") or []
    if not patterns:
        return []
    if patterns != [SCRAPE_GLOB]:
        raise ValueError(f"unsupported Prometheus native fragment set: {patterns}")
    directory = root / "prometheus/consumers"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("missing or unsafe native Prometheus fragment directory")
    paths = sorted(directory.glob("*.yml"))
    if not paths or any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError("missing or unsafe Prometheus consumer fragment")
    return paths


def _all_scrape_jobs(root: Path) -> list[dict]:
    prometheus = _read_owner_yaml(root / CONFIGS[1])
    jobs = prometheus.get("scrape_configs")
    if not isinstance(jobs, list):
        raise ValueError("missing Prometheus scrape_configs")
    result = list(jobs)
    for path in _fragment_paths(root):
        fragment = _read_owner_yaml(path)
        if set(fragment) != {"scrape_configs"} or not isinstance(fragment["scrape_configs"], list):
            raise ValueError(f"invalid native Prometheus fragment structure: {path}")
        result.extend(fragment["scrape_configs"])
    names = [job.get("job_name") for job in result if isinstance(job, dict)]
    if len(names) != len(result) or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError("duplicate Prometheus job name or invalid job name across native fragments")
    return result



def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate monitoring mapping key: {key}")
        result[key] = value
    return result


def _read_owner_yaml(path: Path) -> dict:
    """Reuse upstream yq; do not implement another YAML dialect or parser."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"invalid monitoring source file: {path}")
    result = subprocess.run(
        ["yq", "-o=json", ".", str(path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"invalid monitoring YAML: {path}: {result.stderr.strip()}")
    try:
        parsed = json.loads(result.stdout, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid monitoring JSON projection: {path}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"monitoring YAML must be an object: {path}")
    return parsed


def verify_loaded_prometheus(live: Path, loaded: dict) -> int:
    """Read-only consumer-edge seam, not complete process or notification proof."""
    disk = _read_owner_yaml(live / CONFIGS[1])
    expected = _prometheus_projection(disk, (live / "prometheus"))
    observed = _prometheus_projection(loaded, (live / "prometheus"))
    if expected != observed:
        differing = [
            key for key in sorted(expected) if expected[key] != observed[key]
        ]
        raise ValueError(f"loaded Prometheus consumer graph differs: {differing}")
    # Prometheus /status/config intentionally reports the main YAML and fragment
    # references, not the expanded job graph. Never mistake main-only for all.
    return len(_all_scrape_jobs(live))


def verify_loaded_active_targets(live: Path, pool_data: dict, target_data: dict) -> int:
    return verify_active_targets(_all_scrape_jobs(live), pool_data, target_data)


def _api_payload(path: str) -> dict:
    # A local observation must not inherit a developer-shell HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:29090{path}", timeout=8) as response:
        value = json.load(response, object_pairs_hook=_no_duplicate_keys)
    if value.get("status") != "success":
        raise ValueError(f"Prometheus native API unsuccessful: {path}")
    return value


def verify_loaded_prometheus_local(live: Path) -> int:
    """Only the current locally listening Prometheus API is an observed source."""
    payload = _api_payload("/api/v1/status/config")
    if not isinstance(payload.get("data"), dict):
        raise ValueError("Prometheus loaded config API is not successful")
    source = payload["data"].get("yaml")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Prometheus loaded config API omitted YAML")
    parsed = subprocess.run(
        ["yq", "-o=json", ".", "-"], input=source,
        capture_output=True, text=True, check=False,
    )
    if parsed.returncode != 0:
        raise ValueError("Prometheus loaded config YAML cannot be parsed")
    loaded = json.loads(parsed.stdout, object_pairs_hook=_no_duplicate_keys)
    if not isinstance(loaded, dict):
        raise ValueError("invalid Prometheus loaded config projection")
    count = verify_loaded_prometheus(live, loaded)
    pools = _api_payload("/api/v1/scrape_pools")
    active = _api_payload("/api/v1/targets?state=active")
    if verify_loaded_active_targets(live, pools, active) != count:
        raise ValueError("incomplete loaded Prometheus consumer graph")
    return count


def verify_probe_consumer_edges(source: Path) -> int:
    """Prove configuration graph edges only; not live Blackbox or consumer effects."""
    blackbox = _read_owner_yaml(source / CONFIGS[0])
    modules = blackbox.get("modules")
    jobs = _all_scrape_jobs(source)
    if not isinstance(modules, dict) or not isinstance(jobs, list):
        raise ValueError("missing Blackbox modules or Prometheus scrape_configs")
    names: set[str] = set()
    checked = 0
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("invalid Prometheus scrape job")
        name = job.get("job_name")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError(f"missing or duplicate Prometheus job name: {name!r}")
        names.add(name)
        if job.get("metrics_path", "/metrics") != "/probe":
            continue
        checked += 1
        params = job.get("params")
        selected = params.get("module") if isinstance(params, dict) else None
        if (not isinstance(selected, list) or len(selected) != 1
                or not isinstance(selected[0], str) or selected[0] not in modules):
            raise ValueError(f"Blackbox probe job {name}: unknown/ambiguous module")
        relabels = job.get("relabel_configs")
        if not isinstance(relabels, list) or not all(isinstance(r, dict) for r in relabels):
            raise ValueError(f"Blackbox probe job {name}: missing relabel configurations")
        if any(r.get("target_label") == "__param_module" for r in relabels):
            raise ValueError(f"Blackbox probe job {name}: dynamically overridden module")
        if not any(
            r.get("target_label") == "__param_target"
            and r.get("source_labels") == ["__address__"]
            for r in relabels
        ):
            raise ValueError(f"Blackbox probe job {name}: target not forwarded to probe")
        if not any(
            r.get("target_label") == "__address__"
            and isinstance(r.get("replacement"), str)
            and bool(r["replacement"])
            for r in relabels
        ):
            raise ValueError(f"Blackbox probe job {name}: exporter endpoint not bound")
    if not checked:
        raise ValueError("no Blackbox probe consumers in monitoring source")
    return checked

def verify(source: Path, live: Path) -> str:
    for label, tree in (("source", source), ("live", live)):
        if tree.is_symlink():
            raise ValueError(f"unmanaged monitoring root: {label}")
    # Source declares the closed set, including Prometheus-native fragments;
    # extra live YAML might still be a consumer, never silently delete it.
    fragments = _fragment_paths(source)
    declared = (*CONFIGS, *(path.relative_to(source).as_posix() for path in fragments))
    for tree in (source, live):
        for folder in ("blackbox", "prometheus"):
            directory = tree / folder
            if directory.is_symlink():
                raise ValueError(f"unmanaged monitoring directory: {folder}")
            if not directory.is_dir():
                continue
            for path in directory.rglob("*"):
                name = path.relative_to(tree).as_posix()
                if path.is_symlink():
                    raise ValueError(f"unmanaged monitoring symlink: {name}")
                if path.is_file() and path.suffix.lower() in {".yml", ".yaml"} and name not in declared:
                    raise ValueError(f"unmanaged monitoring configuration: {name}")
    candidate = []
    for name in declared:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid source monitoring file: {name}")
        candidate.append(path.read_bytes())
    present = [(live / name).exists() or (live / name).is_symlink() for name in declared]
    if not any(present):
        return "FIRST_INSTALL"
    if not all(present):
        raise ValueError("incomplete live monitoring SourceCut")
    for name, data in zip(declared, candidate, strict=True):
        path = live / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"live monitoring differs from source: {name}")
    return "IDENTICAL_SOURCECUT"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("config"))
    parser.add_argument("--live", type=Path, default=Path("/etc/network-v2"))
    parser.add_argument("--check-loaded-prometheus", action="store_true",
                        help="read-only compare process-loaded Prometheus config to disk")
    parser.add_argument("--check-edges", action="store_true",
                        help="validate exact Prometheus to Blackbox module/target bindings")
    args = parser.parse_args()
    try:
        if args.check_loaded_prometheus:
            count = verify_loaded_prometheus_local(args.live)
            print(f"MONITORING_LOADED_CONSUMER_GRAPH=MATCHED scrapeJobs={count}")
            return 0
        if args.check_edges:
            count = verify_probe_consumer_edges(args.source)
            print(f"MONITORING_CONSUMER_EDGES=VALID probeJobs={count}")
            return 0
        standing = verify(args.source, args.live)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        parser.exit(4, f"MONITORING_SOURCECUT=BLOCKED {exc}\n")
    print(f"MONITORING_SOURCECUT={standing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
