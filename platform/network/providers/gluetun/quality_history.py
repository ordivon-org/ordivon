#!/usr/bin/env python3
"""On-demand VPN country quality evidence from native Gluetun + Prometheus.

This is NOT a watch loop or an endpoint registry.  Observations are
historical; one WireGuard session cannot prove an unconnected standby.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

import native_profile as native

JOBS = (
    "blackbox-scoped-claude-api",
    "blackbox-scoped-codex-mcp",
    "blackbox-vpn-pypi",
)
PROM = "http://127.0.0.1:29090"
CONNECT = re.compile(
    r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z).*"
    r"\[wireguard\] Connecting to ((?:\d{1,3}\.){3}\d{1,3}):\d+"
)
MIN_SESSION = timedelta(minutes=18)
WARMUP = timedelta(minutes=3)
WITNESS_MIN = 12
SUCCESS_FLOOR = 0.97
HISTORICAL_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class Segment:
    start: datetime
    end: datetime
    country: str | None
    endpoint: str
    hostname: str | None = None
    @property
    def minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60


def endpoint_countries(raw: str) -> dict[str, str | None]:
    rows: dict[str, set[str]] = {}
    for item in json.loads(raw)["surfshark"]["servers"]:
        if item.get("vpn") != "wireguard":
            continue
        for ip in item.get("ips", []):
            rows.setdefault(ip, set()).add(item.get("country", ""))
    return {ip: next(iter(names)) if len(names) == 1 else None
            for ip, names in rows.items()}


def endpoint_hostnames(raw: str) -> dict[str, str | None]:
    """A public Surfshark hostname is a catalog identity, not current reachability."""
    rows: dict[str, set[str]] = {}
    for item in json.loads(raw)["surfshark"]["servers"]:
        if item.get("vpn") != "wireguard":
            continue
        for ip in item.get("ips", []):
            rows.setdefault(ip, set()).add(item.get("hostname", ""))
    return {ip: next(iter(names)) if len(names) == 1 else None
            for ip, names in rows.items()}


def segments(
    lines: str, names: dict[str, str | None], now: datetime,
    hostnames: dict[str, str | None] | None = None,
) -> list[Segment]:
    events: list[tuple[datetime, str]] = []
    for line in lines.splitlines():
        m = CONNECT.search(line)
        if m:
            ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
            if ts <= now:
                events.append((ts, m.group(2)))
    events.sort()
    result: list[Segment] = []
    for index, (start, ip) in enumerate(events):
        end = events[index + 1][0] if index + 1 < len(events) else now
        if end - start >= MIN_SESSION:
            result.append(Segment(start, end, names.get(ip), ip,
                                  (hostnames or {}).get(ip)))
    return result


def parse_matrix(rows: list[dict], metric: str, start: datetime, end: datetime) -> dict[str, list[float]]:
    outputs: dict[str, list[float]] = {}
    for row in rows:
        job = row.get("metric", {}).get("job", "")
        if job not in JOBS:
            continue
        values = []
        for timestamp, raw in row.get("values", []):
            if not (start.timestamp() <= float(timestamp) <= end.timestamp()):
                continue
            try:
                number = float(raw)
            except (ValueError, TypeError):
                continue
            if number == number and 0 <= number < float("inf"):
                values.append(number)
        outputs[job] = values
    return outputs


def qualify(
    segment: Segment, success: dict[str, list[float]],
    duration: dict[str, list[float]], now: datetime, allowed: set[str],
) -> dict[str, object]:
    base: dict[str, object] = {
        "catalogCountry": segment.country,
        "catalogHostname": segment.hostname,
        "segmentStartUtc": segment.start.isoformat(),
        "segmentEndUtc": segment.end.isoformat(),
        "sessionMinutes": round(segment.minutes, 1),
        "lastObservedHoursAgo": round((now - segment.end).total_seconds()/3600, 2),
        "basis": "endpoint dwell plus correlated Prometheus consumer observations",
    }
    if segment.country is None:
        return base | {"standing": "UNKNOWN_CATALOG_IDENTITY"}
    if segment.country not in allowed:
        return base | {"standing": "REJECTED_NOT_ALLOWED"}
    checks: list[dict[str, object]] = []
    for job in JOBS:
        values = success.get(job, [])
        delays = duration.get(job, [])
        if len(values) < WITNESS_MIN or len(delays) < WITNESS_MIN:
            return base | {"standing": "UNKNOWN_INSUFFICIENT_CONSUMER_EVIDENCE",
                           "samples": {job: {"success": len(values), "latency": len(delays)}}}
        ratio = sum(v >= 1.0 for v in values)/len(values)
        checks.append({
            "job": job,
            "samples": len(values),
            "successRatio": round(ratio, 5),
            "medianMs": round(1000*statistics.median(delays)),
            "p90Ms": round(1000*sorted(delays)[int(.9*(len(delays)-1))]),
        })
    if any(float(c["successRatio"]) < SUCCESS_FLOOR for c in checks):
        status = "OBSERVED_CONSUMER_DEGRADED"
    elif now - segment.end > HISTORICAL_TTL:
        status = "STALE_HISTORICAL_SUCCESS"
    else:
        status = "RECENT_HISTORICAL_CONSUMER_SUCCESS"
    # Rank only within the evidence-compatible set. A historical sample
    # cannot be promoted to QUALIFIED_NOW_STANDBY without a live tunnel.
    p90s = [int(c["p90Ms"]) for c in checks]
    success_floor = min(float(c["successRatio"]) for c in checks)
    return base | {
        "standing": status,
        "consumers": checks,
        "worstConsumerSuccessRatio": round(success_floor, 5),
        "medianOfConsumerP90Ms": round(statistics.median(p90s)),
        "qualifiedNowStandby": False,
    }


def decision(
    *, active_healthy: bool | None, underlay_reachable: bool | None,
    evidence: list[dict[str, object]], now: datetime,
    last_switch: datetime | None = None, cooldown: timedelta = timedelta(minutes=10),
    current_country: str | None = None,
) -> dict[str, object]:
    """A bounded one-shot recommendation, never a switch authorization."""
    if active_healthy is True:
        return {"decision": "HOLD_WORKING_ACTIVE", "trialCountry": None}
    if active_healthy is None:
        return {"decision": "HOLD_ACTIVE_HEALTH_UNKNOWN", "trialCountry": None}
    if underlay_reachable is not True:
        return {"decision": "HOLD_SHARED_UNDERLAY_OR_UNKNOWN", "trialCountry": None}
    if last_switch is not None and now - last_switch < cooldown:
        return {"decision": "HOLD_COOLDOWN", "trialCountry": None}
    candidates = [row for row in evidence
                  if row.get("standing") == "RECENT_HISTORICAL_CONSUMER_SUCCESS"
                  and row.get("catalogCountry") is not None
                  and row.get("catalogCountry") != current_country]
    if not candidates:
        return {"decision": "HOLD_NO_RECENT_EVIDENCE", "trialCountry": None}
    candidates.sort(key=lambda row: (
        int(row.get("medianOfConsumerP90Ms", 1000000)),
        -float(row.get("worstConsumerSuccessRatio", 0)),
        float(row.get("lastObservedHoursAgo", 1000000)),
    ))
    return {
        "decision": "TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
        "trialCountry": candidates[0]["catalogCountry"],
        "historicalCatalogHostname": candidates[0].get("catalogHostname"),
        "certifiedHotStandbyCount": 0,
    }


def http_query(metric: str, start: datetime, end: datetime) -> list[dict]:
    expr = metric+'{job=~"'+ "|".join(JOBS)+'"}'
    url = PROM + "/api/v1/query_range?" + urlencode({
        "query": expr, "start": int(start.timestamp()),
        "end": int(end.timestamp()), "step": "60s",
    })
    with urlopen(url, timeout=14) as r:
        data = json.load(r)
    if data.get("status") != "success" or data.get("data", {}).get("resultType") != "matrix":
        raise ValueError("Prometheus range query is not valid")
    return data["data"]["result"]


def recent_failure_witness(now: datetime) -> bool | None:
    """Require three actually sampled consecutive failures in all three lanes.

    Missing or stale time-series evidence is UNKNOWN, not FALSE.
    """
    start = now - timedelta(minutes=7)
    rows = parse_matrix(http_query("probe_success", start, now),
                        "probe_success", start, now)
    samples = [rows.get(job, [])[-3:] for job in JOBS]
    if any(len(a) < 3 for a in samples):
        return None
    return all(all(v == 0 for v in samples_for_job) for samples_for_job in samples)


def current_catalog_country(catalog: str) -> str | None:
    """Current kernel WG identity, independent of public HTTPS availability."""
    import observe_active
    pid = subprocess.run(
        ["/usr/bin/podman", "inspect", "network-v2-gluetun-owned-r1",
         "--format", "{{.State.Pid}}"],
        check=True, capture_output=True, text=True, timeout=8,
    ).stdout.strip()
    if not pid.isdecimal() or int(pid) <= 1:
        return None
    raw = subprocess.run(
        ["/usr/bin/nsenter", "-t", pid, "-n", "/usr/bin/wg", "show", "all", "endpoints"],
        check=True, capture_output=True, text=True, timeout=8,
    ).stdout
    return observe_active.catalog_country(catalog, observe_active.endpoint_ip(raw))


def observe(*, hours: int) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    allowed = set(native.parse_allowed_policy(native.ALLOW_POLICY.read_text())["allowedCountries"])
    catalog = subprocess.run(
        ["/usr/bin/podman", "exec", "network-v2-gluetun-owned-r1",
         "cat", "/gluetun/servers.json"],
        check=True, capture_output=True, text=True, timeout=18,
    ).stdout
    log = subprocess.run(
        ["/usr/bin/journalctl", "-u", "network-v2-gluetun-owned.service",
         "--since", (now-timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S UTC"),
         "--output=cat", "--no-pager"],
        check=True, capture_output=True, text=True, timeout=30,
    ).stdout
    relevant = [s for s in segments(
        log, endpoint_countries(catalog), now, endpoint_hostnames(catalog),
    ) if s.country in allowed and s.minutes >= 18][-8:]
    results: list[dict[str, object]] = []
    for segment in relevant:
        start = segment.start + WARMUP
        end = segment.end - timedelta(minutes=1)
        success = parse_matrix(http_query("probe_success", start, end), "probe_success", start, end)
        duration = parse_matrix(http_query("probe_duration_seconds", start, end), "probe_duration_seconds", start, end)
        results.append(qualify(segment, success, duration, now, allowed))
    # Live evidence is distinct from the historical trend. Do not infer
    # active failure from a missing metric or merely an older journal session.
    import observe_active
    try:
        live = observe_active.observe()
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
        live = {"standing": "UNKNOWN_CONSUMER_PROBE_INCOMPLETE"}
    observed = live.get("standing")
    active_ok = True if observed == "QUALIFIED_ACTIVE_SAMPLE" else None
    failed_sample: bool | None = None
    if active_ok is not True:
        failed_sample = recent_failure_witness(now)
        if failed_sample is True:
            active_ok = False
    catalog_identity = live.get("currentCatalogCountry")
    if catalog_identity is None:
        try:
            catalog_identity = current_catalog_country(catalog)
        except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
            catalog_identity = None
    # Physical baseline is synthetic and does NOT route user traffic outside
    # VPN. If it cannot be verified, no endpoint switching is recommended.
    underlay_ok: bool | None = None
    if active_ok is False:
        try:
            response = subprocess.run([
                "/usr/bin/curl", "-q", "--noproxy", "*", "-4",
                "--silent", "--show-error", "--connect-timeout", "3",
                "--max-time", "7", "-o", "/dev/null", "-w", "%{http_code}",
                "https://example.com/",
            ], capture_output=True, text=True, timeout=9)
            underlay_ok = response.returncode == 0 and response.stdout == "200"
        except (OSError, subprocess.SubprocessError):
            underlay_ok = None
    plan = decision(
        active_healthy=active_ok, underlay_reachable=underlay_ok,
        evidence=results, now=now,
        current_country=catalog_identity,
    )
    if active_ok is False and catalog_identity is None:
        plan = {"decision": "HOLD_ACTIVE_ENDPOINT_UNKNOWN", "trialCountry": None}
    return {
        "kind": "ordivon.network.gluetun-country-history",
        "observationUtc": now.isoformat(),
        "scope": "correlated historical endpoint dwell and VPN consumer probe quality",
        "history": results,
        "active": {
            "standing": observed,
            "catalogCountry": catalog_identity,
            "publicExitCountryCode": live.get("currentPublicExitCountryCode"),
            "threeLaneConsecutiveFailure": failed_sample,
        },
        "recommended": plan,
        "certifiedHotStandbyCount": 0,
        "limits": ["historical correlation is not proof of causal endpoint performance",
                   "same country may have different Surfshark endpoint IPs",
                   "no standby is verified without its own actual WireGuard tunnel",
                   "recommended is advisory only: no automatic switching or credentials"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=48)
    args = parser.parse_args()
    if not (1 <= args.hours <= 168):
        parser.error("hours must be 1..168")
    try:
        result = observe(hours=args.hours)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(json.dumps({
            "kind": "ordivon.network.gluetun-country-history",
            "standing": "UNKNOWN",
            "reasonClass": type(exc).__name__,
        }))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
