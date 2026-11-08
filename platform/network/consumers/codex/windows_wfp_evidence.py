#!/usr/bin/env python3
"""Classify bounded native Windows WFP 5156/5157 XML without publishing endpoints.

Input is a JSON envelope with source Security-event XML from Windows' native
Get-WinEvent. This is a read-only evidence refinement, not a WFP controller.
An event-free trace NEVER establishes that the application did not bypass VPN.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
SUPPORTED = {5156: "ALLOWED", 5157: "BLOCKED"}
DIRECTIONS = {
    "%%14592": "INBOUND", "%%14593": "OUTBOUND", "%%14594": "LOOPBACK",
    "Inbound": "INBOUND", "Outbound": "OUTBOUND", "Loopback": "LOOPBACK",
}
TARGETS = {"codex.exe", "chatgpt.exe", "codex-code-mode-host.exe",
           "codex-computer-use-swift.exe"}
MAX_EVENTS = 5000


def address_class(value: str) -> str:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return "UNKNOWN"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.is_multicast:
        return "MULTICAST"
    if str(ip) == "255.255.255.255":
        return "BROADCAST"
    if ip.is_loopback:
        return "LOOPBACK"
    if ip.is_link_local:
        return "LINK_LOCAL"
    if ip.is_unspecified:
        return "UNSPECIFIED"
    if ip.is_global:
        return "PUBLIC_UNICAST"
    if ip.is_private:
        return "PRIVATE_UNICAST"
    return "NONPUBLIC_OTHER"


def _time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp must include UTC offset")
    return dt.astimezone(timezone.utc)


def decode_event(raw: str) -> dict:
    if not isinstance(raw, str) or len(raw) > 25000:
        raise ValueError("Missing or oversized WFP event")
    root = ET.fromstring(raw)
    if root.tag != "{%s}Event" % NS["e"]:
        raise ValueError("Not a native Windows event")
    path = lambda name: root.findtext("e:System/e:" + name, namespaces=NS)
    if path("Channel") != "Security":
        raise ValueError("Unexpected Windows event channel")
    provider = root.find("e:System/e:Provider", NS)
    if provider is None or provider.get("Name") != "Microsoft-Windows-Security-Auditing":
        raise ValueError("Unexpected Windows event provider")
    event_id = int(path("EventID") or 0)
    if event_id not in SUPPORTED:
        raise ValueError("Not a WFP connection allow/block event")
    created = root.find("e:System/e:TimeCreated", NS)
    if created is None:
        raise ValueError("Missing WFP timestamp")
    at = _time(created.get("SystemTime") or "")
    record = int(path("EventRecordID") or 0)
    if record < 1:
        raise ValueError("Invalid Windows event record ID")
    fields = {}
    for entry in root.findall("e:EventData/e:Data", NS):
        if entry.get("Name"):
            fields[entry.get("Name")] = entry.text or ""
    required = ("ProcessID", "Application", "Direction",
                "DestAddress", "DestPort", "Protocol")
    if any(not fields.get(k) for k in required):
        raise ValueError("Incomplete WFP connection event")
    app = fields["Application"].replace("\\", "/").split("/")[-1].casefold()
    try:
        pid = int(fields["ProcessID"], 0)
        dest_port = int(fields["DestPort"])
        protocol = int(fields["Protocol"])
    except ValueError as exc:
        raise ValueError("Invalid WFP connection scalar") from exc
    if pid < 0 or not 0 <= dest_port <= 65535:
        raise ValueError("Invalid PID or port")
    direction = DIRECTIONS.get(fields["Direction"], "UNKNOWN")
    return {
        "id": event_id, "recordId": record, "at": at,
        "process": app, "pid": pid, "protocol": protocol,
        "direction": direction, "destination": address_class(fields["DestAddress"]),
        "port": dest_port,
    }


def classify(event: dict, proxy_port: int = 19781) -> str:
    if event["direction"] != "OUTBOUND":
        return "NON_OUTBOUND"
    if event["id"] == 5157:
        return "BLOCKED_OUTBOUND"
    if event["id"] != 5156:
        return "UNKNOWN"
    if event["destination"] == "LOOPBACK" and event["port"] == proxy_port:
        return "PROXY_CONNECTION_ALLOWED"
    if event["destination"] == "PUBLIC_UNICAST":
        # This is a counterexample to strict proxy-only *connection* routing,
        # not proof of a completed application request or unauthorized policy.
        return "PUBLIC_UNICAST_CONNECTION_ALLOWED"
    if event["destination"] == "UNKNOWN":
        return "UNKNOWN_DESTINATION"
    return "NONPUBLIC_CONNECTION_ALLOWED"


def summarize(envelope: dict) -> dict:
    if not isinstance(envelope, dict):
        raise ValueError("Invalid evidence envelope")
    raw = envelope.get("events")
    if not isinstance(raw, list) or len(raw) > MAX_EVENTS:
        raise ValueError("WFP evidence missing or exceeds read budget")
    start = _time(envelope["windowStartUtc"])
    end = _time(envelope["windowEndUtc"])
    if end <= start or (end - start).total_seconds() > 120:
        raise ValueError("Unbounded or invalid WFP window")
    result = defaultdict(Counter)
    counted = 0
    seen = set()
    for xml in raw:
        event = decode_event(xml)
        if not start <= event["at"] <= end:
            raise ValueError("WFP event outside declared window")
        if event["recordId"] in seen:
            raise ValueError("Duplicate WFP record ID")
        seen.add(event["recordId"])
        if event["process"] not in TARGETS:
            continue
        counted += 1
        category = classify(event)
        result[event["process"]][category] += 1
        if event["id"] == 5157 and event["destination"] == "MULTICAST":
            result[event["process"]]["BLOCKED_MULTICAST"] += 1
        if event["protocol"] == 17:
            result[event["process"]]["UDP_EVENTS"] += 1
        if event["destination"] == "PUBLIC_UNICAST":
            result[event["process"]]["PUBLIC_ADDRESS_EVENTS"] += 1
    sensor_claim = envelope.get("auditEnabledDuringWindow") is True
    complete_claim = envelope.get("captureComplete") is True and len(raw) < MAX_EVENTS
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.windows-wfp-bounded-connection-evidence",
        "standing": "SAMPLED_EVENTS" if sensor_claim and complete_claim and counted
                    else "UNKNOWN",
        "sensorClaimed": sensor_claim, "readCompleteClaimed": complete_claim,
        "windowSeconds": (end-start).total_seconds(),
        "inputEventCount": len(raw), "targetEventCount": counted,
        "perProcess": {k: dict(sorted(v.items())) for k, v in sorted(result.items())},
        "unproved": [
            "WFP audit policy and OS log completeness independently verified",
            "all unseen, dropped, prior or future process traffic",
            "process start generation and actual application request correlation",
            "VPN Carrier packet-level same-request identity",
            "non-WFP IPv4/IPv6 DNS, QUIC or kernel bypass impossibility",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None,
                        help="JSON evidence envelope; stdin when omitted")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8")
                      if args.input else sys.stdin.read())
    print(json.dumps(summarize(data), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
