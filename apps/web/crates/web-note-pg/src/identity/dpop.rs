//! Durable logical replay fence, independent bounded physical expiry cleanup.
//! Proof verification, identity derivation and trust remain external.
use super::{deferred, hash_text, safe, unknown};
use crate::{
    OwnerError, PgNoteStore,
    owner_error::{db, one},
};
impl PgNoteStore {
    pub async fn consume_dpop_proof(
        &self,
        proof_id: &str,
        now: i64,
        ttl: i64,
    ) -> Result<(), OwnerError> {
        if !(1..=256).contains(&proof_id.len()) || ttl < 1 || !safe(now) || !safe(ttl) {
            return Err(OwnerError::DpopInvalid);
        }
        let expiry = now
            .checked_add(ttl)
            .filter(|n| safe(*n))
            .ok_or(OwnerError::DpopInvalid)?;
        let hash = hash_text(proof_id);
        self.owner_write(|e|unknown("dpop-consume",&hash,e),async |tx|{
   let locked:bool=tx.query_one("SELECT pg_try_advisory_xact_lock(hashtextextended('web-dpop:'||$1,0))",&[&hash]).await.map_err(|e|db("dpop identity",e))?.get(0);
   if !locked{return Err(OwnerError::Busy)}
   let row=tx.query_opt("SELECT expires_at FROM dpop_proofs WHERE proof_hash=$1 FOR UPDATE NOWAIT",&[&hash]).await.map_err(|e|db("dpop row",e))?;
   if let Some(r)=row{
    let prior:i64=r.get(0);
    if !safe(prior){return Err(OwnerError::Corrupt)}
    if prior>now{return Err(OwnerError::DpopReplayed)}
   }
   one(tx.execute("INSERT INTO dpop_proofs VALUES($1,$2) ON CONFLICT(proof_hash) DO UPDATE SET expires_at=excluded.expires_at WHERE dpop_proofs.expires_at<=$3",&[&hash,&expiry,&now]).await.map_err(|e|db("dpop claim",e))?,"dpop claim")?;
   deferred(tx).await?;
   let read=tx.query_opt("SELECT expires_at FROM dpop_proofs WHERE proof_hash=$1",&[&hash]).await.map_err(|e|db("dpop readback",e))?;
   if read.map(|r|r.get::<_,i64>(0))!=Some(expiry){return Err(OwnerError::Mismatch("dpop claim"))}
   Ok(())
  }).await
    }
    /// Maintenance, not admission: bounded batch, skip rows held by claimers,
    /// exact selected identities and absence checked before acknowledging.
    pub async fn cleanup_dpop_proofs(&self, now: i64, limit: u32) -> Result<u64, OwnerError> {
        if !safe(now) || limit == 0 || limit > 10_000 {
            return Err(OwnerError::Invalid);
        }
        self.owner_write(|e|unknown("dpop-cleanup","batch",e),async |tx|{
   let selected=tx.query("SELECT proof_hash FROM dpop_proofs WHERE expires_at<=$1 ORDER BY expires_at,proof_hash LIMIT $2 FOR UPDATE SKIP LOCKED",&[&now,&i64::from(limit)]).await.map_err(|e|db("dpop cleanup select",e))?;
   let mut expected:Vec<String>=selected.iter().map(|r|r.get(0)).collect();
   if expected.is_empty(){return Ok(0)}
   let rows=tx.query("DELETE FROM dpop_proofs WHERE proof_hash=ANY($1) AND expires_at<=$2 RETURNING proof_hash",&[&expected,&now]).await.map_err(|e|db("dpop cleanup delete",e))?;
   let mut actual:Vec<String>=rows.iter().map(|r|r.get(0)).collect();expected.sort_unstable();actual.sort_unstable();
   if actual!=expected{return Err(OwnerError::Mismatch("dpop cleanup"))}
   deferred(tx).await?;
   let count:i64=tx.query_one("SELECT count(*) FROM dpop_proofs WHERE proof_hash=ANY($1)",&[&expected]).await.map_err(|e|db("dpop cleanup readback",e))?.get(0);
   if count!=0{return Err(OwnerError::Mismatch("dpop cleanup"))}
   Ok(expected.len() as u64)
  }).await
    }
}
