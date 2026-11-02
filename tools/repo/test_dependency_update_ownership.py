#!/usr/bin/env python3
"""Keep dependency-update authority and cross-directory grouping unambiguous."""
from __future__ import annotations

import json
import subprocess
import tomllib
import unittest
from pathlib import Path, PurePosixPath

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _dependency_update_owner_violations(root, ecosystem, manifests, watch_roots):
    """Exact manifest -> updater root relation; only proved workspace members inherit."""
    if ecosystem not in {"npm", "cargo"}:
        raise ValueError(f"unsupported ecosystem: {ecosystem}")
    violations = {}
    for manifest in manifests:
        parent = PurePosixPath(manifest).parent
        consumers = []
        for declared in watch_roots:
            if not declared.startswith("/"):
                continue
            owner = PurePosixPath(declared.lstrip("/"))
            if parent == owner:
                consumers.append(declared)
                continue
            try:
                relative = parent.relative_to(owner)
            except ValueError:
                continue
            # Nested manifests only inherit a watcher through a real package
            # manager workspace, not merely because a parent directory exists.
            if ecosystem == "npm":
                workspace = root / str(owner) / "pnpm-workspace.yaml"
                if not workspace.is_file():
                    continue
                data = yaml.safe_load(workspace.read_text(encoding="utf-8")) or {}
                patterns = data.get("packages", [])
            else:
                workspace = root / str(owner) / "Cargo.toml"
                if not workspace.is_file():
                    continue
                patterns = tomllib.loads(workspace.read_text(encoding="utf-8")).get(
                    "workspace", {}
                ).get("members", [])
            # Dependabot's updater root must cover a declared workspace
            # member from its *start*, not an arbitrary trailing subtree.
            # PurePath.match is right-anchored for relative patterns and
            # wrongly admits vendor/apps/foo as apps/*; full_match uses
            # owner-relative whole-path matching, including genuine **.
            if any(
                not pattern.startswith("!")
                and relative.full_match(pattern)
                for pattern in patterns
            ):
                consumers.append(declared)
        if len(consumers) != 1:
            violations[manifest] = consumers
    return violations


