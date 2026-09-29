import json
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProviderCarrierContractTests(unittest.TestCase):
    def test_opa_declares_distinct_portable_and_host_carriers(self):
        value = json.loads((ROOT / "providers.lock.json").read_text(encoding="utf-8"))
        opa = next(row for row in value["providers"] if row["name"] == "opa")
        portable = opa["portableExecutable"]
        self.assertEqual(portable["provider"], "mise")
        self.assertEqual(portable["artifact"], "opa_linux_amd64_static")
        self.assertRegex(portable["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(opa["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotEqual(portable["sha256"], opa["sha256"])
        self.assertTrue(opa["executable"].startswith("/"))

    def test_portable_verify_does_not_require_host_locator(self):
        value = tomllib.loads((ROOT / "mise.toml").read_text(encoding="utf-8"))
        portable = value["tasks"]["verify"]["run"]
        host = value["tasks"]["verify:host-provider"]["run"]
        self.assertIn("mise which opa", portable)
        self.assertIn('portableExecutable', portable)
        self.assertNotIn('print(opa["executable"])', portable)
        self.assertIn('print(opa["executable"])', host)
        self.assertIn('print(opa["sha256"])', host)


if __name__ == "__main__":
    unittest.main()
