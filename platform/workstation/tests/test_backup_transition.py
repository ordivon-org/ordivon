"""Schedule contract: independent finite calendar model and fail-closed effects."""
from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from itertools import combinations

import pytest

from postgresql import backup_transition as policy

BASE = datetime(2026, 11, 26, 4, tzinfo=policy.CALENDAR)
SIZE = 7_000_000_000
DB = {"id": 1, "repo-key": 1}


def entry(day, kind, base=None, prior=None):
    start = BASE + timedelta(days=day)
    suffix = {"full": "F", "diff": "D", "incr": "I"}[kind]
    label = start.strftime("%Y%m%d-%H%M%S") + suffix
    if base:
        label = base + "_" + label
    return {"label": label, "type": kind, "error": False, "database": dict(DB),
            "timestamp": {"start": int(start.timestamp()), "stop": int(start.timestamp())+60},
            "info": {"size": SIZE}, "prior": prior,
            "reference": [base] if base else None}


def inventory():
    return [{"name": "ordivon", "status": {"code": 0, "lock": {
        "backup": {"held": False}, "restore": {"held": False}}},
        "repo": [{"key": 1, "status": {"code": 0}}],
        "db": [{**DB, "system-id": 7683346773935274339}], "backup": [entry(0, "full")]}]


def at(day):
    return BASE + timedelta(days=day, hours=1)


def append(doc, day, kind):
    backups = doc[0]["backup"]
    if kind == "full":
        new = entry(day, kind)
    else:
        base = next(b["label"] for b in reversed(backups) if b["type"] == "full")
        new = entry(day, kind, base, base if kind == "diff" else backups[-1]["label"])
    backups.append(new)


@pytest.mark.parametrize("day,expected", [(1,"incr"),(2,"incr"),(3,"diff"),
                                          (6,"diff"),(7,"full"),(14,"full")])
def test_age_threshold(day, expected):
    assert policy.choose_kind(inventory(), at(day))["type"] == expected


def test_successful_diff_suppresses_duplicate_diff():
    doc = inventory()
    append(doc, 3, "diff")
    assert policy.choose_kind(doc, at(4))["type"] == "incr"


def test_explicit_calendar_not_utc_date():
    # UTC is still Nov26, but local date is Nov27.
    now = datetime(2026,11,26,16,1,tzinfo=UTC)
    assert policy.choose_kind(inventory(), now)["age_days"] == 1


def test_all_470_missed_calendar_schedules():
    count = 0
    for n in range(4):
        for missing in combinations(range(1,15),n):
            doc = inventory()
            last_full = 0
            diff_done = False
            for d in range(1,15):
                if d in missing:
                    continue
                # Independent schedule obligations, not a copy of native metadata parsing.
                actual = policy.choose_kind(doc, at(d))["type"]
                if d-last_full >= 7:
                    assert actual == "full"
                    last_full, diff_done = d, False
                elif d-last_full >= 3 and not diff_done:
                    assert actual == "diff"
                    diff_done = True
                else:
                    assert actual == "incr"
                append(doc,d,actual)
                assert d-last_full <= 6
            count += 1
    assert count == 470


@pytest.mark.parametrize("case", ["lock","restore","repo","mixed-db","missing-base",
    "failed","duplicate","future","bad-prior","cross-reference","wrong-type","wrong-db",
    "unknown-size","bad-order"])
def test_native_inventory_fails_closed(case):
    doc = inventory()
    append(doc, 1, "incr")
    s=doc[0]; b=s["backup"][-1]
    if case=="lock": s["status"]["lock"]["backup"]["held"]=True
    elif case=="restore": s["status"]["lock"]["restore"]["held"]=None
    elif case=="repo": s["repo"][0]["status"]["code"]=1
    elif case=="mixed-db": s["db"].append({"id":2,"repo-key":1})
    elif case=="missing-base": s["backup"].pop(0)
    elif case=="failed": b["error"]=None
    elif case=="duplicate": s["backup"].append(deepcopy(b))
    elif case=="future": b["timestamp"]["stop"]=int(at(3).timestamp())
    elif case=="bad-prior": b["prior"]="missing"
    elif case=="cross-reference": b["reference"]=["missing"]
    elif case=="wrong-type": b["type"]="diff"
    elif case=="wrong-db": b["database"]["id"]=2
    elif case=="unknown-size": b["info"]["size"]=None
    elif case=="bad-order": b["timestamp"]["start"]=0
    with pytest.raises(policy.Unqualified):
        policy.choose_kind(doc, at(2))


@pytest.mark.parametrize("case", ["expired","far","disk","memory"])
def test_capacity_and_deadline(case):
    now=at(1); plan=policy.choose_kind(inventory(),now)
    deadline=now+timedelta(days=7);free=100*policy.GIB;memory=2*policy.GIB
    if case=="expired": deadline=now
    elif case=="far": deadline=now+timedelta(days=15)
    elif case=="disk": free=1
    elif case=="memory": memory=1
    with pytest.raises(policy.Unqualified):
        policy.transition_args(plan,now,deadline,free,memory)


