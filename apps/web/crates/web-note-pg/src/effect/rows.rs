//! Exact persisted row projections. Raw JSON is evidence, not a normalized
//! replacement. Parse only where the original domain consumes the value.
use super::domain::{db, scope_contains};
use super::{EffectError, EffectRequest, GrantFence};
use crate::domain::representable;
use serde::Serialize;
use tokio_postgres::Row;
macro_rules! row_type{
    ($(#[$meta:meta])* $vis:vis struct $name:ident { $($field:ident:$ty:ty),* $(,)? })=>{
        $(#[$meta])* #[derive(Debug,Clone,PartialEq,Eq)] $vis struct $name{$(pub $field:$ty),*}
        impl $name{pub(crate) fn read(r:&Row)->Result<Self,EffectError>{
            Ok(Self{$($field:r.try_get(stringify!($field)).map_err(|e|db("row projection",e))?),*})
        }}
    }
}
row_type! {pub(crate) struct GrantRow{
    grant_id:String,grant_digest:String,principal_id:String,agent_id:String,audience:String,
    allowed_actions_json:String,resource_prefixes_json:String,expires_at:i64,max_risk_class:String,
    step_up_at_or_above:String,remaining_effects:i64,active:i64,revision:i64
}}
impl GrantRow {
    pub fn checked(&self) -> Result<(Vec<String>, Vec<String>), EffectError> {
        let safe = |n| representable("", "", n);
        let risk = |s: &str| matches!(s, "R0" | "R1" | "R2" | "R3" | "R4" | "R5");
        if !safe(self.expires_at)
            || !safe(self.remaining_effects)
            || !safe(self.revision)
            || self.remaining_effects < 0
            || self.revision < 1
            || !matches!(self.active, 0 | 1)
            || !risk(&self.max_risk_class)
            || !risk(&self.step_up_at_or_above)
        {
            return Err(EffectError::Corrupt);
        }
        Ok((
            serde_json::from_str(&self.allowed_actions_json).map_err(|_| EffectError::Corrupt)?,
            serde_json::from_str(&self.resource_prefixes_json).map_err(|_| EffectError::Corrupt)?,
        ))
    }
    pub fn current(&self, g: &GrantFence, now: i64) -> bool {
        self.grant_id == g.grant_id
            && self.grant_digest == g.grant_digest
            && self.revision == g.revision
            && self.active == 1
            && self.expires_at > now
            && self.remaining_effects > 0
            && self.revision < 9_007_199_254_740_991
    }
    pub fn binds(
        &self,
        g: &GrantFence,
        r: &EffectRequest,
        actions: &[String],
        prefixes: &[String],
    ) -> bool {
        self.principal_id == g.principal_id
            && self.agent_id == g.agent_id
            && self.agent_id == r.agent_id
            && self.audience == r.audience
            && actions.contains(&r.action)
            && prefixes.iter().any(|p| scope_contains(p, &r.resource))
    }
}
row_type! {pub(crate) struct ApprovalRow{
    effect_id:String,effect_digest:String,principal_id:String,credential_id:String,
    verified_at:i64,expires_at:i64,consumed_at:Option<i64>
}}
row_type! {#[derive(Serialize)] #[serde(rename_all="camelCase")] pub struct EffectReceipt{
    effect_id:String,effect_digest:String,principal_id:String,agent_id:String,grant_id:String,
    action:String,resource:String,result_json:String,committed_at:i64
}}
impl EffectReceipt {
    pub fn replay(&self, r: &EffectRequest) -> Result<(), EffectError> {
        if self.agent_id != r.agent_id {
            return Err(EffectError::ActorMismatch);
        }
        if self.effect_digest != r.effect_digest
            || self.action != r.action
            || self.resource != r.resource
        {
            return Err(EffectError::Conflict);
        }
        if !representable("", "", self.committed_at)
            || serde_json::from_str::<serde_json::Value>(&self.result_json).is_err()
        {
            return Err(EffectError::Corrupt);
        }
        Ok(())
    }
}
row_type! {pub(crate) struct AuditRow{
    event_id:String,principal_id:Option<String>,event_type:String,object_type:Option<String>,
    object_id:Option<String>,detail_json:String,created_at:i64
}}

row_type! {#[derive(Serialize)] #[serde(rename_all="camelCase")] pub struct PendingApproval{
    effect_id:String,effect_digest:String,principal_id:String,expires_at:i64,created_at:i64
}}
