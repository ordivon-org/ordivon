from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from source_name_resolution import resolve_source_name


def source_cut(rows):
    return {
        "truthRole": "SOURCE_NAVIGATION_NOT_OWNER_OR_LEGO_QUALIFICATION",
        "sourceRevision": "a" * 40,
        "sourceTree": "b" * 40,
        "ownerManifestIdentity": "100644:blob:" + "c" * 40,
        "classifierSourceIdentity": "100644:blob:" + "d" * 40,
        "entries": rows,
    }


def row(path, cell, label, owner, *, region=None, section=None):
    return {
        "path": path,
        "sourceIdentity": "100644:blob:" + ("a" * 40),
        "sourceCell": cell,
        "sourceCellDisplayName": label,
        "sourceSection": section,
        "sourceRegion": region,
        "semanticName": "Implementations" if owner else "Documentation",
        "verificationOwner": owner,
        "sourceCellRole": "UNQUALIFIED_NESTED_CELL",
        "sourceSectionRole": "UNQUALIFIED_SECTION",
        "sourceFileForm": "PYTHON_SOURCE_FILE",
        "classificationStanding": "REGISTERED_OWNER_SOURCE"
        if owner
        else "DECLARED_SOURCE_REGION",
    }


class SourceNameResolutionTests(unittest.TestCase):
    def setUp(self):
        self.cut = source_cut(
            [
                row(
                    "services/runtime/src/job.py",
                    "runtime/src/job",
                    "Common Tools",
                    "runtime",
                ),
                row(
                    "services/runtime/src/work.py",
                    "runtime/src/job",
                    "Common Tools",
                    "runtime",
                ),
                row(
                    "services/harness/src/bridge.py",
                    "harness/src/bridge",
                    "Common Tools",
                    "harness",
                ),
                row(
                    "services/gateway/src/route.py",
                    "gateway/src/route",
                    "Gateway Routing",
                    "gateway",
                ),
                row("docs/architecture/README.md", None, None, None, region="docs"),
            ]
        )

    def test_interface_form_resolver_never_guesses_a_unique_server(self):
        for idx, value in enumerate(self.cut["entries"][:3]):
            value["sourceInterfaceForm"] = (
                "MCP_SERVER_ADAPTER" if idx in (0, 2)
                else "MCP_CLIENT_ADAPTER"
            )
            value["sourceInterfaceStanding"] = (
                "SOURCE_ONLY_NOT_INSTALLED_OR_CAPABILITY_ADMITTED"
            )
        candidates = resolve_source_name(
            self.cut, name="MCP_SERVER_ADAPTER", field="sourceInterfaceForm"
        )
        self.assertEqual(candidates["standing"],
                         "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")
        self.assertEqual(candidates["candidateGroupCount"], 2)
        self.assertEqual(
            {x["sourceInterfaceForm"] for x in candidates["candidates"]},
            {"MCP_SERVER_ADAPTER"},
        )
        self.assertFalse(candidates["semanticIdentityQualified"])
        self.assertFalse(candidates["physicalRenameAdmissible"])
        scoped = resolve_source_name(
            self.cut, name="MCP_SERVER_ADAPTER", field="sourceInterfaceForm",
            scope_prefix="services/runtime/",
        )
        self.assertEqual(scoped["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")

    def test_unique_area_name_groups_many_nested_cells_without_false_collision(self):
        records = source_cut([
            row("services/runtime/src/a.rs", "runtime/src/a", "runtime / src / a",
                "runtime"),
            row("services/runtime/crates/b.rs", "runtime/crates/b",
                "runtime / crates / b", "runtime"),
            row("services/harness/src/h.py", "harness/src/h",
                "harness / src / h", "harness"),
        ])
        for item in records["entries"]:
            item["semanticName"] = (
                "physical-execution-runtime" if item["verificationOwner"] == "runtime"
                else "bounded-agent-run-harness"
            )
        result = resolve_source_name(records, name="physical-execution-runtime",
                                     field="semanticName")
        self.assertEqual(result["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(result["candidates"][0]["sourceGroup"],
                         "verification-region/runtime")
        self.assertEqual(result["candidates"][0]["sourceName"],
                         "physical-execution-runtime")
        self.assertEqual(result["candidates"][0]["matchedPaths"], 2)
        self.assertFalse(result["semanticIdentityQualified"])

    def test_section_name_groups_nested_source_cells_but_not_similar_sections(self):
        records = source_cut([
            row("services/runtime/crates/a.rs", "runtime/crates/a",
                "runtime / crates / a", "runtime", section="runtime/crates"),
            row("services/runtime/crates/b.rs", "runtime/crates/b",
                "runtime / crates / b", "runtime", section="runtime/crates"),
            row("services/harness/crates/c.rs", "harness/crates/c",
                "harness / crates / c", "harness", section="harness/crates"),
        ])
        result = resolve_source_name(records, name="runtime/crates",
                                     field="sourceSection")
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(result["candidates"][0]["sourceGroup"],
                         "source-section/runtime/crates")
        self.assertEqual(result["candidates"][0]["matchedPaths"], 2)

    def test_colliding_display_name_must_be_ambiguous(self):
        result = resolve_source_name(
            self.cut, name="Common Tools", field="sourceCellDisplayName"
        )
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")
        self.assertEqual(result["candidateGroupCount"], 2)
        self.assertEqual(result["candidates"][1]["matchedPaths"], 2)
        self.assertFalse(result["semanticIdentityQualified"])
        self.assertFalse(result["physicalRenameAdmissible"])

    def test_explicit_scope_recovers_unique_group_without_guessing(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tools",
            field="sourceCellDisplayName",
            scope_prefix="services/runtime/",
        )
        self.assertEqual(result["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(result["candidates"][0]["sourceGroup"], "runtime/src/job")
        self.assertEqual(result["candidates"][0]["matchedPaths"], 2)

    def test_source_cell_identity_excludes_similar_name(self):
        result = resolve_source_name(
            self.cut, name="runtime/src/job", field="sourceCell"
        )
        self.assertEqual(result["candidateGroupCount"], 1)
        self.assertEqual(
            result["candidates"][0]["sampleSourceObjects"][0]["path"],
            "services/runtime/src/job.py",
        )

    def test_same_owner_semantic_name_is_not_unique_across_many_cells(self):
        result = resolve_source_name(
            self.cut, name="Implementations", field="semanticName"
        )
        self.assertEqual(result["candidateGroupCount"], 3)
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")

    def test_truncated_never_silently_selects_first(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tools",
            field="sourceCellDisplayName",
            max_candidates=1,
        )
        self.assertTrue(result["truncated"])
        self.assertEqual(result["candidateGroupCount"], 2)
        self.assertEqual(result["standing"], "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS")

    def test_absent_label_fails_closed_no_implicit_fuzzy_matching(self):
        result = resolve_source_name(
            self.cut,
            name="Common Tool",
            field="sourceCellDisplayName",
        )
        self.assertEqual(result["standing"], "NOT_FOUND")
        self.assertEqual(result["candidateGroupCount"], 0)

    def test_navigation_only_region_never_becomes_approval_authority(self):
        result = resolve_source_name(self.cut, name="docs", field="sourceRegion")
        self.assertEqual(result["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(
            result["candidates"][0]["classificationStanding"], "DECLARED_SOURCE_REGION"
        )
        self.assertFalse(result["proofReuseAdmissible"])

    def test_scope_with_internal_dot_is_rejected_not_reported_absent(self):
        for scope in ("services/./runtime/", "services/runtime/./"):
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, "canonical"):
                resolve_source_name(self.cut, name="Common Tools",
                                    field="sourceCellDisplayName", scope_prefix=scope)

    def test_scope_cannot_cross_git_file_symlink_or_submodule(self):
        for identity in ("100644:blob:", "120000:blob:", "160000:commit:"):
            opaque = row("services/link", None, None, None)
            opaque["sourceIdentity"] = identity + "a" * 40
            cut = source_cut(self.cut["entries"] + [opaque])
            with self.subTest(identity=identity), self.assertRaisesRegex(ValueError, "non-directory"):
                resolve_source_name(cut, name="Common Tools",
                                    field="sourceCellDisplayName",
                                    scope_prefix="services/link/child/")

    def test_canonical_empty_scope_and_exact_whitespace_paths_remain_inspectable(self):
        empty = resolve_source_name(self.cut, name="Common Tools",
                                    field="sourceCellDisplayName",
                                    scope_prefix="services/not-present/")
        self.assertEqual(empty["standing"], "NOT_FOUND")
        spaced = source_cut([row("odd/ leading/call.py", "odd-cell", "Exact Source", None)])
        found = resolve_source_name(spaced, name="Exact Source",
                                    field="sourceCellDisplayName", scope_prefix="odd/ leading/")
        self.assertEqual(found["candidateGroupCount"], 1)

    def test_cli_rejects_noncanonical_scope_with_usage_error(self):
        repo = Path(__file__).resolve().parents[2]
        cut = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        proc = subprocess.run(
            [sys.executable, str(repo / "tools/repo/source_name_resolution.py"),
             "--source-cut", cut, "--repo", str(repo),
             "--name", "runtime", "--field", "verificationOwner",
             "--scope-prefix", "services/./runtime/"],
            cwd=repo, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("canonical", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_invalid_names_fields_and_source_cut_truth_are_rejected(self):
        for kwargs in (
            {"name": " Common Tools"},
            {"field": "approval"},
            {"scope_prefix": "../"},
            {"scope_prefix": "/"},
            {"scope_prefix": "services//runtime/"},
            {"max_candidates": True},
            {"max_candidates": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                resolve_source_name(
                    self.cut,
                    **(
                        {"name": "Common Tools", "field": "sourceCellDisplayName"}
                        | kwargs
                    ),
                )
        with self.assertRaises(ValueError):
            resolve_source_name(
                {"truthRole": "fake", "sourceRevision": "a"},
                name="Common Tools",
                field="sourceCellDisplayName",
            )

    def test_cli_on_real_git_source_cut(self):
        repo = Path(__file__).resolve().parents[2]
        cut = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        result = subprocess.run(
            [
                sys.executable,
                str(repo / "tools/repo/source_name_resolution.py"),
                "--source-cut",
                cut,
                "--repo",
                str(repo),
                "--name",
                "runtime",
                "--field",
                "verificationOwner",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["sourceRevision"], cut)
        self.assertEqual(output["candidateGroupCount"], 1)
        self.assertEqual(output["standing"], "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
        self.assertEqual(output["candidates"][0]["sourceGroup"],
                         "verification-region/runtime")
        self.assertFalse(output["semanticIdentityQualified"])


    def test_current_git_cut_every_declared_area_name_resolves_uniquely(self):
        import tomllib
        from affected_owners import project_source_classification

        repo = Path(__file__).resolve().parents[2]
        cut = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        manifest_bytes = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{cut}:tools/repo/owners.toml"]
        )
        manifest = tomllib.loads(manifest_bytes.decode())
        projection = project_source_classification(repo, cut)
        for owner in manifest["owners"]:
            with self.subTest(area=owner["name"]):
                result = resolve_source_name(
                    projection, name=owner["semantic_name"], field="semanticName"
                )
                self.assertEqual(result["candidateGroupCount"], 1)
                self.assertEqual(result["standing"],
                                 "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
                self.assertEqual(
                    result["candidates"][0]["sourceGroup"],
                    f"verification-region/{owner['name']}",
                )
                self.assertFalse(result["semanticIdentityQualified"])
        for region in manifest.get("source_regions", []):
            with self.subTest(region=region["name"]):
                result = resolve_source_name(
                    projection, name=region["name"], field="sourceRegion"
                )
                self.assertEqual(result["candidateGroupCount"], 1)
                self.assertEqual(result["standing"],
                                 "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF")
                self.assertFalse(result["physicalRenameAdmissible"])


if __name__ == "__main__":
    unittest.main()
