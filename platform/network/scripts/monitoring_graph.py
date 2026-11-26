"""Bounded Prometheus consumer-graph contracts; no native API or mutation authority."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def prometheus_projection(config: dict, base: Path) -> dict:
    """Compare consumer routing fields, not Prometheus-injected YAML defaults."""
    jobs: dict[str, dict] = {}
    for job in config.get("scrape_configs", []):
        if not isinstance(job, dict) or not isinstance(job.get("job_name"), str):
            raise ValueError("invalid loaded Prometheus scrape job")
        name = job["job_name"]
        if name in jobs:
            raise ValueError(f"duplicate Prometheus job name: {name}")
        def relabels(field: str) -> list[dict]:
            rules = job.get(field) or []
            if not isinstance(rules, list):
                raise ValueError(f"invalid loaded Prometheus {field}: {name}")
            defaults = {
                "source_labels": [], "target_label": "",
                "replacement": "$1", "action": "replace", "separator": ";",
            }
            if any(not isinstance(rule, dict) for rule in rules):
                raise ValueError(f"invalid Prometheus relabel rule: {name}")
            return [{**defaults, **rule} for rule in rules]
        jobs[name] = {
            "metrics_path": job.get("metrics_path", "/metrics"),
            "scheme": job.get("scheme", "http"),
            "proxy_url": job.get("proxy_url") or "",
            "proxy_from_environment": job.get("proxy_from_environment", False),
            "follow_redirects": job.get("follow_redirects", True),
            "honor_labels": job.get("honor_labels", False),
            "honor_timestamps": job.get("honor_timestamps", True),
            "track_timestamps_staleness": job.get("track_timestamps_staleness", False),
            "metric_relabel_configs": relabels("metric_relabel_configs"),
            "params": job.get("params") or {},
            "static_configs": job.get("static_configs") or [],
            "relabel_configs": relabels("relabel_configs"),
        }
    rule_paths = config.get("rule_files") or []
    if not isinstance(rule_paths, list):
        raise ValueError("invalid Prometheus rule_files")
    rules = sorted(str((base / path).resolve()) for path in rule_paths)
    native_files = config.get("scrape_config_files") or []
    if not isinstance(native_files, list):
        raise ValueError("invalid Prometheus scrape_config_files")
    native_paths = sorted(str((base / path).resolve()) for path in native_files)
    alerting = config.get("alerting") or {}
    if not isinstance(alerting, dict):
        raise ValueError("invalid Prometheus alerting config")
    return {
        "jobs": jobs,
        "rule_files": rules,
        "scrape_config_files": native_paths,
        "alertmanagers": alerting.get("alertmanagers") or [],
        "remote_write": config.get("remote_write") or [],
    }


def verify_active_targets(expected: list[dict], pool_data: dict, target_data: dict) -> int:
    """Independent process projection: include jobs must actually be active."""
    names = {job["job_name"] for job in expected}
    if (not isinstance(pool_data, dict) or not isinstance(pool_data.get("data"), dict) or
            not isinstance(target_data, dict) or not isinstance(target_data.get("data"), dict)):
        raise ValueError("invalid loaded Prometheus API envelope")
    loaded_pools = pool_data["data"].get("scrapePools")
    if (not isinstance(loaded_pools, list) or
            any(not isinstance(pool, str) for pool in loaded_pools) or
            set(loaded_pools) != names or len(loaded_pools) != len(names)):
        raise ValueError("loaded Prometheus scrape pools differ from native fragment graph")
    targets = target_data["data"].get("activeTargets")
    if not isinstance(targets, list):
        raise ValueError("Prometheus active target API omitted target graph")
    indexed: dict[str, list] = {}
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get("labels"), dict):
            raise ValueError("invalid active target labels")
        name = target["labels"].get("job")
        if not isinstance(name, str):
            raise ValueError("invalid active target job identity")
        indexed.setdefault(name, []).append(target)
    if set(indexed) != names:
        raise ValueError("active target job set differs from declared source")
    for job in expected:
        name = job["job_name"]
        declared_targets = [
            target for group in job.get("static_configs", [])
            for target in group.get("targets", [])
        ]
        observed = indexed[name]
        if len(declared_targets) != 1 or len(observed) != 1:
            raise ValueError(f"ambiguous Prometheus target cardinality: {name}")
        target = observed[0]
        url = target.get("scrapeUrl")
        discovered = target.get("discoveredLabels")
        if not isinstance(url, str) or not isinstance(discovered, dict):
            raise ValueError(f"invalid loaded target observation: {name}")
        parsed = urlsplit(url)
        if (target["labels"].get("instance") != declared_targets[0] or
                discovered.get("__address__") != declared_targets[0]):
            raise ValueError(f"loaded target identity differs: {name}")
        if parsed.scheme != job.get("scheme", "http") or parsed.fragment:
            raise ValueError(f"loaded scrape scheme or fragment differs: {name}")
        params = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
        declared_params = dict(job.get("params") or {})
        if target.get("scrapePool") != name:
            raise ValueError(f"wrong loaded scrape pool: {name}")
        if job.get("metrics_path") == "/probe":
            module = (job.get("params") or {}).get("module")
            actual = discovered.get("__param_module")
            declared_params["target"] = declared_targets
            if (not isinstance(module, list) or len(module) != 1 or
                    params.get("module") != module or actual != module[0] or
                    params != declared_params):
                raise ValueError(f"loaded Blackbox module/target differs: {name}")
            exporter = next(
                (r.get("replacement") for r in job.get("relabel_configs", [])
                 if r.get("target_label") == "__address__"), None)
            if parsed.netloc != exporter or parsed.path != "/probe":
                raise ValueError(f"loaded Blackbox exporter binding differs: {name}")
        elif (parsed.netloc != declared_targets[0] or
              parsed.path != job.get("metrics_path", "/metrics") or params != declared_params):
            raise ValueError(f"loaded direct scrape differs: {name}")
    return len(names)
