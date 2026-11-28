"""Offline regression for the direct-chain concurrent acceptance oracle.

Runs the exact four-probe shell block with an in-process fake curl;
never starts services or makes network requests.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "acceptance/connectivity/direct-chain.sh"
BEGIN = "# Concurrent connection admission: no request may silently fall out of the proxy."
END = 'start_sb "$SB4_UNIT"'


def concurrent_block() -> str:
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count(BEGIN) == 1 and source.count(END) == 1
    return source.split(BEGIN, 1)[1].split(END, 1)[0]


class DirectChainConcurrencyTest(unittest.TestCase):
    def run_case(self, failing: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="network-direct-chain-test-") as work:
            shell = """
set -euo pipefail
TMP="$CASE_TMP"
curl() {
  local output="" previous="" arg
  for arg in "$@"; do
    if [[ "$previous" == "-o" ]]; then output="$arg"; break; fi
    previous="$arg"
  done
  [[ -n "$output" ]] || return 96
  if [[ "$FAIL_INDEX" != "none" && "$output" == */c."$FAIL_INDEX" ]]; then
    return 7
  fi
  echo 'Example Domain' > "$output"
}
""" + concurrent_block() + """
echo 'offline-concurrent-accepted'
"""
            env = {**os.environ, "CASE_TMP": work, "FAIL_INDEX": failing}
            return subprocess.run(["/bin/bash", "-c", shell], env=env, text=True, capture_output=True, timeout=10, check=False)

    def test_all_four_success(self) -> None:
        result = self.run_case("none")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("offline-concurrent-accepted", result.stdout)

    def test_each_failed_child_must_fail_aggregate(self) -> None:
        for index in ("1", "2", "3", "4"):
            with self.subTest(failed_probe=index):
                result = self.run_case(index)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn("offline-concurrent-accepted", result.stdout)
                self.assertIn("concurrent-admission=FAIL failed=1", result.stderr)


if __name__ == "__main__":
    unittest.main()
