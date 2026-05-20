mod adapter;
mod authority;
mod ledger;
mod projection;
mod redteam;
mod schema;

pub use adapter::{
    AdapterContract, AdapterDispatchResult, AdapterFailureClass, MockDispatchRequest,
};
pub use redteam::{run_postgres_red_team, PostgresRedTeamRunner, RedTeamRunConfig};

use serde::Serialize;
use sqlx::{postgres::PgPoolOptions, PgPool};
use std::env;

use crate::LedgerError;

pub struct PostgresKernelStore {
    pub(crate) pool: PgPool,
}

impl PostgresKernelStore {
    pub async fn connect_from_env() -> Result<Self, LedgerError> {
        let url = database_url_from_env()?;
        let pool = PgPoolOptions::new()
            .max_connections(5)
            .connect(&url)
            .await
            .map_err(db_err)?;
        let store = Self { pool };
        store.ensure_schema().await?;
        Ok(store)
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }

    pub async fn ensure_schema(&self) -> Result<(), LedgerError> {
        schema::ensure_schema(&self.pool).await
    }

    #[cfg(test)]
    pub async fn reset_kernel_tables(&self) -> Result<(), LedgerError> {
        sqlx::query(
            "TRUNCATE TABLE
                    kernel_projection_heads,
                    kernel_seal_segments,
                    kernel_observed_events,
                    kernel_adapter_dispatches,
                    kernel_mock_records,
                    kernel_policy_decisions,
                    kernel_authority_revocations,
                    kernel_authority_uses,
                    kernel_debts,
                    kernel_ledger_events
                 RESTART IDENTITY",
        )
        .execute(&self.pool)
        .await
        .map_err(db_err)?;
        Ok(())
    }
}

pub(crate) fn database_url_from_env() -> Result<String, LedgerError> {
    env::var("ORDIVON_APP_DATABASE_URL")
        .or_else(|_| env::var("ORDIVON_TEST_DATABASE_URL"))
        .or_else(|_| env::var("ORDIVON_DB_URL"))
        .map_err(|_| {
            LedgerError::Database(
                "ORDIVON_APP_DATABASE_URL, ORDIVON_TEST_DATABASE_URL, or ORDIVON_DB_URL is required"
                    .to_string(),
            )
        })
}

pub fn migration_database_url_from_env() -> Result<String, LedgerError> {
    env::var("ORDIVON_MIGRATION_DATABASE_URL")
        .or_else(|_| env::var("ORDIVON_TEST_DATABASE_URL"))
        .or_else(|_| env::var("ORDIVON_DB_URL"))
        .map_err(|_| {
            LedgerError::Database(
                "ORDIVON_MIGRATION_DATABASE_URL, ORDIVON_TEST_DATABASE_URL, or ORDIVON_DB_URL is required"
                    .to_string(),
            )
        })
}

pub fn test_admin_database_url_from_env() -> Result<String, LedgerError> {
    env::var("ORDIVON_TEST_ADMIN_DATABASE_URL")
        .or_else(|_| env::var("ORDIVON_TEST_DATABASE_URL"))
        .or_else(|_| env::var("ORDIVON_DB_URL"))
        .map_err(|_| {
            LedgerError::Database(
                "ORDIVON_TEST_ADMIN_DATABASE_URL, ORDIVON_TEST_DATABASE_URL, or ORDIVON_DB_URL is required"
                    .to_string(),
            )
        })
}

pub(crate) fn db_err(err: sqlx::Error) -> LedgerError {
    LedgerError::Database(err.to_string())
}

pub(crate) fn enum_str<T: Serialize>(value: &T) -> String {
    serde_json::to_value(value)
        .ok()
        .and_then(|value| value.as_str().map(ToString::to_string))
        .unwrap_or_else(|| "UNKNOWN".to_string())
}
