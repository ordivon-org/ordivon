"""Regression contract: PG binary and Runner are built without SQLite features."""
from __future__ import annotations

import argparse
import hashlib
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
try:
    _deploy = runpy.run_path(str(SCRIPTS / "ordivon-runtime-deploy"), run_name="pg_release_test")
finally:
    sys.path.remove(str(SCRIPTS))


class PgOnlyReleaseBuildContract(unittest.TestCase):
    def test_two_native_binaries_do_not_share_all_features_invocation(self) -> None:
        cargo = Path("/opt/cargo/bin/cargo")
        dest = Path("/var/cache/ordivon/commit/release")
        cmds = _deploy["candidate_build_commands"](
            cargo, dest, ["ordivon-runtime-pg", "ordivon-runtime-runner"],
            explicit_binary_selection=True,
        )
        self.assertEqual(len(cmds), 2)
        for cmd in cmds:
            self.assertEqual(cmd[:3], [str(cargo), "build", "--release"])
            self.assertIn("--no-default-features", cmd)
            self.assertNotIn("--all-features", cmd)
            self.assertEqual(cmd[-2:], ["--target-dir", str(dest.parent)])
        self.assertEqual(cmds[0][cmds[0].index("-p") + 1], "ordivon-runtime-mcp")
        self.assertEqual(cmds[0][cmds[0].index("--features") + 1], "postgres-runtime")
        self.assertEqual(cmds[1][cmds[1].index("-p") + 1], "ordivon-runtime-core")
        self.assertEqual(cmds[1][cmds[1].index("--features") + 1], "postgres-registry-admission")

    def test_legacy_profiles_keep_the_previous_build_contract(self) -> None:
        cargo = Path("/opt/cargo/bin/cargo")
        dest = Path("/var/cache/ordivon/commit/release")
        expected = [[str(cargo), "build", "--release", "--workspace",
                     "--all-features", "--target-dir", str(dest.parent)]]
        for binaries, selected in (
            (["ordivon-runtime", "ordivon-runtime-runner"], True),
            (["ordivon-runtime-pg", "ordivon-runtime-runner"], False),
        ):
            with self.subTest(binaries=binaries, selected=selected):
                cmds = _deploy["candidate_build_commands"](
                    cargo, dest, binaries, explicit_binary_selection=selected,
                )
                self.assertEqual(cmds, expected)

    def test_native_dual_binary_pg_reclaimer_is_qualified_release_artifact(self) -> None:
        """Reclaimer must be in the SAME immutable release, not a stale sidecar."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "scripts").mkdir(parents=True)
            reclaimer_bytes = b"#!/usr/bin/env python3\nprint('reclaimer current')\n"
            (source / "scripts" / "ordivon-runtime-pg-reclaim").write_bytes(reclaimer_bytes)
            target = root / "target" / "release"
            target.mkdir(parents=True)
            args = argparse.Namespace(
                binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
                include_pg_reclaimer=True, candidate_dir=target,
            )
            specs = _deploy["release_artifact_specs"](args)
            self.assertEqual([str(item["name"]) for item in specs], [
                "ordivon-runtime-pg", "ordivon-runtime-runner",
                "ordivon-runtime-pg-reclaim",
            ])
            self.assertEqual(specs[-1]["kind"], "operator")
            for name in args.binaries:
                (target / name).write_bytes(name.encode())
                (target / name).chmod(0o755)
            _deploy["stage_operator_artifacts"](args, source)
            self.assertEqual((target / "ordivon-runtime-pg-reclaim").read_bytes(), reclaimer_bytes)
            candidate = _deploy["candidate_artifacts"](args)
            reclaimer = next(item for item in candidate if item["name"] == "ordivon-runtime-pg-reclaim")
            self.assertEqual(reclaimer["digest"], "sha256:" + hashlib.sha256(reclaimer_bytes).hexdigest())
            source_reclaimer = source / "scripts" / "ordivon-runtime-pg-reclaim"
            source_reclaimer.unlink()
            with self.assertRaisesRegex(RuntimeError, "missing or unsafe"):
                _deploy["stage_operator_artifacts"](args, source)
            source_reclaimer.symlink_to(target / "ordivon-runtime-pg-reclaim")
            with self.assertRaisesRegex(RuntimeError, "missing or unsafe"):
                _deploy["stage_operator_artifacts"](args, source)

    def test_manifest_rejects_nonunique_or_inconsistent_artifact_records(self) -> None:
        import copy
        import json
        import subprocess

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "-c", "user.name=Test",
                 "-c", "user.email=test@example.invalid", "commit",
                 "--allow-empty", "-qm", "initial"], check=True,
            )
            commit = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            target = root / "target" / "release"
            target.mkdir(parents=True)
            args = argparse.Namespace(
                binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
                include_pg_reclaimer=True, candidate_dir=target,
                candidate_manifest=root / "manifest.json",
                source_repo=repo, commit=commit, git=Path("/usr/bin/git"),
            )
            for spec in _deploy["release_artifact_specs"](args):
                path = target / str(spec["name"])
                path.write_bytes(b"x" if spec["name"] == args.binaries[0]
                                 else str(spec["name"]).encode())
                path.chmod(0o755)
            candidate = _deploy["candidate_artifacts"](args)
            tool = {"version": "test", "resolvedPath": "/test",
                    "digest": "sha256:" + "a" * 64}
            manifest = {
                "schemaVersion": _deploy["SCHEMA_VERSION"],
                "commit": commit, "sourceRepo": str(repo),
                "sourceMaterialization": "detached_git_checkout",
                "candidateDir": str(target),
                "toolchain": {"cargo": tool, "rustc": tool, "host": "test"},
                "artifacts": candidate,
                "binaries": [item for item in candidate if item["kind"] == "binary"],
            }

            def blockers(value):
                args.candidate_manifest.write_text(json.dumps(value))
                return _deploy["validate_candidate_manifest"](args, candidate)[1]

            self.assertEqual(blockers(manifest), [])
            # A validation receipt must hash the exact bytes it parsed.
            from unittest.mock import patch

            original = json.dumps(manifest).encode()
            replacement = json.dumps({**manifest, "commit": "0" * 40}).encode()
            args.candidate_manifest.write_bytes(original)
            args.candidate_manifest_digest = (
                "sha256:" + hashlib.sha256(replacement).hexdigest()
            )
            validate = _deploy["validate_candidate_manifest"]
            layout = validate.__globals__["release_source_layout"]

            def replace_after_parse(*layout_args):
                result = layout(*layout_args)
                args.candidate_manifest.write_bytes(replacement)
                return result

            with patch.dict(validate.__globals__, {"release_source_layout": replace_after_parse}):
                summary, errors = validate(args, candidate)
            self.assertEqual(summary["digest"], "sha256:" + hashlib.sha256(original).hexdigest())
            self.assertIn("candidate manifest digest does not match structured release request", errors)
            del args.candidate_manifest_digest

            # Wire-level duplicate object members and nonfinite numbers
            # cannot be recovered after a permissive JSON-to-dict projection.
            wire = original.decode()
            for raw in (
                wire.replace('"commit":', '"commit":"wrong", "commit":', 1),
                wire.replace('"digest":', '"digest":"wrong", "digest":', 1),
                wire[:-1] + ', "extra": NaN}',
                wire[:-1] + ', "extra": 1e400}',
            ):
                with self.subTest(raw=raw[:120]):
                    args.candidate_manifest.write_text(raw)
                    with self.assertRaisesRegex(RuntimeError, "invalid candidate manifest representation"):
                        validate(args, candidate)
            for case in ("schema_float", "artifact_bytes_bool", "binary_mode_float"):
                with self.subTest(case=case):
                    value = json.loads(wire)
                    if case == "schema_float":
                        value["schemaVersion"] = float(value["schemaVersion"])
                    elif case == "artifact_bytes_bool":
                        value["artifacts"][0]["bytes"] = True
                    else:
                        value["binaries"][0]["mode"] = float(value["binaries"][0]["mode"])
                    self.assertTrue(blockers(value), case)

            for case in ("duplicate_artifact", "shadowed_artifact", "nonrecord_artifact",
                         "duplicate_binary", "shadowed_binary", "nonrecord_binary",
                         "inconsistent_binary"):
                with self.subTest(case=case):
                    value = json.loads(json.dumps(manifest))
                    if case == "duplicate_artifact":
                        value["artifacts"].append(copy.deepcopy(value["artifacts"][0]))
                    elif case == "shadowed_artifact":
                        bad = {**value["artifacts"][0], "digest": "sha256:" + "0" * 64}
                        value["artifacts"].insert(0, bad)
                    elif case == "nonrecord_artifact":
                        value["artifacts"].append(None)
                    elif case == "duplicate_binary":
                        value["binaries"].append(copy.deepcopy(value["binaries"][0]))
                    elif case == "shadowed_binary":
                        bad = {**value["binaries"][0], "digest": "sha256:" + "0" * 64}
                        value["binaries"].insert(0, bad)
                    elif case == "nonrecord_binary":
                        value["binaries"].append(None)
                    else:
                        value["binaries"][0]["digest"] = "sha256:" + "0" * 64
                    self.assertTrue(blockers(value), case)

    def test_binary_subset_retains_old_mode_and_wrong_opt_in_pair_is_rejected(self) -> None:
        subset = argparse.Namespace(
            binaries=["ordivon-runtime-pg", "ordivon-runtime-runner"],
            include_pg_reclaimer=False,
        )
        self.assertEqual(
            [item["name"] for item in _deploy["release_artifact_specs"](subset)],
            list(subset.binaries),
        )
        invalid = argparse.Namespace(
            binaries=["ordivon-runtime-pg"],
            include_pg_reclaimer=True,
        )
        with self.assertRaisesRegex(RuntimeError, "full native PG binary pair"):
            _deploy["release_artifact_specs"](invalid)


if __name__ == "__main__":
    unittest.main()
