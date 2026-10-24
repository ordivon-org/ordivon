"""Consumer contracts for one owner-scoped, cold Workspace entrypoint."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("workspace-ready")


class WorkspaceReadyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ordivon-workspace-ready-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = self.root / "tools" / "repo" / "workspace-ready"
        self.script.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE, self.script)
        self.script.chmod(0o755)
        self.scope = self.root / "services" / "harness"
        self.scope.mkdir(parents=True)
        self.provider = self.root / "platform/network/consumers/developer-egress/profile.sh"
        self.provider.parent.mkdir(parents=True)
        self.provider.write_text(
            "#!/bin/bash\n"
            "[[ \"$1\" == -- ]] || exit 2\n"
            "shift\n"
            "exec \"$@\"\n"
        )
        (self.scope / "mise.toml").write_text("[tools]\npython = '3.14.9'\n")
        self.log = self.root / "events.log"
        self.mise = self.root / "mise"
        self.mise.write_text(
            "#!/bin/sh\n"
            "printf 'mise:%s\\n' \"$*\" >> \"$RECORDER\"\n"
            "if [ \"$1\" = install ] && [ \"$2\" = --dry-run-code ] && [ \"$3\" = --include-task-tools ]; then\n"
            "  [ \"$MISE_PREFLIGHT_BROKEN\" = true ] && exit 7\n"
            "  [ \"$MISE_INSTALLED\" = true ] && exit 0\n"
            "  exit 1\n"
            "fi\n"
            "if [ \"$1\" = which ] && [ \"$2\" = python ]; then\n"
            "  [ -n \"$MISE_SELECTED_PYTHON\" ] && printf '%s\\n' \"$MISE_SELECTED_PYTHON\"\n"
            "  exit 0\n"
            "fi\n"
            "if [ \"$1\" = env ] && [ \"$2\" = --paths ]; then\n"
            "  [ -n \"$MISE_SELECTED_BIN\" ] && printf '%s\\n' \"$MISE_SELECTED_BIN\"\n"
            "  exit 0\n"
            "fi\n"
            "if [ \"$1\" = exec ]; then\n"
            "  shift 2\n"
            "  [ -n \"$MISE_REORDER_PATH\" ] && PATH=\"$MISE_REORDER_PATH:$PATH\" && export PATH\n"
            "  exec \"$@\"\n"
            "fi\n"
        )
        self.mise.chmod(0o755)
        self.env = dict(os.environ, MISE_BIN=str(self.mise), RECORDER=str(self.log))
        self.env["PATH"] = "/usr/bin:/bin"

    def events(self):
        # Normalize the transport-only env layer; cases inspect the command
        # and the separate shadowed-tool test inspects actual binary identity.
        return [
            re.sub(r" /usr/bin/env PATH=\S+", "", event)
            for event in self.log.read_text().splitlines()
        ]


    def run_ready(self, *args, cwd=None):
        return subprocess.run(
            [str(self.script), *args],
            cwd=cwd or self.root,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )

    def test_cold_owner_prepares_then_executes_command_in_scoped_mise(self):
        scripts = self.scope / "scripts"
        scripts.mkdir()
        owner = scripts / "owner-environment"
        owner.write_text(
            "#!/bin/sh\n"
            "printf 'owner:%s\\n' \"$1\" >> \"$RECORDER\"\n"
        )
        owner.chmod(0o755)
        result = self.run_ready(
            "services/harness", "--", "/usr/bin/printf", "cold consumer ready"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "cold consumer ready")
        self.assertEqual(
            self.events(),
            [
                "mise:install --dry-run-code --include-task-tools",
                "mise:install --include-task-tools",
                "mise:env --paths",
                "mise:exec -- /usr/bin/bash scripts/owner-environment bootstrap",
                "owner:bootstrap",
                "mise:exec -- /usr/bin/bash scripts/owner-environment doctor",
                "owner:doctor",
                "mise:exec -- /usr/bin/printf cold consumer ready",
            ],
        )

    def test_cold_workspace_installs_task_owned_tools_not_just_global_tools(self):
        # A task may declare tools that are absent from [tools]; mise already
        # knows how to find/install them without a second Ordivon registry.
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mise:install --dry-run-code --include-task-tools", self.events())
        self.assertIn("mise:install --include-task-tools", self.events())

    def test_installed_tools_work_in_restricted_runtime_path(self):
        """Host mise exists, but a clean Runtime job has no system PATH."""
        self.env["PATH"] = "/nonexistent-ordivon-test-binaries"
        self.env["MISE_INSTALLED"] = "true"
        self.env["ORDIVON_DEV_VPN"] = "off"
        self.provider.unlink()
        result = self.run_ready("services/harness", "--", "/usr/bin/printf", "offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "offline")
        self.assertEqual(
            self.events(),
            ["mise:install --dry-run-code --include-task-tools", "mise:env --paths", "mise:exec -- /usr/bin/printf offline"],
        )

    def test_installed_owner_tools_run_without_network_provider_or_vpn(self):
        # A ready host must not depend on egress for a read-only local command.
        self.provider.unlink()
        self.env["ORDIVON_DEV_VPN"] = "off"
        self.env["MISE_INSTALLED"] = "true"
        result = self.run_ready("services/harness", "--", "/usr/bin/printf", "offline")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "offline")
        self.assertEqual(
            self.events(),
            ["mise:install --dry-run-code --include-task-tools", "mise:env --paths", "mise:exec -- /usr/bin/printf offline"],
        )

    def test_pinned_tool_wins_over_ambient_shadow_in_nonlogin_workspace(self):
        selected = self.root / "selected" / "bin"
        shadow = self.root / "shadow" / "bin"
        selected.mkdir(parents=True)
        shadow.mkdir(parents=True)
        (selected / "task").write_text("#!/bin/sh\necho selected\n")
        (shadow / "task").write_text("#!/bin/sh\necho shadow\n")
        (selected / "task").chmod(0o755)
        (shadow / "task").chmod(0o755)
        self.env["MISE_INSTALLED"] = "true"
        self.env["MISE_SELECTED_BIN"] = str(selected)
        self.env["PATH"] = str(shadow) + ":/usr/bin:/bin"
        self.env["MISE_REORDER_PATH"] = str(shadow)
        result = self.run_ready("services/harness", "--", "task")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "selected")

    def test_preflight_failure_other_than_missing_must_not_download(self):
        self.env["MISE_PREFLIGHT_BROKEN"] = "true"
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preflight", result.stderr.lower())
        self.assertNotIn("mise:install --include-task-tools\n", self.log.read_text())
        self.assertEqual(self.events(), ["mise:install --dry-run-code --include-task-tools"])

    def test_installed_tools_still_use_vpn_for_owner_bootstrap(self):
        scripts = self.scope / "scripts"
        scripts.mkdir()
        owner = scripts / "owner-environment"
        owner.write_text("#!/bin/sh\nprintf 'owner:%s\\n' \"$1\" >> \"$RECORDER\"\n")
        owner.chmod(0o755)
        self.env["MISE_INSTALLED"] = "true"
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = self.events()
        self.assertEqual(entries[0], "mise:install --dry-run-code --include-task-tools")
        self.assertNotIn("mise:install --include-task-tools", entries)
        self.assertIn("mise:exec -- /usr/bin/bash scripts/owner-environment bootstrap", entries)

    def test_cold_owner_auto_resolves_from_cwd_without_repeating_owner_path(self):
        bindir = self.scope / ".venv" / "bin"
        bindir.mkdir(parents=True)
        interpreter = bindir / "python"
        interpreter.write_text("#!/bin/sh\nprintf 'selected-owner-venv'\n")
        interpreter.chmod(0o755)
        result = self.run_ready("--", "python", cwd=self.scope)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "selected-owner-venv")
        self.assertIn("mise:install --include-task-tools", self.events())

    def test_nested_owner_path_discovers_nearest_ancestor(self):
        nested = self.scope / "src" / "ordivon_agent"
        nested.mkdir(parents=True)
        result = self.run_ready("--", "/usr/bin/pwd", cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.scope.resolve())

    def test_explicit_nested_pnpm_consumer_inherits_nearest_mise_and_materializes(self):
        nested = self.scope / "node"
        nested.mkdir()
        (nested / "package.json").write_text('{"name":"nested-consumer"}\n')
        (nested / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text("#!/bin/sh\nprintf 'pnpm:%s\\n' \"$*\" >> \"$RECORDER\"\n")
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        result = self.run_ready("services/harness/node", "--", "/usr/bin/pwd")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), nested.resolve())
        self.assertIn("pnpm:install --frozen-lockfile --offline", self.events())

    def test_security_nested_js_consumers_bind_owner_pnpm_and_node(self):
        # Legacy local c582107's consumer invariant uses the existing owner,
        # never a resurrected standalone workspace-environment registry.
        import json
        import tomllib

        security = SOURCE.parents[2] / "platform/security"
        owner = tomllib.loads((security / "mise.toml").read_text())["tools"]
        for nested in (
            "contracts/agent-request-verifier-v1",
            "labs/agent-admission-rs",
        ):
            with self.subTest(nested=nested):
                package = json.loads((security / nested / "package.json").read_text())
                self.assertEqual(package["packageManager"], f"pnpm@{owner['pnpm']}")
                self.assertEqual(package["engines"]["node"], owner["node"])

    def test_nested_pnpm_version_must_match_owner_selection_before_install(self):
        # Historical local c582107 consumer condition, now at workspace-ready.
        # A real packageManager override must not select an older pnpm binary
        # despite the owner having a newer, already-installed tool.
        nested = self.scope / "node"
        nested.mkdir()
        (nested / "package.json").write_text(
            '{"name":"nested","packageManager":"pnpm@12.14.0"}\n'
        )
        (nested / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "--version" ]; then echo 12.15.0; exit 0; fi\n'
            'printf "pnpm:%s\\n" "$*" >> "$RECORDER"\n'
        )
        pnpm.chmod(0o755)
        node = toolbin / "node"
        node.write_text("#!/bin/sh\necho pnpm@12.14.0\n")
        node.chmod(0o755)
        self.env["MISE_INSTALLED"] = "true"
        self.env["MISE_SELECTED_BIN"] = str(toolbin)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        result = self.run_ready("services/harness/node", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packageManager", result.stderr)
        self.assertNotIn("pnpm:install", self.log.read_text())

        # The identical consumer with the selected owner's version is admitted.
        node.write_text("#!/bin/sh\necho pnpm@12.15.0\n")
        (nested / "package.json").write_text(
            '{"name":"nested","packageManager":"pnpm@12.15.0"}\n'
        )
        accepted = self.run_ready("services/harness/node", "--", "/usr/bin/true")
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_package_manager_cannot_self_select_older_version_during_probe(self):
        # pnpm can auto-switch based on the cwd packageManager. Comparing its
        # version *in that cwd* with the same field is circular and unsound.
        (self.scope / "package.json").write_text(
            '{"name":"owner","packageManager":"pnpm@12.14.0"}\n'
        )
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "--version" ]; then\n'
            '  if [ -f package.json ] && grep -q "12.14.0" package.json; then\n'
            '    echo 12.14.0; else echo 12.15.0; fi\n'
            "  exit 0\n"
            "fi\n"
            'printf "pnpm:%s\\n" "$*" >> "$RECORDER"\n'
        )
        pnpm.chmod(0o755)
        node = toolbin / "node"
        node.write_text("#!/bin/sh\necho pnpm@12.14.0\n")
        node.chmod(0o755)
        self.env["MISE_INSTALLED"] = "true"
        self.env["MISE_SELECTED_BIN"] = str(toolbin)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("packageManager", result.stderr)
        self.assertNotIn("pnpm:install", self.log.read_text())

    def test_nested_dependency_without_lock_is_rejected_before_any_effect(self):
        nested = self.scope / "node"
        nested.mkdir()
        (nested / "package.json").write_text('{"name":"nested-consumer"}\n')
        result = self.run_ready("services/harness/node", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pnpm-lock", result.stderr)
        self.assertFalse(self.log.exists())

    def test_no_arguments_bootstraps_current_owner_without_exec(self):
        result = self.run_ready(cwd=self.scope)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.events(), ["mise:install --dry-run-code --include-task-tools", "mise:install --include-task-tools", "mise:env --paths"])

    def test_implicit_owner_outside_repo_is_rejected_before_effect(self):
        with tempfile.TemporaryDirectory(prefix="external-workspace-") as outside:
            result = self.run_ready("--", "/usr/bin/true", cwd=Path(outside))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside repository", result.stderr)
        self.assertFalse(self.log.exists())
    def test_scope_escape_is_rejected_without_effect(self):
        result = self.run_ready("../outside", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_uv_sync_uses_owner_mise_python_not_stale_python_version_file(self):
        (self.scope / "pyproject.toml").write_text(
            "[project]\nname='probe'\nversion='0.0.1'\n"
            "requires-python='==3.15.1'\n"
        )
        (self.scope / "uv.lock").write_text('requires-python = "==3.15.1"\n')
        (self.scope / ".python-version").write_text("3.14.9\n")
        selected = self.root / "selected" / "bin"
        selected.mkdir(parents=True)
        (selected / "python").write_text("#!/bin/sh\n")
        (selected / "python").chmod(0o755)
        (selected / "uv").write_text(
            "#!/bin/sh\n"
            '[ "$1" = sync ] || exit 81\n'
            '[ "$UV_PYTHON" = "$MISE_SELECTED_PYTHON" ] || exit 82\n'
            'printf "owner-python=%s\n" "$UV_PYTHON"\n'
        )
        (selected / "uv").chmod(0o755)
        self.env["MISE_INSTALLED"] = "true"
        self.env["MISE_SELECTED_BIN"] = str(selected)
        self.env["MISE_SELECTED_PYTHON"] = str(selected / "python")
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"owner-python={selected / 'python'}", result.stdout)

    def test_unknown_dependency_install_is_not_silently_skipped(self):
        (self.scope / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n")
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lock", result.stderr.lower())

    def test_materialized_venv_is_used_by_python_consumer(self):
        bindir = self.scope / ".venv" / "bin"
        bindir.mkdir(parents=True)
        python = bindir / "python"
        python.write_text("#!/bin/sh\nprintf 'venv-selected'\n")
        python.chmod(0o755)
        result = self.run_ready("services/harness", "--", "python")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "venv-selected")

    def test_existing_network_provider_wraps_installs_not_consumer(self):
        provider = self.root / "platform" / "network" / "consumers" / "developer-egress" / "profile.sh"
        provider.parent.mkdir(parents=True, exist_ok=True)
        provider.write_text(
            "#!/bin/bash\n"
            "printf 'vpn:%s\\n' \"$*\" >> \"$RECORDER\"\n"
            "[[ \"$1\" == '--' ]] || exit 2\n"
            "shift\n"
            "exec \"$@\"\n"
        )
        result = self.run_ready("services/harness", "--", "/usr/bin/printf", "ready")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ready")
        entries = self.events()
        self.assertEqual(entries[0], "mise:install --dry-run-code --include-task-tools")
        self.assertEqual(entries[1], f"vpn:-- {self.mise} install --include-task-tools")
        self.assertEqual(entries[2], "mise:install --include-task-tools")
        self.assertEqual(entries[-1], "mise:exec -- /usr/bin/printf ready")
        self.assertEqual(sum(entry.startswith("vpn:") for entry in entries), 1)

    def test_missing_network_provider_cannot_silently_download_direct(self):
        self.provider.unlink()
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provider", result.stderr.lower())
        self.assertEqual(self.events(), ["mise:install --dry-run-code --include-task-tools"])

    def test_existing_scope_without_project_dependencies_runs_with_mise(self):
        result = self.run_ready("services/harness", "--", "/usr/bin/printf", "ok")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ok")
        self.assertEqual(self.events(), [
            "mise:install --dry-run-code --include-task-tools",
            "mise:install --include-task-tools",
            "mise:env --paths",
            "mise:exec -- /usr/bin/printf ok",
        ])


    def test_explicit_vpn_off_must_not_install_tools(self):
        self.env["ORDIVON_DEV_VPN"] = "off"
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VPN", result.stderr)
        self.assertEqual(self.events(), ["mise:install --dry-run-code --include-task-tools"])

    def test_absent_python_lock_fails_before_mise_preflight_or_install(self):
        (self.scope / "pyproject.toml").write_text(
            "[project]\nname='missing-lock'\nversion='0.1.0'\n"
        )
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uv.lock", result.stderr)
        self.assertFalse(self.log.exists())

    def test_absent_pnpm_lock_fails_before_mise_preflight_or_install(self):
        (self.scope / "package.json").write_text('{"name":"missing-lock"}\n')
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pnpm-lock.yaml", result.stderr)
        self.assertFalse(self.log.exists())

    def test_mixed_npm_and_pnpm_locks_fail_before_any_tool_or_network_effect(self):
        # A partially migrated consumer must fail closed, not arbitrarily
        # select the pnpm branch and ignore its stale npm lock.
        (self.scope / "package.json").write_text('{"name":"conflicted-locks"}\n')
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        (self.scope / "package-lock.json").write_text('{"lockfileVersion":3}\n')
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mixed npm and pnpm locks", result.stderr)
        self.assertFalse(self.log.exists())

    def test_mixed_technology_owner_requires_every_lock_before_side_effects(self):
        (self.scope / "pyproject.toml").write_text(
            "[project]\nname='mixed-owner'\nversion='0.1.0'\n"
        )
        (self.scope / "uv.lock").write_text("version = 1\n")
        (self.scope / "package.json").write_text('{"name":"mixed-owner"}\n')
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pnpm-lock.yaml", result.stderr)
        self.assertFalse(self.log.exists())

    def test_invalid_cli_does_not_trigger_mise_preflight_or_installs(self):
        for args in (("--",), ("services/harness", "--"), ("services/harness", "wrong")):
            with self.subTest(args=args):
                if self.log.exists():
                    self.log.unlink()
                result = self.run_ready(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.log.exists())


    def test_native_npm_nested_consumer_is_rejected_before_side_effects(self):
        nested = self.scope / "node-qualification"
        nested.mkdir()
        (nested / "package.json").write_text('{"name":"node-qualification"}\n')
        (nested / "package-lock.json").write_text('{"lockfileVersion":3}\n')
        self.env["MISE_INSTALLED"] = "true"
        result = self.run_ready("services/harness/node-qualification", "--", "/usr/bin/pwd")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("npm lock unsupported", result.stderr)
        self.assertIn("pnpm import", result.stderr)
        self.assertFalse(self.log.exists(), "reject before tool detection or downloads")

    def test_implicit_nested_pnpm_consumer_uses_closest_locked_project(self):
        nested = self.scope / "providers" / "cloudflare"
        nested.mkdir(parents=True)
        (nested / "package.json").write_text('{"name":"cloudflare"}\n')
        (nested / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text('#!/bin/sh\nprintf "pnpm:%s\\n" "$*" >> "$RECORDER"\n')
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        result = self.run_ready("--", "/usr/bin/pwd", cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), nested.resolve())
        self.assertIn("pnpm:install --frozen-lockfile --offline", self.events())

    def test_pnpm_workspace_member_consumes_parent_shared_lock(self):
        (self.scope / "package.json").write_text('{"name":"studio"}\n')
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        (self.scope / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n")
        member = self.scope / "apps" / "preview"
        member.mkdir(parents=True)
        (member / "package.json").write_text('{"name":"preview"}\n')
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text('#!/bin/sh\nprintf "pnpm:%s\\n" "$*" >> "$RECORDER"\n')
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        result = self.run_ready("--", "/usr/bin/pwd", cwd=member)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.scope.resolve())
        self.assertIn("pnpm:install --frozen-lockfile --offline", self.events())

    def test_nested_python_consumer_uses_parent_mise_python_and_own_uv_lock(self):
        nested = self.scope / "providers" / "python"
        nested.mkdir(parents=True)
        (nested / "pyproject.toml").write_text('[project]\nname="sample"\nversion="0.1.0"\n')
        (nested / "uv.lock").write_text('version = 1\n')
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        uv = toolbin / "uv"
        uv.write_text('#!/bin/sh\nprintf "uv:%s\\n" "$*" >> "$RECORDER"\n')
        uv.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.env["MISE_SELECTED_PYTHON"] = "/usr/bin/python3"
        result = self.run_ready("--", "/usr/bin/pwd", cwd=nested)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), nested.resolve())
        self.assertIn("uv:sync --locked --offline", self.events())


    def test_nested_preflight_and_version_projection_use_owner_mise_directory(self):
        nested = self.scope / "providers" / "cloudflare"
        nested.mkdir(parents=True)
        (nested / "package.json").write_text('{"name":"cloudflare"}\n')
        (nested / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text("#!/bin/sh\nexit 0\n")
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.mise.write_text(
            "#!/bin/sh\n"
            'printf "cwd:%s|command:%s\\n" "$PWD" "$*" >> "$RECORDER"\n'
            'if [ "$1" = install ]; then exit 0; fi\n'
            'if [ "$1" = env ]; then exit 0; fi\n'
            'if [ "$1" = exec ]; then shift 2; exec "$@"; fi\n'
        )
        self.mise.chmod(0o755)
        result = self.run_ready("services/harness/providers/cloudflare", "--", "/usr/bin/pwd")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), nested.resolve())
        entries = self.log.read_text().splitlines()
        self.assertIn(
            f"cwd:{self.scope.resolve()}|command:install --dry-run-code --include-task-tools",
            entries,
        )
        self.assertIn(f"cwd:{self.scope.resolve()}|command:env --paths", entries)


    def test_cached_pnpm_dependencies_bootstrap_without_vpn_or_provider(self):
        (self.scope / "package.json").write_text('{"name":"cache-ready"}\n')
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text(
            '#!/bin/sh\nprintf "pnpm:%s\\n" "$*" >> "$RECORDER"\n'
            '[ "$3" = "--offline" ] || exit 82\n'
        )
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.env["MISE_INSTALLED"] = "true"
        self.env["ORDIVON_DEV_VPN"] = "off"
        self.provider.unlink()
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("pnpm:install --frozen-lockfile --offline", self.events())
        self.assertNotIn("pnpm:install --frozen-lockfile", self.events())

    def test_missing_pnpm_cache_uses_existing_network_provider_as_fallback(self):
        (self.scope / "package.json").write_text('{"name":"cache-missing"}\n')
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text(
            '#!/bin/sh\nprintf "pnpm:%s\\n" "$*" >> "$RECORDER"\n'
            'case "$*" in *--offline*) exit 73;; esac\n'
        )
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.env["MISE_INSTALLED"] = "true"
        self.provider.write_text(
            '#!/bin/bash\nprintf "network:%s\\n" "$*" >> "$RECORDER"\n'
            '[[ "$1" == -- ]] || exit 2\nshift\nexec "$@"\n'
        )
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        events = self.events()
        self.assertLess(
            events.index("pnpm:install --frozen-lockfile --offline"),
            events.index("pnpm:install --frozen-lockfile"),
        )
        self.assertEqual(sum(event.startswith("network:") for event in events), 1)

    def test_offline_python_cache_bootstrap_without_vpn_or_provider(self):
        (self.scope / "pyproject.toml").write_text(
            '[project]\nname="cached-python"\nversion="0.1.0"\n'
        )
        (self.scope / "uv.lock").write_text("version = 1\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        uv = toolbin / "uv"
        uv.write_text(
            '#!/bin/sh\nprintf "uv:%s\\n" "$*" >> "$RECORDER"\n'
            '[ "$3" = "--offline" ] || exit 82\n'
        )
        uv.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.env["MISE_INSTALLED"] = "true"
        self.env["MISE_SELECTED_PYTHON"] = "/usr/bin/python3"
        self.env["ORDIVON_DEV_VPN"] = "off"
        self.provider.unlink()
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uv:sync --locked --offline", self.events())

    def test_missing_offline_cache_does_not_disable_vpn_policy(self):
        (self.scope / "package.json").write_text('{"name":"offline-missing"}\n')
        (self.scope / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
        toolbin = self.root / "toolbin"
        toolbin.mkdir()
        pnpm = toolbin / "pnpm"
        pnpm.write_text(
            '#!/bin/sh\nprintf "pnpm:%s\\n" "$*" >> "$RECORDER"\nexit 73\n'
        )
        pnpm.chmod(0o755)
        self.env["PATH"] = f"{toolbin}:/usr/bin:/bin"
        self.env["MISE_INSTALLED"] = "true"
        self.env["ORDIVON_DEV_VPN"] = "off"
        result = self.run_ready("services/harness", "--", "/usr/bin/true")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VPN", result.stderr)
        self.assertIn("pnpm:install --frozen-lockfile --offline", self.events())
        self.assertNotIn("pnpm:install --frozen-lockfile", self.events())

if __name__ == "__main__":
    unittest.main()
