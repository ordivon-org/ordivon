"""Pure native historical observation representation and statistics.

No network I/O, provider selection, credentials or effect authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import statistics

JOBS = (
    "blackbox-scoped-claude-api",
    "blackbox-scoped-codex-mcp",
    "blackbox-vpn-pypi",
)

@dataclass(frozen=True)
class HistoricalSeries:
    """A metric-independent source identity and its original sample coordinates."""

    labels: tuple[tuple[str, str], ...]
    samples: dict[float, float]


def parse_matrix(rows: list[dict], metric: str, start: datetime, end: datetime) -> dict[str, HistoricalSeries]:
    """Project original samples only, rejecting ambiguous roles in this window."""
    if metric not in ("probe_success", "probe_duration_seconds"):
        raise ValueError("Unsupported historical metric")
    if not isinstance(rows, list) or start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError("Invalid historical observation window or rows")
    lower, upper = start.timestamp(), end.timestamp()
    outputs: dict[str, HistoricalSeries] = {}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("metric"), dict):
            raise ValueError("Historical observation lacks source identity")
        labels = row["metric"]
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in labels.items()):
            raise ValueError("Historical observation has invalid source labels")
        job = labels.get("job", "")
        if job not in JOBS:
            continue
        samples: dict[float, float] = {}
        coordinates: set[float] = set()
        values = row.get("values")
        valid = labels.get("__name__", metric) == metric and isinstance(values, list)
        for value in values if isinstance(values, list) else ():
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                valid = False
                break
            timestamp, raw = value
            if isinstance(timestamp, bool) or isinstance(raw, bool):
                valid = False
                break
            try:
                stamp = float(timestamp)
            except (ValueError, TypeError):
                valid = False
                break
            if not math.isfinite(stamp):
                valid = False
                break
            if not lower <= stamp <= upper:
                continue
            if stamp in coordinates:
                valid = False
                break
            coordinates.add(stamp)
            try:
                number = float(raw)
            except (ValueError, TypeError):
                valid = False
                break
            # NaN represents missing telemetry, never an observation.
            if math.isnan(number):
                continue
            if (not math.isfinite(number) or not math.isfinite(number*1000) or number < 0
                    or (metric == "probe_success" and number not in (0.0, 1.0))):
                valid = False
                break
            samples[stamp] = number
        # A different identity outside this segment is not evidence for it.
        # Invalid observations, including unknown timestamps, are ambiguous.
        if valid and not coordinates:
            continue
        if job in seen:
            outputs.pop(job, None)
            continue
        seen.add(job)
        if valid:
            identity = tuple(sorted((k,v) for k,v in labels.items() if k != "__name__"))
            outputs[job] = HistoricalSeries(identity, samples)
    return outputs


@dataclass(frozen=True)
class PairedSample:
    timestamp: float
    success: float
    duration: float


@dataclass(frozen=True)
class PairedSeries:
    labels: tuple[tuple[str, str], ...]
    samples: tuple[PairedSample, ...]


def paired_matrix(success_rows: list[dict], duration_rows: list[dict],
                  start: datetime, end: datetime) -> dict[str, PairedSeries]:
    """Require exact identity and coordinates, retain original timestamps."""
    successes = parse_matrix(success_rows, "probe_success", start, end)
    durations = parse_matrix(duration_rows, "probe_duration_seconds", start, end)
    result = {}
    for job in successes.keys() & durations.keys():
        a, b = successes[job], durations[job]
        if a.labels != b.labels or a.samples.keys() != b.samples.keys():
            continue
        result[job] = PairedSeries(a.labels, tuple(
            PairedSample(stamp, a.samples[stamp], b.samples[stamp])
            for stamp in sorted(a.samples)))
    return result


@dataclass(frozen=True)
class WindowCoverage:
    sample_count: int
    leading_gap_seconds: float | None
    trailing_gap_seconds: float | None
    max_internal_gap_seconds: float | None
    complete: bool

    def report(self) -> dict[str, object]:
        return {
            "sampleCount": self.sample_count,
            "leadingGapSeconds": self.leading_gap_seconds,
            "trailingGapSeconds": self.trailing_gap_seconds,
            "maxInternalGapSeconds": self.max_internal_gap_seconds,
            "withinDeclaredGapBound": self.complete,
        }


def window_coverage(samples: tuple[PairedSample, ...], start: datetime,
                    end: datetime, *, minimum: int, max_gap: float) -> WindowCoverage:
    """Bound silence at both window edges and every consecutive scrape.

    This is an observation coverage contract, not an availability estimate.
    """
    if start.tzinfo is None or end.tzinfo is None or minimum < 1 or not math.isfinite(max_gap) or max_gap <= 0:
        raise ValueError("Invalid coverage contract")
    lower, upper = start.timestamp(), end.timestamp()
    stamps = [s.timestamp for s in samples]
    if not stamps or upper <= lower or not all(math.isfinite(t) for t in stamps):
        return WindowCoverage(len(stamps), None, None, None, False)
    leading, trailing = stamps[0] - lower, upper - stamps[-1]
    gaps = [b-a for a,b in zip(stamps, stamps[1:])]
    internal = max(gaps, default=0.0)
    complete = (len(stamps) >= minimum and 0 <= leading <= max_gap
                and 0 <= trailing <= max_gap
                and all(0 < gap <= max_gap for gap in gaps))
    return WindowCoverage(len(stamps), leading, trailing, internal, complete)


def latency_summary(values: list[float]) -> dict[str, int | None]:
    if not values:
        return {"medianMs": None, "p90Ms": None}
    ordered = sorted(values)
    # Preserve the existing lower empirical order-statistic convention.
    return {"medianMs": round(1000*statistics.median(ordered)),
            "p90Ms": round(1000*ordered[int(.9*(len(ordered)-1))])}


def summarize_samples(samples: tuple[PairedSample, ...]) -> dict[str, object]:
    if not samples or any(isinstance(s.success, bool) or s.success not in (0, 1) or
                          not math.isfinite(s.duration) or not math.isfinite(s.duration*1000)
                          or s.duration < 0 for s in samples):
        raise ValueError("Invalid paired historical samples")
    successful = [s.duration for s in samples if s.success == 1]
    failed = [s.duration for s in samples if s.success == 0]
    return {
        "samples": len(samples),
        "successRatio": len(successful)/len(samples),
        **latency_summary([s.duration for s in samples]),
        "successfulProbeLatency": {"samples": len(successful), **latency_summary(successful)},
        "failedProbeLatency": {"samples": len(failed), **latency_summary(failed)},
    }
