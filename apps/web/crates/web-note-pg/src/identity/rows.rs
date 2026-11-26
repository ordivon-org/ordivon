use super::{safe, valid_text};
use crate::{OwnerError, owner_error::db};
use serde::Serialize;
use tokio_postgres::Row;
macro_rules! row{
 ($name:ident{$($f:ident:$t:ty),*$(,)?})=>{
 #[derive(Clone,PartialEq,Eq)]
 pub(super) struct $name{$(pub $f:$t),*}
 impl $name{pub fn read(row:&Row)->Result<Self,OwnerError>{Ok(Self{$($f:row.try_get(stringify!($f)).map_err(|e|db("identity projection",e))?),*})}}
 }
}
row!(PrincipalRow {
    principal_id: String,
    user_name: String,
    display_name: String,
    created_at: i64
});
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Principal {
    pub principal_id: String,
    pub user_name: String,
    pub display_name: String,
}
impl PrincipalRow {
    pub fn view(&self) -> Result<Principal, OwnerError> {
        if !safe(self.created_at) || !valid_text(&self.principal_id) || !valid_text(&self.user_name)
        {
            return Err(OwnerError::Corrupt);
        }
        Ok(Principal {
            principal_id: self.principal_id.clone(),
            user_name: self.user_name.clone(),
            display_name: self.display_name.clone(),
        })
    }
}
row!(CredentialRow{credential_id:String,principal_id:String,public_key:Vec<u8>,counter:i64,transports_json:String,device_type:String,backed_up:i64,created_at:i64,last_used_at:i64,revoked_at:Option<i64>});
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Credential {
    pub credential_id: String,
    pub principal_id: String,
    pub public_key: Vec<u8>,
    pub counter: i64,
    pub transports: Vec<String>,
    pub device_type: String,
    pub backed_up: bool,
    pub created_at: i64,
    pub last_used_at: i64,
    pub revoked_at: Option<i64>,
}
impl CredentialRow {
    pub fn view(&self) -> Result<Credential, OwnerError> {
        if !(0..=i64::from(u32::MAX)).contains(&self.counter)
            || !safe(self.created_at)
            || !safe(self.last_used_at)
            || self.revoked_at.is_some_and(|n| !safe(n))
            || !matches!(self.backed_up, 0 | 1)
            || !valid_text(&self.credential_id)
            || !valid_text(&self.principal_id)
            || self.public_key.is_empty()
        {
            return Err(OwnerError::Corrupt);
        }
        Ok(Credential {
            credential_id: self.credential_id.clone(),
            principal_id: self.principal_id.clone(),
            public_key: self.public_key.clone(),
            counter: self.counter,
            transports: serde_json::from_str(&self.transports_json)
                .map_err(|_| OwnerError::Corrupt)?,
            device_type: self.device_type.clone(),
            backed_up: self.backed_up == 1,
            created_at: self.created_at,
            last_used_at: self.last_used_at,
            revoked_at: self.revoked_at,
        })
    }
}
row!(SessionRow{session_id:String,token_hash:String,principal_id:String,created_at:i64,authenticated_at:i64,last_seen_at:i64,idle_expires_at:i64,absolute_expires_at:i64,revoked_at:Option<i64>,authn_method:String,user_agent:Option<String>});
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SessionView {
    pub session_id: String,
    pub principal_id: String,
    pub created_at: i64,
    pub authenticated_at: i64,
    pub last_seen_at: i64,
    pub idle_expires_at: i64,
    pub absolute_expires_at: i64,
    pub revoked_at: Option<i64>,
    pub authn_method: String,
    pub user_agent: Option<String>,
}
impl SessionRow {
    pub fn view(&self) -> Result<SessionView, OwnerError> {
        if ![
            self.created_at,
            self.authenticated_at,
            self.last_seen_at,
            self.idle_expires_at,
            self.absolute_expires_at,
        ]
        .into_iter()
        .all(safe)
            || self.revoked_at.is_some_and(|n| !safe(n))
            || self.authn_method != "webauthn"
            || self.token_hash.len() != 64
            || !self
                .token_hash
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        {
            return Err(OwnerError::Corrupt);
        }
        Ok(SessionView {
            session_id: self.session_id.clone(),
            principal_id: self.principal_id.clone(),
            created_at: self.created_at,
            authenticated_at: self.authenticated_at,
            last_seen_at: self.last_seen_at,
            idle_expires_at: self.idle_expires_at,
            absolute_expires_at: self.absolute_expires_at,
            revoked_at: self.revoked_at,
            authn_method: self.authn_method.clone(),
            user_agent: self.user_agent.clone(),
        })
    }
}
#[derive(Clone, PartialEq, Eq)]
pub struct AuthenticatedSession {
    pub token_hash: String,
    pub principal: Principal,
    pub session: SessionView,
}
