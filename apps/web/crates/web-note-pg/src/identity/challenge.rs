//! Exact v1 JSON payload bytes from the trusted ceremony producer.
//! This is NOT the authenticator challenge generator or verifier.
use super::{deferred, hash_text, safe, unknown, valid_text};
use crate::{
    OwnerError, PgNoteStore,
    owner_error::{db, one},
};
use serde::Serialize;
use tokio_postgres::{Row, Transaction};
use uuid::Uuid;
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum ChallengePurpose {
    Register,
    Login,
    GrantIssue,
    GrantRevoke,
    EffectApprove,
}
impl ChallengePurpose {
    fn as_str(self) -> &'static str {
        match self {
            Self::Register => "register",
            Self::Login => "login",
            Self::GrantIssue => "grant-issue",
            Self::GrantRevoke => "grant-revoke",
            Self::EffectApprove => "effect-approve",
        }
    }
}
#[derive(Clone, PartialEq, Eq)]
pub struct ChallengeRecord {
    pub challenge_id: String,
    pub purpose: ChallengePurpose,
    pub principal_id: String,
    pub challenge: String,
    pub payload_digest: String,
    pub payload_json: String,
    pub expires_at: i64,
}
pub struct PreparedChallenge(ChallengeRecord);
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChallengeObservation {
    ExactUnconsumed,
    ExactConsumed(i64),
    Unobserved,
    Mismatch,
}
impl PreparedChallenge {
    /// payload_json is the exact v1 producer serialization (JSON.stringify
    /// snapshot). Rust does not reorder generic object fields or float spellings.
    pub fn new(
        purpose: ChallengePurpose,
        principal: &str,
        challenge: &str,
        payload_json: String,
        now: i64,
        ttl: i64,
    ) -> Result<Self, OwnerError> {
        if !valid_text(principal)
            || !valid_text(challenge)
            || ttl <= 0
            || !safe(now)
            || serde_json::from_str::<serde_json::Value>(&payload_json).is_err()
        {
            return Err(OwnerError::Invalid);
        }
        let expires_at = now
            .checked_add(ttl)
            .filter(|n| safe(*n))
            .ok_or(OwnerError::Invalid)?;
        Ok(Self(ChallengeRecord {
            challenge_id: Uuid::new_v4().to_string(),
            purpose,
            principal_id: principal.into(),
            challenge: challenge.into(),
            payload_digest: format!("sha256:{}", hash_text(&payload_json)),
            payload_json,
            expires_at,
        }))
    }
    pub fn record(&self) -> &ChallengeRecord {
        &self.0
    }
}
#[derive(Clone, PartialEq, Eq)]
struct Stored {
    challenge_id: String,
    purpose: String,
    principal_id: String,
    challenge: String,
    payload_digest: String,
    payload_json: String,
    expires_at: i64,
    consumed_at: Option<i64>,
}
impl Stored {
    fn read(r: &Row) -> Result<Self, OwnerError> {
        macro_rules! f {
            ($n:literal) => {
                r.try_get($n).map_err(|e| db("challenge projection", e))?
            };
        }
        Ok(Self {
            challenge_id: f!("challenge_id"),
            purpose: f!("purpose"),
            principal_id: f!("principal_id"),
            challenge: f!("challenge"),
            payload_digest: f!("payload_digest"),
            payload_json: f!("payload_json"),
            expires_at: f!("expires_at"),
            consumed_at: f!("consumed_at"),
        })
    }
    fn from_record(r: &ChallengeRecord) -> Self {
        Self {
            challenge_id: r.challenge_id.clone(),
            purpose: r.purpose.as_str().into(),
            principal_id: r.principal_id.clone(),
            challenge: r.challenge.clone(),
            payload_digest: r.payload_digest.clone(),
            payload_json: r.payload_json.clone(),
            expires_at: r.expires_at,
            consumed_at: None,
        }
    }
    fn record(&self, purpose: ChallengePurpose) -> Result<ChallengeRecord, OwnerError> {
        if !safe(self.expires_at)
            || self.consumed_at.is_some_and(|n| !safe(n))
            || serde_json::from_str::<serde_json::Value>(&self.payload_json).is_err()
            || self.payload_digest != format!("sha256:{}", hash_text(&self.payload_json))
        {
            return Err(OwnerError::ChallengeCorrupt);
        }
        Ok(ChallengeRecord {
            challenge_id: self.challenge_id.clone(),
            purpose,
            principal_id: self.principal_id.clone(),
            challenge: self.challenge.clone(),
            payload_digest: self.payload_digest.clone(),
            payload_json: self.payload_json.clone(),
            expires_at: self.expires_at,
        })
    }
}
async fn read(tx: &Transaction<'_>, id: &str, lock: bool) -> Result<Option<Stored>, OwnerError> {
    let sql = if lock {
        "SELECT * FROM webauthn_challenges WHERE challenge_id=$1 FOR UPDATE NOWAIT"
    } else {
        "SELECT * FROM webauthn_challenges WHERE challenge_id=$1"
    };
    tx.query_opt(sql, &[&id])
        .await
        .map_err(|e| db("challenge row", e))?
        .as_ref()
        .map(Stored::read)
        .transpose()
}
impl PgNoteStore {
    pub async fn issue_challenge(&self, p: &PreparedChallenge) -> Result<(), OwnerError> {
        let expected = Stored::from_record(p.record());
        self.owner_write(
            |e| unknown("challenge-issue", &expected.challenge_id, e),
            async |tx| {
                one(
                    tx.execute(
                        "INSERT INTO webauthn_challenges(challenge_id,purpose,principal_id,challenge,payload_digest,payload_json,expires_at,consumed_at) VALUES($1,$2,$3,$4,$5,$6,$7,NULL)",
                        &[
                            &expected.challenge_id,
                            &expected.purpose,
                            &expected.principal_id,
                            &expected.challenge,
                            &expected.payload_digest,
                            &expected.payload_json,
                            &expected.expires_at,
                        ],
                    )
                    .await
                    .map_err(|e| db("challenge insert", e))?,
                    "challenge",
                )?;
                if p.record().purpose==ChallengePurpose::Login{
                    one(tx.execute("INSERT INTO webauthn_login_completions(challenge_id) VALUES($1)",&[&expected.challenge_id]).await.map_err(|e|db("login eligibility",e))?,"login eligibility")?;
                }
                deferred(tx).await?;
                if read(tx, &expected.challenge_id, false).await?.as_ref() != Some(&expected) {
                    return Err(OwnerError::Mismatch("challenge"));
                }
                if p.record().purpose==ChallengePurpose::Login&&super::login::marker(tx,&expected.challenge_id,false).await?!=Some((None,None)){return Err(OwnerError::Mismatch("login eligibility"))}
                Ok(())
            },
        )
        .await
    }
    /// Bind the intended Principal as well as purpose before consumption.
    /// A successful consume authorizes no action by itself.
    pub async fn consume_challenge(
        &self,
        id: &str,
        purpose: ChallengePurpose,
        principal: &str,
        now: i64,
    ) -> Result<ChallengeRecord, OwnerError> {
        if !safe(now) {
            return Err(OwnerError::Invalid);
        }
        self.owner_write(|e|unknown("challenge-consume",id,e),async |tx|{
   let mut expected=read(tx,id,true).await?.ok_or(OwnerError::ChallengeInvalid)?;
   if expected.purpose!=purpose.as_str()||expected.principal_id!=principal||expected.consumed_at.is_some()||expected.expires_at<=now{return Err(OwnerError::ChallengeInvalid)}
   let record=expected.record(purpose)?;
   one(tx.execute("UPDATE webauthn_challenges SET consumed_at=$2 WHERE challenge_id=$1 AND consumed_at IS NULL",&[&id,&now]).await.map_err(|e|db("challenge consume",e))?,"challenge consume")?;
   expected.consumed_at=Some(now);deferred(tx).await?;
   if read(tx,id,false).await?.as_ref()!=Some(&expected){return Err(OwnerError::Mismatch("challenge consume"))}Ok(record)
  }).await
    }
    pub async fn observe_challenge(
        &self,
        p: &PreparedChallenge,
    ) -> Result<ChallengeObservation, OwnerError> {
        let mut lease = self.connect().await.map_err(OwnerError::Pool)?;
        let row = lease
            .client()
            .query_opt(
                "SELECT c.*, m.challenge_id AS login_marker FROM webauthn_challenges c LEFT JOIN webauthn_login_completions m USING(challenge_id) WHERE c.challenge_id=$1",
                &[&p.record().challenge_id],
            )
            .await
            .map_err(|e| db("challenge observe", e))?;
        let marker_ok = row.as_ref().is_none_or(|r| {
            p.record().purpose != ChallengePurpose::Login
                || r.get::<_, Option<String>>("login_marker").is_some()
        });
        let result = match row.as_ref().map(Stored::read).transpose()? {
            None => ChallengeObservation::Unobserved,
            Some(mut r) => {
                let consumed = r.consumed_at.take();
                if !marker_ok
                    || r != Stored::from_record(p.record())
                    || consumed.is_some_and(|n| !safe(n))
                {
                    ChallengeObservation::Mismatch
                } else {
                    consumed.map_or(
                        ChallengeObservation::ExactUnconsumed,
                        ChallengeObservation::ExactConsumed,
                    )
                }
            }
        };
        lease.reusable();
        Ok(result)
    }
}

pub(super) async fn verify_consumed_login(
    tx: &Transaction<'_>,
    record: &ChallengeRecord,
    consumed: i64,
    lock: bool,
) -> Result<(), OwnerError> {
    if record.purpose != ChallengePurpose::Login || !safe(consumed) || consumed >= record.expires_at
    {
        return Err(OwnerError::ChallengeInvalid);
    }
    let row = read(tx, &record.challenge_id, lock)
        .await?
        .ok_or(OwnerError::ChallengeInvalid)?;
    let mut expected = Stored::from_record(record);
    expected.consumed_at = Some(consumed);
    if row != expected || row.record(ChallengePurpose::Login)? != *record {
        return Err(OwnerError::ChallengeInvalid);
    }
    Ok(())
}
