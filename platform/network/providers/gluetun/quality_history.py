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
SOURCE_TRIAL_HINTS = Path(__file__).resolve().parent / "config/recovery-hints.json"
SOURCE_HINT_MAX_AGE = timedelta(days=7)

def source_trial_hints(now: datetime, allowed: set[str],
                       path: Path = SOURCE_TRIAL_HINTS) -> list[dict[str, object]]:
    """A finite, *stale-able* source preference, not current node liveness.

    Existing Gluetun journald is bounded and a 3178-restart shared-underlay
    incident can discard past successful-country journal segments. When that
    happens two actually observed historic candidates must not disappear from
    the only fallback plan. Only a real fresh 3-lane consumer outage, healthy
    independent underlay and official authenticated post-trial receipt can
    authorize any effect. This file NEVER grants those conditions.
    """
    raw = native._strict_json_mapping(path.read_text(encoding="utf-8"),
                                      "VPN recovery trial hints")
    if set(raw) != {"kind", "observedAtUtc", "expiresAtUtc", "candidates"} or (
        raw["kind"] != "ordivon.network.historical-consumer-trial-hints"
    ):
        raise ValueError("Unexpected VPN recovery trial hint schema")
    observed = datetime.fromisoformat(str(raw["observedAtUtc"]).replace("Z", "+00:00"))
    expires = datetime.fromisoformat(str(raw["expiresAtUtc"]).replace("Z", "+00:00"))
    if observed.tzinfo is None or expires.tzinfo is None or (
        expires <= observed or expires - observed > SOURCE_HINT_MAX_AGE
    ):
        raise ValueError("Invalid historic trial hint time boundary")
    if not isinstance(raw["candidates"], list) or not (1 <= len(raw["candidates"]) <= 2):
        raise ValueError("Only one or two source historic trial hints are admitted")
    seen: set[str] = set()
    results: list[dict[str, object]] = []
    for row in raw["candidates"]:
        if not isinstance(row, dict) or set(row) != {
            "country", "worstConsumerSuccessRatio", "medianOfConsumerP90Ms"
        }:
            raise ValueError("Invalid historic candidate evidence")
        country = row["country"]
        if (not isinstance(country, str) or country not in allowed or
            country == "Hong Kong" or country in seen):
            raise ValueError("Unknown, forbidden or duplicate source trial candidate")
        seen.add(country)
        ratio = row["worstConsumerSuccessRatio"]
        ms = row["medianOfConsumerP90Ms"]
        if (isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or
            not 0.97 <= ratio <= 1 or isinstance(ms, bool) or
            not isinstance(ms, int) or not 1 <= ms <= 60_000):
            raise ValueError("No bounded consumer quality evidence for source trial hint")
        results.append({
            "catalogCountry": country,
            "standing": "SOURCE_TIME_BOUNDED_CONSUMER_TRIAL_HINT",
            "lastObservedHoursAgo": round(max(0,(now-observed).total_seconds())/3600,2),
            "medianOfConsumerP90Ms": ms,
            "worstConsumerSuccessRatio": ratio,
            "qualifiedNowStandby": False,
            "evidenceBasis": "prior verified real Gluetun journal + three-lane Prometheus",
            "expiresAtUtc": expires.isoformat(),
        })
    if not observed <= now < expires:
        return []  # Expired or future evidence must never authorize trials.
    return results



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
                  if row.get("standing") in (
                      "RECENT_HISTORICAL_CONSUMER_SUCCESS",
                      "SOURCE_TIME_BOUNDED_CONSUMER_TRIAL_HINT")
                  and row.get("catalogCountry") is not None
                  and row.get("catalogCountry") != current_country]
    if not candidates:
        return {"decision": "HOLD_NO_RECENT_EVIDENCE", "trialCountry": None}
    candidates.sort(key=lambda row: (
        0 if row["standing"] == "RECENT_HISTORICAL_CONSUMER_SUCCESS" else 1,
        int(row.get("medianOfConsumerP90Ms", 1000000)),
        -float(row.get("worstConsumerSuccessRatio", 0)),
        float(row.get("lastObservedHoursAgo", 1000000)),
    ))
    # Only unique countries: multiple segments for one failed country must not
    # consume all recovery attempts and starve a distinct successful country.
    distinct = []
    for row in candidates:
        if row["catalogCountry"] not in {x["country"] for x in distinct}:
            distinct.append({"country": row["catalogCountry"],
                             "historicalHostname": row.get("catalogHostname")})
        if len(distinct) == 2:
            break
    return {
        "decision": "TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF",
        "trialCountry": distinct[0]["country"],
        "trialCountries": [row["country"] for row in distinct],
        "historicalCatalogHostname": distinct[0]["historicalHostname"],
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


def http_raw_samples(metric: str, now: datetime) -> list[dict]:
    """Return actual Prometheus scrape timestamps, NEVER query_range steps.

    A query_range instant selector can repeat the final failed value for up
    to the lookback delta after scraping stops. Query a range vector at one
    instant to receive original raw sample times and distinguish silence.
    """
    if metric != "probe_success":
        raise ValueError("Native failure admission accepts only probe_success")
    expr = metric + '{job=~"' + "|".join(JOBS) + '"}[7m]'
    url = PROM + "/api/v1/query?" + urlencode({
        "query": expr, "time": now.timestamp(),
    })
    with urlopen(url, timeout=11) as response:
        data = json.load(response)
    if (data.get("status") != "success" or
        data.get("data", {}).get("resultType") != "matrix"):
        raise ValueError("Raw Prometheus range-vector observation invalid")
    return data["data"]["result"]


def recent_failure_witness(now: datetime) -> bool | None:
    """Require three actually sampled consecutive failures in all three lanes.

    Missing or stale time-series evidence is UNKNOWN, not FALSE.
    """
    start = now - timedelta(minutes=7)
    rows = http_raw_samples("probe_success", now)
    by_job: dict[str, list[tuple[float, int]]] = {}
    for row in rows:
        job = row.get("metric", {}).get("job", "")
        if job not in JOBS:
            continue
        # More than one distinct instance for a single lane means our
        # source identity is ambiguous; do not arbitrarily pick a series.
        if job in by_job:
            return None
        samples: list[tuple[float, int]] = []
        for ts, raw in row.get("values", []):
            try:
                stamp = float(ts)
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if val in (0.0, 1.0) and start.timestamp() <= stamp <= now.timestamp():
                samples.append((stamp, int(val)))
        by_job[job] = sorted(samples)
    if any(len(by_job.get(job, [])) < 3 for job in JOBS):
        return None
    windows = [by_job[job][-3:] for job in JOBS]
    for values in windows:
        times = [row[0] for row in values]
        # Monitor silence must never become a fresh VPN failure; require
        # three distinct scrape evaluations and a recent last measurement.
        if (len(set(times)) != 3 or
            now.timestamp() - times[-1] > 150 or
            now.timestamp() - times[0] > 300):
            return None
    # All lanes must refer to a comparable observation window; accepting
    # disjoint epochs would fabricate correlated failure.
    if max(x[-1][0] for x in windows) - min(x[-1][0] for x in windows) > 90:
        return None
    return all(all(v == 0 for _, v in values) for values in windows)


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
    if relevant:
        # Query the monitoring service just twice, rather than 2*8
        # individual range requests when several historical nodes exist.
        # This keeps the outage-time decision path bounded under latency.
        earliest = min(segment.start + WARMUP for segment in relevant)
        latest = max(segment.end - timedelta(minutes=1) for segment in relevant)
        successes = http_query("probe_success", earliest, latest)
        durations = http_query("probe_duration_seconds", earliest, latest)
        for segment in relevant:
            start = segment.start + WARMUP
            end = segment.end - timedelta(minutes=1)
            success = parse_matrix(successes, "probe_success", start, end)
            duration = parse_matrix(durations, "probe_duration_seconds", start, end)
            results.append(qualify(segment, success, duration, now, allowed))
    # Live evidence is distinct from the historical trend. Do not infer
    # active failure from a missing metric or merely an older journal session.
    import observe_active
    failed_sample = recent_failure_witness(now)
    if failed_sample is True:
        # When the 3-lane fresh failure is already proved, 3 more sequential
        # external HTTPS timeouts cannot add useful evidence to triage.
        # The switcher independently rechecks consumers at the action edge.
        live = {"standing": "OBSERVED_CORRELATED_CONSUMER_FAILURE"}
        active_ok: bool | None = False
    else:
        try:
            live = observe_active.observe()
        except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError):
            live = {"standing": "UNKNOWN_CONSUMER_PROBE_INCOMPLETE"}
        active_ok = True if live.get("standing") == "QUALIFIED_ACTIVE_SAMPLE" else None
    observed = live.get("standing")
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
    # Preference-only evidence is read ONLY at a witnessed outage boundary.
    # It cannot change a healthy VPN, or defeat missing/failed underlay.
    hints = source_trial_hints(now, allowed) if (
        active_ok is False and underlay_ok is True) else []
    plan = decision(
        active_healthy=active_ok, underlay_reachable=underlay_ok,
        evidence=results + hints, now=now,
        current_country=catalog_identity,
    )
    # A lost kernel WG endpoint is an expected symptom of a genuine outage.
    # Safe action still requires authorized native API readback of the prior
    # settings, a fresh three-lane failure, and independent healthy underlay.
    return {
        "kind": "ordivon.network.gluetun-country-history",
        "observationUtc": now.isoformat(),
        "scope": "correlated historical endpoint dwell and VPN consumer probe quality",
        "history": results,
        "sourceTrialHints": hints,
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
