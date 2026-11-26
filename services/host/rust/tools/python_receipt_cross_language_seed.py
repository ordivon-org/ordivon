from __future__ import annotations
import json, os, sys
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput, WorkState
from ordivon_host_v2.work_store import WorkStore
from ordivon_host_v2.work_receipt_retention import expand_work_receipts_and_fence
dsn=os.environ["R23_PRIVATE_DSN"]
actor="actor:agent:r23-cross-language"
work="work:r23-cross-language"
legacy=WorkStore(dsn)
compact=WorkStore(dsn,compact_work_receipts=True)
ActorReferenceStore(dsn).declare_actor(ActorRefInput(actor_ref=actor,actor_kind=ActorKind.AGENT),client_request_id="r23:actor")
initial=WorkCreateInput(work_ref=work,kind="test",actor_ref=actor,initial_snapshot=WorkSnapshotInput(objective="synthetic",frontier="r1",established=["repeat","repeat"]))
def commit(store,key,revision):
    return store.commit_snapshot(work,expected_revision=revision,snapshot=WorkSnapshotInput(objective="synthetic",frontier=f"r{revision+1}",established=["a","a","b"]),actor_ref=actor,state=WorkState.OPEN,client_request_id=key)
first=legacy.create_work(initial,client_request_id="r23:legacy")
with psycopg.connect(dsn) as c:
    c.execute("ALTER TABLE command_receipts DROP CONSTRAINT command_receipt_legacy_only")
second=commit(compact,"r23:compact",1)
later=compact.create_work(initial,client_request_id="r23:later")
third=commit(legacy,"r23:head",2)
expected={"legacy":{**first,"admission":"existing"},"compact":{**second,"admission":"existing"},"later":{**later,"admission":"existing"}}
assert legacy.create_work(initial,client_request_id="r23:legacy")==expected["legacy"]
assert commit(legacy,"r23:compact",1)==expected["compact"]
assert legacy.create_work(initial,client_request_id="r23:later")==expected["later"]
with psycopg.connect(dsn,row_factory=dict_row) as c:
    rows=c.execute("SELECT client_request_id,response->>'kind' AS kind,receipt_work_ref,receipt_work_revision FROM command_receipts WHERE client_request_id IN ('r23:legacy','r23:compact','r23:later') ORDER BY client_request_id").fetchall()
assert second["revision"]==later["revision"]==2 and third["revision"]==3
assert [r["kind"] for r in rows]==["ordivon.host-work-receipt-ref-v1","ordivon.host-work-receipt-ref-v1","ordivon.host-work"]
assert rows[0]["receipt_work_revision"]==rows[1]["receipt_work_revision"]==2
print("PYTHON_NATIVE",json.dumps(rows,sort_keys=True),"CURRENT_REVISION",third["revision"])
Path(sys.argv[1]).write_text(json.dumps(expected,sort_keys=True),encoding="utf-8")
