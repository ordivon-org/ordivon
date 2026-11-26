//! Original Workspace reader/writer lease conflict model, without a second lock or registry.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::{Component, Path};

#[derive(Clone, Debug, Default, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceAccess {
    /// Declares no Workspace writes. May share with other readers.
    #[serde(default)]
    pub read_only: bool,
    /// Declared relative input dependencies for lease conflicts and source commitments.
    /// Omitted means the whole tree. This is not OS-enforced read confinement.
    #[serde(default)]
    pub read_paths: Vec<String>,
    /// Existing relative directories where writes are permitted. Omitted mutable
    /// access is exclusive. Linux native read-only mounts protect other Workspace
    /// paths during ordinary execution; this is not a privileged-process sandbox.
    #[serde(default)]
    pub write_paths: Vec<String>,
}

// Prefix comparison over borrowed native path components. Ignore the same
// non-Normal components as the original normalization; an empty prefix is
// the entire tree. This does not replace admission path validation.
fn overlap(a: &str, b: &str) -> bool {
    let normal = |component| match component {
        Component::Normal(value) => Some(value),
        _ => None,
    };
    Path::new(a)
        .components()
        .filter_map(normal)
        .zip(Path::new(b).components().filter_map(normal))
        .all(|(left, right)| left == right)
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
        // An omitted read set means the whole tree, not an empty set.
        // Short-circuit that wildcard before any pairwise component checks.
        if (!self.write_paths.is_empty() && other.read_paths.is_empty())
            || (!other.write_paths.is_empty() && self.read_paths.is_empty())
        {
            return true;
        }
        self.write_paths.iter().any(|w| {
            other
                .write_paths
                .iter()
                .chain(&other.read_paths)
                .any(|p| overlap(w, p))
        }) || other
            .write_paths
            .iter()
            .any(|w| self.read_paths.iter().any(|p| overlap(w, p)))
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
    // Exact previous operator retained only as a differential test oracle.
    fn reference_normalized(path: &str) -> String {
        Path::new(path)
            .components()
            .filter_map(|p| match p {
                Component::Normal(v) => Some(v.to_string_lossy().into_owned()),
                _ => None,
            })
            .collect::<Vec<_>>()
            .join("/")
    }
    fn reference_overlap(a: &str, b: &str) -> bool {
        let a = reference_normalized(a);
        let b = reference_normalized(b);
        a.is_empty()
            || b.is_empty()
            || a == b
            || a.starts_with(&(b.clone() + "/"))
            || b.starts_with(&(a + "/"))
    }
    fn reference_conflicts(a: &WorkspaceAccess, other: &WorkspaceAccess) -> bool {
        if a.exclusive() || other.exclusive() {
            return true;
        }
        if a.read_only && other.read_only {
            return false;
        }
        let reads = if a.read_paths.is_empty() {
            vec![".".into()]
        } else {
            a.read_paths.clone()
        };
        let other_reads = if other.read_paths.is_empty() {
            vec![".".into()]
        } else {
            other.read_paths.clone()
        };
        a.write_paths.iter().any(|w| {
            other
                .write_paths
                .iter()
                .chain(&other_reads)
                .any(|p| reference_overlap(w, p))
        }) || other
            .write_paths
            .iter()
            .any(|w| reads.iter().any(|p| reference_overlap(w, p)))
    }

    fn access_strategy() -> impl proptest::strategy::Strategy<Value = WorkspaceAccess> {
        use proptest::prelude::*;
        let path = || {
            prop::sample::select(vec![
                ".".to_string(),
                "./a".to_string(),
                "a//b".to_string(),
                "a/b/c".to_string(),
                "a-b".to_string(),
                "a".to_string(),
                "a/.".to_string(),
                "中文/路径".to_string(),
                "中文".to_string(),
                "A".to_string(),
                "a/b".to_string(),
                "a/bb".to_string(),
                "../a".to_string(),
                "/a".to_string(),
                "".to_string(),
                "a\\b".to_string(),
                "a\\b/c".to_string(),
            ])
        };
        (
            any::<bool>(),
            prop::collection::vec(path(), 0..8),
            prop::collection::vec(path(), 0..8),
        )
            .prop_map(|(read_only, read_paths, write_paths)| WorkspaceAccess {
                read_only,
                read_paths,
                write_paths,
            })
    }

    proptest::proptest! {
        #![proptest_config(proptest::test_runner::Config::with_cases(2048))]
        #[test]
        fn borrowed_operator_preserves_previous_conflict_relation(
            a in access_strategy(), b in access_strategy()
        ) {
            proptest::prop_assert_eq!(a.conflicts(&b), reference_conflicts(&a, &b));
            proptest::prop_assert_eq!(a.conflicts(&b), b.conflicts(&a));
        }
    }

    #[test]
    fn explicit_disjoint_writers_share_input_but_omitted_reads_conflict() {
        let left = WorkspaceAccess {
            read_paths: vec!["input".into()],
            write_paths: vec!["output/left".into()],
            ..Default::default()
        };
        let right = WorkspaceAccess {
            read_paths: vec!["input".into()],
            write_paths: vec!["output/right".into()],
            ..Default::default()
        };
        assert!(!left.conflicts(&right));
        let wildcard = WorkspaceAccess {
            read_paths: vec![],
            ..right.clone()
        };
        assert!(left.conflicts(&wildcard));
        assert!(wildcard.conflicts(&left));
        assert!(left.conflicts(&WorkspaceAccess::default()));
        assert!(left.conflicts(&WorkspaceAccess {
            read_only: true,
            read_paths: vec!["output".into()],
            ..Default::default()
        }));
    }
}
