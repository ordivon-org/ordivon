#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sys
import urllib.request
import uuid

DEFAULT_URL = "http://127.0.0.1:5678/webhook/ordivon-discord-research-v0"
REQUEST_TYPE = "io.ordivon.research.community.discord.search.request.v1"
RESULT_TYPE = "io.ordivon.research.community.discord.search.result.v1"
KNOWN_STATUSES = {
    "OK",
    "INDEXING_RETRY",
    "RATE_LIMITED",
    "DENIED",
    "PROVIDER_REQUEST_REJECTED",
    "NOT_FOUND",
    "PROVIDER_UNAVAILABLE",
    "UNKNOWN",
}


def make_event(args: argparse.Namespace) -> dict:
    data: dict = {
        "authorityRef": args.authority_ref,
        "guildId": args.guild_id,
        "channelIds": args.channel_id,
        "content": args.content,
        "limit": args.limit,
        "offset": args.offset,
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
        "includeNsfw": False,
    }
    if args.author_id:
        data["authorIds"] = args.author_id
    if args.has:
        data["has"] = args.has
    return {
        "specversion": "1.0",
        "id": args.event_id or str(uuid.uuid4()),
        "source": "urn:ordivon:research:discord:v0:invoker",
        "type": REQUEST_TYPE,
        "time": dt.datetime.now(dt.UTC).isoformat(),
        "datacontenttype": "application/json",
        "data": data,
    }


def invoke(url: str, event: dict, timeout: float) -> dict:
    body = json.dumps(event, separators=(",", ":")).encode()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if payload.get("specversion") != "1.0":
        raise RuntimeError(f"bad result specversion: {payload!r}")
    if payload.get("type") != RESULT_TYPE:
        raise RuntimeError(f"bad result type: {payload!r}")
    if payload.get("correlationid") != event["id"]:
        raise RuntimeError(f"correlation mismatch: {payload!r}")
    status = payload.get("data", {}).get("status")
    if status not in KNOWN_STATUSES:
        raise RuntimeError(f"unknown contract status: {payload!r}")
    if payload.get("data", {}).get("externalEffectPerformed") is not False:
        raise RuntimeError(f"unexpected Discord effect claim: {payload!r}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--authority-ref", required=True)
    parser.add_argument("--guild-id", required=True)
    parser.add_argument("--channel-id", action="append", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--author-id", action="append")
    parser.add_argument("--has", action="append")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--sort-by", choices=("timestamp", "relevance"), default="relevance")
    parser.add_argument("--sort-order", choices=("asc", "desc"), default="desc")
    parser.add_argument("--id", dest="event_id")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--require-ok", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    event = make_event(args)
    result = invoke(args.url, event, args.timeout)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    if args.require_ok and result["data"]["status"] != "OK":
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
