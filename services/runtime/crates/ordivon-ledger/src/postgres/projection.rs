use sqlx::Row;

use super::{db_err, PostgresKernelStore};
use crate::{build_projection_manifest, LedgerError, ProjectionManifest, GENESIS_DIGEST};

impl PostgresKernelStore {
    pub async fn build_and_store_projection(
        &self,
        projection_id: &str,
        rebuilt_at: &str,
    ) -> Result<ProjectionManifest, LedgerError> {
        let events = self.read_events().await?;
        let manifest = build_projection_manifest(projection_id, &events, rebuilt_at)?;
        sqlx::query(
                "INSERT INTO kernel_projection_heads
                 (projection_id, source_first_seq, source_last_seq, event_count, head_hash, rebuilt_at)
                 VALUES ($1,$2,$3,$4,$5,$6)
                 ON CONFLICT (projection_id) DO UPDATE SET
                    source_first_seq = EXCLUDED.source_first_seq,
                    source_last_seq = EXCLUDED.source_last_seq,
                    event_count = EXCLUDED.event_count,
                    head_hash = EXCLUDED.head_hash,
                    rebuilt_at = EXCLUDED.rebuilt_at",
            )
            .bind(&manifest.projection_id)
            .bind(manifest.source_first_seq as i64)
            .bind(manifest.source_last_seq as i64)
            .bind(manifest.event_count as i64)
            .bind(&manifest.head_hash)
            .bind(&manifest.rebuilt_at)
            .execute(&self.pool)
            .await
            .map_err(db_err)?;
        Ok(manifest)
    }

    pub async fn verify_projection(&self, projection_id: &str) -> Result<(), LedgerError> {
        let row =
            sqlx::query("SELECT head_hash FROM kernel_projection_heads WHERE projection_id = $1")
                .bind(projection_id)
                .fetch_one(&self.pool)
                .await
                .map_err(db_err)?;
        let expected: String = row.get("head_hash");
        let actual = self
            .read_events()
            .await?
            .last()
            .map(|event| event.event_hash.clone())
            .unwrap_or_else(|| GENESIS_DIGEST.to_string());
        if expected != actual {
            return Err(LedgerError::ProjectionDrift { expected, actual });
        }
        Ok(())
    }
}
