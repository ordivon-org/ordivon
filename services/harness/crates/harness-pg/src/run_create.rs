//! Rust-native immutable Run birth in one PG transaction.
use crate::{
    contract_semantics,
    journal_write::{Admission, WriteError},
    valid_schema,
};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};
use postgres::{Client, Transaction};
const CONTRACT_KIND: &str = "harness-run-contract";
const EVENT_KIND: &str = "ordivon.harness-run-event-payload";

struct Birth<'a> {
    run: &'a str,
    caller: &'a str,
    caller_ref: &'a str,
    at: i64,
    digest: String,
    bytes: Vec<u8>,
    event_id: String,
    payload_digest: String,
    payload: Vec<u8>,
}
fn text<'a>(v: &'a CanonicalDocument, k: &str) -> Result<&'a str, WriteError> {
    v.field(k)
        .and_then(|f| f.as_str())
        .ok_or(WriteError::Invalid("missing Contract identity"))
}
fn prepare(v: &CanonicalDocument) -> Result<Birth<'_>, WriteError> {
    contract_semantics::validate_contract(v).map_err(WriteError::Read)?;
    if v.field("schemaVersion").and_then(|f| f.integer_text()) != Some("2") {
        return Err(WriteError::Invalid("native Run birth requires Contract v2"));
    }
    let run = text(v, "harnessRunId")?;
    let caller = text(v, "callerId")?;
    let caller_ref = text(v, "callerRunRef")?;
    let at = v
        .field("createdAtMs")
        .and_then(|f| f.integer_text())
        .ok_or(WriteError::Invalid("missing createdAtMs"))?
        .parse::<i64>()
        .map_err(|_| WriteError::Invalid("createdAtMs exceeds PG bigint"))?;
    let bytes = canonical_bytes(v);
    let digest = digest_bytes(&bytes);
    let key = CanonicalDocument::object(vec![
        ("harnessRunId".into(), CanonicalDocument::string(run)),
        ("contractDigest".into(), CanonicalDocument::string(&digest)),
    ])?;
    let event_id = format!(
        "event:harness-run-created:{}",
        digest_bytes(&canonical_bytes(&key)).trim_start_matches("sha256:")
    );
    let data = CanonicalDocument::object(vec![
        ("contractDigest".into(), CanonicalDocument::string(&digest)),
        (
            "contractObjectDigest".into(),
            CanonicalDocument::string(&digest),
        ),
        ("callerId".into(), CanonicalDocument::string(caller)),
        ("callerRunRef".into(), CanonicalDocument::string(caller_ref)),
    ])?;
    let payload_doc = CanonicalDocument::object(vec![
        (
            "schemaVersion".into(),
            CanonicalDocument::integer_from_decimal("1")?,
        ),
        ("kind".into(), CanonicalDocument::string(EVENT_KIND)),
        (
            "eventKind".into(),
            CanonicalDocument::string("harness.run-created"),
        ),
        ("data".into(), data),
    ])?;
    let payload = canonical_bytes(&payload_doc);
    let payload_digest = digest_bytes(&payload);
    Ok(Birth {
        run,
        caller,
        caller_ref,
        at,
        digest,
        bytes,
        event_id,
        payload_digest,
        payload,
    })
}
fn store_cas(
    tx: &mut Transaction<'_>,
    digest: &str,
    kind: &str,
    bytes: &[u8],
    at: i64,
) -> Result<(), WriteError> {
    let len = i64::try_from(bytes.len()).map_err(|_| WriteError::Overflow)?;
    tx.execute(
        "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) \
  VALUES($1,$2,$3,$4,$5) ON CONFLICT(digest) DO NOTHING",
        &[&digest, &kind, &len, &bytes, &at],
    )?;
    let row = tx
        .query_opt(
            "SELECT kind,byte_length,content FROM objects WHERE digest=$1",
            &[&digest],
        )?
        .ok_or_else(|| WriteError::Conflict("missing CAS".into()))?;
    if row.get::<_, String>("kind") != kind
        || row.get::<_, i64>("byte_length") != len
        || row.get::<_, Vec<u8>>("content") != bytes
    {
        return Err(WriteError::Conflict(
            "existing immutable CAS bytes or kind changed".into(),
        ));
    }
    Ok(())
}

