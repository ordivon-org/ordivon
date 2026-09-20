import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "scripts/artifact_delivery.py"
DOCTOR = ROOT / "scripts/artifact_delivery_toolchain_doctor.py"
MANIFEST = ROOT / "artifact-delivery/compatibility-retirement-manifest-v1.json"

ALLOWED = {
    "KEEP_CLI",
    "KEEP_COMPAT_WRAPPER",
    "MOVE_TO_OWNER",
    "DEPRECATE",
    "DROP",
}


class ArtifactCompatibilityRetirementA14Tests(unittest.TestCase):
    def _delivery_symbols(self):
        tree = ast.parse(DELIVERY.read_text(encoding="utf-8"))
        return {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        }

    def test_manifest_exists_and_covers_every_live_delivery_callable_exactly_once(self):
        self.assertTrue(MANIFEST.is_file())
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entries = value["symbols"]
        names = [item["symbol"] for item in entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), self._delivery_symbols())

    def test_every_manifest_entry_has_bounded_retirement_contract(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for item in value["symbols"]:
            with self.subTest(symbol=item["symbol"]):
                self.assertIn(item["disposition"], ALLOWED)
                self.assertTrue(item["currentOwner"])
                self.assertTrue(item["targetOwner"])
                self.assertTrue(item["consumerClass"])
                self.assertTrue(item["retirementGate"])
                self.assertIn(item["standing"], {
                    "KEEP",
                    "ACTIVE_BLOCKED",
                    "READY_TO_REMOVE",
                })

    def test_cli_contract_covers_every_parser_verb(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = {item["verb"] for item in value["cliVerbs"]}
        tree = ast.parse(DELIVERY.read_text(encoding="utf-8"))
        main = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        source = DELIVERY.read_text(encoding="utf-8")
        segment = ast.get_source_segment(source, main)
        observed = set()
        for line in segment.splitlines():
            marker = 'sub.add_parser("'
            if marker in line:
                observed.add(line.split(marker, 1)[1].split('"', 1)[0])
        self.assertEqual(declared, observed)

    def test_toolchain_doctor_no_longer_imports_delivery_python_facade(self):
        source = DOCTOR.read_text(encoding="utf-8")
        self.assertNotIn("import artifact_delivery", source)
        self.assertNotIn("artifact_delivery_runtime.", source)
        self.assertIn("artifact_trust.vsa", source)

    def test_proven_dead_helpers_are_removed(self):
        tree = ast.parse(DELIVERY.read_text(encoding="utf-8"))
        funcs = {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        for name in (
            "load_json",
            "_require_uri",
            "_cosign_executable",
            "_cosign_selection_provenance",
        ):
            self.assertNotIn(name, funcs)

    def test_production_python_modules_do_not_import_delivery_facade(self):
        roots = (
            ROOT / "scripts",
            ROOT / "artifact_core",
            ROOT / "artifact_capabilities",
            ROOT / "artifact_evidence",
            ROOT / "artifact_trust",
            ROOT / "artifact_verification",
            ROOT / "artifact_verifiers",
            ROOT / "artifact_operations",
        )
        offenders = []
        for base in roots:
            for path in base.rglob("*.py"):
                if path == DELIVERY:
                    continue
                source = path.read_text(encoding="utf-8")
                if (
                    "import artifact_delivery" in source
                    or "from artifact_delivery import" in source
                ):
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_toolchain_doctor_audits_trust_owner_source_not_delivery_source(self):
        source = DOCTOR.read_text(encoding="utf-8")
        self.assertIn('ROOT / "artifact_trust/vsa.py"', source)
        self.assertNotIn(
            'source_text = (ROOT / "scripts/artifact_delivery.py").read_text()',
            source,
        )

    def test_manifest_records_dead_helpers_as_retired_evidence(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        retired = {item["symbol"]: item for item in value["retiredSymbols"]}
        for name in (
            "load_json",
            "_require_uri",
            "_cosign_executable",
            "_cosign_selection_provenance",
        ):
            self.assertEqual(retired[name]["wave"], "A14")
            self.assertEqual(retired[name]["reason"], "zero-live-callers")


if __name__ == "__main__":
    unittest.main()
