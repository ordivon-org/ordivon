"""Independent host-operator release dispatcher: no new Registry or scheduler."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
loader=importlib.machinery.SourceFileLoader(
    "ordivon_runtime_pg_release_dispatch",str(SCRIPTS/"ordivon-runtime-pg-release-dispatch")
)
spec=importlib.util.spec_from_loader(loader.name,loader)
dispatcher=importlib.util.module_from_spec(spec)
loader.exec_module(dispatcher)


class PgReleaseDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory(prefix="ordivon-pg-dispatch-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.config={
            "sourceRepo":str(self.root/"source"),
            "installDir":str(self.root/"installed"),
            "envFile":str(self.root/"operator.env"),
            "receiptRoot":str(self.root/"receipt"),
            "service":"ordivon-runtime.service",
            "lockFile":str(self.root/"dispatch.lock"),
            "pgSchema":"fresh",
            "sourceSha256":"a"*64,
            "binaries":["ordivon-runtime-pg","ordivon-runtime-runner"],
            "requiredTools":["runtime.describe","release.get"],
        }
        self.path=self.root/"qualified.json"
        self.path.write_text(json.dumps(self.config),encoding="utf-8")
        self.path.chmod(0o600)

    def owner_config(self, uid: int = 0) -> dict[str, object]:
        # CI normally runs unprivileged; production MUST still reject it.
        # Change only this fixture's observed UID, preserving the real mode,
        # regular-file and symlink checks inside load_owner_config().
        native_stat = Path.stat

        def fixture_stat(path: Path, *args: object, **kwargs: object):
            metadata = native_stat(path, *args, **kwargs)
            if path != self.path:
                return metadata
            fields = list(metadata)
            fields[4] = uid  # POSIX stat_result.st_uid
            return os.stat_result(fields)

        with patch.object(Path, "stat", fixture_stat):
            return dispatcher.load_owner_config(self.path)

    def test_only_root_owned_nonwritable_config_is_accepted(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "root-owned"):
            self.owner_config(uid=65534)
        qualified=self.owner_config()
        self.assertEqual(qualified["service"],"ordivon-runtime.service")
        self.assertIsInstance(qualified["sourceRepo"],Path)
        self.path.chmod(0o666)
        with self.assertRaisesRegex(RuntimeError,"root-owned"):
            self.owner_config()
        self.path.unlink()
        self.path.symlink_to(self.root/"other")
        with self.assertRaisesRegex(RuntimeError,"absolute regular"):
            self.owner_config()

    def test_no_agent_chosen_service_or_unsafe_binary(self) -> None:
        for name,value in (("service","arbitrary.service"),("binaries",["/usr/bin/sh"])):
            self.config[name]=value
            self.path.unlink(missing_ok=True)
            self.path.write_text(json.dumps(self.config),encoding="utf-8")
            self.path.chmod(0o600)
            with self.assertRaises(RuntimeError):
                self.owner_config()
            self.config[name]=("ordivon-runtime.service" if name=="service"
                               else ["ordivon-runtime-pg","ordivon-runtime-runner"])

    def test_incomplete_or_duplicate_native_release_set_is_rejected(self) -> None:
        # A complete Runtime release includes BOTH native executable images.
        # The originally permitted PG-only subset must not bypass Runner
        # attestation, even with an otherwise root-qualified config file.
        invalid = (
            ["ordivon-runtime-pg"],
            ["ordivon-runtime-runner"],
            ["ordivon-runtime-pg", "ordivon-runtime-pg"],
            ["ordivon-runtime-pg", "ordivon-runtime-runner", "ordivon-runtime-runner"],
            ["ordivon-runtime-pg", "ordivon-runtime-runner", "/usr/bin/sh"],
            [],
            "ordivon-runtime-pg",
        )
        for binaries in invalid:
            with self.subTest(binaries=binaries):
                self.config["binaries"] = binaries
                self.path.write_text(json.dumps(self.config), encoding="utf-8")
                self.path.chmod(0o600)
                with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                    self.owner_config()
        # Ordering of exactly the two required names is not security relevant.
        self.config["binaries"] = ["ordivon-runtime-runner", "ordivon-runtime-pg"]
        self.path.write_text(json.dumps(self.config), encoding="utf-8")
        self.path.chmod(0o600)
        self.assertEqual(
            self.owner_config()["binaries"],
            ["ordivon-runtime-runner", "ordivon-runtime-pg"],
        )

    def test_programmatic_sweep_cannot_bypass_full_native_binary_set(self) -> None:
        # The native timer calls main(), but sweep() is also an importable
        # entry point. It must fail before even opening the PG connection.
        qualified = self.owner_config()
        qualified["binaries"] = ["ordivon-runtime-pg"]
        with patch.dict(os.environ, {"ORDIVON_PG_RELEASE_OPERATOR_DSN": "operator-only"}), \
             patch.object(dispatcher.operator, "pg_connection") as connect:
            with self.assertRaisesRegex(RuntimeError, "complete native PG and Runner"):
                dispatcher.sweep(qualified)
            connect.assert_not_called()

    def test_committed_row_uses_only_operator_configured_paths(self) -> None:
        config=self.owner_config()
        row={
            "principal":"pg-consumer","client_request_id":"exact-consumer",
            "effect_id":"b"*64,"commit_revision":"c"*40,
            "candidate_manifest_digest":"sha256:"+"d"*64,"expected_tool_count":21,
        }
        with patch.dict(os.environ,{"ORDIVON_PG_RELEASE_OPERATOR_DSN":"operator-only"}):
            args=dispatcher.release_effect_to_args(config,row)
        self.assertEqual(args.service,"ordivon-runtime.service")
        self.assertEqual(args.candidate_dir,config["sourceRepo"]/"target"/
                         "ordivon-release-candidates"/("c"*40)/"release")
        self.assertEqual(args.pg_dsn,"operator-only")
        self.assertEqual(args.effect_id,"b"*64)
        row["commit_revision"]="../not-a-commit"
        with self.assertRaisesRegex(RuntimeError,"invalid release commit"):
            dispatcher.release_effect_to_args(config,row)

    def test_sweep_empty_does_not_touch_systemd(self) -> None:
        config=self.owner_config()
        conn=MagicMock()
        conn.execute.return_value.fetchall.return_value=[]
        context=MagicMock()
        context.__enter__.return_value=conn
        with patch.dict(os.environ,{"ORDIVON_PG_RELEASE_OPERATOR_DSN":"operator-only"}),\
             patch.object(dispatcher.operator,"pg_connection",return_value=context),\
             patch.object(dispatcher.operator,"qualified_operator") as qualify,\
             patch.object(dispatcher.operator,"apply_release") as apply:
            self.assertEqual(dispatcher.sweep(config),0)
        qualify.assert_called_once()
        apply.assert_not_called()

    def test_one_pending_effect_invokes_exact_qualified_operator(self) -> None:
        config=self.owner_config()
        row={
            "principal":"pg-consumer","client_request_id":"exact-001",
            "effect_id":"b"*64,"commit_revision":"c"*40,
            "candidate_manifest_digest":"sha256:"+"d"*64,"expected_tool_count":21,
        }
        conn=MagicMock()
        conn.execute.return_value.fetchall.return_value=[row]
        context=MagicMock()
        context.__enter__.return_value=conn
        with (
            patch.dict(os.environ,{"ORDIVON_PG_RELEASE_OPERATOR_DSN":"operator-only"}),
            patch.object(dispatcher.operator,"pg_connection",return_value=context),
            patch.object(dispatcher.operator,"qualified_operator") as qualify,
            patch.object(dispatcher.operator,"apply_release",
                return_value={"status":"deployed","pgTerminal":"succeeded"}) as apply,
        ):
            self.assertEqual(dispatcher.sweep(config),0)
        qualify.assert_called_once()
        apply.assert_called_once()
        exact=apply.call_args.args[0]
        self.assertEqual(exact.effect_id,row["effect_id"])
        self.assertEqual(exact.client_request_id,"exact-001")
        self.assertEqual(exact.service,"ordivon-runtime.service")

    def test_sweep_ambiguous_multiple_effects_fails_without_dispatch(self) -> None:
        config=self.owner_config()
        conn=MagicMock()
        conn.execute.return_value.fetchall.return_value=[{"id":1},{"id":2}]
        context=MagicMock()
        context.__enter__.return_value=conn
        with patch.dict(os.environ,{"ORDIVON_PG_RELEASE_OPERATOR_DSN":"operator-only"}),\
             patch.object(dispatcher.operator,"pg_connection",return_value=context),\
             patch.object(dispatcher.operator,"qualified_operator"),\
             patch.object(dispatcher.operator,"apply_release") as apply:
            with self.assertRaisesRegex(RuntimeError,"more than one"):
                dispatcher.sweep(config)
        apply.assert_not_called()


if __name__=="__main__":
    unittest.main()
