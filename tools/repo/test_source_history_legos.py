"""Native source graph LEGO: two-sided exact patch classes and no false consumer claims."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.repo import source_history_legos
from tools.repo.source_history_legos import history

CANONICAL_OWNER_HEADER = (
    'schema_version = 1\n'
    'truth_role = "repository-mechanics-only-not-domain-authority"\n'
)


def git(p: Path, *args: str) -> str:
    # Synthetic repositories must not spawn background maintenance while
    # TemporaryDirectory is removing their .git trees (Python 3.15).
    return subprocess.check_output(
        ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0", "-C", str(p), *args],
        text=True,
    ).strip()



class SourceHistoryLegosTests(unittest.TestCase):
    def test_complete_graph_and_patch_equivalence_no_automatic_retirement(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-legos-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            owner = root / "tools/repo/owners.toml"
            owner.parent.mkdir(parents=True)
            owner.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            (root / "README").write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            tracked = root / "services/runtime/contract.txt"
            tracked.parent.mkdir(parents=True)
            tracked.write_text("same property\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local property")
            local_patch = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            tracked.parent.mkdir(parents=True, exist_ok=True)
            tracked.write_text("same property\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "equivalent remote property")
            remote_patch = git(root, "rev-parse", "HEAD")
            (root / "remote-only.txt").write_text("remote unique\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote unique")

            projection = history(root, "main", "remote-main")
            self.assertEqual(projection["counts"], {"local": 1, "remote": 2})
            records = {record["commit"]: record for record in projection["commits"]}
            self.assertEqual(
                records[local_patch]["patchRelation"], "PATCH_ID_EQUIVALENT"
            )
            self.assertEqual(
                records[remote_patch]["patchRelation"], "PATCH_ID_EQUIVALENT"
            )
            self.assertEqual(records[local_patch]["owners"], ["runtime"])
            self.assertEqual(
                records[local_patch]["pathRelations"], {"SAME_BLOB_AND_MODE": 1}
            )
            for record in records.values():
                self.assertEqual(
                    record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
                )
            self.assertEqual(
                sum(projection["patchClasses"].values()),
                sum(projection["counts"].values()),
            )
            # Independently scoped agents must see only their Owner's commits
            # while retaining exact immutable global source identity.
            runtime = source_history_legos.owner_slice(projection, "runtime")
            self.assertEqual(runtime["sourceCut"], projection["sourceCut"])
            self.assertEqual(runtime["counts"], {"local": 1, "remote": 1})
            self.assertEqual(runtime["unfilteredCounts"], projection["counts"])
            self.assertEqual(
                {entry["commit"] for entry in runtime["commits"]},
                {local_patch, remote_patch},
            )
            self.assertTrue(all(
                entry["consumerQualification"] == "UNKNOWN_REQUIRES_OWNER_CDC"
                for entry in runtime["commits"]
            ))
            unmapped = source_history_legos.owner_slice(projection, "ROOT_UNOWNED")
            self.assertEqual(unmapped["counts"], {"local": 0, "remote": 1})
            self.assertEqual(
                {entry["commit"] for entry in runtime["commits"]}.union(
                    entry["commit"] for entry in unmapped["commits"]
                ),
                set(records),
            )
            with self.assertRaisesRegex(ValueError, "unknown Owner"):
                source_history_legos.owner_slice(projection, "missing-owner")
            # A forged global count must not permit a false complete Owner view.
            altered = {**projection, "counts": {"local": 2, "remote": 2}}
            with self.assertRaisesRegex(ValueError, "DAG coverage mismatch"):
                source_history_legos.owner_slice(altered, "runtime")
            # Agent CLI yields a small source-bound subset, not the full DAG.
            cli = json.loads(subprocess.check_output(
                [
                    sys.executable,
                    str(Path(__file__).with_name("source_history_legos.py")),
                    "--repo", str(root),
                    "--left", "main",
                    "--right", "remote-main",
                    "--owner", "runtime",
                ],
                text=True,
            ))
            self.assertEqual(cli, runtime)

    def test_declared_owner_with_no_commits_has_valid_zero_delta_view(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-empty-owner-cut-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
                + '[[owners]]\nname = "harness"\nroot = "services/harness/"\n'
                + 'verify_task = "harness:verify"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "registered owners but no effects")
            git(root, "branch", "remote-main")
            report = history(root, "main", "remote-main")
            self.assertEqual(report["counts"], {"local": 0, "remote": 0})
            for owner in ("runtime", "harness", "tools/repo"):
                scoped = source_history_legos.owner_slice(report, owner)
                self.assertEqual(scoped["counts"], {"local": 0, "remote": 0})
                self.assertEqual(scoped["commits"], [])
                self.assertEqual(scoped["sourceCut"], report["sourceCut"])
            with self.assertRaisesRegex(ValueError, "unknown Owner"):
                source_history_legos.owner_slice(report, "phantom")
            target = root / "services/runtime/safe.txt"
            target.parent.mkdir(parents=True)
            target.write_text("runtime newer\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "runtime only")
            changed = history(root, "main", "remote-main")
            runtime = source_history_legos.owner_slice(changed, "runtime")
            harness = source_history_legos.owner_slice(changed, "harness")
            self.assertEqual(runtime["counts"], {"local": 1, "remote": 0})
            self.assertEqual(harness["counts"], {"local": 0, "remote": 0})
            self.assertEqual(harness["commits"], [])

    def test_one_sided_dag_owner_views_are_an_overlapping_cover(self):
        # The common fast-forward shape has NO local-only commits. A missing
        # Counter key must not be confused with a missing Git source cut.
        complete = {
            "truthRole": "derived-readonly-no-retirement-authority",
            "sourceCut": {"local": "a" * 40, "remote": "b" * 40,
                          "commonAncestor": "a" * 40},
            "ownerMappingSourceCut": "b" * 40,
            "ownerUniverse": ["harness", "runtime"],
            "counts": {"local": 0, "remote": 2},
            "ownerMembership": {
                "remote:runtime": 2,
                "remote:harness": 1,
            },
            "warning": "Native Owner CDC required.",
            "commits": [
                {"commit": "c" * 40, "side": "remote",
                 "owners": ["runtime", "harness"],
                 "consumerQualification": "UNKNOWN_REQUIRES_OWNER_CDC"},
                {"commit": "d" * 40, "side": "remote",
                 "owners": ["runtime"],
                 "consumerQualification": "UNKNOWN_REQUIRES_OWNER_CDC"},
            ],
        }
        runtime = source_history_legos.owner_slice(complete, "runtime")
        harness = source_history_legos.owner_slice(complete, "harness")
        self.assertEqual(runtime["counts"], {"local": 0, "remote": 2})
        self.assertEqual(harness["counts"], {"local": 0, "remote": 1})
        self.assertGreater(
            len(runtime["commits"]) + len(harness["commits"]),
            len(complete["commits"]),
        )
        self.assertEqual(
            {x["commit"] for view in (runtime, harness)
             for x in view["commits"]},
            {x["commit"] for x in complete["commits"]},
        )
        invalid = {**complete, "ownerMembership": {"remote:runtime": 3}}
        with self.assertRaisesRegex(ValueError, "Owner membership mismatch"):
            source_history_legos.owner_slice(invalid, "runtime")

    def test_unique_cross_path_bytes_are_not_consumer_or_rename_proofs(self):
        # Different catalog locations can contain identical bytes without
        # either commit being cherry-pick-equivalent or consumer-equivalent.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-relocation-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            owner = root / "tools/repo/owners.toml"
            owner.parent.mkdir(parents=True)
            owner.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "authority"\nroot = "meta/next/"\n'
                + 'verify_task = "repo:ci"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")

            old = "catalogs/authorities/observations/example.json"
            new = "meta/next/authorities/observations/example.json"
            source = root / old
            source.parent.mkdir(parents=True)
            shared_bytes = b'{"shared":"exact"}\n'
            source.write_bytes(shared_bytes)
            git(root, "add", ".")
            git(root, "commit", "-qm", "local catalog")
            left = git(root, "rev-parse", "HEAD")

            git(root, "switch", "-q", "remote-main")
            dest = root / new
            dest.parent.mkdir(parents=True)
            dest.write_bytes(shared_bytes)
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote catalog")
            right = git(root, "rev-parse", "HEAD")

            report = history(root, "main", "remote-main")
            records = {r["commit"]: r for r in report["commits"]}
            for oid, path, match in [(left, old, new), (right, new, old)]:
                row = records[oid]
                self.assertEqual(
                    row["pathRelations"], {"CROSS_PATH_EXACT_BLOB_AND_MODE": 1}
                )
                self.assertEqual(
                    row["exactCrossPathMatches"],
                    [{"sourcePath": path, "oppositePath": match}],
                )
                self.assertEqual(
                    row["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
                )
                self.assertEqual(
                    row["patchRelation"], "PATCH_DISTINCT_UNQUALIFIED"
                )

            # Duplicate content yields no unique identity => fail closed.
            alias = dest.with_name("copy.json")
            alias.write_bytes(dest.read_bytes())
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote duplicate")
            report = history(root, "main", "remote-main")
            local = next(r for r in report["commits"] if r["commit"] == left)
            self.assertEqual(
                local["pathRelations"], {"OPPOSITE_TIP_ABSENT": 1}
            )
            self.assertEqual(local["exactCrossPathMatches"], [])

            # Different executable modes invalidate apparent byte equality.
            alias.unlink()
            dest.chmod(0o755)
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote mode changed")
            report = history(root, "main", "remote-main")
            local = next(r for r in report["commits"] if r["commit"] == left)
            self.assertEqual(
                local["pathRelations"], {"OPPOSITE_TIP_ABSENT": 1}
            )
            self.assertEqual(local["exactCrossPathMatches"], [])

    def test_unmapped_path_presence_is_symmetric_and_never_an_owner_proof(self):
        # ROOT_UNOWNED is only a path-mapping gap, not a natural owner or
        # consumer-based permission to revive/retire a historical project.
        with tempfile.TemporaryDirectory(prefix="ordivon-unmapped-presence-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            shared = root / "both-present.txt"
            shared.write_text("base")
            absent = root / "both-absent.txt"
            absent.write_text("retired")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            shared.write_text("local value")
            absent.unlink()
            local = root / "catalogs/local.json"
            local.parent.mkdir(parents=True)
            local.write_text('{"local":1}')
            git(root, "add", "-A")
            git(root, "commit", "-qm", "local unmapped project")
            local_sha = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            shared.write_text("remote value")
            absent.unlink()
            remote = root / "studies/remote.txt"
            remote.parent.mkdir(parents=True)
            remote.write_text("remote")
            git(root, "add", "-A")
            git(root, "commit", "-qm", "remote unmapped project")
            remote_sha = git(root, "rev-parse", "HEAD")

            report = history(root, "main", "remote-main")
            records = {r["commit"]: r for r in report["commits"]}
            for sha, expected in [
                (local_sha, {"LOCAL_ONLY": 1, "BOTH_PRESENT": 1, "BOTH_ABSENT": 1}),
                (remote_sha, {"REMOTE_ONLY": 1, "BOTH_PRESENT": 1, "BOTH_ABSENT": 1}),
            ]:
                record = records[sha]
                self.assertEqual(record["owners"], ["ROOT_UNOWNED"])
                self.assertEqual(record["unmappedPathTipPresence"], expected)
                self.assertEqual(
                    sum(record["unmappedPathTipPresence"].values()),
                    len(record["changedPaths"]),
                )
                self.assertEqual(
                    record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
                )

    def test_merge_connectors_are_preserved_not_mistaken_for_patch_proofs(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-merge-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            (root / "README").write_text("base")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            (root / "local.txt").write_text("left")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local")
            git(root, "switch", "-q", "remote-main")
            git(root, "switch", "-q", "-c", "feature")
            (root / "remote.txt").write_text("remote")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote feature")
            git(root, "switch", "-q", "remote-main")
            git(root, "merge", "--no-ff", "-qm", "remote merge", "feature")
            report = history(root, "main", "remote-main")
            self.assertEqual(report["counts"], {"local": 1, "remote": 2})
            merges = [x for x in report["commits"] if x["kind"] == "merge-provenance"]
            self.assertEqual(len(merges), 1)
            self.assertEqual(merges[0]["patchRelation"], "NOT_APPLICABLE")
            self.assertEqual(len(merges[0]["parents"]), 2)
            # Merge connectors are not blank: their first-parent transition
            # can contain the only surviving consumer implementation.
            self.assertEqual(merges[0]["changedPaths"], ["remote.txt"])
            self.assertEqual(merges[0]["owners"], ["ROOT_UNOWNED"])
            self.assertEqual(merges[0]["resultDistinctFromAllParentsPaths"], [])

    def test_merge_conflict_resolution_has_real_owner_and_nonpatch_effect(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-resolution-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            consumer = root / "services/runtime/consumer.txt"
            consumer.parent.mkdir(parents=True)
            consumer.write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            consumer.write_text("local behavior\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local consumer")
            git(root, "switch", "-q", "remote-main")
            consumer.write_text("remote behavior\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote consumer")
            git(root, "branch", "feature", "main")
            merge = subprocess.run(
                ["git", "-C", str(root), "merge", "--no-ff", "feature"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(merge.returncode, 0)
            consumer.write_text("resolved behavior unique to merge\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "resolved provider contract")
            merged_oid = git(root, "rev-parse", "HEAD")
            report = history(root, "main", "remote-main")
            record = next(
                row for row in report["commits"] if row["commit"] == merged_oid
            )
            self.assertEqual(record["kind"], "merge-provenance")
            self.assertEqual(record["patchRelation"], "NOT_APPLICABLE")
            self.assertEqual(record["changedPaths"], ["services/runtime/consumer.txt"])
            self.assertEqual(record["owners"], ["runtime"])
            self.assertEqual(
                record["resultDistinctFromAllParentsPaths"],
                ["services/runtime/consumer.txt"],
            )
            self.assertEqual(
                record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
            )

    def test_newline_paths_and_header_like_names_keep_exact_git_identity(self):
        # Git paths are byte strings: line splitting or C-quoting changes owner identity.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-weird-path-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            expected = [
                "services/runtime/part\nbroken.txt",
                "services/runtime/\nleading.txt",
                "__ORDIVON_HISTORY_RECORD__< " + "0" * 40,
            ]
            for name in expected:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "unusual paths")
            left = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            (root / "remote-only").write_text("remote")
            git(root, "add", ".")
            git(root, "commit", "-qm", "independent remote")
            result = history(root, "main", "remote-main")
            record = next(row for row in result["commits"] if row["commit"] == left)
            self.assertEqual(sorted(record["changedPaths"]), sorted(expected))
            self.assertEqual(record["owners"], ["ROOT_UNOWNED", "runtime"])
            self.assertEqual(
                record["pathRelations"], {"OPPOSITE_TIP_ABSENT": len(expected)}
            )

    def test_owner_type_universe_is_bound_to_right_source_not_worktree(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-owners-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            runtime_file = root / "services/runtime/contract.txt"
            runtime_file.parent.mkdir(parents=True)
            runtime_file.write_text("local change\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local runtime owner")
            left = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            (root / "remote.txt").write_text("remote change\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote")
            remote = git(root, "rev-parse", "HEAD")
            before = history(root, "main", "remote-main")
            # Workspace materialization may be dirty or checked out at a
            # different ref. Its manifest must not change historical evidence.
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "fake"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            after = history(root, "main", "remote-main")
            first = next(x for x in before["commits"] if x["commit"] == left)
            second = next(x for x in after["commits"] if x["commit"] == left)
            self.assertEqual(first["owners"], ["runtime"])
            self.assertEqual(second["owners"], ["runtime"])
            self.assertEqual(after["ownerMappingSourceCut"], remote)

    def test_criss_cross_merge_bases_cannot_be_called_one_common_ancestor(self):
        # A real Git DAG may have two best common ancestors. A projection
        # claiming one canonical ancestor would lose provenance information.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-crisscross-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "left")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            owner = root / "tools/repo/owners.toml"
            owner.parent.mkdir(parents=True)
            owner.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "right")
            (root / "left.txt").write_text("left")
            git(root, "add", ".")
            git(root, "commit", "-qm", "left first")
            left_first = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "right")
            (root / "right.txt").write_text("right")
            git(root, "add", ".")
            git(root, "commit", "-qm", "right first")
            right_first = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "left")
            git(root, "merge", "--no-ff", "-qm", "left merge", right_first)
            git(root, "switch", "-q", "right")
            git(root, "merge", "--no-ff", "-qm", "right merge", left_first)
            self.assertEqual(
                len(git(root, "merge-base", "--all", "left", "right").splitlines()), 2
            )
            with self.assertRaisesRegex(ValueError, "ambiguous merge bases"):
                history(root, "left", "right")

    def test_invalid_reference_fails_not_reported_as_empty(self):
        with (
            tempfile.TemporaryDirectory(prefix="ordivon-history-invalid-") as temp,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            history(Path(temp), "main", "nonexistent")


    def test_repo_mechanics_owner_is_distinct_from_unknown_root(self):
        # tools/repo is the existing natural owner in Formal Issue Census,
        # despite not being a domain entry in owners.toml.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-repo-owner-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                CANONICAL_OWNER_HEADER
                + '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
                + 'verify_task = "runtime:verify"\n'
            )
            (root / "README").write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")

            local_file = root / "tools/repo/selected_consumer.py"
            local_file.write_text("consumer = 1\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "native repo consumer")
            local_commit = git(root, "rev-parse", "HEAD")

            git(root, "switch", "-q", "remote-main")
            (root / "unattributed-root.txt").write_text("remote\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote independent")
            report = history(root, "main", "remote-main")
            row = next(r for r in report["commits"] if r["commit"] == local_commit)
            self.assertEqual(row["owners"], ["tools/repo"])
            self.assertEqual(row["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC")



    def test_rejects_noncanonical_historical_owner_root(self):
        # Commit source-bound evidence still uses the repo's native Owner type.
        with tempfile.TemporaryDirectory(prefix="ordivon-invalid-owner-source-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                'schema_version = 1\n'
                'truth_role = "repository-mechanics-only-not-domain-authority"\n'
                '[[owners]]\nname = "runtime"\n'
                'root = "services/runtime"\n'
                'verify_task = "runtime:verify"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "malformed owner root")
            git(root, "branch", "remote-main")
            unowned = root / "services/runtime-extra/consumer.txt"
            unowned.parent.mkdir(parents=True)
            unowned.write_text("should not become runtime owner")
            git(root, "add", ".")
            git(root, "commit", "-qm", "unowned consumer")
            git(root, "switch", "-q", "remote-main")
            (root / "README").write_text("remote")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote")
            with self.assertRaisesRegex(ValueError, "end with"):
                history(root, "main", "remote-main")

    def test_source_membership_query_separates_membership_and_values(self):
        """Negative dependencies require querying the namespace, not only old files."""
        with tempfile.TemporaryDirectory(prefix="ordivon-git-membership-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            namespace = root / "services/runtime/providers"
            namespace.mkdir(parents=True)
            (namespace / "a.rs").write_text("healthy", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "initial member")
            initial = git(root, "rev-parse", "HEAD")
            query = source_history_legos.source_membership_query
            a = query(root, initial, "services/runtime/providers/")
            self.assertTrue(a["gitSourceQueryComplete"])
            self.assertFalse(a["proofReuseAdmissible"])
            self.assertEqual(a["memberCount"], 1)
            self.assertEqual(
                [entry["path"] for entry in a["members"]],
                ["services/runtime/providers/a.rs"],
            )
            (namespace / "a.rs").write_text(
                "still healthy but different", encoding="utf-8"
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "change value only")
            after_value = git(root, "rev-parse", "HEAD")
            b = query(root, after_value, "services/runtime/providers/")
            self.assertEqual(a["memberSetDigest"], b["memberSetDigest"])
            self.assertNotEqual(a["memberValuesDigest"], b["memberValuesDigest"])

            (namespace / "b.rs").write_text("failed", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "add failed provider")
            after_add = git(root, "rev-parse", "HEAD")
            c = query(root, after_add, "services/runtime/providers/")
            self.assertNotEqual(b["memberSetDigest"], c["memberSetDigest"])
            self.assertNotEqual(b["memberValuesDigest"], c["memberValuesDigest"])
            self.assertEqual(c["memberCount"], 2)
            self.assertEqual(a, query(root, initial, "services/runtime/providers/"))

            (namespace / "b.rs").rename(namespace / "renamed.rs")
            git(root, "add", "-A")
            git(root, "commit", "-qm", "rename identical object bytes")
            after_rename = git(root, "rev-parse", "HEAD")
            d = query(root, after_rename, "services/runtime/providers/")
            self.assertNotEqual(c["memberSetDigest"], d["memberSetDigest"])
            self.assertNotEqual(c["memberValuesDigest"], d["memberValuesDigest"])
            missing_a = query(root, initial, "services/runtime/absent/")
            missing_b = query(root, initial, "services/runtime/other-absent/")
            self.assertEqual(missing_a["memberCount"], 0)
            self.assertEqual(missing_b["memberCount"], 0)
            self.assertNotEqual(missing_a["memberSetDigest"], missing_b["memberSetDigest"])

    def test_source_membership_scope_rejects_ambiguous_inputs_and_truncation(self):
        with tempfile.TemporaryDirectory(
            prefix="ordivon-git-membership-fence-"
        ) as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            (root / "provider.txt").write_text("one", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            commit = git(root, "rev-parse", "HEAD")
            query = source_history_legos.source_membership_query
            for bad in (
                "",
                "/",
                "../hidden/",
                "/absolute/",
                "services//runtime/",
                "services/./runtime/",
                "services\\runtime/",
            ):
                with (
                    self.subTest(prefix=bad),
                    self.assertRaisesRegex(ValueError, "canonical non-root directory"),
                ):
                    query(root, commit, bad)
            with self.assertRaisesRegex(ValueError, "exact 40-hex"):
                query(root, "HEAD", "services/runtime/")
            with self.assertRaisesRegex(ValueError, "non-directory source boundary"):
                query(root, commit, "provider.txt/nested/")
            with self.assertRaisesRegex(ValueError, "positive integer"):
                query(root, commit, "services/runtime/", max_members=0)
            (root / "services").mkdir()
            (root / "services" / "a.txt").write_text("a", encoding="utf-8")
            (root / "services" / "b.txt").write_text("b", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "two members")
            with self.assertRaisesRegex(ValueError, "membership bound exceeded"):
                query(root, git(root, "rev-parse", "HEAD"), "services/", max_members=1)


    def test_source_membership_delta_is_selective_and_fails_closed_on_additions(self):
        """One real Git delta must separate paths from negative namespace reads."""
        with tempfile.TemporaryDirectory(prefix="ordivon-git-delta-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            prefix = "services/runtime/registry/"
            directory = root / prefix
            directory.mkdir(parents=True)
            (directory / "cas.rs").write_text("state == accepted", encoding="utf8")
            (directory / "unrelated.rs").write_text("unchanged", encoding="utf8")
            (root / "README").write_text("initial", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            baseline = git(root, "rev-parse", "HEAD")
            delta = source_history_legos.source_membership_delta
            no_change = delta(root, baseline, baseline, prefix)
            self.assertEqual(no_change["changedRefs"], [])
            self.assertFalse(no_change["proofReuseAdmissible"])
            self.assertTrue(no_change["gitSourceQueryComplete"])

            (root / "README").write_text("outside", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "unrelated outside")
            outside = git(root, "rev-parse", "HEAD")
            self.assertEqual(delta(root, baseline, outside, prefix)["changedRefs"], [])

            (directory / "cas.rs").write_text("true", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "regress CAS")
            weakened = git(root, "rev-parse", "HEAD")
            changed = delta(root, outside, weakened, prefix)
            self.assertEqual(changed["changedValuePaths"], [prefix + "cas.rs"])
            self.assertEqual(changed["addedPaths"], [])
            self.assertFalse(changed["membershipChanged"])
            self.assertEqual(
                changed["changedRefs"], [changed["sourceScopeRef"] + ":path:" + prefix + "cas.rs"]
            )

            (directory / "new.rs").write_text("failed", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "new provider")
            added = git(root, "rev-parse", "HEAD")
            new = delta(root, weakened, added, prefix)
            self.assertEqual(new["addedPaths"], [prefix + "new.rs"])
            self.assertTrue(new["membershipChanged"])
            self.assertEqual(
                new["changedRefs"],
                sorted([
                    new["sourceScopeRef"] + ":members:" + prefix,
                    new["sourceScopeRef"] + ":path:" + prefix + "new.rs",
                ])
            )

            # A path containing newlines, colon or percent must not collide
            # with other typed source dependencies when encoded.
            (directory / "odd:\\n%.rs").write_text("opaque")
            git(root, "add", ".")
            git(root, "commit", "-qm", "odd path")
            escaped = delta(root, added, git(root, "rev-parse", "HEAD"), prefix)
            self.assertTrue(any("%3A" in item and "%25" in item for item in escaped["changedRefs"]))
            self.assertEqual(
                delta(root, baseline, baseline, prefix, max_members=2)["changedRefs"], []
            )
            self.assertTrue(set(new["changedRefs"]).issubset(new["authorityRefs"]))
            self.assertIn(new["membershipRef"], new["authorityRefs"])
            with self.assertRaisesRegex(ValueError, "membership bound exceeded"):
                delta(root, baseline, added, prefix, max_members=2)
            # Two independent Git worktrees with matching relative paths
            # cannot alias each other's source-root or proof-dependency refs.
            second = root / "other-repository"
            second.mkdir()
            git(second, "init", "-q", "-b", "main")
            git(second, "config", "user.name", "Ordivon Test")
            git(second, "config", "user.email", "test@example.invalid")
            matching = second / prefix / "cas.rs"
            matching.parent.mkdir(parents=True)
            matching.write_text("state == accepted", encoding="utf8")
            git(second, "add", ".")
            git(second, "commit", "-qm", "same relative path, different source")
            other_cut = git(second, "rev-parse", "HEAD")
            second_scope = delta(second, other_cut, other_cut, prefix)
            assert second_scope["sourceScopeRef"] != no_change["sourceScopeRef"]
            assert set(second_scope["authorityRefs"]).isdisjoint(no_change["authorityRefs"])


    def test_same_git_common_authority_has_stable_refs_across_worktrees(self):
        """A Runtime workspace is not a new source authority or proof identity."""
        with tempfile.TemporaryDirectory(prefix="ordivon-reusable-git-source-") as temp:
            outer = Path(temp)
            source = outer / "source"
            source.mkdir()
            git(source, "init", "-q", "-b", "main")
            git(source, "config", "user.name", "Ordivon Test")
            git(source, "config", "user.email", "test@example.invalid")
            prefix = "services/runtime/providers/"
            provider = source / prefix / "cas.rs"
            provider.parent.mkdir(parents=True)
            provider.write_text("accepted", encoding="utf-8")
            git(source, "add", ".")
            git(source, "commit", "-qm", "exact source")
            commit = git(source, "rev-parse", "HEAD").strip()
            nested = outer / "detached-runtime-workspace"
            git(source, "worktree", "add", "-q", "--detach", str(nested), commit)

            projection = source_history_legos.source_membership_delta
            first = projection(source, commit, commit, prefix)
            second = projection(nested, commit, commit, prefix)
            self.assertEqual(first["memberValuesDigests"], second["memberValuesDigests"])
            self.assertEqual(first["sourceCuts"], second["sourceCuts"])
            # This is a single Git repository: the temporary worktree's
            # physical path must not invalidate an unchanged source claim.
            self.assertEqual(first["sourceScopeRef"], second["sourceScopeRef"])
            self.assertEqual(first["authorityRefs"], second["authorityRefs"])
            self.assertEqual(first["changedRefs"], second["changedRefs"])

            # A different Git repository with identical text/paths is not
            # automatically the same authority, even when blobs are equal.
            unrelated = outer / "unrelated"
            unrelated.mkdir()
            git(unrelated, "init", "-q", "-b", "main")
            git(unrelated, "config", "user.name", "Ordivon Test")
            git(unrelated, "config", "user.email", "test@example.invalid")
            another = unrelated / prefix / "cas.rs"
            another.parent.mkdir(parents=True)
            another.write_text("accepted", encoding="utf-8")
            git(unrelated, "add", ".")
            git(unrelated, "commit", "-qm", "same bytes distinct authority")
            other_cut = git(unrelated, "rev-parse", "HEAD").strip()
            isolated = projection(unrelated, other_cut, other_cut, prefix)
            self.assertNotEqual(first["sourceScopeRef"], isolated["sourceScopeRef"])
            self.assertTrue(set(first["authorityRefs"]).isdisjoint(isolated["authorityRefs"]))

    def test_source_membership_delta_requires_ancestral_order_for_proof_evolution(self):
        """Opposite Git branches are a comparison, not a previous/current transition."""
        with tempfile.TemporaryDirectory(prefix="ordivon-git-delta-history-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            path = root / "services" / "runtime" / "proving" / "a.rs"
            path.parent.mkdir(parents=True)
            path.write_text("base", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            ancestor = git(root, "rev-parse", "HEAD")
            git(root, "branch", "left")
            path.write_text("right", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "right branch change")
            right = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "-q", "left")
            path.write_text("left", encoding="utf8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "left branch change")
            left = git(root, "rev-parse", "HEAD")
            query = source_history_legos.source_membership_delta
            prefix = "services/runtime/proving/"
            self.assertEqual(query(root, ancestor, ancestor, prefix)["changedRefs"], [])
            self.assertEqual(len(query(root, ancestor, left, prefix)["changedRefs"]), 1)
            with self.assertRaisesRegex(ValueError, "ancestry"):
                query(root, left, right, prefix)
            with self.assertRaisesRegex(ValueError, "ancestry"):
                query(root, right, left, prefix)
            with self.assertRaisesRegex(ValueError, "ancestry"):
                query(root, left, ancestor, prefix)


    def test_ancestral_source_cuts_ignore_replace_ref_spoof(self):
        """A replace ref must not turn divergent commits into a valid temporal delta."""
        with tempfile.TemporaryDirectory(prefix="ordivon-ancestry-spoof-") as td:
            root = Path(td)
            git(root, "init", "-q")
            git(root, "config", "user.name", "Test")
            git(root, "config", "user.email", "test@example.invalid")
            (root / "a").write_text("A")
            git(root, "add", ".")
            git(root, "commit", "-qm", "A")
            baseline = git(root, "rev-parse", "HEAD")
            (root / "a").write_text("A2")
            git(root, "add", ".")
            git(root, "commit", "-qm", "A2")
            descendant = git(root, "rev-parse", "HEAD")
            git(root, "checkout", "--orphan", "other")
            (root / "a").write_text("B")
            git(root, "add", ".")
            git(root, "commit", "-qm", "B")
            divergent = git(root, "rev-parse", "HEAD")
            with self.assertRaisesRegex(ValueError, "ancestry not established"):
                source_history_legos.require_ancestral_source_cuts(
                    root, baseline, divergent
                )
            git(root, "replace", divergent, descendant)
            # Without --no-replace-objects Git falsely admits A as ancestor of B.
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(root), "merge-base", "--is-ancestor",
                     baseline, divergent], check=False, capture_output=True
                ).returncode, 0
            )
            with self.assertRaisesRegex(ValueError, "ancestry not established"):
                source_history_legos.require_ancestral_source_cuts(
                    root, baseline, divergent
                )


if __name__ == "__main__":
    unittest.main()
