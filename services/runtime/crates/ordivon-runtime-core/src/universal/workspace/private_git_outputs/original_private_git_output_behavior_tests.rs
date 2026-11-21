// Verify delivered-output semantics at the Git boundary rather than asserting
// any Rust source filename, function body, or module layout. These cases also
// prevent a false-green when the root worktree itself remains unmodified.
use super::*;

fn git(args: &[&str]) -> String {
    let output = workspace_git_command()
        .args(args)
        .output()
        .expect("native Git must be available");
    assert!(
        output.status.success(),
        "git {:?}: {}",
        args,
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout)
        .expect("Git output must be UTF-8")
        .trim()
        .to_owned()
}

fn original_with_private_index() -> (
    tempfile::TempDir,
    std::path::PathBuf,
    std::path::PathBuf,
    String,
) {
    let temp = tempfile::tempdir().expect("isolated original Git source");
    let source = temp.path().join("original");
    let private = temp.path().join("agent-git");
    fs::create_dir(&source).unwrap();
    let source_path = source.to_str().unwrap();
    let private_path = private.to_str().unwrap();
    git(&["-C", source_path, "init", "-q"]);
    git(&["-C", source_path, "config", "user.name", "Native Git Test"]);
    git(&[
        "-C",
        source_path,
        "config",
        "user.email",
        "test@example.invalid",
    ]);
    fs::write(source.join("tracked.txt"), b"original bytes").unwrap();
    git(&["-C", source_path, "add", "tracked.txt"]);
    git(&["-C", source_path, "commit", "-qm", "original"]);
    let revision = git(&["-C", source_path, "rev-parse", "HEAD"]);
    git(&["init", "--quiet", "--bare", private_path]);
    git(&[
        "--git-dir",
        private_path,
        "fetch",
        "--no-tags",
        "--depth=1",
        source_path,
        &revision,
    ]);
    git(&[
        "--git-dir",
        private_path,
        "update-ref",
        "refs/heads/agent-work",
        &revision,
    ]);
    git(&[
        "--git-dir",
        private_path,
        "symbolic-ref",
        "HEAD",
        "refs/heads/agent-work",
    ]);
    git(&[
        "--git-dir",
        private_path,
        "--work-tree",
        source_path,
        "read-tree",
        "HEAD",
    ]);
    assert!(
        !workspace_private_git_has_outputs(&private, &revision).unwrap(),
        "an unchanged private snapshot is not a consumer hold"
    );
    (temp, source, private, revision)
}

#[test]
fn private_empty_commit_is_unreceived_even_with_identical_original_source_bytes() {
    let (_tmp, source, private, revision) = original_with_private_index();
    let root = source.to_str().unwrap();
    let git_dir = private.to_str().unwrap();
    git(&[
        "--git-dir",
        git_dir,
        "--work-tree",
        root,
        "-c",
        "user.name=Private Output Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--allow-empty",
        "-qm",
        "only private Git has an output",
    ]);
    assert_eq!(
        fs::read(source.join("tracked.txt")).unwrap(),
        b"original bytes"
    );
    assert!(
        workspace_private_git_has_outputs(&private, &revision).unwrap(),
        "a unique private commit must block close until an independent receiver accepts it"
    );
}

#[test]
fn staged_only_private_output_blocks_close_even_after_source_bytes_are_restored() {
    let (_tmp, source, private, revision) = original_with_private_index();
    let root = source.to_str().unwrap();
    let git_dir = private.to_str().unwrap();
    fs::write(source.join("tracked.txt"), b"staged candidate bytes").unwrap();
    git(&[
        "--git-dir",
        git_dir,
        "--work-tree",
        root,
        "add",
        "tracked.txt",
    ]);
    fs::write(source.join("tracked.txt"), b"original bytes").unwrap();
    assert_eq!(
        fs::read(source.join("tracked.txt")).unwrap(),
        b"original bytes"
    );
    assert!(
        workspace_private_git_has_outputs(&private, &revision).unwrap(),
        "the private index is an output consumer even with a clean original worktree"
    );
    git(&[
        "--git-dir",
        git_dir,
        "--work-tree",
        root,
        "reset",
        "-q",
        "HEAD",
        "--",
        "tracked.txt",
    ]);
    assert!(
        !workspace_private_git_has_outputs(&private, &revision).unwrap(),
        "retiring the only private staged candidate must restore normal cleanup eligibility"
    );
}
