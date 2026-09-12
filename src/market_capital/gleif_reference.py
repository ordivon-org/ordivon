from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

GLEIF_ENDPOINT = "https://api.gleif.org/api/v1/lei-records"


@dataclass(frozen=True)
class RequestedEntity:
    symbol: str
    legal_name: str


def _legal_name(record: dict[str, Any]) -> str | None:
    return (
        record.get("attributes", {})
        .get("entity", {})
        .get("legalName", {})
        .get("name")
    )


def _registration_status(record: dict[str, Any]) -> str | None:
    return record.get("attributes", {}).get("registration", {}).get("status")


def select_exact_issued(records: list[dict[str, Any]], requested_name: str) -> dict[str, Any]:
    matches = [
        r
        for r in records
        if (_legal_name(r) or "").casefold() == requested_name.casefold()
        and _registration_status(r) == "ISSUED"
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one ISSUED exact legal-name match for {requested_name!r}; got {len(matches)}"
        )
    return matches[0]


def fetch_entity(entity: RequestedEntity, timeout: float = 20.0) -> tuple[dict[str, Any], dict[str, Any]]:
    query = urllib.parse.urlencode(
        {"filter[entity.legalName]": entity.legal_name, "page[size]": "20"}
    )
    url = f"{GLEIF_ENDPOINT}?{query}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.api+json", "User-Agent": "OrdivonMarketCapital/0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    record = select_exact_issued(payload.get("data", []), entity.legal_name)
    attrs = record.get("attributes", {})
    normalized = {
        "symbol": entity.symbol,
        "requested_legal_name": entity.legal_name,
        "lei": record["id"],
        "legal_name": _legal_name(record),
        "registration_status": _registration_status(record),
        "jurisdiction": attrs.get("entity", {}).get("jurisdiction"),
        "entity_status": attrs.get("entity", {}).get("status"),
    }
    return payload, normalized


def collect_reference(universe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw: dict[str, Any] = {}
    normalized: list[dict[str, Any]] = []
    for item in universe["instruments"]:
        requested = RequestedEntity(symbol=item["symbol"], legal_name=item["legal_name"])
        payload, entity = fetch_entity(requested)
        raw[item["symbol"]] = payload
        normalized.append(entity)
    reference = {
        "source": "GLEIF API",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "entities": normalized,
    }
    return raw, reference