class DependencyUpdateOwnershipTests(unittest.TestCase):
    def test_unconsumed_opa_toolchain_pins_are_retired(self):
        """Capital uses native Python; Artifact binds an external release OPA carrier."""
        for owner in ("domains/capital", "capabilities/artifact"):
            manifest = tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
            self.assertNotIn("opa", manifest["tools"], f"{owner} must not install unused OPA")
        # Do not confuse an unconsumed Mise version pin with Artifact's actual
        # OCI release policy: the production carrier is an explicit external
        # executable whose path and SHA-256 enter the release evidence.
        carrier = (ROOT / "capabilities/artifact/scripts/artifact_oci_package.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ARTIFACT_OPA"', carrier)
        self.assertIn('sha256_file(DEFAULT_OPA)', carrier)
        active_security = tomllib.loads(
            (ROOT / "platform/security/mise.toml").read_text(encoding="utf-8")
        )
        self.assertIn("opa", active_security["tools"])
        # Distribution's synthetic R7 n8n consumer uses a JSON intent fixture,
        # not its formerly self-tested Python/OPA decision interpreter.
        retired = tomllib.loads(
            (ROOT / "capabilities/distribution/mise.toml").read_text(encoding="utf-8")
        )
        self.assertNotIn("opa", retired["tools"])
        self.assertFalse((ROOT / "capabilities/distribution/policy/distribution.rego").exists())
        self.assertTrue(
            (ROOT / "capabilities/distribution/evidence/"
             "r7-artifact-development-publication-intent.json").is_file()
        )

    def test_active_opa_policy_owners_consume_one_current_version(self):
        """Actual Security and Composition consumers converge; Next no longer owns OPA."""
        owners = ("platform/security", "packages/composition")
        versions = {
            owner: tomllib.loads((ROOT / owner / "mise.toml").read_text(encoding="utf-8"))
            ["tools"]["opa"]
            for owner in owners
        }
        self.assertEqual(len(set(versions.values())), 1, versions)
        next_tools = tomllib.loads(
            (ROOT / "meta/next/mise.toml").read_text(encoding="utf-8")
        )["tools"]
        self.assertNotIn("opa", next_tools)
        self.assertTrue(
            (ROOT / "packages/composition/tests/test_research_adopted_policy.py").is_file()
        )

    def test_python_uv_lock_has_one_updater(self):
        renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        # Python uv and Mise tool versions have distinct canonical file owners.
        # Dependabot continues to own npm/Cargo/Nix, so enabling those Renovate
        # managers would create competing dependency update authorities.
        self.assertEqual(set(renovate["enabledManagers"]), {"pep621", "mise"})
        self.assertTrue(renovate["lockFileMaintenance"]["enabled"])
        self.assertEqual(
            renovate["packageRules"],
            [
                {"matchManagers": ["pep621"], "groupName": "Python {{depName}}"},
                {"matchManagers": ["mise"], "groupName": "Mise {{depName}}"},
            ],
        )
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        ecosystems = [item["package-ecosystem"] for item in config["updates"]]
        self.assertNotIn("uv", ecosystems)

    def test_mise_toolchain_updates_have_one_nonduplicated_owner(self):
        """Mise pins are real consumers, not covered by Python-only Renovate."""
        renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        self.assertTrue(
            (ROOT / "mise.toml").is_file(), "no root Mise consumer for the manager"
        )
        self.assertEqual(set(renovate["enabledManagers"]), {"pep621", "mise"})
        self.assertNotIn(
            "mise", {row["package-ecosystem"] for row in config["updates"]}
        )
        self.assertFalse(renovate.get("automerge", False))
        self.assertLessEqual(renovate["prConcurrentLimit"], 4)

    def test_all_tracked_npm_and_cargo_manifests_have_one_update_owner(self):
        """Every new dependency manifest must have exactly one real updater."""
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        by_ecosystem = {row["package-ecosystem"]: row for row in config["updates"]}
        tracked = [
            path for path in subprocess.check_output(
                ["git", "ls-files", "-z"], cwd=ROOT,
            ).decode("utf-8").split("\0") if path
        ]
        for ecosystem, name in (("npm", "package.json"), ("cargo", "Cargo.toml")):
            manifests = [path for path in tracked if Path(path).name == name]
            self.assertTrue(manifests, ecosystem)
            violations = _dependency_update_owner_violations(
                ROOT, ecosystem, manifests, by_ecosystem[ecosystem]["directories"],
            )
            self.assertEqual(violations, {}, f"{ecosystem} owner holes/duplications: {violations}")

    def test_update_owner_cover_rejects_new_orphan_and_duplicate_paths(self):
        """Negative controls: unregistered manifests or ambiguous watchers cannot pass."""
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        by_ecosystem = {row["package-ecosystem"]: row for row in config["updates"]}
        for ecosystem, path in (
            ("npm", "domains/research/unadmitted/package.json"),
            ("cargo", "domains/research/unadmitted/Cargo.toml"),
        ):
            actual = _dependency_update_owner_violations(
                ROOT, ecosystem, [path], by_ecosystem[ecosystem]["directories"],
            )
            self.assertEqual(actual, {path: []})
        # A directory beneath a valid watcher is not automatically a valid
        # workspace package (media admits only apps/* and packages/*).
        nested = "capabilities/media/apps/unknown/nested/package.json"
        self.assertEqual(
            _dependency_update_owner_violations(
                ROOT, "npm", [nested], by_ecosystem["npm"]["directories"],
            ),
            {nested: []},
        )
        # pathlib.PurePath.match uses right-anchored matching for relative
        # patterns. vendor/apps/rogue must not be treated as apps/* at the
        # package-manager workspace root, nor vendor/crates as crates/*.
        for ecosystem, path, declared in (
            ("npm", "capabilities/media/vendor/apps/rogue/package.json", ["/capabilities/media"]),
            ("cargo", "services/runtime/vendor/crates/rogue/Cargo.toml", ["/services/runtime"]),
        ):
            self.assertEqual(
                _dependency_update_owner_violations(ROOT, ecosystem, [path], declared),
                {path: []},
                f"{ecosystem} relative workspace pattern impersonation",
            )
        duplicate = _dependency_update_owner_violations(
            ROOT, "npm", ["domains/game/package.json"], ["/domains/game", "/domains/game"],
        )
        self.assertEqual(duplicate, {"domains/game/package.json": ["/domains/game", "/domains/game"]})

    def test_same_name_groups_preserve_separate_owner_locks(self):
        config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
        by_ecosystem = {x["package-ecosystem"]: x for x in config["updates"]}
        self.assertEqual(len(by_ecosystem), len(config["updates"]))
        for name in ("npm", "nix"):
            update = by_ecosystem[name]
            self.assertGreater(len(update["directories"]), 1)
            self.assertEqual(update["groups"]["same-dependency"], {"group-by": "dependency-name"})
            self.assertEqual(len(update["directories"]), len(set(update["directories"])))
        cargo = by_ecosystem["cargo"]
        self.assertEqual(
            set(cargo["directories"]),
            {"/services/runtime"},
        )
        self.assertEqual(
            cargo["groups"]["same-dependency"], {"group-by": "dependency-name"}
        )
        self.assertNotIn("directory", cargo)
        for directory in cargo["directories"]:
            self.assertTrue((ROOT / directory.lstrip("/") / "Cargo.toml").is_file())
            self.assertTrue((ROOT / directory.lstrip("/") / "Cargo.lock").is_file())
        self.assertEqual(by_ecosystem["github-actions"]["directory"], "/")


if __name__ == "__main__":
    unittest.main()
