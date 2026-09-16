from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordivon_harness.skills import SkillCatalog, SkillCatalogError, SkillSource, TrustState
from ordivon_harness.skills.parser import SkillParseError, parse_skill_frontmatter


def write_skill(root: Path, directory: str, name: str, description: str) -> Path:
    skill_dir = root / directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    path = skill_dir / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )
    return path


class SkillParserTests(unittest.TestCase):
    def test_reads_required_fields_without_needing_full_yaml_dependency(self) -> None:
        parsed = parse_skill_frontmatter(
            "---\nmetadata:\n  nested: true\ndescription: \"Do careful work\"\nname: tdd\n---\n# TDD\n"
        )
        self.assertEqual(parsed.name, "tdd")
        self.assertEqual(parsed.description, "Do careful work")

    def test_supports_folded_description(self) -> None:
        parsed = parse_skill_frontmatter(
            "---\nname: tdd\ndescription: >\n  Build behavior from tests\n  before implementation.\n---\n"
        )
        self.assertEqual(parsed.description, "Build behavior from tests before implementation.")

    def test_missing_description_fails_closed(self) -> None:
        with self.assertRaisesRegex(SkillParseError, "description"):
            parse_skill_frontmatter("---\nname: tdd\n---\n")


class SkillCatalogR2Tests(unittest.TestCase):
    def test_inventory_preserves_same_name_from_multiple_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            project = base / "project"
            vendor = base / "vendor"
            write_skill(project, "tdd", "test-driven-development", "Project TDD")
            write_skill(vendor, "tdd", "test-driven-development", "Vendor TDD")
            catalog = SkillCatalog.scan(
                [
                    SkillSource("project", project, "project", 900, TrustState.TRUSTED),
                    SkillSource("vendor", vendor, "vendor", 600, TrustState.APPROVED),
                ]
            )

            self.assertEqual(
                [record.skill_id for record in catalog.candidates("test-driven-development")],
                ["project/test-driven-development", "vendor/test-driven-development"],
            )
            resolution = catalog.resolve("test-driven-development")
            self.assertEqual(resolution.resolved.skill_id, "project/test-driven-development")
            self.assertEqual(
                [record.skill_id for record in resolution.shadowed],
                ["vendor/test-driven-development"],
            )
            self.assertEqual(resolution.reason, "source-priority")

    def test_fully_qualified_ref_bypasses_friendly_name_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            high = base / "high"
            low = base / "low"
            write_skill(high, "tdd", "tdd", "High")
            write_skill(low, "tdd", "tdd", "Low")
            catalog = SkillCatalog.scan(
                [
                    SkillSource("high", high, "project", 900, TrustState.TRUSTED),
                    SkillSource("low", low, "vendor", 1, TrustState.APPROVED),
                ]
            )
            self.assertEqual(catalog.resolve("low/tdd").resolved.description, "Low")

    def test_blocked_and_untrusted_sources_remain_in_raw_inventory_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            blocked = base / "blocked"
            untrusted = base / "untrusted"
            write_skill(blocked, "a", "a", "Blocked")
            write_skill(untrusted, "b", "b", "Untrusted")
            catalog = SkillCatalog.scan(
                [
                    SkillSource("blocked", blocked, "project", 10, TrustState.BLOCKED),
                    SkillSource("untrusted", untrusted, "project", 10, TrustState.UNTRUSTED),
                ]
            )
            self.assertEqual(
                [record.skill_id for record in catalog.inventory],
                ["blocked/a", "untrusted/b"],
            )
            self.assertEqual(catalog.records, ())

    def test_catalog_and_snapshot_revisions_separate_raw_from_effective_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_skill(root, "a", "a", "Blocked but inventoried")
            blocked = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.BLOCKED)]
            )
            approved = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.APPROVED)]
            )
            self.assertNotEqual(blocked.catalog_revision, approved.catalog_revision)
            self.assertNotEqual(blocked.snapshot_revision, approved.snapshot_revision)
            self.assertEqual(len(blocked.inventory), 1)
            self.assertEqual(blocked.records, ())
            self.assertEqual(len(approved.records), 1)

    def test_snapshot_revision_is_deterministic_and_changes_with_skill_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = write_skill(root, "a", "a", "First")
            source = SkillSource("source", root, "user", 5, TrustState.APPROVED)
            before = SkillCatalog.scan([source])
            same = SkillCatalog.scan([source])
            self.assertEqual(before.snapshot_revision, same.snapshot_revision)
            skill.write_text("---\nname: a\ndescription: Second\n---\n", encoding="utf-8")
            after = SkillCatalog.scan([source])
            self.assertNotEqual(before.snapshot_revision, after.snapshot_revision)

    def test_stale_instruction_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = write_skill(root, "a", "a", "First")
            catalog = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.APPROVED)]
            )
            digest = catalog.by_skill_id("source/a").instruction_digest
            skill.write_text("---\nname: a\ndescription: Changed\n---\n", encoding="utf-8")
            with self.assertRaisesRegex(SkillCatalogError, "source/a") as captured:
                catalog.read_text("source/a", expected_instruction_digest=digest)
            self.assertEqual(captured.exception.code, "DIGEST_MISMATCH")

    def test_resource_path_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            write_skill(root, "a", "a", "First")
            (base / "secret.txt").write_text("secret", encoding="utf-8")
            catalog = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.APPROVED)]
            )
            with self.assertRaises(SkillCatalogError) as captured:
                catalog.read_text("source/a", relative_path="../../secret.txt")
            self.assertEqual(captured.exception.code, "PATH_ESCAPE")

    def test_symlinked_skill_file_is_not_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            target = write_skill(outside, "a", "a", "Outside")
            linked_dir = root / "a"
            linked_dir.mkdir()
            (linked_dir / "SKILL.md").symlink_to(target)
            catalog = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.APPROVED)]
            )
            self.assertEqual(catalog.records, ())

    def test_search_ranks_name_match_above_description_only_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_skill(root, "debug", "systematic-debugging", "Investigate failures")
            write_skill(root, "other", "incident-analysis", "Debug service incidents")
            catalog = SkillCatalog.scan(
                [SkillSource("source", root, "user", 5, TrustState.APPROVED)]
            )
            self.assertEqual(
                [record.name for record in catalog.search("debug")],
                ["systematic-debugging", "incident-analysis"],
            )


if __name__ == "__main__":
    unittest.main()
