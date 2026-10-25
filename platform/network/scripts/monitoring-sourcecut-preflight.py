#!/usr/bin/env python3
"""Fail closed before a Network install could erase existing live monitoring bytes.

Two existing Owner files are compared as exact immutable source-cut values.
The check is deliberately stricter than YAML semantic equivalence: intended
changes require a separately qualified migration, never a silent overwrite.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from pathlib import Path

CONFIGS = ("blackbox/blackbox.yml", "prometheus/prometheus.yml")



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


def _prometheus_projection(config: dict, base: Path) -> dict:
    """Compare consumer routing fields, not Prometheus-injected YAML defaults."""
    jobs: dict[str, dict] = {}
    for job in config.get("scrape_configs", []):
        if not isinstance(job, dict) or not isinstance(job.get("job_name"), str):
            raise ValueError("invalid loaded Prometheus scrape job")
        name = job["job_name"]
        if name in jobs:
            raise ValueError(f"duplicate Prometheus job name: {name}")
        relabels = []
        for rule in job.get("relabel_configs") or []:
            if not isinstance(rule, dict):
                raise ValueError(f"invalid Prometheus relabel rule: {name}")
            defaults = {
                "source_labels": [], "target_label": "",
                "replacement": "$1", "action": "replace", "separator": ";",
            }
            relabels.append({**defaults, **rule})
        jobs[name] = {
            "metrics_path": job.get("metrics_path", "/metrics"),
            "scheme": job.get("scheme", "http"),
            "proxy_url": job.get("proxy_url") or "",
            "params": job.get("params") or {},
            "static_configs": job.get("static_configs") or [],
            "relabel_configs": relabels,
        }
    rule_paths = config.get("rule_files") or []
    if not isinstance(rule_paths, list):
        raise ValueError("invalid Prometheus rule_files")
    rules = sorted(str((base / path).resolve()) for path in rule_paths)
    alerting = config.get("alerting") or {}
    if not isinstance(alerting, dict):
        raise ValueError("invalid Prometheus alerting config")
    return {
        "jobs": jobs,
        "rule_files": rules,
        "alertmanagers": alerting.get("alertmanagers") or [],
        "remote_write": config.get("remote_write") or [],
    }


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
    return len(expected["jobs"])


def verify_loaded_prometheus_local(live: Path) -> int:
    """Only the current locally listening Prometheus API is an observed source."""
    with urllib.request.urlopen(
        "http://127.0.0.1:29090/api/v1/status/config", timeout=8
    ) as response:
        payload = json.load(response, object_pairs_hook=_no_duplicate_keys)
    if payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
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
    return verify_loaded_prometheus(live, loaded)


def verify_probe_consumer_edges(source: Path) -> int:
    """Prove configuration graph edges only; not live Blackbox or consumer effects."""
    blackbox = _read_owner_yaml(source / CONFIGS[0])
    prometheus = _read_owner_yaml(source / CONFIGS[1])
    modules = blackbox.get("modules")
    jobs = prometheus.get("scrape_configs")
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
    # The two declared configs are a closed set for this install owner.
    # Extra YAML may be a previously deployed consumer or alert rule.
    for tree in (source, live):
        for folder in ("blackbox", "prometheus"):
            directory = tree / folder
            if directory.is_symlink():
                raise ValueError(f"unmanaged monitoring directory: {folder}")
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                name = f"{folder}/{path.name}"
                if path.suffix.lower() in {".yml", ".yaml"} and name not in CONFIGS:
                    raise ValueError(f"unmanaged monitoring configuration: {name}")
    candidate = []
    for name in CONFIGS:
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"invalid source monitoring file: {name}")
        candidate.append(path.read_bytes())
    present = [(live / name).exists() or (live / name).is_symlink() for name in CONFIGS]
    if not any(present):
        return "FIRST_INSTALL"
    if not all(present):
        raise ValueError("incomplete live monitoring SourceCut")
    for name, data in zip(CONFIGS, candidate, strict=True):
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
