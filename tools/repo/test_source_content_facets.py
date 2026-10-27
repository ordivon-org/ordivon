"""Phase-1-only source-content classification, never execution or proof."""
from __future__ import annotations
import importlib.util
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("source_content_facets",
                pathlib.Path(__file__).with_name("source_content_facets.py"))
assert spec and spec.loader
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

class SourceContentFacetTests(unittest.TestCase):
    def test_json_kind_remains_a_claim_not_authority(self):
        v=M.content_probe("test.json","100644",48,b'{"kind":"claimed-owner","schemaVersion":1}')
        self.assertEqual(v["claimedFields"]["kind"],"claimed-owner")
        self.assertEqual(v["contentForm"],"JSON_OBJECT_DECLARATION")
        self.assertNotIn("semanticQualified",v)
    def test_syntax_failure_is_not_semantic_absence(self):
        v=M.content_probe("p.json","100644",7,b'{"x":')
        self.assertEqual(v["readStanding"],"PARSE_FAILURE")
    def test_python_ast_does_not_import_run_or_require_packages(self):
        v=M.content_probe("tests/test_effect.py","100644",59,
                          b"def test_effect():\n    import not_installed_or_safe_to_execute\n")
        self.assertEqual(v["contentForm"],"PYTHON_TEST_SOURCE")
        self.assertEqual(v["topSymbols"],["test_effect"])
    def test_binary_and_large_have_explicit_unknown(self):
        self.assertEqual(M.content_probe("asset.png","100644",3,None)["readStanding"],"SKIPPED_BINARY")
        self.assertEqual(M.content_probe("source.py","100644",100000,None)["readStanding"],"SKIPPED_SIZE_BOUND")
    def test_narrower_prefix_wins_navigation_only(self):
        z=[{"sourceRef":"region","sourcePrefix":".agents/skills/"},
           {"sourceRef":"foundation","sourcePrefix":".agents/skills/recursive-lego-calculus/"}]
        self.assertEqual(M.candidate_zone(".agents/skills/recursive-lego-calculus/SKILL.md",z),"foundation")
    def test_duplicate_specific_rules_rejected(self):
        z=[{"sourceRef":"x","sourcePrefix":"services/"},
           {"sourceRef":"y","sourcePrefix":"services/"}]
        with self.assertRaisesRegex(ValueError,"equally-specific"):
            M.candidate_zone("services/host/src.py",z)
    def test_unlisted_source_is_exposed(self):
        with self.assertRaisesRegex(ValueError,"Unclassified"):
            M.candidate_zone("unknown/source.py",[{"sourceRef":"runtime","sourcePrefix":"services/runtime/"}])
    def test_rootfiles_own_zone_only_if_no_slash(self):
        z=[{"sourceRef":"region/repository-root-config","sourcePrefix":""}]
        self.assertEqual(M.candidate_zone("AGENTS.md",z),"region/repository-root-config")
        with self.assertRaises(ValueError):M.candidate_zone("weird/AGENTS.md",z)
    def test_symbolic_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"exact"):
            M.exact_git_commit(ROOT,"HEAD")
    def test_specific_aliases_never_authorize_rename(self):
        seed=json.loads((ROOT / "docs/architecture/evidence/ORDIVON_PHASE1_NAME_SEEDS_20261027_R4.json").read_text())
        self.assertEqual(len(seed["specificPathDisplayAliases"]),26)
        self.assertEqual(len({v["candidateName"] for v in seed["specificPathDisplayAliases"]}),26)
        self.assertTrue(all(x["semanticQualification"]=="UNQUALIFIED"
                            and x["canRenamePhysicalPath"] is False
                            and x["consumerStanding"]=="UNKNOWN"
                            for x in seed["specificPathDisplayAliases"]))

    def test_external_standards_records_are_not_runtime_authority(self):
        seed=json.loads((ROOT / "docs/architecture/evidence/ORDIVON_PHASE1_NAME_SEEDS_20261027_R4.json").read_text())
        original={x["sourcePrefix"]:x for x in seed["specificPathDisplayAliases"]}
        self.assertIn("external-standard",original["meta/next/authorities/records/"]["candidateName"])
        self.assertIn("observations",original["meta/next/authorities/observations/"]["candidateName"])
        self.assertNotEqual(original["meta/next/authorities/records/"]["candidateName"],
                            original["meta/next/authorities/observations/"]["candidateName"])

    def test_shebang_without_extension_is_observable(self):
        v=M.content_probe("scripts/check-provider","100755",26,b"#!/usr/bin/env bash\nexit 0\n")
        self.assertEqual(v["contentForm"],"SHEBANG_SCRIPT")


if __name__=="__main__":
    unittest.main()
