//! Original Workspace reader/writer lease conflict model, without a second lock or registry.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::{Component, Path};

#[derive(Clone, Debug, Default, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceAccess {
    /// Full Workspace read access with no writes. May share with other readers.
    #[serde(default)]
    pub read_only: bool,
    /// Declared relative read sets for scoped mutable jobs; omitted means whole tree.
    #[serde(default)]
    pub read_paths: Vec<String>,
    /// Existing relative directories where writes are permitted. Omitted mutable
    /// access is exclusive. Native read-only mounts protect other Workspace paths.
    #[serde(default)]
    pub write_paths: Vec<String>,
}

fn normalized(path: &str) -> String {
    Path::new(path)
        .components()
        .filter_map(|p| match p {
            Component::Normal(v) => Some(v.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect::<Vec<_>>()
        .join("/")
}
fn overlap(a: &str, b: &str) -> bool {
    let a = normalized(a);
    let b = normalized(b);
    a.is_empty()
        || b.is_empty()
        || a == b
        || a.starts_with(&(b.clone() + "/"))
        || b.starts_with(&(a + "/"))
}
impl WorkspaceAccess {
    pub fn exclusive(&self) -> bool {
        !self.read_only && self.write_paths.is_empty()
    }
    pub fn conflicts(&self, other: &Self) -> bool {
        if self.exclusive() || other.exclusive() {
            return true;
        }
        if self.read_only && other.read_only {
            return false;
        }
        let reads = if self.read_paths.is_empty() {
            vec![".".into()]
        } else {
            self.read_paths.clone()
        };
        let other_reads = if other.read_paths.is_empty() {
            vec![".".into()]
        } else {
            other.read_paths.clone()
        };
        self.write_paths.iter().any(|w| {
            other
                .write_paths
                .iter()
                .chain(&other_reads)
                .any(|p| overlap(w, p))
        }) || other
            .write_paths
            .iter()
            .any(|w| reads.iter().any(|p| overlap(w, p)))
    }
}

#[cfg(test)]
mod scoped_workspace_business_tests {
    use super::*;

    #[test]
    fn nested_write_conflicts_with_reader_but_sibling_prefix_does_not() {
        let reader = WorkspaceAccess {
            read_only: true,
            read_paths: vec!["docs/api".to_string()],
            ..Default::default()
        };
        let conflicting_writer = WorkspaceAccess {
            write_paths: vec!["docs".to_string()],
            ..Default::default()
        };
        let sibling_writer = WorkspaceAccess {
            write_paths: vec!["docs-v2".to_string()],
            ..Default::default()
        };
        assert!(reader.conflicts(&conflicting_writer));
        assert!(conflicting_writer.conflicts(&reader));
        assert!(!reader.conflicts(&sibling_writer));
        assert!(!sibling_writer.conflicts(&reader));
        assert!(!reader.conflicts(&reader));
    }
}
