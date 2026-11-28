// Original PG ReleaseEffect independent current PG release-qualified source stamp.
use super::{io, PgRuntime, RuntimeResult};

/// A PG-native release is a distinct durable Effect, not a generic Runner Job.
/// Only admit after the MCP adapter independently verifies the configured
/// operator/service, exact Git owner revision and immutable candidate manifest.
/// The independent installed systemd operator, not Runtime's generic scheduler,
/// consumes the accepted side row and attests installed bytes and live MCP.
impl PgRuntime {
    /// Release advertisement needs independently qualified durable authority.
    /// Querying the app role cannot grant the qualification itself.
    pub fn release_qualified(&self) -> RuntimeResult<bool> {
        let mut db = self.store()?;
        let row=db.client.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='release'",
            &[],
        ).map_err(io)?;
        Ok(row.is_some_and(|row| {
            row.get::<_, String>(0) == "QUALIFIED_RELEASE"
                && row.get::<_, String>(1) == self.config.source_sha256
                && row.get::<_, bool>(2)
        }))
    }
}
