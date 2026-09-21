from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

_SOH = "\x01"
_SIDE = {"BUY": "1", "SELL": "2"}
_TIF = {"DAY": "0", "GTC": "1", "IOC": "3"}


class Fix44ProjectionError(ValueError):
    """Invalid input for the bounded sessionless FIX 4.4 projection contract."""


def _ascii_field(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise Fix44ProjectionError(f"{name} must be a non-empty string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise Fix44ProjectionError(f"{name} must be ASCII") from exc
    if _SOH in value or "\r" in value or "\n" in value:
        raise Fix44ProjectionError(f"{name} contains a FIX field delimiter/control")
    return value


def _positive_decimal_text(value: Any) -> str:
    text = _ascii_field(value, name="orderQty")
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise Fix44ProjectionError("orderQty must be decimal-compatible") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise Fix44ProjectionError("orderQty must be positive and finite")
    return text


def _fix_utc_millis(value: Any) -> tuple[str, str]:
    text = _ascii_field(value, name="transactTimeUtc")
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Fix44ProjectionError("transactTimeUtc must be ISO-8601") from exc
    if dt.tzinfo is None:
        raise Fix44ProjectionError("transactTimeUtc must include a timezone")
    dt = dt.astimezone(UTC)
    fix_text = dt.strftime("%Y%m%d-%H:%M:%S.") + f"{dt.microsecond // 1000:03d}"
    canonical = dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return fix_text, canonical


def project_new_order_single(
    *,
    seq: int,
    sender_comp_id: str,
    cl_ord_id: str,
    symbol: str,
    side: str,
    order_qty: str,
    time_in_force: str,
    ex_destination: str,
    transact_time_utc: str,
) -> dict[str, Any]:
    """Project the exact sessionless FIX 4.4 field sequence qualified against QuickFIX/n.

    This is not a FIX session engine and not a complete network wire frame: BodyLength (9)
    and CheckSum (10) are intentionally absent because the qualified historical QuickFIX/n
    Message.ToString() contract omitted session framing as well.
    """
    if not isinstance(seq, int) or isinstance(seq, bool) or seq <= 0:
        raise Fix44ProjectionError("seq must be a positive integer")
    sender = _ascii_field(sender_comp_id, name="senderCompId")
    clid = _ascii_field(cl_ord_id, name="clOrdId")
    sym = _ascii_field(symbol, name="symbol")
    dest = _ascii_field(ex_destination, name="exDestination")
    qty = _positive_decimal_text(order_qty)
    try:
        side_code = _SIDE[side]
    except KeyError as exc:
        raise Fix44ProjectionError("side must be BUY or SELL") from exc
    try:
        tif_code = _TIF[time_in_force]
    except KeyError as exc:
        raise Fix44ProjectionError("timeInForce must be DAY, GTC, or IOC") from exc
    fix_time, canonical_time = _fix_utc_millis(transact_time_utc)

    fields = (
        ("8", "FIX.4.4"),
        ("35", "D"),
        ("34", str(seq)),
        ("49", sender),
        ("52", fix_time),
        ("56", f"{dest}_QUALIFICATION"),
        ("11", clid),
        ("38", qty),
        ("40", "1"),
        ("54", side_code),
        ("55", sym),
        ("59", tif_code),
        ("60", fix_time),
        ("100", dest),
    )
    raw = "".join(f"{tag}={value}{_SOH}" for tag, value in fields)
    raw_bytes = raw.encode("ascii")
    return {
        "protocol": "FIX.4.4",
        "msgType": "D",
        "clOrdId": clid,
        "symbol": sym,
        "side": side_code,
        "orderQty": qty,
        "ordType": "1",
        "timeInForce": tif_code,
        "exDestination": dest,
        "transactTimeUtc": canonical_time,
        "rawSha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw": raw,
    }


def project_document(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("kind") != "ordivon.capital.market.fix44-projection-input":
        raise Fix44ProjectionError("unexpected projection input kind")
    if document.get("purpose") != "MECHANICS_ONLY_NON_ECONOMIC":
        raise Fix44ProjectionError("only mechanics-only non-economic projection is admitted")
    if document.get("networkSessionEnabled"):
        raise Fix44ProjectionError("FIX projector must remain sessionless")
    if document.get("externalFinancialWritesAllowed"):
        raise Fix44ProjectionError("FIX projector must not admit external writes")

    evidence_sha = _ascii_field(document.get("sourceEvidenceSha256"), name="sourceEvidenceSha256")
    if len(evidence_sha) != 64 or any(c not in "0123456789abcdefABCDEF" for c in evidence_sha):
        raise Fix44ProjectionError("invalid source evidence sha256")

    sender = _ascii_field(document.get("senderCompId"), name="senderCompId")
    tx = _ascii_field(document.get("transactTimeUtc"), name="transactTimeUtc")
    intents = document.get("intents")
    if not isinstance(intents, list) or not intents:
        raise Fix44ProjectionError("intents must be a non-empty list")

    rows = []
    for seq, row in enumerate(intents, start=1):
        if not isinstance(row, dict):
            raise Fix44ProjectionError("each intent must be an object")
        if row.get("ordType") != "MARKET":
            raise Fix44ProjectionError("only MARKET is admitted")
        result = project_new_order_single(
            seq=seq,
            sender_comp_id=sender,
            cl_ord_id=row.get("clOrdId"),
            symbol=row.get("symbol"),
            side=row.get("side"),
            order_qty=row.get("orderQty"),
            time_in_force=row.get("timeInForce"),
            ex_destination=row.get("exDestination"),
            transact_time_utc=tx,
        )
        result.pop("raw")
        rows.append(result)

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.fix44-projection-result",
        "standing": "PASS_BOUNDED_LOCAL_FIX44_TAGVALUE_PROJECTION",
        "purpose": "MECHANICS_ONLY_NON_ECONOMIC",
        "projectionImplementation": "LOCAL_BOUNDED_FIX44_TAGVALUE_PROJECTOR",
        "semanticReference": "FIX Trading Community FIX Latest / FIX Orchestra",
        "legacyWireProfile": "FIX.4.4",
        "quickfixDifferentialReference": {
            "library": "QuickFIX/n",
            "version": "1.14.1",
            "cases": 120,
            "byteExactMatches": 120,
            "mismatches": 0,
        },
        "sourceEvidenceSha256": evidence_sha.lower(),
        "networkSessionEnabled": False,
        "wireFrameComplete": False,
        "bodyLengthAndChecksumPresent": False,
        "brokerCredentialsUsed": False,
        "externalFinancialWritesAttempted": False,
        "projectedIntents": rows,
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        raise SystemExit("usage: python -m ordivon_capital.trading.fix44_projection INPUT OUTPUT")
    input_path, output_path = map(Path, args)
    result = project_document(json.loads(input_path.read_text()))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
