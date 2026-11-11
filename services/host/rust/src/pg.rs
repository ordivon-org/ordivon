//! PostgreSQL schema gate and a read-only Host summary projection.
//! Bounded pooled PostgreSQL connections are used for each transaction.
use crate::attention::{self, TargetKind};
use crate::social::{
    self, AddMessageRelation, CreateSpace, CreateTopic, ListMessageRelations, ListSpaces,
    ParticipationStanding, PostMessage, SearchMessages, TopicState,
};
use crate::work::{self, ActorDeclare, CommitSnapshot, CreateWork, ListWorks};
use deadpool_postgres::{Manager, ManagerConfig, Pool, RecyclingMethod};
use serde::Serialize;
use serde_json::{json, Value};
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

    // Native Social lifetime is a B-owned Postgres domain. The MCP bridge only
    // checks out one bounded connection; it never duplicates SQL/CAS/receipts.
    pub async fn social_space_create(&self, command: &CreateSpace) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::create_space(&mut client, command).await?)
    }

    /// B owns all Social inventory read models and PostgreSQL snapshot
    /// semantics. MCP borrows a bounded pool connection and delegates.
    pub async fn social_space_list(&self, input: &ListSpaces<'_>) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::list_spaces(&mut client, input).await?)
    }

    pub async fn social_space_subject_list(
        &self,
        space_ref: &str,
        after_subject_ref: Option<&str>,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(
            social::list_space_subjects(
                &mut client,
                space_ref,
                after_subject_ref,
                limit,
                max_bytes,
            )
            .await?,
        )
    }

    pub async fn social_space_participation_list(
        &self,
        space_ref: &str,
        after_actor_ref: Option<&str>,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(
            social::list_participations(&mut client, space_ref, after_actor_ref, limit, max_bytes)
                .await?,
        )
    }

    pub async fn social_space_get(
        &self,
        space_ref: &str,
        participant_limit: i64,
        topic_limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::get_space(
            &mut client,
            space_ref,
            participant_limit,
            topic_limit,
            max_bytes,
        )
        .await?)
    }

    pub async fn social_topic_create(&self, command: &CreateTopic) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::create_topic(&mut client, command).await?)
    }

    pub async fn social_participation_set(
        &self,
        space_ref: &str,
        actor_ref: &str,
        standing: ParticipationStanding,
        request_id: &str,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(
            social::set_participation(&mut client, space_ref, actor_ref, standing, request_id)
                .await?,
        )
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

    /// B-owned immutable read and ranked=false indexed search, preserving
    /// its transaction, verified message digest and byte-budget semantics.
    pub async fn social_message_get(
        &self,
        message_ref: &str,
        expected_digest: Option<&str>,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::get_message(&mut client, message_ref, expected_digest).await?)
    }

    /// B's native relation and Topic inventory queries already implement
    /// repeatable-read snapshot/pagination; this is solely the MCP pool seam.
    pub async fn social_message_relation_list(
        &self,
        input: &ListMessageRelations,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::list_message_relations(&mut client, input).await?)
    }

    pub async fn social_topic_list(
        &self,
        space_ref: &str,
        after_topic_ref: Option<&str>,
        limit: i64,
        max_bytes: usize,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::list_topics(&mut client, space_ref, after_topic_ref, limit, max_bytes).await?)
    }

    pub async fn social_message_search(
        &self,
        input: &SearchMessages,
    ) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(social::search_messages(&mut client, input).await?)
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

    /// Delegate actor reference declaration to A's original-PG-compatible
    /// Work implementation. An ActorRef is a label, not authentication.
    pub async fn actor_declare(&self, command: &ActorDeclare) -> Result<Value, HostDbError> {
        let mut client = self.connect().await?;
        Ok(work::declare_actor(&mut client, command).await?)
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
        self.status("summary").await
    }

    /// One PostgreSQL MVCC snapshot for both the authority projection and all
    /// Doctor checks. The original Python Host remains the differential oracle.
    /// No alternate truth store or repaired synthetic history is permitted.
    pub async fn status(&self, detail: &'static str) -> Result<HostSummary, HostDbError> {
        if !matches!(detail, "summary" | "integrity" | "history") {
            return Err(HostDbError::Pool("invalid status detail".into()));
        }
        let observed_at_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|_| HostDbError::Clock)?
            .as_millis() as u64;
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
        let doctor = if detail == "summary" {
            None
        } else {
            // Exact legacy HostV2.status check order and labels. A clean
            // current pointer does NOT imply contiguous historical revisions.
            let mut checks: Vec<Value> = Vec::with_capacity(8);
            let mut add_check = |name: &'static str, ok: bool, description: String| {
                checks.push(json!({
                    "name": name, "status": if ok {"ok"} else {"error"},
                    "detail": description
                }));
            };
            add_check(
                "postgres.schema",
                schema == REQUIRED_SCHEMA,
                schema.to_string(),
            );
            let current_bad = count(
                &tx,
                "SELECT count(*) FROM works w LEFT JOIN work_snapshots s                  ON s.work_ref=w.work_ref AND s.revision=w.current_revision                  WHERE s.work_ref IS NULL OR s.snapshot_digest<>w.current_snapshot_digest"
            ).await?;
            add_check(
                "work.current_snapshot",
                current_bad == 0,
                format!("invalid={current_bad}"),
            );
            let topic_bad = count(
                &tx,
                "SELECT count(*) FROM messages m JOIN topics t USING(topic_ref)                  WHERE m.space_ref<>t.space_ref"
            ).await?;
            add_check(
                "social.message_topic_space",
                topic_bad == 0,
                format!("invalid={topic_bad}"),
            );
            let reply_bad = count(
                &tx,
                "SELECT count(*) FROM message_relations r                  JOIN messages s ON s.message_ref=r.source_message_ref                  LEFT JOIN messages t ON t.message_ref=r.target_ref                  WHERE r.relation='reply_to' AND                  (t.message_ref IS NULL OR s.space_ref<>t.space_ref OR s.topic_ref<>t.topic_ref)"
            ).await?;
            add_check(
                "social.reply_integrity",
                reply_bad == 0,
                format!("invalid={reply_bad}"),
            );
            let cursor_bad: i64 = tx
                .query_one(
                    "SELECT count(*) FROM attention_cursors WHERE cursor>$1",
                    &[&change_high_sequence],
                )
                .await?
                .get(0);
            add_check(
                "attention.cursor_bounds",
                cursor_bad == 0,
                format!("invalid={cursor_bad};high={change_high_sequence}"),
            );
            let receipt_bad = count(
                &tx,
                "SELECT count(*) FROM command_receipts WHERE response IS NULL",
            )
            .await?;
            add_check(
                "command_receipts.complete",
                receipt_bad == 0,
                format!("incomplete={receipt_bad}"),
            );
            let history_bad = count(
                &tx,
                "SELECT count(*) FROM (                 SELECT w.work_ref,w.current_revision,count(s.revision) AS snapshots,                 min(s.revision) AS rmin,max(s.revision) AS rmax                  FROM works w LEFT JOIN work_snapshots s USING(work_ref)                  GROUP BY w.work_ref,w.current_revision                 ) x WHERE snapshots<>current_revision OR rmin<>1 OR rmax<>current_revision"
            ).await?;
            add_check(
                "work.snapshot_history_contiguous",
                history_bad == 0,
                format!("invalidWorks={history_bad}"),
            );
            if detail == "history" {
                // Use a PostgreSQL server-side Portal instead of query() or
                // fetchall(): at most 128 JSONB rows are resident per batch.
                // The transaction remains REPEATABLE READ READ ONLY.
                let portal = tx
                    .bind("SELECT snapshot_digest,payload FROM work_snapshots", &[])
                    .await?;
                let mut digest_bad: i64 = 0;
                loop {
                    let batch = tx.query_portal(&portal, 128).await?;
                    if batch.is_empty() {
                        break;
                    }
                    for row in batch {
                        let expected: String = row.get("snapshot_digest");
                        let payload: Value = row.get("payload");
                        let valid = payload.is_object()
                            && work::canonical_digest(&payload).ok().as_deref() == Some(&expected);
                        if !valid {
                            digest_bad += 1;
                        }
                    }
                }
                add_check(
                    "work.snapshot_history_digest",
                    digest_bad == 0,
                    format!("invalid={digest_bad}"),
                );
            }
            Some(json!({
                "healthy": checks.iter().all(|check| check["status"] == "ok"),
                "checks": checks,
            }))
        };
        tx.commit().await?;
        Ok(HostSummary {
            schema_version: 3,
            kind: "ordivon.host-status",
            observed_at_ms,
            detail,
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
            doctor,
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
    pub doctor: Option<Value>,
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
