from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def required_claims(profile_id: str) -> set[str]:
    path = ROOT / "artifact-delivery/shadow-v2/examples" / f"{profile_id}-v2.json"
    value = json.loads(path.read_text())
    return {
        key
        for key, claim in value["requiredEvidence"].items()
        if claim.get("required") is True
    }


def native_claim_keys(profile_id: str, module: ModuleType) -> set[str]:
    by_profile = getattr(module, "CLAIM_POINTERS_BY_PROFILE", None)
    if isinstance(by_profile, dict) and profile_id in by_profile:
        return set(by_profile[profile_id])
    pointers = getattr(module, "CLAIM_POINTERS", None)
    if isinstance(pointers, dict):
        return set(pointers)
    if profile_id == "audio-wave-pcm16-r1":
        return set(module._claims())  # noqa: SLF001 - explicit legacy native contract
    if profile_id == "still-image-png-srgb-r1":
        return set(module._claim_results())  # noqa: SLF001 - explicit legacy native contract
    return set()


class ArtifactNativeClaimCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        donor = load_module(ROOT / "scripts/artifact_donor_export.py", "artifact_donor_export_claim_coverage")
        cls.validator_by_profile = dict(donor.VALIDATOR_BY_PROFILE)
        cls.bound_profiles = {
            json.loads(path.read_text())["profileId"]
            for path in (ROOT / "artifact-delivery/shadow-bindings").glob("*.json")
        }

    def test_every_current_bound_profile_has_a_validator_mapping(self) -> None:
        self.assertEqual(set(self.validator_by_profile), self.bound_profiles)

    def test_every_bound_profile_has_exact_required_native_claim_keys(self) -> None:
        for index, profile_id in enumerate(sorted(self.bound_profiles)):
            script = ROOT / self.validator_by_profile[profile_id]
            module = load_module(script, f"claim_coverage_{index}")
            with self.subTest(profileId=profile_id, script=str(script.relative_to(ROOT))):
                self.assertEqual(native_claim_keys(profile_id, module), required_claims(profile_id))

    def test_every_mapped_verifier_physically_emits_or_decorates_claim_results(self) -> None:
        for profile_id, relative in sorted(self.validator_by_profile.items()):
            source = (ROOT / relative).read_text()
            with self.subTest(profileId=profile_id, script=relative):
                self.assertTrue(
                    "claimResults" in source
                    or "emits_explicit_claim_results" in source
                    or "emits_profile_explicit_claim_results" in source,
                    f"{relative} declares no native claimResults emission surface",
                )

    def test_mapping_json_pointers_are_explicit_and_absolute(self) -> None:
        for index, (profile_id, relative) in enumerate(sorted(self.validator_by_profile.items())):
            module = load_module(ROOT / relative, f"claim_pointer_{index}")
            by_profile = getattr(module, "CLAIM_POINTERS_BY_PROFILE", None)
            if isinstance(by_profile, dict) and profile_id in by_profile:
                pointers = by_profile[profile_id]
            else:
                pointers = getattr(module, "CLAIM_POINTERS", None)
            if pointers is None:
                continue  # WAVE/PNG own explicit native envelope constructors.
            with self.subTest(profileId=profile_id):
                self.assertTrue(all(isinstance(pointer, str) and pointer.startswith("/") for pointer in pointers.values()))


if __name__ == "__main__":
    unittest.main()
