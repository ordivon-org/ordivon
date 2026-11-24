"""Known control-input qualification for read-only Owner impact projection.

This does not attest dynamic inputs, a full dependency graph or proof reuse.
It rejects mixing a historical Git diff with a different local policy cut.
"""
from __future__ import annotations

from pathlib import Path

from source_history_legos import current_tree, git

# Bounded direct producer inputs of the current selector. The later
# pg_issuer_consumer adapter is checked if present in the target tree.
CONTROL_INPUTS = (
    "tools/repo/evidence_validity.py",
    "tools/repo/evidence_github_checks.py",
    "tools/repo/evidence_check_decision.py",
    "tools/repo/evidence_source_policy.py",
    "tools/repo/source_history_legos.py",
    "tools/repo/convergence_plan.py",
    "tools/repo/affected_owners.py",
    "tools/repo/owners.toml",
    "tools/repo/dependency_contracts.toml",
    "tools/formal/verify.py",
    "docs/architecture/structure-r2-transition-r1.json",
    "mise.toml",
)


def qualify_current_selector(repo: Path, source_cut: str) -> None:
    repo = repo.resolve()
    producer_root = Path(__file__).resolve().parents[2]
    if (
        repo != producer_root
        or git(repo, "rev-parse", "HEAD").strip() != source_cut
    ):
        raise ValueError("selector policy checkout differs from requested SourceCut")
    tree = current_tree(repo, source_cut)
    paths = (*CONTROL_INPUTS, "tools/repo/pg_issuer_consumer.py") if (
        "tools/repo/pg_issuer_consumer.py" in tree
    ) else CONTROL_INPUTS
    for relative in paths:
        file = repo / relative
        identity = tree.get(relative, "")
        if (
            not identity.startswith(("100644:blob:", "100755:blob:"))
            or not file.is_file()
            or file.is_symlink()
            or file.resolve() != file
        ):
            raise ValueError("selector control input is not a regular Git file")
        actual = git(repo, "hash-object", "--no-filters", "--", relative).strip()
        if actual != identity.rsplit(":", 1)[1]:
            raise ValueError(f"selector control input differs from SourceCut: {relative}")
