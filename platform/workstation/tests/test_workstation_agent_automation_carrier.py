from __future__ import annotations

import fcntl
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'workstation'))
import agent_automation_carrier as w


class AgentAutomationWrapperTests(unittest.TestCase):
    def test_wrapper_targets_browserless_temporal_facade_not_legacy_tool(self):
        text=(ROOT/'workstation/agent_automation_carrier.py').read_text()
        self.assertIn('agent_automation_browserless.py',text)
        self.assertIn('agent-automation-mcp-v1/.venv/bin/python',text)
        self.assertIn('subprocess.run',text)
        self.assertNotIn('from agent_automation_browserless import main',text)
        self.assertIn('/etc/ordivon/agent-automation-browserless.json',text)
        self.assertNotIn('agent_automation_tool',text)

    def test_wrapper_defaults_to_immutable_current_release(self):
        text=(ROOT/'workstation/agent_automation_carrier.py').read_text()
        self.assertIn('/opt/ordivon/agent-automation/current',text)
        self.assertNotIn('"/root/workstation-lab"',text)
        self.assertNotIn('ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT',text)

    def test_wrapper_delegates_facade_to_dependency_bearing_control_runtime(self):
        completed=subprocess.CompletedProcess([],0)
        with patch.object(w,'CONTROL_PYTHON',Path('/control/python')), patch.object(w,'DEFAULT_SOURCE_ROOT',ROOT), patch.object(Path,'is_file',return_value=True), patch.object(w.subprocess,'run',return_value=completed) as run, patch.object(sys,'argv',['agent-automation','provider-preflight','--endpoint-id','carrier-a']):
            self.assertEqual(w.main(),0)
        argv=run.call_args.args[0]
        self.assertEqual(argv[0],'/control/python')
        self.assertTrue(str(argv[1]).endswith('scripts/agent_automation_browserless.py'))
        self.assertEqual(argv[2:4],['--config','/etc/ordivon/agent-automation-browserless.json'])
        self.assertIn('provider-preflight',argv)

    def test_closed_gate_blocks_mutating_admission_but_not_read_only_action(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); lock=root/'release.lock'; closed=root/'closed.json'; root.mkdir(exist_ok=True); closed.write_text('{}')
            with patch.object(w,'ADMISSION_ROOT',root), patch.object(w,'ADMISSION_LOCK',lock), patch.object(w,'ADMISSION_CLOSED',closed):
                with self.assertRaisesRegex(SystemExit,'HOLD_CLOSED'):
                    with w._admission_read_lease('birth'): pass
                with w._admission_read_lease(None): pass

    def test_mutating_cli_lease_blocks_behind_cross_process_release_fence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); lock=root/'release.lock'; ready=root/'ready'
            lock.touch()
            code=(
                "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
                "import agent_automation_carrier as w; r=Path(sys.argv[2]); "
                "w.ADMISSION_ROOT=r; w.ADMISSION_LOCK=r/'release.lock'; w.ADMISSION_CLOSED=r/'closed.json'; "
                "(r/'ready').write_text('ready'); "
                "cm=w._admission_read_lease('birth'); cm.__enter__(); print('ADMITTED',flush=True); cm.__exit__(None,None,None)"
            )
            with lock.open('a+') as handle:
                fcntl.flock(handle.fileno(),fcntl.LOCK_EX)
                child=subprocess.Popen([sys.executable,'-c',code,str(ROOT/'workstation'),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                deadline=time.monotonic()+3
                while not ready.exists() and time.monotonic()<deadline: time.sleep(0.01)
                self.assertTrue(ready.exists(),'child did not reach admission attempt')
                time.sleep(0.1); self.assertIsNone(child.poll(),'mutating CLI crossed an exclusive release fence')
                fcntl.flock(handle.fileno(),fcntl.LOCK_UN)
                out,err=child.communicate(timeout=5)
            self.assertEqual(child.returncode,0,err); self.assertEqual(out.strip(),'ADMITTED')


if __name__=='__main__': unittest.main()
