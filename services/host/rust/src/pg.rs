//! PostgreSQL schema gate and a read-only Host summary projection.
//! Bounded pooled PostgreSQL connections are used for each transaction.
use crate::attention::{self, TargetKind};
use crate::social::{self, AddMessageRelation, PostMessage, TopicState};
use crate::work::{self, CommitSnapshot, CreateWork, ListWorks};
use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};
use serde::Serialize;
use serde_json::Value;
use std::collections::BTreeMap;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;
use tokio_postgres::NoTls;

pub const REQUIRED_SCHEMA: i32 = 13;

#[derive(Debug, Error)]
pub enum HostDbError {
    #[error("PostgreSQL: {0}")]
    Postgres(#[from] tokio_postgres::Error),
    #[error("Host schema is not at required version 13 (observed={0})")]
    Schema(i32),
    #[error("Host schema row is missing")]
    MissingSchema,
    #[error("Work transaction: {0}")]
    Work(#[from] work::WorkError),
    #[error("Attention transaction: {0}")]
    Attention(#[from] attention::AttentionError),
    #[error("Clock before Unix epoch")]
    Clock,
    #[error("PostgreSQL connection pool: {0}")]
    Pool(String),
    #[error("PostgreSQL pool checkout: {0}")]
    PoolCheckout(#[from] deadpool_postgres::PoolError),
}

#[derive(Clone)]
pub struct HostPg {
    pool: Pool,
}

impl HostPg {
    /// Preserve the legacy deployment's pool-size knob and hard bounds.
    pub fn try_new(dsn: impl Into<String>) -> Result<Self, HostDbError> {
        let limit = match std::env::var("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE") {
            Ok(raw) => raw.parse::<usize>().map_err(|_| {
                HostDbError::Pool("ORDIVON_HOST_V2_PG_POOL_MAX_SIZE must be an integer".into())
            })?,
            Err(std::env::VarError::NotPresent) => 8,
            Err(_) => return Err(HostDbError::Pool("invalid pool-size environment".into())),
        };
        Self::with_pool_limit(dsn.into(), limit)
    }

    fn with_pool_limit(dsn: String, limit: usize) -> Result<Self, HostDbError> {
        if !(1..=64).contains(&limit) {
            return Err(HostDbError::Pool("pool max size must be in [1,64]".into()));
        }
        let config: tokio_postgres::Config = dsn.parse()?;
        let manager = Manager::from_config(
            config,
            NoTls,
            ManagerConfig {
                recycling_method: RecyclingMethod::Fast,
            },
        );
        let pool = Pool::builder(manager)
            .max_size(limit)
            .runtime(deadpool_postgres::Runtime::Tokio1)
            .wait_timeout(Some(std::time::Duration::from_secs(5)))
            .build()
            .map_err(|error| HostDbError::Pool(error.to_string()))?;
        Ok(Self { pool })
    }

    async fn connect(&self) -> Result<deadpool_postgres::Object, HostDbError> {
        Ok(self.pool.get().await?)
    }

    pub async fn subscription_follow(
        &self,
        actor: &str,
        kind: TargetKind,
        target: &str,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::follow(&mut client, actor, kind, target, request_id).await?)
    }

    pub async fn subscription_unfollow(
        &self,
        actor: &str,
        kind: TargetKind,
        target: &str,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::unfollow(&mut client, actor, kind, target, request_id).await?)
    }

    pub async fn subscription_list(
        &self,
        actor: &str,
        kind: Option<TargetKind>,
        after: Option<(&str, &str)>,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(
            attention::list_subscriptions(&mut client, actor, kind, after, limit, max_bytes)
                .await?,
        )
    }

    pub async fn attention_get(
        &self,
        actor: &str,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::get(&mut client, actor, limit, max_bytes).await?)
    }

    pub async fn attention_delta(
        &self,
        actor: &str,
        after: i64,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::delta(&mut client, actor, after, limit, max_bytes).await?)
    }

    pub async fn attention_reentry(
        &self,
        actor: &str,
        after: Option<i64>,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::reentry(&mut client, actor, after, limit, max_bytes).await?)
    }

    pub async fn attention_ack(
        &self,
        actor: &str,
        cursor: i64,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(attention::ack(&mut client, actor, cursor, request_id).await?)
    }

    // Social operations delegate to B's existing single-transaction domain
    // layer. The adapter only borrows a bounded pool connection per call.
    pub async fn social_topic_resume(
        &self,
        topic: &str,
        after: i64,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::resume_topic(&mut client, topic, after, limit, max_bytes).await?)
    }

    pub async fn social_topic_cursor_get(
        &self,
        actor: &str,
        topic: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::get_topic_cursor(&mut client, actor, topic).await?)
    }

    pub async fn social_topic_cursor_ack(
        &self,
        actor: &str,
        topic: &str,
        cursor: i64,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::ack_topic_cursor(&mut client, actor, topic, cursor, request_id).await?)
    }

    pub async fn social_topic_state_set(
        &self,
        topic: &str,
        actor: &str,
        state: TopicState,
        expected_state: TopicState,
        expected_high: i64,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::set_topic_state(
            &mut client,
            topic,
            actor,
            state,
            expected_state,
            expected_high,
            request_id,
        )
        .await?)
    }

    pub async fn social_message_post(&self, value: &PostMessage) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::post_message(&mut client, value).await?)
    }

    pub async fn social_message_relation_add(
        &self,
        value: &AddMessageRelation,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::add_message_relation(&mut client, value, request_id).await?)
    }

    pub async fn work_get(
        &self,
        work_ref: &str,
        revision: Option<i64>,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(work::get_work(&mut client, work_ref, revision).await?)
    }

    pub async fn work_create(&self, cmd: &CreateWork) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(work::create_work(&mut client, cmd).await?)
    }

    pub async fn work_list(&self, input: &ListWorks) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(work::list_works(&mut client, input).await?)
    }

    pub async fn work_snapshot_commit(&self, cmd: &CommitSnapshot) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(work::commit_snapshot(&mut client, cmd).await?)
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
    fn bounded_pool_is_constructible_without_database_access() {
        let host = HostPg::with_pool_limit(
            "host=127.0.0.1 user=nonexistent dbname=nonexistent".into(),
            2,
        )
        .expect("pool setup does not connect");
        assert_eq!(host.pool.status().max_size, 2);
        assert!(HostPg::with_pool_limit("host=localhost".into(), 0).is_err());
        assert!(HostPg::with_pool_limit("host=localhost".into(), 65).is_err());
    }

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
