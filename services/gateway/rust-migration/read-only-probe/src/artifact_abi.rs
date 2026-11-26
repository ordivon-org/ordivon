//! Directional v1 projection and separate private retained-byte evidence kind.
//! No public route/version change, no authority, no semantic completion.
use crate::{
    artifact_chunk::{self, Window},
    artifact_descriptor::Descriptor,
    artifact_stream::Standing,
};
use rmcp::schemars;
use serde::Serialize;
use serde_json::{Value, json};

#[derive(Debug, Serialize)]
pub(crate) struct ArtifactChunkV1<'a> {
    schema_version: u8,
    kind: &'static str,
    operation_ref: &'a str,
    owner_id: &'a str,
    native_id: &'a str,
    artifact_id: &'a str,
    offset: u64,
    next_offset: u64,
    eof: bool,
    digest: &'a str,
    content: &'a str,
}
pub(crate) fn project(input: &Value) -> Value {
    let reference = input["operationRef"].as_str().unwrap_or_default();
    match artifact_chunk::qualify(
        reference,
        &input["descriptor"],
        &input["request"],
        &input["response"],
    ) {
        Window::Unobserved { reason } => json!({"standing":"unobserved","reason":reason}),
        Window::Qualified {
            owner,
            native_id,
            artifact_id,
            digest,
            offset,
            next_offset,
            eof,
            content,
            ..
        } => {
            json!({"standing":"qualified","chunk":ArtifactChunkV1{schema_version:1,kind:"ordivon.gateway-artifact-chunk",
                operation_ref:reference,owner_id:owner,native_id,artifact_id,offset,next_offset,eof,digest,content}})
        }
    }
}

#[derive(Debug, Serialize, schemars::JsonSchema)]
#[schemars(crate = "rmcp::schemars")]
#[serde(deny_unknown_fields)]
pub(crate) struct RetainedEvidence {
    #[schemars(extend("const"=1))]
    schema_version: u8,
    #[schemars(extend("const"="ordivon.gateway-artifact-retained-byte-evidence"))]
    kind: &'static str,
    #[schemars(extend("const"="non-authoritative-retained-byte-verification"))]
    truth_role: &'static str,
    operation_ref: String,
    descriptor: Descriptor,
    evidence: Standing,
}
impl RetainedEvidence {
    pub(crate) fn new(operation_ref: String, descriptor: Descriptor, evidence: Standing) -> Self {
        Self {
            schema_version: 1,
            kind: "ordivon.gateway-artifact-retained-byte-evidence",
            truth_role: "non-authoritative-retained-byte-verification",
            operation_ref,
            descriptor,
            evidence,
        }
    }
}
pub(crate) fn schema() -> Value {
    serde_json::to_value(schemars::schema_for!(RetainedEvidence)).expect("schema serialization")
}