/// Create a new current Contract v2. An unchanged initial replay is Existing.
/// Changed identity, committed progress, missing Event or altered edges fail closed.
pub fn create_run(
    db: &mut Client,
    schema: &str,
    contract: &CanonicalDocument,
) -> Result<Admission, WriteError> {
    if !valid_schema(schema) {
        return Err(WriteError::Invalid("schema"));
    }
    let n = prepare(contract)?;
    let mut tx = db.transaction()?;
    tx.batch_execute(&format!("SET LOCAL search_path TO {schema}"))?;
    let version: Option<String> = tx
        .query_opt(
            "SELECT value FROM schema_info WHERE key='schema_version'",
            &[],
        )?
        .map(|r| r.get(0));
    if version.as_deref() != Some("1") {
        return Err(WriteError::Invalid("unsupported Harness PG schema"));
    }
    store_cas(&mut tx, &n.digest, CONTRACT_KIND, &n.bytes, n.at)?;
    store_cas(&mut tx, &n.payload_digest, EVENT_KIND, &n.payload, n.at)?;
    let present = tx.query_opt(
        "SELECT contract_digest,contract_object_digest,caller_id,caller_run_ref,status,revision \
   FROM runs WHERE harness_run_id=$1 FOR UPDATE",
        &[&n.run],
    )?;
    if let Some(row) = present {
        if row.get::<_, String>("contract_digest") != n.digest
            || row.get::<_, String>("contract_object_digest") != n.digest
            || row.get::<_, String>("caller_id") != n.caller
            || row.get::<_, String>("caller_run_ref") != n.caller_ref
            || row.get::<_, String>("status") != "created"
            || row.get::<_, i64>("revision") != 1
        {
            return Err(WriteError::Conflict(
                "different or progressed Run identity".into(),
            ));
        }
        let event=tx.query_opt("SELECT harness_run_id,run_revision,event_kind,payload_digest,caused_by_event_id,recorded_at_ms \
      FROM run_events WHERE event_id=$1",&[&n.event_id])?
      .ok_or_else(||WriteError::Conflict("missing created Event".into()))?;
        if event.get::<_, String>("harness_run_id") != n.run
            || event.get::<_, i64>("run_revision") != 1
            || event.get::<_, String>("event_kind") != "harness.run-created"
            || event.get::<_, String>("payload_digest") != n.payload_digest
            || event
                .get::<_, Option<String>>("caused_by_event_id")
                .is_some()
            || event.get::<_, i64>("recorded_at_ms") != n.at
        {
            return Err(WriteError::Conflict("created Event changed".into()));
        }
        let refs = tx.query(
            "SELECT digest,role FROM run_object_refs WHERE event_id=$1",
            &[&n.event_id],
        )?;
        let mut actual: Vec<(String, String)> = refs
            .iter()
            .map(|r| (r.get("digest"), r.get("role")))
            .collect();
        actual.sort();
        let mut expected = vec![
            (n.digest.clone(), "reference".into()),
            (n.payload_digest.clone(), "payload".into()),
        ];
        expected.sort();
        if actual != expected {
            return Err(WriteError::Conflict(
                "created CAS reference edges differ".into(),
            ));
        }
        tx.commit()?;
        return Ok(Admission::Existing);
    }
    tx.execute("INSERT INTO runs(harness_run_id,contract_digest,contract_object_digest,caller_id,caller_run_ref, \
     status,revision,created_at_ms,updated_at_ms) VALUES($1,$2,$3,$4,$5,'created',1,$6,$6)",
    &[&n.run,&n.digest,&n.digest,&n.caller,&n.caller_ref,&n.at])?;
    tx.execute(
        "INSERT INTO run_events(event_id,harness_run_id,run_revision,event_kind,payload_digest, \
     caused_by_event_id,recorded_at_ms) VALUES($1,$2,1,'harness.run-created',$3,NULL,$4)",
        &[&n.event_id, &n.run, &n.payload_digest, &n.at],
    )?;
    for (digest, role) in [(&n.payload_digest, "payload"), (&n.digest, "reference")] {
        tx.execute(
            "INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) VALUES($1,$2,$3,$4)",
            &[&n.run, &n.event_id, digest, &role],
        )?;
    }
    tx.commit()?;
    Ok(Admission::Created)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_document_is_not_a_run() {
        let bad = CanonicalDocument::object(vec![]).unwrap();
        assert!(prepare(&bad).is_err());
    }
}
