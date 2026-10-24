"""Security owner contract: one native OPA verifier keeps both source and effect fences."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

MIISE = Path(__file__).resolve().parents[1] / "mise.toml"


class OpaVerificationContainerContract(unittest.TestCase):
    def test_private_workspace_opa_verifier_combines_security_fences(self) -> None:
        source = tomllib.loads(MIISE.read_text(encoding="utf-8"))
        verification = source["tasks"]["verify"]["run"]
        actual = [line for line in verification.splitlines() if line.startswith("docker run --rm ")]
        self.assertEqual(len(actual), 1, "one selected native OPA verification command required")
        command = actual[0]
        for required in (
            "--network none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt no-new-privileges",
            """--user "$(stat -c '%u:%g' policies)" """,
            '--volume "$PWD/policies:/policies:ro"',
            '"$image" test -v /policies',
        ):
            with self.subTest(required=required):
                self.assertIn(required, command)


if __name__ == "__main__":
    unittest.main()
