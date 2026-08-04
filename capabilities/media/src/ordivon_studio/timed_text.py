from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class Cue:
    cue_id: str
    start_tick: int
    end_tick: int
    text: str


def _validated_cues(document: dict[str, Any]) -> tuple[int, list[Cue]]:
    time_base = document.get("timeBase")
    if not isinstance(time_base, dict):
        raise ValueError("timeBase must be an object")
    ticks_per_second = time_base.get("ticksPerSecond")
    if not isinstance(ticks_per_second, int) or ticks_per_second <= 0:
        raise ValueError("ticksPerSecond must be a positive integer")

    raw_cues = document.get("cues")
    if not isinstance(raw_cues, list):
        raise ValueError("cues must be an array")

    cues: list[Cue] = []
    seen: set[str] = set()
    previous_start = -1
    for item in raw_cues:
        if not isinstance(item, dict):
            raise ValueError("each cue must be an object")
        cue_id = item.get("id")
        start = item.get("startTick")
        end = item.get("endTick")
        text = item.get("text")
        if not isinstance(cue_id, str) or not cue_id:
            raise ValueError("cue id must be a non-empty string")
        if cue_id in seen:
            raise ValueError(f"duplicate cue id: {cue_id}")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
            raise ValueError(f"invalid cue interval: {cue_id}")
        if start < previous_start:
            raise ValueError(f"cues are not ordered: {cue_id}")
        if not isinstance(text, str):
            raise ValueError(f"cue text must be a string: {cue_id}")
        seen.add(cue_id)
        previous_start = start
        cues.append(Cue(cue_id, start, end, text))
    return ticks_per_second, cues


def _milliseconds(tick: int, ticks_per_second: int) -> int:
    return round(tick * 1000 / ticks_per_second)


def _timestamp(milliseconds: int, separator: str) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{millis:03d}"


def export_webvtt(document: dict[str, Any]) -> str:
    ticks_per_second, cues = _validated_cues(document)
    lines = ["WEBVTT", ""]
    for cue in cues:
        start = _timestamp(_milliseconds(cue.start_tick, ticks_per_second), ".")
        end = _timestamp(_milliseconds(cue.end_tick, ticks_per_second), ".")
        lines.extend([cue.cue_id, f"{start} --> {end}", cue.text, ""])
    return "\n".join(lines)


def export_srt(document: dict[str, Any]) -> str:
    ticks_per_second, cues = _validated_cues(document)
    lines: list[str] = []
    for index, cue in enumerate(cues, start=1):
        start = _timestamp(_milliseconds(cue.start_tick, ticks_per_second), ",")
        end = _timestamp(_milliseconds(cue.end_tick, ticks_per_second), ",")
        lines.extend([str(index), f"{start} --> {end}", cue.text, ""])
    return "\n".join(lines)


def iter_cues(document: dict[str, Any]) -> Iterable[Cue]:
    _, cues = _validated_cues(document)
    return tuple(cues)
