from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass

from .model import EligibilityState

_REQUIRES_RE = re.compile(
    r'''["']?requires["']?\s*:\s*\{(?P<body>[^{}]{0,4096})\}''',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class RequirementSpec:
    bins: tuple[str, ...] = ()
    any_bins: tuple[str, ...] = ()
    env_names: tuple[str, ...] = ()
    config_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EligibilityObservation:
    state: EligibilityState
    reasons: tuple[str, ...] = ()


def _frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def _string_list(body: str, *keys: str) -> tuple[str, ...]:
    for key in keys:
        pattern = re.compile(
            rf'''["']?{re.escape(key)}["']?\s*:\s*\[(?P<items>[^\]]{{0,4096}})\]''',
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(body)
        if not match:
            continue
        values: list[str] = []
        for double, single in re.findall(
            r'''"([^"\\]*(?:\\.[^"\\]*)*)"|'([^'\\]*(?:\\.[^'\\]*)*)' ''',
            match.group("items"),
        ):
            value = (double or single).strip()
            if value and value not in values:
                values.append(value)
        return tuple(values)
    return ()


def parse_declared_requirements(text: str, adapter: str | None) -> RequirementSpec | None:
    if adapter is None:
        return None
    if adapter != "openclaw-metadata":
        raise ValueError(f"unsupported eligibility adapter: {adapter}")
    match = _REQUIRES_RE.search(_frontmatter(text))
    if not match:
        return RequirementSpec()
    body = match.group("body")
    return RequirementSpec(
        bins=_string_list(body, "bins"),
        any_bins=_string_list(body, "anyBins", "any_bins"),
        env_names=_string_list(body, "env", "envNames", "env_names"),
        config_keys=_string_list(body, "config", "configKeys", "config_keys"),
    )


def observe_eligibility(text: str, adapter: str | None) -> EligibilityObservation:
    spec = parse_declared_requirements(text, adapter)
    if spec is None:
        return EligibilityObservation(EligibilityState.UNKNOWN)
    if not any((spec.bins, spec.any_bins, spec.env_names, spec.config_keys)):
        return EligibilityObservation(EligibilityState.UNKNOWN)

    reasons: list[str] = []
    missing_bins = [name for name in spec.bins if shutil.which(name) is None]
    if missing_bins:
        reasons.append("missing bins: " + ", ".join(missing_bins))
    if spec.any_bins and not any(shutil.which(name) is not None for name in spec.any_bins):
        reasons.append("none of anyBins present: " + ", ".join(spec.any_bins))
    missing_env = [name for name in spec.env_names if name not in os.environ]
    if missing_env:
        reasons.append("missing env names: " + ", ".join(missing_env))
    if reasons:
        return EligibilityObservation(EligibilityState.BLOCKED, tuple(reasons))
    if spec.config_keys:
        return EligibilityObservation(
            EligibilityState.UNKNOWN,
            ("config requirements need an explicit observer",),
        )
    return EligibilityObservation(EligibilityState.READY)
