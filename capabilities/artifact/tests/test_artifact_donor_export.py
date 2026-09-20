import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_donor_export", ROOT / "scripts/artifact_donor_export.py")
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
BASE = "72f41bb46e1e787920643bd26d9db191053eb919"

class ArtifactDonorExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donor = M.build(BASE)

    def test_manifest_schema_validates(self):
        self.assertEqual(M.validate(self.donor), [])

    def test_all_taxonomy_families_and_profiles_are_represented(self):
        c = self.donor["coverage"]
        self.assertEqual(c["taxonomyFamilies"], 16)
        self.assertEqual(c["representedFamilies"], 16)
        taxonomy=json.loads((ROOT/"artifact-delivery/taxonomy-v1.json").read_text())
        expected=sum(len(row.get("currentProfiles",[])) for row in taxonomy["families"])
        self.assertEqual(c["normalizedProfiles"], expected)

    def test_all_shadow_bindings_remain_live_proven(self):
        bound = [p for p in self.donor["profiles"] if p["capabilityBinding"] is not None]
        self.assertEqual(self.donor["coverage"]["liveProvenShadowBindings"], len(bound))
        self.assertTrue(all(p["capabilityBinding"]["standing"] == "LOCAL_LIVE_PROVEN" for p in bound))

    def test_all_isolated_shadow_validators_are_preserved_without_legacy_orchestrator(self):
        refs = [p["validatorImplementation"]["path"] for p in self.donor["profiles"] if p["validatorImplementation"]]
        self.assertEqual(self.donor["coverage"]["isolatedValidatorImplementations"], len(refs))
        self.assertNotIn("scripts/artifact_delivery.py", refs)
        self.assertTrue(all("temporal" not in x.lower() and "runtime" not in x.lower() for x in refs))

    def test_source_taxonomy_and_profile_v2_manifest_are_digest_bound(self):
        for r in self.donor["sourceReferences"].values():
            path=ROOT/r["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), r["sha256"])

    def test_every_file_reference_is_digest_exact(self):
        refs=list(self.donor["sourceReferences"].values())
        for p in self.donor["profiles"]:
            refs.append(p["sourceProfile"])
            if p["objectContract"]: refs.append(p["objectContract"]["schema"])
            if p["capabilityBinding"]: refs.append(p["capabilityBinding"]["reference"])
            if p["validatorImplementation"]: refs.append(p["validatorImplementation"])
        refs += [x["reference"] for x in self.donor["excludedInfrastructure"] if x.get("reference")]
        for r in refs:
            path=ROOT/r["path"]
            self.assertTrue(path.is_file(), r)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), r["sha256"], r["path"])

    def test_composition_sequence_is_never_inferred(self):
        self.assertTrue(all(p["compositionCandidate"]["sequencing"] == "NOT_ENCODED_DO_NOT_INFER" for p in self.donor["profiles"]))

    def test_candidate_problem_keys_are_explicitly_non_core(self):
        self.assertIn("not a universal Core ontology commitment", self.donor["principles"][-2])
        self.assertEqual(len({p["candidateProblemKey"] for p in self.donor["profiles"]}), self.donor["coverage"]["normalizedProfiles"])

    def test_observed_migration_gaps_are_preserved_not_invented_away(self):
        gaps={x["id"]:x for x in self.donor["knownGaps"]}
        profiles=self.donor["profiles"]
        with_contract=sum(p["objectContract"] is not None for p in profiles)
        with_nonclaims=sum(bool(p["resultBoundary"].get("nonClaims")) for p in profiles)
        encoded=sum(p["compositionCandidate"]["sequencing"] != "NOT_ENCODED_DO_NOT_INFER" for p in profiles)
        self.assertEqual(gaps["object-contract-coverage"]["observation"], {"profilesWithExplicitObjectContract":with_contract,"profilesWithoutExplicitObjectContract":len(profiles)-with_contract})
        self.assertEqual(gaps["result-boundary-coverage"]["observation"], {"profilesWithExplicitNonClaims":with_nonclaims,"profilesWithoutExplicitNonClaims":len(profiles)-with_nonclaims})
        self.assertEqual(gaps["composition-sequencing"]["observation"], {"profilesWithEncodedSequence":encoded,"profilesWithoutEncodedSequence":len(profiles)-encoded})
        self.assertTrue(all(x["standing"]=="PRESERVE_GAP_DO_NOT_INVENT" for x in gaps.values()))

    def test_execution_wiring_is_never_promoted(self):
        self.assertTrue(all(p["migrationDisposition"]["executionWiring"] == "DO_NOT_PROMOTE" for p in self.donor["profiles"]))
        concepts=" ".join(x["concept"] for x in self.donor["excludedInfrastructure"]).lower()
        self.assertIn("temporal", concepts)
        self.assertIn("orchestration", concepts)
        self.assertIn("transport", concepts)

if __name__ == "__main__": unittest.main()
