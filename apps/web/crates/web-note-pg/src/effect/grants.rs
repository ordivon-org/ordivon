//! Native Grant writes, checked selection and coherent issuance evidence.
use super::domain::{db, one, scope_contains};
use super::rows::{AuditRow, GrantRow};
use super::{EffectError, GrantObservation, GrantSnapshot, PreparedGrant};
use crate::{PgNoteStore, domain::representable};
use tokio_postgres::{IsolationLevel, Transaction};
async fn get_row(tx: &Transaction<'_>, id: &str) -> Result<Option<GrantRow>, EffectError> {
    tx.query_opt("SELECT * FROM agent_grants WHERE grant_id=$1", &[&id])
        .await
        .map_err(|e| db("grant read", e))?
        .as_ref()
        .map(GrantRow::read)
        .transpose()
}
async fn issuance_audits(
    tx: &Transaction<'_>,
    prepared: &PreparedGrant,
) -> Result<Vec<AuditRow>, EffectError> {
    tx.query("SELECT * FROM audit_events WHERE event_id=$1 OR (event_type='agent.grant.issued' AND object_type='agent-grant' AND object_id=$2) LIMIT 2",&[&prepared.audit.event_id,&prepared.row.grant_id]).await.map_err(|e|db("grant issuance evidence",e))?.iter().map(AuditRow::read).collect()
}
fn immutable_match(actual: &GrantRow, expected: &GrantRow) -> bool {
    let mut projection = actual.clone();
    projection.remaining_effects = expected.remaining_effects;
    projection.active = expected.active;
    projection.revision = expected.revision;
    projection == *expected
}
impl PgNoteStore {
    /// Prepared identity and original decision belong to the trusted caller.
    /// New insert only; duplicates are not a successful replay.
    pub async fn issue_grant(
        &self,
        prepared: &PreparedGrant,
    ) -> Result<GrantSnapshot, EffectError> {
        let r = &prepared.row;
        let a = &prepared.audit;
        self.owner_write(|source|EffectError::AuthorityCommitUnknown{operation:"grant-issuance",coordinate:a.event_id.clone(),source},async |tx|{
            one(tx.execute("INSERT INTO agent_grants(grant_id,grant_digest,principal_id,agent_id,audience,allowed_actions_json,resource_prefixes_json,expires_at,max_risk_class,step_up_at_or_above,remaining_effects,active,revision) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,1,1)",
            &[&r.grant_id,&r.grant_digest,&r.principal_id,&r.agent_id,&r.audience,&r.allowed_actions_json,&r.resource_prefixes_json,&r.expires_at,&r.max_risk_class,&r.step_up_at_or_above,&r.remaining_effects]).await.map_err(|e|db("grant insert",e))?,"grant")?;
            one(tx.execute("INSERT INTO audit_events VALUES($1,$2,$3,$4,$5,$6,$7)",&[&a.event_id,&a.principal_id,&a.event_type,&a.object_type,&a.object_id,&a.detail_json,&a.created_at]).await.map_err(|e|db("issuance audit",e))?,"issuance audit")?;
            tx.batch_execute("SET CONSTRAINTS ALL IMMEDIATE").await.map_err(|e|db("issuance deferred",e))?;
            if get_row(tx,&r.grant_id).await?.as_ref()!=Some(r){return Err(EffectError::Mismatch("grant issuance"))}
            if issuance_audits(tx,prepared).await?.as_slice()!=[a.clone()]{return Err(EffectError::Mismatch("grant issuance audit"))}
            r.snapshot()
        }).await
    }
    pub async fn observe_grant_issuance(
        &self,
        prepared: &PreparedGrant,
    ) -> Result<GrantObservation, EffectError> {
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let tx = lease
            .client()
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()
            .await
            .map_err(|e| db("observe issuance begin", e))?;
        let row = get_row(&tx, &prepared.row.grant_id).await?;
        let audits = issuance_audits(&tx, prepared).await?;
        let outcome = match row {
            None if audits.is_empty() => GrantObservation::Unobserved,
            Some(r)
                if immutable_match(&r, &prepared.row)
                    && audits.as_slice() == [prepared.audit.clone()] =>
            {
                match r.snapshot() {
                    Ok(s)
                        if s.revision > 1
                            || (s.remaining_effects == prepared.row.remaining_effects
                                && s.active) =>
                    {
                        GrantObservation::Exact(Box::new(s))
                    }
                    _ => GrantObservation::Mismatch,
                }
            }
            _ => GrantObservation::Mismatch,
        };
        tx.rollback()
            .await
            .map_err(|e| db("observe issuance end", e))?;
        lease.reusable();
        Ok(outcome)
    }
    pub async fn get_grant(&self, id: &str) -> Result<GrantSnapshot, EffectError> {
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let row = lease
            .client()
            .query_opt("SELECT * FROM agent_grants WHERE grant_id=$1", &[&id])
            .await
            .map_err(|e| db("get grant", e))?
            .ok_or(EffectError::GrantNotFound)?;
        let result = GrantRow::read(&row)?.snapshot()?;
        lease.reusable();
        Ok(result)
    }
    pub async fn list_grants(&self, principal: &str) -> Result<Vec<GrantSnapshot>, EffectError> {
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let rows = lease
            .client()
            .query(
                "SELECT * FROM agent_grants WHERE principal_id=$1 ORDER BY grant_id",
                &[&principal],
            )
            .await
            .map_err(|e| db("list grants", e))?;
        let result = rows
            .iter()
            .map(|r| GrantRow::read(r)?.snapshot())
            .collect::<Result<Vec<_>, _>>()?;
        lease.reusable();
        Ok(result)
    }
    /// Scope selection only. Risk, authentication and admission are external.
    /// Preserve ambiguity even if a matching Grant has exhausted its quota.
    pub async fn resolve_grant(
        &self,
        agent: &str,
        audience: &str,
        action: &str,
        resource: &str,
        now: i64,
    ) -> Result<GrantSnapshot, EffectError> {
        if !representable("", "", now) {
            return Err(EffectError::Invalid);
        }
        let mut lease = self.connect().await.map_err(EffectError::Pool)?;
        let rows=lease.client().query("SELECT * FROM agent_grants WHERE agent_id=$1 AND audience=$2 AND active=1 AND expires_at>$3",&[&agent,&audience,&now]).await.map_err(|e|db("resolve grant",e))?;
        // Decode every candidate before selection, including nonmatching
        // scope; a corrupt row must not silently disappear.
        let snapshots = rows
            .iter()
            .map(|r| GrantRow::read(r)?.snapshot())
            .collect::<Result<Vec<_>, _>>()?;
        lease.reusable();
        let mut matches = snapshots.into_iter().filter(|g| {
            g.allowed_actions.iter().any(|a| a == action)
                && g.resource_prefixes
                    .iter()
                    .any(|p| scope_contains(p, resource))
        });
        let one = matches.next().ok_or(EffectError::GrantUnavailable)?;
        if matches.next().is_some() {
            return Err(EffectError::GrantAmbiguous);
        }
        Ok(one)
    }
}
