#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sys
import urllib.request
import uuid

URL = "http://127.0.0.1:5678/webhook/ordivon-integration-smoke-v1"
REQUEST_TYPE = "io.ordivon.integration.smoke.request.v1"
RESULT_TYPE = "io.ordivon.integration.result.v1"


def make_event(event_id: str | None = None) -> dict:
    event_id = event_id or str(uuid.uuid4())
    return {
        "specversion": "1.0",
        "id": event_id,
        "source": "urn:ordivon:acceptance:n8n-smoke",
        "type": REQUEST_TYPE,
        "time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "datacontenttype": "application/json",
        "data": {"message": "ordivon-n8n-smoke", "sequence": 1},
    }


def invoke(event: dict, timeout: float = 20.0) -> dict:
    body = json.dumps(event, separators=(",", ":")).encode()
    request = urllib.request.Request(
        URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if payload.get("specversion") != "1.0":
        raise RuntimeError(f"bad result specversion: {payload!r}")
    if payload.get("type") != RESULT_TYPE:
        raise RuntimeError(f"bad result type: {payload!r}")
    if payload.get("correlationid") != event["id"]:
        raise RuntimeError(f"correlation mismatch: {payload!r}")
    echoed = payload.get("data", {}).get("echoedPayload", {})
    if echoed.get("payload") != event.get("data"):
        raise RuntimeError(f"payload mismatch: {payload!r}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", dest="event_id")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    event = make_event(args.event_id)
    result = invoke(event)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
