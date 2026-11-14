//! Read-only Provider endpoint/configuration snapshot, bound through an
//! existing Harness RunContract.sourceRefs CAS reference.
//!
//! A caller-created JSON object is NEVER sufficient. Only A's PG readback
//! can create an ObservedProviderTransport, and it is NOT a lease, current
//! Provider dispatch grant, Security credential, or billing authorization.
use crate::pg_domain_read::ObservedNoToolRun;
use ordivon_harness_core::CanonicalDocument;
use ordivon_harness_pg::{read_cas_object_readonly, read_run_readonly, ReadError};
use postgres::Client;
use reqwest::Url;
use std::fmt;

pub const SOURCE_KIND: &str = "harness-provider-transport-snapshot";

#[derive(Debug)]
pub enum ProviderTransportError {
    Store(ReadError),
    SourceNotBound,
    InvalidSource,
    ContractDrift,
}
impl From<ReadError> for ProviderTransportError {
    fn from(value: ReadError) -> Self {
        Self::Store(value)
    }
}
struct SourceFields {
    endpoint: String,
    credential_ref: String,
}
fn validate_source(
    doc: &CanonicalDocument,
    provider_id: &str,
    adapter_id: &str,
    model_id: &str,
) -> Result<SourceFields, ProviderTransportError> {
    if doc.object_len() != Some(7)
        || doc.field("schemaVersion").and_then(|v| v.integer_text()) != Some("1")
        || doc.field("kind").and_then(|v| v.as_str())
            != Some("ordivon.harness-provider-transport-snapshot")
        || doc.field("providerId").and_then(|v| v.as_str()) != Some(provider_id)
        || doc.field("adapterId").and_then(|v| v.as_str()) != Some(adapter_id)
        || doc.field("requestedModelId").and_then(|v| v.as_str()) != Some(model_id)
    {
        return Err(ProviderTransportError::InvalidSource);
    }
    let endpoint = doc
        .field("endpoint")
        .and_then(|v| v.as_str())
        .ok_or(ProviderTransportError::InvalidSource)?;
    let url = Url::parse(endpoint).map_err(|_| ProviderTransportError::InvalidSource)?;
    let loopback = url.scheme() == "http" && url.host_str() == Some("127.0.0.1");
    if !(url.scheme() == "https" || loopback)
        || url.username() != ""
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
        || !url.has_host()
        || !url.path().starts_with('/')
        || endpoint.len() > 2048
    {
        return Err(ProviderTransportError::InvalidSource);
    }
    let credential_ref = doc
        .field("credentialRef")
        .and_then(|v| v.as_str())
        .ok_or(ProviderTransportError::InvalidSource)?;
    if !credential_ref.starts_with("credential:")
        || credential_ref.trim() != credential_ref
        || credential_ref.len() > 300
        || credential_ref.len() <= "credential:".len()
    {
        return Err(ProviderTransportError::InvalidSource);
    }
    Ok(SourceFields {
        endpoint: endpoint.to_string(),
        credential_ref: credential_ref.to_string(),
    })
}

/// Private constructor: only exact authentic PG sourceRef/CAS and matched
/// Contract/model identity allow this *observation*. No dispatch permission.
pub struct ObservedProviderTransport {
    run_id: String,
    contract_digest: String,
    source_digest: String,
    endpoint: String,
    credential_ref: String,
    model_id: String,
}
impl fmt::Debug for ObservedProviderTransport {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("ObservedProviderTransport")
            .field("run_id", &self.run_id)
            .field("contract_digest", &self.contract_digest)
            .field("source_digest", &self.source_digest)
            .field("endpoint", &"<redacted>")
            .field("credential_ref", &"<redacted>")
            .finish()
    }
}
impl ObservedProviderTransport {
    pub fn run_id(&self) -> &str {
        &self.run_id
    }
    pub fn contract_digest(&self) -> &str {
        &self.contract_digest
    }
    pub fn source_digest(&self) -> &str {
        &self.source_digest
    }
    pub fn endpoint(&self) -> &str {
        &self.endpoint
    }
    pub fn credential_ref(&self) -> &str {
        &self.credential_ref
    }
    pub fn model_id(&self) -> &str {
        &self.model_id
    }
}

