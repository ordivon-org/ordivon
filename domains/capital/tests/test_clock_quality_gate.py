from pathlib import Path
import json
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ClockQualityGateTests(unittest.TestCase):
    def test_private_execution_fails_closed(self):
        cfg=json.loads((ROOT/'config/clock_quality_gate.json').read_text())
        ev=json.loads((ROOT/'evidence/clock-quality-audit-20260913.json').read_text())
        self.assertEqual(cfg['standing'],'BLOCK_PRIVATE_EXECUTION')
        self.assertGreater(ev['observedAbsOffsetMsMax'],cfg['privateExecutionMaxAbsOffsetMs'])
        self.assertFalse(cfg['wslIndependentNtpDaemonAllowed'])
        self.assertFalse(cfg['applicationClockForgeryAllowed'])
        self.assertFalse(ev['consequence']['demoExecutionAdmission'])
        self.assertFalse(ev['consequence']['liveExecutionAdmission'])

    def test_gate_checker(self):
        out=subprocess.check_output([str(ROOT/'scripts/check-clock-quality-gate')],text=True)
        x=json.loads(out)
        self.assertEqual(x['standing'],'CLOCK_GATE_BLOCKING_PRIVATE_EXECUTION')
        self.assertTrue(x['publicShadowAllowed'])
        self.assertFalse(x['privateExecutionAllowed'])

if __name__=='__main__':
    unittest.main()
