import json
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class ClockQualityGateTests(unittest.TestCase):
    def _load(self):
        cfg=json.loads((ROOT/'config/clock_quality_gate.json').read_text())
        ev=json.loads((ROOT/cfg['latestEvidence']).read_text())
        return cfg,ev
    def test_clock_timing_gate_passes_but_overall_execution_does_not(self):
        cfg,ev=self._load()
        self.assertEqual(cfg['standing'],'PASS_PRIVATE_EXECUTION_CLOCK_QUALITY')
        self.assertEqual(ev['standing'],'PASS_PRIVATE_EXECUTION_CLOCK_GATE')
        self.assertLessEqual(ev['observedAbsOffsetMsMax'],cfg['privateExecutionMaxAbsOffsetMs'])
        self.assertTrue(ev['consequence']['demoExecutionAdmission'])
        self.assertTrue(ev['consequence']['liveExecutionAdmission'])
        self.assertFalse(ev['consequence']['overallPrivateExecutionAdmission'])
        self.assertFalse(cfg['wslIndependentNtpDaemonAllowed'])
        self.assertFalse(cfg['applicationClockForgeryAllowed'])
    def test_windows_authority_and_wsl_host_ptp_are_healthy(self):
        _,ev=self._load()
        self.assertEqual(ev['windows']['status'],'RUNNING')
        self.assertGreater(ev['windows']['stratum'],0)
        self.assertNotIn('Local CMOS',ev['windows']['observedSource'])
        self.assertTrue(ev['wslHostPtp']['serviceActive'])
        self.assertFalse(ev['rootCause']['adminRemediationRequired'])
    def test_gate_checker(self):
        x=json.loads(subprocess.check_output([str(ROOT/'scripts/check-clock-quality-gate')],text=True))
        self.assertEqual(x['standing'],'CLOCK_GATE_PASS_PRIVATE_EXECUTION_TIMING')
        self.assertTrue(x['privateExecutionTimingAllowed'])
        self.assertFalse(x['overallPrivateExecutionAllowed'])
if __name__=='__main__': unittest.main()
