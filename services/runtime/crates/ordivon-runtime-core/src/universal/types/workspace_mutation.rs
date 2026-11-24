//! Original workspace mutation behavior and native data contract.
use super::{
    default_schema_version, invalid, require_schema, valid_digest, validate_id,
    validate_relative_path, UniversalExecError, MAX_WORKSPACE_IO_BYTES, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
#[schemars(inline)]
pub enum WorkspaceMutationMode {
    Write,
    Append,
    ReplaceExact,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceMutation {
    pub relative_path: String,
    pub mode: WorkspaceMutationMode,
    #[serde(default)]
    pub content: String,
    /// Required when the target already exists; protects the complete file version.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expected_digest: Option<String>,
    /// Required only for REPLACE_EXACT; must occur exactly once in the current file.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expected_text: Option<String>,
}

impl WorkspaceMutation {
    fn validate_shape(&self, mutation_index: usize) -> Result<(), UniversalExecError> {
        validate_relative_path(
            &self.relative_path,
            &format!("mutations[{mutation_index}].relativePath"),
        )?;
        if self.content.len() as u64 > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("mutation content exceeds {MAX_WORKSPACE_IO_BYTES} bytes"),
                format!("mutations[{mutation_index}].content"),
            ));
        }
        if self
            .expected_digest
            .as_ref()
            .is_some_and(|digest| !valid_digest(digest))
        {
            return Err(invalid(
                "expectedDigest must be canonical lowercase SHA-256",
                format!("mutations[{mutation_index}].expectedDigest"),
            ));
        }
        match self.mode {
            WorkspaceMutationMode::ReplaceExact => {
                let expected = self.expected_text.as_ref().ok_or_else(|| {
                    invalid(
                        "REPLACE_EXACT requires expectedText",
                        format!("mutations[{mutation_index}].expectedText"),
                    )
                })?;
                if expected.is_empty() || expected.len() as u64 > MAX_WORKSPACE_IO_BYTES {
                    return Err(invalid(
                        "expectedText must be non-empty and bounded",
                        format!("mutations[{mutation_index}].expectedText"),
                    ));
                }
            }
            WorkspaceMutationMode::Write | WorkspaceMutationMode::Append => {
                if self.expected_text.is_some() {
                    return Err(invalid(
                        "expectedText is only valid for REPLACE_EXACT",
                        format!("mutations[{mutation_index}].expectedText"),
                    ));
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceMutateRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[schemars(length(min = 1))]
    pub mutations: Vec<WorkspaceMutation>,
}

impl WorkspaceMutateRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        if self.mutations.is_empty() {
            return Err(invalid("mutations must not be empty", "mutations"));
        }
        let mut paths = BTreeSet::new();
        for (mutation_index, mutation) in self.mutations.iter().enumerate() {
            mutation.validate_shape(mutation_index)?;
            if !paths.insert(&mutation.relative_path) {
                return Err(invalid(
                    "a batch cannot mutate the same path more than once",
                    format!("mutations[{mutation_index}].relativePath"),
                ));
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceMutationResult {
    pub relative_path: String,
    pub after_digest: String,
    pub byte_length: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceMutateResult {
    pub mutations: Vec<WorkspaceMutationResult>,
}

#[cfg(test)]
mod workspace_batch_behavior_tests {
    use super::*;

    fn write(path: &str) -> WorkspaceMutation {
        WorkspaceMutation {
            relative_path: path.to_owned(),
            mode: WorkspaceMutationMode::Write,
            content: "original-byte".to_owned(),
            expected_digest: None,
            expected_text: None,
        }
    }

    #[test]
    fn batch_rejects_same_physical_path_twice_before_any_write() {
        let mut request = WorkspaceMutateRequest {
            schema_version: 1,
            workspace_id: "ws-native-original".to_owned(),
            mutations: vec![write("src/original.rs"), write("src/other.rs")],
        };
        assert!(request.validate_shape().is_ok());
        request.mutations[1].relative_path = request.mutations[0].relative_path.clone();
        let error = request
            .validate_shape()
            .expect_err("duplicate writes are ambiguous");
        assert_eq!(error.field.as_deref(), Some("mutations[1].relativePath"));
        assert!(error.message.contains("same path"));
        request.mutations.pop();
        assert!(request.validate_shape().is_ok());
    }

    #[test]
    fn exact_replacement_requires_original_fragment_and_nonexact_write_must_not_claim_it() {
        let mut request = WorkspaceMutateRequest {
            schema_version: 1,
            workspace_id: "ws-native-original".to_owned(),
            mutations: vec![write("src/readme.txt")],
        };
        request.mutations[0].mode = WorkspaceMutationMode::ReplaceExact;
        assert!(request.validate_shape().is_err());
        request.mutations[0].expected_text = Some("one original fragment".to_owned());
        assert!(request.validate_shape().is_ok());
        request.mutations[0].mode = WorkspaceMutationMode::Append;
        assert!(request.validate_shape().is_err());
        request.mutations[0].expected_text = None;
        assert!(request.validate_shape().is_ok());
    }
}