def test_execution_args_have_no_expiry_or_shell():
    now=at(1); plan=policy.choose_kind(inventory(),now)
    args=policy.transition_args(plan,now,now+timedelta(days=7),100*policy.GIB,2*policy.GIB)
    assert args[-5:]==("--type=incr","--no-expire-auto","--process-max=1",
                       "--log-level-console=info","backup")


@pytest.mark.parametrize("case", ["deleted","changed","extra","wrong-kind","wrong-prior"])
def test_native_postcondition_detects_drift(case):
    before=inventory();append(before,1,"incr")
    now=at(2);plan=policy.choose_kind(before,now)
    after=deepcopy(before);append(after,2,"incr")
    assert policy.check_additive(before,after,plan,now)==after[0]["backup"][-1]["label"]
    if case=="deleted":after[0]["backup"].pop(0)
    elif case=="changed":after[0]["backup"][0]["info"]["size"]+=1
    elif case=="extra":append(after,3,"incr")
    elif case=="wrong-kind":
        after=deepcopy(before);append(after,2,"diff")
    elif case=="wrong-prior":after[0]["backup"][-1]["prior"]=before[0]["backup"][0]["label"]
    with pytest.raises(policy.Unqualified):
        policy.check_additive(before,after,plan,now)


def test_plan_never_dispatches(monkeypatch,capfd):
    # Fresh timestamps relative to real clock, not the wall time of the test runner.
    doc=inventory()
    shift=int(datetime.now(UTC).timestamp())-doc[0]["backup"][0]["timestamp"]["stop"]-60
    for k in ("start","stop"):
        doc[0]["backup"][0]["timestamp"][k]+=shift
    monkeypatch.setattr(policy,"native_info",lambda:doc)
    def forbidden(*args,**kwargs):
        pytest.fail("plan dispatched a native effect")
    monkeypatch.setattr(policy.subprocess,"run",forbidden)
    assert policy.main([])==0
    assert '"standing": "PLAN"' in capfd.readouterr().out


@pytest.mark.parametrize("case", ["pass","changed","native-failed","bad-post"])
def test_execution_boundary(monkeypatch, case, capfd):
    import subprocess
    from types import SimpleNamespace
    now=datetime.now(UTC)
    doc=inventory()
    start=doc[0]["backup"][0]["timestamp"]["start"]
    shift=int(now.timestamp())-start-120
    for k in ("start","stop"):
        doc[0]["backup"][0]["timestamp"][k]+=shift
    # A distinct increment in the same generation, completed before the test.
    after=deepcopy(doc)
    base=doc[0]["backup"][0]["label"]
    new=entry(1,"incr",base,base)
    new["timestamp"]={"start":int(now.timestamp())-30,"stop":int(now.timestamp())-20}
    after[0]["backup"].append(new)
    observed=deepcopy(doc)
    if case=="changed":
        observed[0]["backup"][0]["info"]["size"]+=1
    if case=="bad-post":
        after[0]["backup"][0]["info"]["size"]+=1
    replies=iter((doc,observed,after))
    monkeypatch.setattr(policy,"native_info",lambda:next(replies))
    monkeypatch.setattr(policy.shutil,"disk_usage",lambda _:SimpleNamespace(free=100*policy.GIB))
    monkeypatch.setattr(policy,"mem_available",lambda:2*policy.GIB)
    calls=[]
    def dispatch(argv, **kwargs):
        calls.append((argv,kwargs))
        if case=="native-failed":
            raise subprocess.CalledProcessError(7,argv)
    monkeypatch.setattr(policy.subprocess,"run",dispatch)
    result=policy.main(["--execute-until",(now+timedelta(days=7)).isoformat()])
    assert result==(0 if case=="pass" else 1)
    assert len(calls)==(0 if case=="changed" else 1)
    if calls:
        assert "--no-expire-auto" in calls[0][0] and "--repo=1" in calls[0][0]
        assert calls[0][1]=={"env":policy.ENV,"check":True}
    output=capfd.readouterr().out
    assert ("ADDITIVE_BACKUP_OBSERVED" in output)==(case=="pass")


def test_no_replacement_of_current_timer_and_native_service():
    from pathlib import Path

    import yaml
    root=Path(__file__).resolve().parents[1]
    tasks=yaml.safe_load((root/"ansible/postgresql-backup.yml").read_text())[0]["tasks"]
    matches=[t["ansible.builtin.copy"] for t in tasks
             if t.get("ansible.builtin.copy",{}).get("dest")==
             "/usr/local/bin/ordivon-pgbackrest-transition"]
    assert len(matches)==1 and matches[0]["owner"]=="root" and matches[0]["mode"]=="0755"
    assert "--type=full" in (root/"postgresql/ordivon-postgresql-backup.service").read_text()
    assert "transition" not in (root/"postgresql/ordivon-postgresql-backup.service").read_text()
    assert "repo1-retention-full=7" in (root/"postgresql/pgbackrest.conf.j2").read_text()
