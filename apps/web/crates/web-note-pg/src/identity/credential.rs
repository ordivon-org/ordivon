use super::{
    Credential, audit, deferred, rows::CredentialRow, safe, unknown, verify_unique_audit,
    write_audit,
};
use crate::{
    OwnerError, PgNoteStore,
    owner_error::{db, one},
};
use serde::Serialize;
use tokio_postgres::Transaction;
use uuid::Uuid;
pub(super) async fn read(tx: &Transaction<'_>, id: &str) -> Result<CredentialRow, OwnerError> {
    let row = tx
        .query_opt(
            "SELECT * FROM webauthn_credentials WHERE credential_id=$1 FOR UPDATE NOWAIT",
            &[&id],
        )
        .await
        .map_err(|e| db("credential lock", e))?
        .ok_or(OwnerError::CredentialNotFound)?;
    CredentialRow::read(&row)
}
impl PgNoteStore {
    /// Public key and metadata supplied only after trusted registration ceremony.
    pub async fn register_credential(
        &self,
        c: &Credential,
        audit_id: Uuid,
    ) -> Result<(), OwnerError> {
        if c.revoked_at.is_some() || c.created_at != c.last_used_at || c.device_type.contains('\0')
        {
            return Err(OwnerError::Invalid);
        }
        let expected = CredentialRow {
            credential_id: c.credential_id.clone(),
            principal_id: c.principal_id.clone(),
            public_key: c.public_key.clone(),
            counter: c.counter,
            transports_json: serde_json::to_string(&c.transports)
                .map_err(|_| OwnerError::Invalid)?,
            device_type: c.device_type.clone(),
            backed_up: i64::from(c.backed_up),
            created_at: c.created_at,
            last_used_at: c.last_used_at,
            revoked_at: None,
        };
        expected.view().map_err(|_| OwnerError::Invalid)?;
        #[derive(Serialize)]
        #[serde(rename_all = "camelCase")]
        struct Detail<'a> {
            device_type: &'a str,
            backed_up: bool,
        }
        let a = audit(
            audit_id,
            &c.principal_id,
            "credential.registered",
            "webauthn-credential",
            &c.credential_id,
            serde_json::to_string(&Detail {
                device_type: &c.device_type,
                backed_up: c.backed_up,
            })
            .map_err(|_| OwnerError::Invalid)?,
            c.created_at,
        );
        self.owner_write(
            |e| unknown("credential-register", &a.event_id, e),
            async |tx| {
                one(
                    tx.execute(
                        "INSERT INTO webauthn_credentials VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,NULL)",
                        &[
                            &expected.credential_id,
                            &expected.principal_id,
                            &expected.public_key,
                            &expected.counter,
                            &expected.transports_json,
                            &expected.device_type,
                            &expected.backed_up,
                            &expected.created_at,
                            &expected.last_used_at,
                        ],
                    )
                    .await
                    .map_err(|e| db("credential insert", e))?,
                    "credential",
                )?;
                write_audit(tx, &a).await?;
                deferred(tx).await?;
                if read(tx, &c.credential_id).await? != expected {
                    return Err(OwnerError::Mismatch("credential"));
                }
                verify_unique_audit(tx, &a).await?;
                Ok(())
            },
        )
        .await
    }
    pub async fn get_active_credential(&self, id: &str) -> Result<Credential, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let row = lease
            .client()
            .query_opt(
                "SELECT * FROM webauthn_credentials WHERE credential_id=$1 AND revoked_at IS NULL",
                &[&id],
            )
            .await
            .map_err(|e| db("credential read", e))?
            .ok_or(OwnerError::CredentialNotFound)?;
        let c = CredentialRow::read(&row)?.view()?;
        lease.reusable();
        Ok(c)
    }
    pub async fn list_credentials(&self, principal: &str) -> Result<Vec<Credential>, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let rows=lease.client().query("SELECT * FROM webauthn_credentials WHERE principal_id=$1 ORDER BY created_at,credential_id",&[&principal]).await.map_err(|e|db("credential list",e))?;
        let result = rows
            .iter()
            .map(|r| CredentialRow::read(r)?.view())
            .collect::<Result<Vec<_>, _>>()?;
        lease.reusable();
        Ok(result)
    }
    /// Caller owns a verified assertion and the exact credential pre-state.
    /// The WebAuthn verifier decides whether a counter is acceptable, including
    /// authenticators that always report zero. Persistence cannot reverify it.
    pub async fn advance_credential(
        &self,
        prior: &Credential,
        new_counter: i64,
        now: i64,
    ) -> Result<Credential, OwnerError> {
        if !(0..=i64::from(u32::MAX)).contains(&new_counter) || !safe(now) {
            return Err(OwnerError::Invalid);
        }
        self.owner_write(
            |e| unknown("credential-advance", &prior.credential_id, e),
            async |tx| {
                let expected = advance_in_tx(tx, prior, new_counter, now).await?;
                deferred(tx).await?;
                if read(tx, &prior.credential_id).await? != expected {
                    return Err(OwnerError::Mismatch("credential counter"));
                }
                expected.view()
            },
        )
        .await
    }
}

pub(super) async fn advance_in_tx(
    tx: &Transaction<'_>,
    prior: &Credential,
    new_counter: i64,
    now: i64,
) -> Result<CredentialRow, OwnerError> {
    if !(0..=i64::from(u32::MAX)).contains(&new_counter) || !safe(now) {
        return Err(OwnerError::Invalid);
    }
    let mut expected = read(tx, &prior.credential_id).await?;
    if expected.view()? != *prior || prior.revoked_at.is_some() || now < prior.last_used_at {
        return Err(OwnerError::CredentialConflict);
    }
    // An unchanged counter at the same timestamp is not an operation receipt.
    // Challenge single consumption must be composed by the trusted caller.
    one(tx.execute("UPDATE webauthn_credentials SET counter=$2,last_used_at=$3 WHERE credential_id=$1 AND counter=$4 AND last_used_at=$5 AND revoked_at IS NULL",&[&prior.credential_id,&new_counter,&now,&prior.counter,&prior.last_used_at]).await.map_err(|e|db("credential advance",e))?,"credential counter")?;
    expected.counter = new_counter;
    expected.last_used_at = now;
    Ok(expected)
}
