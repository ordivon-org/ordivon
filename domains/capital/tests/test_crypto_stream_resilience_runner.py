import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
class ResilienceRunnerTests(unittest.TestCase):
    def test_both_venues_are_fault_injected_in_one_network_v2_session(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text()
        self.assertIn('--target-venue OKX',s)
        self.assertIn('--target-venue BINANCE',s)
        self.assertIn('PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT',s)
    def test_candidate_uses_exact_network_v2_authority_without_surfpath(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3-candidate').read_text()
        self.assertNotIn('surfpath',s.lower())
        self.assertNotIn('--ingresses',s)
        self.assertIn('check-network-v2-public-data',s)
        self.assertIn('ORDIVON_MC_OKX_WS_PROXY',s)
        self.assertIn('ORDIVON_MC_BINANCE_SPOT_WS_PROXY',s)
        session=(ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text()
        self.assertIn('run-capability-python',session)
        self.assertIn('-m ordivon_capital.markets.crypto_stream_resilience',session)
        self.assertNotIn('/usr/bin/uv run',session)
        self.assertNotIn('.venv/bin/python', (ROOT/'scripts/run-crypto-stream-resilience-r3-session').read_text())
    def test_master_keeps_authority_and_clock_gates(self):
        s=(ROOT/'scripts/run-crypto-stream-resilience-r3').read_text()
        self.assertIn('check-execution-policy',s)
        self.assertIn('check-clock-quality-gate',s)
        self.assertIn('PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER',s)
        self.assertNotIn('candidates=(',s)
if __name__=='__main__': unittest.main()


# Native shell entrypoint tests with isolated filesystem/producer fixtures.
# The stubs cannot open market connections or write financial effects.
def _isolated_reconnect_carrier(tmp_path):
    repo = tmp_path / "capital"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "run-crypto-stream-resilience-r3",
        "run-crypto-stream-resilience-r3-candidate",
        "run-crypto-stream-resilience-r3-session",
    ):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)
    producer = scripts / "run-capability-python"
    producer.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
venue = args[args.index("--target-venue")+1]
out = pathlib.Path(args[args.index("--output")+1])
with open(os.environ["TEST_CALLS"], "a") as f:
    f.write(venue + "\\n")
mode = os.environ.get("TEST_MODE", "valid")
flags = dict(brokerCredentialsUsed=False, privateAccountDataUsed=False,
             externalFinancialWritesAttempted=False, demoExecutionAttempted=False,
             liveExecutionAttempted=False, hostWallClockUsedForAdmission=False)
result = dict(schemaVersion=2,
    kind="ordivon.capital.markets.crypto-stream-reconnect-qualification",
    standing="PASS_PUBLIC_STREAM_RECONNECT", targetVenue=venue,
    injectedDisconnect=True, injectedGeneration=1, reconnectedGeneration=2,
    reconnectLatencyMs=1.25, measuredRoundCountRequired=3,
    warmup=dict(qualified=True, role="WARMUP_BEFORE_INJECTION"),
    recovery=dict(qualified=True, role="RECOVERY"),
    measured=[dict(qualified=True, role="MEASURED_AFTER_RECOVERY", sequence=i)
              for i in (1,2,3)], **flags)
if venue == "OKX":
    if mode == "wrong-venue": result["targetVenue"] = "BINANCE"
    if mode == "malformed": result["measured"] = None
    if mode == "short": result["measured"] = []
    if mode == "bool-version": result["schemaVersion"] = True
    if mode == "effect": result["externalFinancialWritesAttempted"] = True
    if mode == "nonfinite": result["reconnectLatencyMs"] = float("inf")
    if mode == "partial-malformed":
        result["standing"] = "PARTIAL_PUBLIC_STREAM_RECONNECT"
        result["reconnectLatencyMs"] = float("inf")
        out.write_text(json.dumps(result).replace("Infinity", "1e309"))
        sys.exit(2)
    if mode == "duplicate-member":
        out.write_text(json.dumps(result).replace('"targetVenue": "OKX"', '"targetVenue": "BINANCE", "targetVenue": "OKX"'))
        sys.exit(0)
    if mode == "exit-mismatch":
        out.write_text(json.dumps(result))
        sys.exit(2)
    if mode == "missing":
        print("synthetic unavailable", file=sys.stderr)
        sys.exit(2)
out.write_text(json.dumps(result))
"""
    )
    producer.chmod(0o755)
    for name in ("check-execution-policy", "check-crypto-data-adapter-policy", "check-clock-quality-gate"):
        p = scripts / name
        p.write_text("#!/usr/bin/env bash\nexit 0\n")
        p.chmod(0o755)
    binding = scripts / "check-network-v2-public-data"
    binding.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' "
        + "'{\"bindingDigest\":\"fixture\",\"authorities\":{\"okxWs\":{\"proxy\":\"offline\"},"
        + "\"binanceSpotWs\":{\"proxy\":\"offline\"}}}'\n"
    )
    binding.chmod(0o755)
    env = {**os.environ, "TEST_CALLS": str(tmp_path / "calls")}
    return repo, env


@pytest.mark.parametrize("entry", ("master", "candidate", "session"))
def test_reconnect_entry_rejects_preexisting_evidence_without_touching_it(tmp_path, entry):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    if entry == "master":
        out = repo / ".artifacts" / "crypto-stream-resilience-r3"
        cmd = [str(repo / "scripts/run-crypto-stream-resilience-r3")]
    elif entry == "candidate":
        out = tmp_path / "candidate"
        cmd = [str(repo / "scripts/run-crypto-stream-resilience-r3-candidate"), str(out)]
    else:
        out = tmp_path / "session"
        cmd = [str(repo / "scripts/run-crypto-stream-resilience-r3-session"), str(repo), str(out)]
    out.mkdir(parents=True)
    (out / "unique.bin").write_bytes(b"prior unconsumed evidence")
    (out / "result.json").write_text('{"standing":"PRIOR_RECEIPT"}')
    result = subprocess.run(cmd, env=env, capture_output=True, timeout=15)
    assert result.returncode != 0
    assert (out / "unique.bin").read_bytes() == b"prior unconsumed evidence"
    assert (out / "result.json").read_text() == '{"standing":"PRIOR_RECEIPT"}'
    assert not (tmp_path / "calls").exists()


@pytest.mark.parametrize("mode", (
    "wrong-venue", "malformed", "short", "bool-version", "effect", "missing",
    "nonfinite", "partial-malformed", "duplicate-member", "exit-mismatch",
))
def test_invalid_venue_receipt_retains_both_results_without_false_pass(tmp_path, mode):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    out = tmp_path / "session"
    result = subprocess.run(
        [str(repo / "scripts/run-crypto-stream-resilience-r3-session"), str(repo), str(out)],
        env={**env, "TEST_MODE": mode}, capture_output=True, timeout=15,
    )
    assert result.returncode != 0
    assert (tmp_path / "calls").read_text().splitlines() == ["OKX", "BINANCE"]
    receipt = json.loads((out / "result.json").read_text())
    assert receipt["standing"] == "PARTIAL_DUAL_VENUE_PUBLIC_STREAM_RECONNECT"
    assert receipt["okx"]["standing"] == "VENUE_RESULT_UNAVAILABLE"
    assert receipt["okx"]["parseError"]
    assert receipt["binance"]["standing"] == "PASS_PUBLIC_STREAM_RECONNECT"
    # A missing or unqualified producer cannot establish no effect.
    assert receipt["externalFinancialWritesAttempted"] is None
    if mode == "missing":
        assert "synthetic unavailable" in receipt["okx"]["stderrTail"]


def test_fresh_reconnect_master_consumes_two_exact_receipts(tmp_path):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    result = subprocess.run(
        [str(repo / "scripts/run-crypto-stream-resilience-r3")],
        env=env, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr.decode()
    payload = json.loads(result.stdout)
    assert payload["standing"] == "PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT_WITH_NETWORK_V2_FAILOVER"
    assert (tmp_path / "calls").read_text().splitlines() == ["OKX", "BINANCE"]
    assert payload["session"]["okx"]["measuredRoundCount"] == 3
    assert payload["session"]["binance"]["measuredRoundCount"] == 3


def test_candidate_exit_agrees_with_session_receipt_not_child_status_alone(tmp_path):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    session = repo / "scripts/run-crypto-stream-resilience-r3-session"
    session.write_text(
        "#!/usr/bin/env bash\nmkdir -- \"$2\"\nprintf '%s\\n' "
        + "'{\"standing\":\"PARTIAL_DUAL_VENUE_PUBLIC_STREAM_RECONNECT\"}' > \"$2/result.json\"\nexit 0\n"
    )
    out = tmp_path / "candidate"
    result = subprocess.run(
        [str(repo / "scripts/run-crypto-stream-resilience-r3-candidate"), str(out)],
        env=env, capture_output=True, timeout=15,
    )
    assert result.returncode != 0
    assert json.loads((out / "result.json").read_text())["standing"] == "WORKLOAD_QUALITY_FAILED"


def test_concurrent_session_claim_has_exactly_one_writer(tmp_path):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    out = tmp_path / "session"
    cmd = [str(repo / "scripts/run-crypto-stream-resilience-r3-session"), str(repo), str(out)]
    first = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    second = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, first_stderr = first.communicate(timeout=15)
    _, second_stderr = second.communicate(timeout=15)
    # Admission is exactly one successful writer; the other process must
    # fail without producer effects. Native launch/diagnostic errors may
    # carry a different nonzero exit. Exact 73 for a rejected mkdir is
    # checked separately with both writable and unwritable diagnostics.
    assert (first.returncode == 0) != (second.returncode == 0), (
        first.returncode, second.returncode, first_stderr, second_stderr
    )
    assert (tmp_path / "calls").read_text().splitlines() == ["OKX", "BINANCE"]
    assert json.loads((out / "result.json").read_text())["standing"] == "PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT"
    assert not list(out.glob(".result-*"))


def test_master_explicit_new_run_does_not_reuse_prior_output(tmp_path):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    entry = str(repo / "scripts/run-crypto-stream-resilience-r3")
    original = subprocess.run([entry], env=env, capture_output=True, timeout=15)
    assert original.returncode == 0
    prior = repo / ".artifacts" / "crypto-stream-resilience-r3" / "result.json"
    before = prior.read_bytes()
    new = tmp_path / "new-run"
    again = subprocess.run([entry, str(new)], env=env, capture_output=True, timeout=15)
    assert again.returncode == 0
    assert prior.read_bytes() == before
    assert json.loads((new / "result.json").read_text())["standing"] == "PASS_DUAL_VENUE_PUBLIC_STREAM_RECONNECT"

@pytest.mark.parametrize("entry", ("master", "candidate", "session"))
@pytest.mark.parametrize("unwritable_stderr", (False, True))
def test_existing_output_rejection_does_not_depend_on_diagnostics(tmp_path, entry, unwritable_stderr):
    repo, env = _isolated_reconnect_carrier(tmp_path)
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "prior.bin"
    sentinel.write_bytes(b"unique prior evidence")
    suffix = "" if entry == "master" else "-" + entry
    exe = str(repo / "scripts" / ("run-crypto-stream-resilience-r3" + suffix))
    cmd = [exe, str(repo), str(out)] if entry == "session" else [exe, str(out)]
    if unwritable_stderr:
        with open("/dev/full", "wb") as error_sink:
            result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=error_sink, timeout=15)
    else:
        result = subprocess.run(cmd, env=env, capture_output=True, timeout=15)
    assert result.returncode == 73
    assert sentinel.read_bytes() == b"unique prior evidence"
    assert not (tmp_path / "calls").exists()
