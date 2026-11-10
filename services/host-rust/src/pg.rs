//! PostgreSQL schema gate and a read-only Host summary projection.
//! This first slice intentionally uses one connection per diagnostic request;
//! a mature bounded connection pool is a cutover prerequisite, not implied here.
use serde::Serialize;
use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;
use tokio_postgres::{Client, NoTls};

pub const REQUIRED_SCHEMA: i32 = 13;

#[derive(Debug, Error)]
pub enum HostDbError {
    #[error("PostgreSQL: {0}")]
    Postgres(#[from] tokio_postgres::Error),
    #[error("Host schema is not at required version 13 (observed={0})")]
    Schema(i32),
    #[error("Host schema row is missing")]
    MissingSchema,
    #[error("Clock before Unix epoch")]
    Clock,
}

#[derive(Clone)]
pub struct HostPg {
    dsn: Arc<str>,
}

impl HostPg {
    pub fn new(dsn: impl Into<String>) -> Self {
        Self {
            dsn: Arc::from(dsn.into()),
        }
    }

    async fn connect(&self) -> Result<Client, HostDbError> {
        let (client, connection) = tokio_postgres::connect(&self.dsn, NoTls).await?;
        tokio::spawn(async move {
            if let Err(error) = connection.await {
                eprintln!("Host PostgreSQL session ended: {error}");
            }
        });
        Ok(client)
    }

    pub async fn check_schema(&self) -> Result<i32, HostDbError> {
        let client = self.connect().await?;
        let row = client
            .query_opt(
                "SELECT schema_version FROM host_v2_schema WHERE singleton",
                &[],
            )
            .await?
            .ok_or(HostDbError::MissingSchema)?;
        let schema: i32 = row.get(0);
        if schema != REQUIRED_SCHEMA {
            return Err(HostDbError::Schema(schema));
        }
        Ok(schema)
    }

    pub async fn summary(&self) -> Result<HostSummary, HostDbError> {
        let mut client = self.connect().await?;
        let tx = client
            .build_transaction()
            .read_only(true)
            .isolation_level(tokio_postgres::IsolationLevel::RepeatableRead)
            .start()
            .await?;
        let schema: i32 = tx
            .query_one(
                "SELECT schema_version FROM host_v2_schema WHERE singleton",
                &[],
            )
            .await?
            .get(0);
        if schema != REQUIRED_SCHEMA {
            return Err(HostDbError::Schema(schema));
        }
        let actor_refs = count(&tx, "SELECT count(*) FROM actor_refs").await?;
        let work_snapshots = count(&tx, "SELECT count(*) FROM work_snapshots").await?;
        let spaces = count(&tx, "SELECT count(*) FROM spaces").await?;
        let topics = count(&tx, "SELECT count(*) FROM topics").await?;
        let messages = count(&tx, "SELECT count(*) FROM messages").await?;
        let subscriptions = count(&tx, "SELECT count(*) FROM subscriptions").await?;
        let change_high_sequence: i64 = tx
            .query_one("SELECT value FROM swf_change_clock WHERE singleton", &[])
            .await?
            .get(0);
        let mut works_by_state = BTreeMap::<String, i64>::new();
        for row in tx
            .query("SELECT state,count(*) FROM works GROUP BY state", &[])
            .await?
        {
            let state: String = row.get(0);
            let count: i64 = row.get(1);
            works_by_state.insert(state, count);
        }
        let works = works_by_state.values().copied().sum();
        tx.commit().await?;
        let observed_at_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|_| HostDbError::Clock)?
            .as_millis() as u64;
        Ok(HostSummary {
            schema_version: 3,
            kind: "ordivon.host-status",
            observed_at_ms,
            detail: "summary",
            authority: HostAuthority {
                journal_backend: "postgresql",
                journal_schema: schema,
                actor_refs,
                works,
                works_by_state,
                work_snapshots,
                spaces,
                topics,
                messages,
                subscriptions,
                change_high_sequence,
            },
            doctor: None,
            truth_boundary: BTreeMap::from([(
                "host",
                "authoritative only for Host Social Work Fabric semantic continuity and collaboration records; Runtime, Git, Identity/Security, effect, and domain truth are not checked"
            )]),
        })
    }
}

async fn count(tx: &tokio_postgres::Transaction<'_>, sql: &str) -> Result<i64, HostDbError> {
    Ok(tx.query_one(sql, &[]).await?.get(0))
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HostSummary {
    pub schema_version: i32,
    pub kind: &'static str,
    pub observed_at_ms: u64,
    pub detail: &'static str,
    pub authority: HostAuthority,
    pub doctor: Option<()>,
    pub truth_boundary: BTreeMap<&'static str, &'static str>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct HostAuthority {
    pub journal_backend: &'static str,
    pub journal_schema: i32,
    pub actor_refs: i64,
    pub works: i64,
    pub works_by_state: BTreeMap<String, i64>,
    pub work_snapshots: i64,
    pub spaces: i64,
    pub topics: i64,
    pub messages: i64,
    pub subscriptions: i64,
    pub change_high_sequence: i64,
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn summary_wire_names_match_python_host() {
        let wire = serde_json::to_value(HostSummary {
            schema_version: 3,
            kind: "ordivon.host-status",
            observed_at_ms: 7,
            detail: "summary",
            authority: HostAuthority {
                journal_backend: "postgresql",
                journal_schema: 13,
                actor_refs: 1,
                works: 2,
                works_by_state: BTreeMap::new(),
                work_snapshots: 2,
                spaces: 3,
                topics: 4,
                messages: 5,
                subscriptions: 6,
                change_high_sequence: 7,
            },
            doctor: None,
            truth_boundary: BTreeMap::from([("host", "test")]),
        })
        .expect("serialize");
        assert_eq!(wire["schemaVersion"], 3);
        assert_eq!(wire["observedAtMs"], 7);
        assert_eq!(wire["authority"]["journalSchema"], 13);
        assert_eq!(wire["authority"]["changeHighSequence"], 7);
        assert!(wire["doctor"].is_null());
    }
}
