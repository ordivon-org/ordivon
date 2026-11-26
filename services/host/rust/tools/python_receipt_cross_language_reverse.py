"""Independent Python oracle; run only against the disposable native test database."""
import json,os,sys
from pathlib import Path
import psycopg
from ordivon_host_v2.work_store import WorkStore
from ordivon_host_v2.work_inputs import WorkCreateInput,WorkSnapshotInput
from ordivon_host_v2.work_receipt_retention import expand_work_receipts_and_fence
from psycopg.rows import dict_row
dsn=os.environ["R23_PRIVATE_DSN"]
value=WorkCreateInput(work_ref="work:r23-cross-language",kind="test",actor_ref="actor:agent:r23-cross-language",initial_snapshot=WorkSnapshotInput(objective="synthetic",frontier="r1",established=["repeat","repeat"]))
got=WorkStore(dsn).create_work(value,client_request_id="r23:rust-legacy")
assert got==json.loads(Path(sys.argv[1]).read_text()),"Rust legacy writer -> Python reader differs"
with psycopg.connect(dsn,row_factory=dict_row) as conn:
    row=conn.execute("SELECT response->>'kind' AS kind,receipt_work_ref,receipt_work_revision FROM command_receipts WHERE client_request_id='r23:rust-legacy'").fetchone()
    assert row=={"kind":"ordivon.host-work","receipt_work_ref":None,"receipt_work_revision":None}
    assert expand_work_receipts_and_fence(conn)==2
print("RUST_LEGACY_TO_PYTHON_EQUAL and native rollback expanded 2 exact pinned roots")
