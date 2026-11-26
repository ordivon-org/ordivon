use super::{
    Principal, audit, deferred, rows::PrincipalRow, safe, unknown, valid_text, verify_unique_audit,
    write_audit,
};
use crate::{
    OwnerError, PgNoteStore,
    owner_error::{db, one},
};
use tokio_postgres::Transaction;
use uuid::Uuid;

// Shared principal fence: session writers take SHARE, bulk revoke takes
// NO KEY UPDATE; compatible with unrelated FK KEY SHARE. All writers cooperate.
pub(super) async fn lock_principal(
    tx: &Transaction<'_>,
    id: &str,
    bulk: bool,
) -> Result<PrincipalRow, OwnerError> {
    let sql = if bulk {
        "SELECT * FROM principals WHERE principal_id=$1 FOR NO KEY UPDATE NOWAIT"
    } else {
        "SELECT * FROM principals WHERE principal_id=$1 FOR SHARE NOWAIT"
    };
    let row = tx
        .query_opt(sql, &[&id])
        .await
        .map_err(|e| db("principal fence", e))?
        .ok_or(OwnerError::PrincipalNotFound)?;
    PrincipalRow::read(&row)
}
impl PgNoteStore {
    pub async fn ensure_principal(
        &self,
        p: &Principal,
        audit_id: Uuid,
        now: i64,
    ) -> Result<Principal, OwnerError> {
        if !valid_text(&p.principal_id)
            || !valid_text(&p.user_name)
            || p.display_name.contains('\0')
            || !safe(now)
        {
            return Err(OwnerError::Invalid);
        }
        let expected = PrincipalRow {
            principal_id: p.principal_id.clone(),
            user_name: p.user_name.clone(),
            display_name: p.display_name.clone(),
            created_at: now,
        };
        let a = audit(
            audit_id,
            &p.principal_id,
            "principal.created",
            "principal",
            &p.principal_id,
            "{}".into(),
            now,
        );
        self.owner_write(
            |e| unknown("principal-create", &a.event_id, e),
            async |tx| {
                // Existing identity is not a new creation and has no new audit.
                let n = tx
                    .execute(
                        "INSERT INTO principals VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                        &[&p.principal_id, &p.user_name, &p.display_name, &now],
                    )
                    .await
                    .map_err(|e| db("principal insert", e))?;
                let row = match lock_principal(tx, &p.principal_id, false).await {
                    Ok(row) => row,
                    Err(OwnerError::PrincipalNotFound) if n == 0 => {
                        if tx
                            .query_opt(
                                "SELECT principal_id FROM principals WHERE user_name=$1",
                                &[&p.user_name],
                            )
                            .await
                            .map_err(|e| db("principal username conflict", e))?
                            .is_some()
                        {
                            return Err(OwnerError::PrincipalConflict);
                        }
                        return Err(OwnerError::Write("principal"));
                    }
                    Err(e) => return Err(e),
                };
                if row.view()? != *p {
                    return Err(OwnerError::PrincipalConflict);
                }
                if n == 0 {
                    return Ok(p.clone());
                }
                one(n, "principal")?;
                write_audit(tx, &a).await?;
                deferred(tx).await?;
                if lock_principal(tx, &p.principal_id, false).await? != expected {
                    return Err(OwnerError::Mismatch("principal"));
                }
                verify_unique_audit(tx, &a).await?;
                Ok(p.clone())
            },
        )
        .await
    }
    pub async fn get_principal(&self, id: &str) -> Result<Principal, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let row = lease
            .client()
            .query_opt("SELECT * FROM principals WHERE principal_id=$1", &[&id])
            .await
            .map_err(|e| db("principal get", e))?
            .ok_or(OwnerError::PrincipalNotFound)?;
        let p = PrincipalRow::read(&row)?.view()?;
        lease.reusable();
        Ok(p)
    }
    pub async fn find_principal(&self, user: &str) -> Result<Principal, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let row = lease
            .client()
            .query_opt("SELECT * FROM principals WHERE user_name=$1", &[&user])
            .await
            .map_err(|e| db("principal find", e))?
            .ok_or(OwnerError::PrincipalNotFound)?;
        let p = PrincipalRow::read(&row)?.view()?;
        lease.reusable();
        Ok(p)
    }
}
