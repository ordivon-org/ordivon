from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any


def _at_pointer(root: Mapping[str, Any], pointer: str) -> object:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("claim native pointer must be an absolute JSON pointer")
    value: object = root
    for raw in pointer[1:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or key not in value:
            raise KeyError(pointer)
        value = value[key]
    return value


def build_explicit_claim_results(
    native_result: Mapping[str, Any],
    claim_pointers: Mapping[str, str],
    *,
    non_claims: Mapping[str, list[str]] | None = None,
    evidence_refs: Mapping[str, list[dict[str, Any]]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Project only verifier-declared native status objects into claimResults.

    `claim_pointers` is verifier-owned semantic mapping. This helper never reads a
    profile, never uses the native overall status, never searches for aliases, and
    never promotes an absent or ambiguous native observation. A mapped native value
    must itself be an object with explicit PASS or FAIL status; otherwise the claim
    remains NOT_EVALUATED.
    """
    if not isinstance(native_result, Mapping):
        raise TypeError("native_result must be a mapping")
    if not isinstance(claim_pointers, Mapping) or not claim_pointers:
        raise ValueError("claim_pointers must be a non-empty mapping")

    boundaries = non_claims or {}
    refs = evidence_refs or {}
    unknown_boundary = sorted(set(boundaries) - set(claim_pointers))
    unknown_refs = sorted(set(refs) - set(claim_pointers))
    if unknown_boundary or unknown_refs:
        raise ValueError(
            f"claim metadata contains undeclared keys: "
            f"nonClaims={unknown_boundary} evidenceRefs={unknown_refs}"
        )

    out: dict[str, dict[str, Any]] = {}
    for claim, pointer in claim_pointers.items():
        if not isinstance(claim, str) or not claim:
            raise ValueError("claim key must be a non-empty string")
        status = "NOT_EVALUATED"
        evaluated = False
        try:
            native = _at_pointer(native_result, pointer)
        except KeyError:
            native = None
        if isinstance(native, Mapping) and native.get("status") in {"PASS", "FAIL"}:
            status = str(native["status"])
            evaluated = True
        out[claim] = {
            "status": status,
            "observationIds": [claim] if evaluated else [],
            "evidenceRefs": list(refs.get(claim, [])) if evaluated else [],
            "nativePointers": [pointer] if evaluated else [],
            "nonClaims": list(boundaries.get(claim, [])),
        }
    return out


def emits_explicit_claim_results(
    claim_pointers: Mapping[str, str],
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Attach exact-key claimResults to every return path of one verifier.

    The mapping is fixed by the verifier at decoration time. This wrapper performs
    no profile lookup and no semantic inference beyond reading the explicitly mapped
    native status objects.
    """
    frozen = dict(claim_pointers)

    def decorate(
        fn: Callable[..., dict[str, Any]],
    ) -> Callable[..., dict[str, Any]]:
        @wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = fn(*args, **kwargs)
            if not isinstance(result, dict):
                raise TypeError("verifier must return a dict before claim projection")
            result["claimResults"] = build_explicit_claim_results(result, frozen)
            return result

        return wrapped

    return decorate


def emits_profile_explicit_claim_results(
    claim_pointers_by_profile: Mapping[str, Mapping[str, str]],
    *,
    profile_field: str = "profileId",
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Attach verifier-declared claim mappings selected by explicit native profile id.

    Unknown or absent profile identity remains unprojected rather than receiving a
    guessed union/intersection claim set. Supported profile mappings are frozen at
    decoration time.
    """
    frozen = {profile: dict(mapping) for profile, mapping in claim_pointers_by_profile.items()}
    if not frozen or any(not profile for profile in frozen):
        raise ValueError("profile claim mappings must be non-empty")

    def decorate(
        fn: Callable[..., dict[str, Any]],
    ) -> Callable[..., dict[str, Any]]:
        @wraps(fn)
        def wrapped(*args: Any, **kwargs: Any) -> dict[str, Any]:
            result = fn(*args, **kwargs)
            if not isinstance(result, dict):
                raise TypeError("verifier must return a dict before claim projection")
            profile = result.get(profile_field)
            mapping = frozen.get(profile) if isinstance(profile, str) else None
            if mapping is not None:
                result["claimResults"] = build_explicit_claim_results(result, mapping)
            return result

        return wrapped

    return decorate
