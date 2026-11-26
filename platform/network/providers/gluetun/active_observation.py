"""Pure producer/receiver contract for one active observation, not an effect receipt."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import math

KIND = "ordivon.network.gluetun-active-qualification"
QUALIFIED = "QUALIFIED_ACTIVE_SAMPLE"
NOT_QUALIFIED = "NOT_QUALIFIED"
NONQUALIFIED = frozenset({NOT_QUALIFIED, "UNKNOWN", "REJECTED_FORBIDDEN_EXIT", "REJECTED_NOT_ALLOWED"})
BUSINESS_ROLES = ("ordinary_https", "github_https")


def parse_curl_receipt(raw: str) -> tuple[bool, float]:
    parts = raw.strip().split()
    if len(parts) != 4:
        return False, 0.0
    try:
        http, connect = int(parts[0]), int(parts[1])
        tls, total = float(parts[2]), float(parts[3])
    except ValueError:
        return False, 0.0
    if not math.isfinite(tls) or not math.isfinite(1000 * total) or total < 0:
        raise ValueError("Nonfinite or negative active observation timing")
    return http == 200 and connect == 200 and 0 < tls <= total, total


def standing(
    *, catalog_location: str | None, actual_exit: str | None,
    allowed: set[str], active_endpoint_stable: bool,
    provider_running: bool, business_receipts: list[bool],
) -> str:
    if catalog_location == "Hong Kong" or actual_exit == "HK":
        return "REJECTED_FORBIDDEN_EXIT"
    if catalog_location is None or actual_exit is None:
        return "UNKNOWN"
    if catalog_location not in allowed:
        return "REJECTED_NOT_ALLOWED"
    if not active_endpoint_stable or not provider_running:
        return "UNKNOWN"
    if len(business_receipts) < 2 or not all(business_receipts):
        return "NOT_QUALIFIED"
    return "QUALIFIED_ACTIVE_SAMPLE"


def exit_status(receipt: dict) -> int:
    return 0 if receipt["standing"] == QUALIFIED else 1


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate active observation field")
        result[name] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("Nonfinite active observation JSON constant")


def receive_observation(stdout: str, returncode: int) -> dict:
    """Validate the existing producer terminal and evidence shape together.

    This is structural consistency, not proof of time freshness, origin,
    or native consumption. A native exit-1 NOT_QUALIFIED is distinct from
    an arbitrary failed or killed child.
    """
    raw = json.loads(stdout, object_pairs_hook=unique_object, parse_constant=reject_constant)
    if not isinstance(raw, dict) or raw.get("kind") != KIND:
        raise ValueError("Unexpected active observation kind")
    state = raw.get("standing")
    if not isinstance(state, str) or state not in NONQUALIFIED | {QUALIFIED}:
        raise ValueError("Unknown active observation standing")
    if type(returncode) is not int or returncode != exit_status(raw):
        raise ValueError("Active observation disagrees with native terminal")
    if state not in (QUALIFIED, NOT_QUALIFIED):
        return raw
    stamp = raw.get("observedAtUtc")
    if not isinstance(stamp, str) or datetime.fromisoformat(stamp).utcoffset() != timedelta(0):
        raise ValueError("Missing UTC observation coordinate")
    country = raw.get("currentCatalogCountry")
    public = raw.get("currentPublicExitCountryCode")
    if (not isinstance(country, str) or not country.strip()
            or not isinstance(public, str) or len(public) != 2
            or country == "Hong Kong" or public == "HK"):
        raise ValueError("Invalid active observation identity")
    if raw.get("actualEndpointStableDuringSample") is not True or raw.get("providerStatus") != "running":
        raise ValueError("Active observation lacks stable running evidence")
    count = raw.get("qualifiedStandbyCount")
    if type(count) is not int or count != 0:
        raise ValueError("Active observation must not assert standby qualification")
    business = raw.get("business")
    if not isinstance(business, dict) or set(business) != set(BUSINESS_ROLES):
        raise ValueError("Missing or ambiguous active observation business roles")
    receipts = []
    for role in BUSINESS_ROLES:
        receipt = business[role]
        if not isinstance(receipt, dict):
            raise ValueError("Malformed active observation business receipt")
        ok, duration = receipt.get("httpTlsAndConnect"), receipt.get("totalMs")
        if type(ok) is not bool or type(duration) is not int or duration < 0:
            raise ValueError("Malformed active observation business evidence")
        receipts.append(ok)
    if (state == QUALIFIED) != all(receipts):
        raise ValueError("Active observation standing contradicts business evidence")
    return raw