/// The transport snapshot is carried by the original RunContract sourceRefs
/// and backed by the EXISTING PostgreSQL CAS. The Run/lease may change after
/// this observation; the caller must recheck dispatch currentness elsewhere.
pub fn inspect_pg_provider_transport(
    connection: &mut Client,
    schema: &str,
    verified: &ObservedNoToolRun,
) -> Result<ObservedProviderTransport, ProviderTransportError> {
    let read = read_run_readonly(connection, schema, verified.run_id())?;
    if read.projection.contract_digest != verified.contract_digest()
        || !matches!(read.projection.status.as_str(), "created" | "active")
    {
        return Err(ProviderTransportError::ContractDrift);
    }
    let doc = &read.contract;
    let provider_id = doc
        .field("providerId")
        .and_then(|v| v.as_str())
        .ok_or(ProviderTransportError::InvalidSource)?;
    let adapter_id = doc
        .field("adapterId")
        .and_then(|v| v.as_str())
        .ok_or(ProviderTransportError::InvalidSource)?;
    let model_id = doc
        .field("requestedModelId")
        .and_then(|v| v.as_str())
        .ok_or(ProviderTransportError::InvalidSource)?;
    if provider_id != verified.provider_id()
        || adapter_id != verified.adapter_id()
        || model_id != verified.model_id()
    {
        return Err(ProviderTransportError::ContractDrift);
    }
    let sources = doc
        .field("sourceRefs")
        .ok_or(ProviderTransportError::InvalidSource)?;
    let n = sources
        .array_len()
        .ok_or(ProviderTransportError::InvalidSource)?;
    let mut bound_digest: Option<String> = None;
    for i in 0..n {
        let item = sources
            .index(i)
            .ok_or(ProviderTransportError::InvalidSource)?;
        if item.field("kind").and_then(|v| v.as_str()) != Some(SOURCE_KIND) {
            continue;
        }
        if bound_digest.is_some()
            || item
                .field("ref")
                .and_then(|v| v.as_str())
                .is_none_or(|v| !v.starts_with("provider-config:"))
        {
            return Err(ProviderTransportError::SourceNotBound);
        }
        let digest = item
            .field("digest")
            .and_then(|v| v.as_str())
            .ok_or(ProviderTransportError::InvalidSource)?;
        bound_digest = Some(digest.to_string());
    }
    let bound_digest = bound_digest.ok_or(ProviderTransportError::SourceNotBound)?;
    let config = read_cas_object_readonly(connection, schema, &bound_digest, SOURCE_KIND)?;
    let source = validate_source(&config, provider_id, adapter_id, model_id)?;
    Ok(ObservedProviderTransport {
        run_id: verified.run_id().to_string(),
        contract_digest: verified.contract_digest().to_string(),
        source_digest: bound_digest,
        endpoint: source.endpoint,
        credential_ref: source.credential_ref,
        model_id: model_id.to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::loads_strict;

    #[test]
    fn rejects_unrelated_model_endpoint_and_embedded_secret() {
        let positive=loads_strict(r#"{"adapterId":"adapter:test","credentialRef":"credential:test","endpoint":"https://example.invalid/v1/chat/completions","kind":"ordivon.harness-provider-transport-snapshot","providerId":"provider:test","requestedModelId":"model:test","schemaVersion":1}"#).unwrap();
        assert!(validate_source(&positive, "provider:test", "adapter:test", "model:test").is_ok());
        assert!(
            validate_source(&positive, "provider:foreign", "adapter:test", "model:test").is_err()
        );
        assert!(
            validate_source(&positive, "provider:test", "adapter:test", "model:foreign").is_err()
        );
        for endpoint in [
            "http://example.com/v1/chat/completions",
            "https://user:secret@example.com/v1/chat/completions",
            "https://example.com/v1/chat/completions?token=x",
        ] {
            let value=loads_strict(&format!(
                r#"{{"adapterId":"adapter:test","credentialRef":"credential:test","endpoint":"{endpoint}","kind":"ordivon.harness-provider-transport-snapshot","providerId":"provider:test","requestedModelId":"model:test","schemaVersion":1}}"#)).unwrap();
            assert!(
                validate_source(&value, "provider:test", "adapter:test", "model:test").is_err()
            );
        }
        let extra=loads_strict(r#"{"adapterId":"adapter:test","credentialRef":"credential:test","endpoint":"https://example.invalid/v1/chat/completions","kind":"ordivon.harness-provider-transport-snapshot","providerId":"provider:test","requestedModelId":"model:test","schemaVersion":1,"apiKey":"should-not-be-in-pg"}"#).unwrap();
        assert!(validate_source(&extra, "provider:test", "adapter:test", "model:test").is_err());
    }
}
