#!/usr/bin/env python3
"""Read-only Network v2 capability router.

The caller provides explicit network requirements. The router selects among current compatible
routes but does not mutate networking, grant authority, materialize credentials, or infer task
requirements from natural language.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping

NETWORK_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = NETWORK_ROOT / "config/network-capability-routes.json"


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    value = _read_json(path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.network-v2.route-policy":
        raise ValueError("network route policy identity mismatch")
    routes = value.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("network route policy requires routes")
    seen: set[str] = set()
    normalized = []
    for raw in routes:
        if not isinstance(raw, dict):
            raise ValueError("network route must be an object")
        route_id = raw.get("routeId")
        priority = raw.get("priority")
        provides = raw.get("provides")
        readiness = raw.get("readiness")
        provider_profile = raw.get("providerProfileId")
        if (
            not isinstance(route_id, str) or not route_id or route_id in seen
            or type(priority) is not int or priority < 0
            or not isinstance(provides, list) or not provides
            or any(not isinstance(x, str) or not x or x != x.strip() for x in provides)
            or len(set(provides)) != len(provides)
            or not isinstance(readiness, dict) or not isinstance(readiness.get("kind"), str)
            or (provider_profile is not None and (not isinstance(provider_profile, str) or not provider_profile))
        ):
            raise ValueError(f"invalid network route: {route_id!r}")
        seen.add(route_id)
        normalized.append(dict(raw))
    return {
        "schemaVersion":1,
        "kind":value["kind"],
        "routes":normalized,
        "nonClaims":value.get("nonClaims", []),
        "policyDigest":canonical_digest(value),
    }


def validate_request(value: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schemaVersion") != 1:
        raise ValueError("network route request requires schemaVersion=1")
    request_id=value.get("requestId")
    if not isinstance(request_id, str) or not request_id or request_id != request_id.strip():
        raise ValueError("requestId must be non-empty trimmed text")

    def features(name: str) -> tuple[str, ...]:
        raw=value.get(name, [])
        if not isinstance(raw, list) or any(
            not isinstance(x, str) or not x or x != x.strip() for x in raw
        ):
            raise ValueError(f"{name} must be a list of non-empty trimmed strings")
        if len(set(raw)) != len(raw):
            raise ValueError(f"{name} must not contain duplicates")
        return tuple(raw)

    required=features("requiredFeatures")
    preferred=features("preferredFeatures")
    known={f for route in policy["routes"] for f in route["provides"]}
    unknown=sorted((set(required)|set(preferred))-known)
    if unknown:
        raise ValueError(f"unknown network routing features: {unknown}")

    provider=value.get("providerProfileId")
    if provider is not None and (not isinstance(provider, str) or not provider or provider != provider.strip()):
        raise ValueError("providerProfileId must be null or non-empty trimmed text")
    explicit=value.get("explicitRouteId")
    if explicit is not None and (not isinstance(explicit, str) or not explicit or explicit != explicit.strip()):
        raise ValueError("explicitRouteId must be null or non-empty trimmed text")
    if explicit is not None and explicit not in {r["routeId"] for r in policy["routes"]}:
        raise ValueError(f"unknown explicitRouteId: {explicit}")

    return {
        "schemaVersion":1,
        "requestId":request_id,
        "requiredFeatures":required,
        "preferredFeatures":preferred,
        "providerProfileId":provider,
        "explicitRouteId":explicit,
    }


def _nested_get(value: Mapping[str, Any], dotted: str) -> Any:
    cur: Any=value
    for part in dotted.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur=cur[part]
    return cur


def probe_route(route: Mapping[str, Any], *, current_kernel: str | None = None) -> dict[str, Any]:
    readiness=route["readiness"]
    kind=readiness["kind"]
    if kind == "systemd-active":
        unit=readiness.get("unit")
        proc=subprocess.run(
            ["/usr/bin/systemctl","is-active","--quiet",str(unit)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        return {"ready":proc.returncode==0,"standing":"READY" if proc.returncode==0 else "UNIT_INACTIVE","unit":unit}
    if kind == "command-json":
        command=readiness.get("command")
        if not isinstance(command, str) or not command.startswith("/") or not Path(command).is_file():
            return {"ready":False,"standing":"READINESS_COMMAND_UNAVAILABLE"}
        proc=subprocess.run(
            [command], text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, check=False,
        )
        value=None
        try:
            value=json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
        expected_kind=readiness.get("expectedKind")
        expected_standing=readiness.get("expectedStanding")
        ready=(
            proc.returncode==0 and isinstance(value, dict)
            and value.get("kind")==expected_kind
            and value.get("standing")==expected_standing
        )
        return {
            "ready":ready,
            "standing":"READY" if ready else "OWNER_READINESS_FAILED",
            "ownerKind":value.get("kind") if isinstance(value,dict) else None,
            "ownerStanding":value.get("standing") if isinstance(value,dict) else None,
            "providerSite":value.get("providerSite") if isinstance(value,dict) else None,
            "probeReturnCode":proc.returncode,
        }
    if kind == "evidence-current-kernel":
        path=NETWORK_ROOT / str(readiness.get("evidencePath") or "")
        if not path.is_file():
            return {"ready":False,"standing":"QUALIFICATION_EVIDENCE_UNAVAILABLE"}
        evidence=_read_json(path)
        evidence_kernel=_nested_get(evidence,"platformEvidence.kernelRelease")
        actual=current_kernel or platform.release()
        claims=readiness.get("requiredClaims", {})
        claims_ok=isinstance(claims,dict) and all(_nested_get(evidence,k)==v for k,v in claims.items())
        if evidence_kernel != actual:
            return {
                "ready":False,
                "standing":"QUALIFICATION_STALE",
                "evidenceKernel":evidence_kernel,
                "currentKernel":actual,
                "claimsSatisfied":claims_ok,
            }
        return {
            "ready":bool(claims_ok),
            "standing":"READY" if claims_ok else "QUALIFICATION_CLAIM_MISSING",
            "evidenceKernel":evidence_kernel,
            "currentKernel":actual,
            "claimsSatisfied":claims_ok,
        }
    return {"ready":False,"standing":"UNKNOWN_READINESS_KIND"}


def plan(
    request_value: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    readiness_provider: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    policy=policy or load_policy()
    request=validate_request(request_value, policy)
    required=set(request["requiredFeatures"])
    preferred=set(request["preferredFeatures"])
    explicit=request["explicitRouteId"]
    provider=request["providerProfileId"]
    probe=readiness_provider or probe_route

    candidates=[]
    for route in policy["routes"]:
        route_id=route["routeId"]
        if explicit is not None and route_id != explicit:
            continue
        provides=set(route["provides"])
        if not required.issubset(provides):
            continue
        route_provider=route.get("providerProfileId")
        if provider is not None and route_provider != provider:
            continue
        readiness=dict(probe(route))
        preferred_matches=sorted(preferred & provides)
        candidates.append({
            "routeId":route_id,
            "priority":route["priority"],
            "providerProfileId":route_provider,
            "provides":route["provides"],
            "preferredMatches":preferred_matches,
            "preferredMatchCount":len(preferred_matches),
            "readiness":readiness,
        })

    ready=[c for c in candidates if c["readiness"].get("ready") is True]
    ready.sort(key=lambda c:(-c["preferredMatchCount"],c["priority"],c["routeId"]))
    selected=ready[0] if ready else None
    standing="SELECTED_ROUTE" if selected else "HOLD_NO_READY_ROUTE"
    return {
        "schemaVersion":1,
        "kind":"ordivon.network-v2.route-plan",
        "standing":standing,
        "requestId":request["requestId"],
        "requestDigest":canonical_digest(dict(request_value)),
        "policyDigest":policy["policyDigest"],
        "selectedRoute":selected,
        "candidates":candidates,
        "nonClaims":[
            "plan-is-not-network-authority",
            "plan-is-not-provider-effect-authority",
            "plan-does-not-mutate-network-state",
        ],
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="command", required=True)
    catalog=sub.add_parser("catalog")
    catalog.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    plan_p=sub.add_parser("plan")
    plan_p.add_argument("--request", type=Path, required=True)
    plan_p.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args=ap.parse_args()
    policy=load_policy(args.policy)
    if args.command=="catalog":
        print(json.dumps(policy, sort_keys=True))
        return 0
    request=_read_json(args.request)
    result=plan(request, policy=policy)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["standing"]=="SELECTED_ROUTE" else 3


if __name__=="__main__":
    raise SystemExit(main())
