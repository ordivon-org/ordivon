#!/usr/bin/python3
"""Bounded additive pgBackRest transition, not a scheduler or expiry engine."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CALENDAR = ZoneInfo("Asia/Shanghai")
STANZA = "ordivon"
REPO = Path("/var/lib/pgbackrest")
COMMAND = (
    "/usr/bin/pgbackrest", "--config=/etc/pgbackrest/pgbackrest.conf",
    "--stanza=ordivon", "--repo=1",
)
ENV = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}
LABEL = re.compile(r"[0-9]{8}-[0-9]{6}F(?:_[0-9]{8}-[0-9]{6}[DI])?")
GIB = 1 << 30


class Unqualified(ValueError):
    """The observed native state does not qualify a transition."""


def require(condition, reason):
    if not condition:
        raise Unqualified(reason)


def exact_int(value):
    return type(value) is int


def valid_inventory(document, now):
    require(isinstance(document, list) and len(document) == 1, "one stanza required")
    stanza = document[0]
    require(stanza["name"] == STANZA, "unexpected stanza")
    require(type(stanza["status"]["code"]) is int and stanza["status"]["code"] == 0,
            "stanza status not ok")
    locks = stanza["status"]["lock"]
    require(all(locks[k]["held"] is False for k in ("backup", "restore")),
            "native lock not clear")
    repos = stanza["repo"]
    require(len(repos) == 1 and repos[0]["key"] == 1
            and repos[0]["status"]["code"] == 0, "repo1 not qualified")
    databases = stanza["db"]
    require(len(databases) == 1 and databases[0]["repo-key"] == 1,
            "mixed database history requires owner reconciliation")
    db = {"id": databases[0]["id"], "repo-key": 1}
    require(exact_int(db["id"]) and db["id"] > 0
            and exact_int(databases[0]["system-id"]) and databases[0]["system-id"] > 0,
            "invalid database identity")
    backups = stanza["backup"]
    require(isinstance(backups, list) and bool(backups), "no retained backup")
    seen = {}
    last_stop = 0
    latest_full = None
    latest_diff = None
    for b in backups:
        label, kind = b["label"], b["type"]
        require(isinstance(label, str) and LABEL.fullmatch(label) and label not in seen,
                "invalid or duplicate backup label")
        require(b["error"] is False and b["database"] == db,
                "backup error or database mismatch")
        start, stop = b["timestamp"]["start"], b["timestamp"]["stop"]
        require(exact_int(start) and exact_int(stop)
                and last_stop <= start <= stop <= now.timestamp(),
                "unordered, incomplete or future backup")
        require(exact_int(b["info"]["size"]) and b["info"]["size"] > 0,
                "unknown backup size")
        if kind == "full":
            require(label.endswith("F") and "_" not in label
                    and b["prior"] is None and b["reference"] is None,
                    "invalid full identity")
            latest_full, latest_diff = b, None
        else:
            require(kind in ("diff", "incr") and latest_full is not None,
                    "missing full base")
            base = latest_full["label"]
            require(label.startswith(base + "_")
                    and label.endswith("D" if kind == "diff" else "I"),
                    "wrong generation or backup type")
            refs = b["reference"]
            require(isinstance(refs, list) and all(isinstance(x, str) for x in refs)
                    and len(set(refs)) == len(refs)
                    and all(x in seen and x.split("_")[0] == base for x in refs),
                    "invalid references")
            # A backup may contain no referenced files; its prior still
            # establishes the generation. Never infer coverage from this list.
            prior = b["prior"]
            require(prior in seen and prior.split("_")[0] == base,
                    "missing or cross-generation prior")
            if kind == "diff":
                require(prior == base, "differential prior must be full")
                latest_diff = b
        seen[label] = b
        last_stop = stop
    require(latest_full is not None, "full base absent")
    return backups, latest_full, latest_diff


def choose_kind(document, now):
    require(now.utcoffset() is not None, "timezone required")
    backups, full, diff = valid_inventory(document, now)
    age = (now.astimezone(CALENDAR).date() -
           datetime.fromtimestamp(full["timestamp"]["stop"], CALENDAR).date()).days
    require(age >= 0, "future calendar age")
    kind = "full" if age >= 7 else "diff" if age >= 3 and diff is None else "incr"
    return {"type": kind, "full": full["label"], "age_days": age,
            "latest": backups[-1]["label"], "size": backups[-1]["info"]["size"]}


def transition_args(plan, now, deadline, free, available):
    require(deadline.utcoffset() is not None and now < deadline <= now + timedelta(days=14),
            "transition deadline absent, elapsed or too distant")
    require(free >= 3 * plan["size"] + 8 * GIB and available >= GIB,
            "insufficient transition capacity")
    return (*COMMAND, "--type=" + plan["type"], "--no-expire-auto",
            "--process-max=1", "--log-level-console=info", "backup")


def native_info():
    result = subprocess.run((*COMMAND, "--output=json", "info"), env=ENV,
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout)


def mem_available():
    line = next(x for x in Path("/proc/meminfo").read_text().splitlines()
                if x.startswith("MemAvailable:"))
    return int(line.split()[1]) * 1024


def check_additive(before, after, plan, now):
    old, _, _ = valid_inventory(before, now)
    new, _, _ = valid_inventory(after, now)
    require(before[0]["db"] == after[0]["db"], "database identity changed")
    require(len(new) == len(old) + 1 and new[:-1] == old,
            "old inventory changed or concurrent result ambiguous")
    require(new[-1]["type"] == plan["type"], "native selected type differs")
    if plan["type"] == "incr":
        require(new[-1]["prior"] == plan["latest"], "increment prior changed")
    return new[-1]["label"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-until", help="explicit UTC/offset transition deadline")
    args = parser.parse_args(argv)
    try:
        now = datetime.now(UTC)
        before = native_info()
        plan = choose_kind(before, now)
        print(json.dumps({"standing": "PLAN", **plan}, sort_keys=True), flush=True)
        if args.execute_until is None:
            return 0
        deadline = datetime.fromisoformat(args.execute_until)
        transition_args(plan, now, deadline, shutil.disk_usage(REPO).free,
                        mem_available())
        # This is a separate observation, not a transactional fence. The
        # native backup lock is authoritative; post-check detects drift.
        observed = native_info()
        dispatch_now = datetime.now(UTC)
        require(choose_kind(observed, dispatch_now) == plan
                and observed[0]["backup"] == before[0]["backup"]
                and observed[0]["db"] == before[0]["db"],
                "inventory or calendar changed before dispatch")
        command = transition_args(plan, dispatch_now, deadline,
                                  shutil.disk_usage(REPO).free, mem_available())
        subprocess.run(command, env=ENV, check=True)
        after = native_info()
        label = check_additive(before, after, plan, datetime.now(UTC))
        print(json.dumps({"standing": "ADDITIVE_BACKUP_OBSERVED", "label": label}),
              flush=True)
        return 0
    except (KeyError, IndexError, AttributeError, TypeError, ValueError, OSError,
            StopIteration, subprocess.SubprocessError) as error:
        print(json.dumps({"standing": "UNKNOWN_OR_FAILED", "reason": str(error)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
