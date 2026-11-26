//! Typed WebAuthn verifier protocol over shared process transport.
use super::super::carrier::{CarrierError, JsonCarrier};
use serde::Deserialize;
use serde_json::Value;
use std::{path::Path, time::Duration};
#[derive(Clone)]
pub struct LocalVerifier(JsonCarrier);
#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub(super) enum Reply {
    Options { options: Value },
    Verified { counter: u32 },
    Denied,
}
impl LocalVerifier {
    pub fn new(
        node: &Path,
        script: &Path,
        max_parallel: usize,
        deadline: Duration,
    ) -> std::io::Result<Self> {
        Ok(Self(JsonCarrier::new(
            node,
            script,
            max_parallel,
            deadline,
        )?))
    }
    pub(super) async fn call(&self, request: Value) -> Result<Reply, CarrierError> {
        self.0.call(request).await
    }
}
