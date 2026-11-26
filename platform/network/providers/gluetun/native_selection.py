"""Pure schema refinement for the existing native selection contract.

No I/O, credentials, routing effects or decision authority.
"""
from __future__ import annotations

from typing import TypedDict


def country_patch(country: str, allowed: set[str]) -> dict:
    if country not in allowed or country == "Hong Kong":
        raise ValueError("Cannot apply a country outside policy")
    return {"provider": {"server_selection": {"countries": [country]}}}


FILTER_FIELDS = ("regions", "cities", "hostnames", "names", "isps", "numbers")


class SelectionSnapshot(TypedDict):
    countries: list[str]
    vpn: str
    provider: str


def settings_parts(raw: object) -> tuple[str, str, dict]:
    if not isinstance(raw, dict) or not isinstance(raw.get("type"), str):
        raise ValueError("Invalid native VPN settings envelope")
    provider = raw.get("provider")
    if not isinstance(provider, dict) or not isinstance(provider.get("name"), str):
        raise ValueError("Invalid native provider envelope")
    selection = provider.get("server_selection")
    if not isinstance(selection, dict):
        raise ValueError("Invalid native server selection shape")
    return raw["type"], provider["name"], selection


def project_settings(raw: object, status: int) -> dict:
    """Only project schema-qualified, nonsecret selection fields from GET."""
    vpn, name, selection = settings_parts(raw)
    countries = selection.get("countries")
    if not isinstance(countries, list) or any(not isinstance(c, str) for c in countries):
        raise ValueError("Invalid native selected country array")
    # This consumer has no contract for nonempty alternate selectors.
    # Reject rather than serialize arbitrary vendor response values.
    for field in FILTER_FIELDS:
        value = selection.get(field)
        if value is not None and (not isinstance(value, list) or value):
            raise ValueError("Unexpected other native server selection filters")
    return {"status": status, "type": vpn,
            "provider": {"name": name, "server_selection": {
                "countries": countries.copy(),
                **{field: selection.get(field) for field in FILTER_FIELDS},
            }}}


def selected_snapshot(raw: object, allowed: set[str]) -> SelectionSnapshot:
    vpn, provider, s = settings_parts(raw)
    if vpn != "wireguard":
        raise ValueError("Unexpected VPN type")
    if provider != "surfshark":
        raise ValueError("Unexpected VPN provider")
    countries = s.get("countries")
    if not isinstance(countries, list) or not countries:
        raise ValueError("Gluetun control country selection violates policy")
    # Official Gluetun v3.41.3 lowercases source SERVER_COUNTRIES in its
    # GET /v1/vpn/settings output. Compare with a case-folded permission map,
    # but always return canonical source names for PUT and rollback.
    canonical_names = {name.casefold(): name for name in allowed}
    if len(canonical_names) != len(allowed):
        raise ValueError("Ambiguous allowed countries after case normalization")
    if any(not isinstance(c, str) or not c or c.casefold() not in canonical_names
           or c.casefold() == "hong kong" for c in countries):
        raise ValueError("Gluetun control country selection violates policy")
    for field in FILTER_FIELDS:
        value = s.get(field)
        if value is not None and (not isinstance(value, list) or value):
            raise ValueError("Unexpected other native server selection filters")
    canonical = [canonical_names[c.casefold()] for c in countries]
    if len(canonical) != len(set(canonical)):
        raise ValueError("Duplicate native selected country")
    return {"countries": canonical, "vpn": vpn, "provider": provider}
