import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_spice", ROOT / "scripts/artifact_spice.py")
M = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(M)

GOOD = """* bounded RC transient fixture\nV1 in 0 PULSE(0 1 0 1u 1u 1m 2m)\nR1 in out 1k\nC1 out 0 1u\n.tran 10u 4m\n.measure tran vmax MAX v(out)\n.measure tran vend FIND v(out) AT=4m\n.end\n"""
BAD = """* malformed fixture\nV1 in 0 1\nTHIS IS NOT A VALID SPICE ELEMENT\n.tran 1u 10u\n.end\n"""


def write_contract(path: Path, *, too_tight: bool = False) -> None:
    path.write_text(json.dumps({
        "schemaVersion": 1, "kind": "eda-spice-transient-measure-contract-v1", "minimumDataRows": 400,
        "measurements": {"vmax": {"min": 0.70, "max": 0.71 if too_tight else 0.73}, "vend": {"min": 0.25, "max": 0.28}}
    }, indent=2) + "\n")


class ArtifactSpiceTests(unittest.TestCase):
    def require_tool(self):
        if not Path("/usr/bin/ngspice").is_file(): self.skipTest("ngspice unavailable")

    def test_transient_measure_contract_passes_real_ngspice(self):
        self.require_tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); net=root/'good.cir'; con=root/'contract.json'; net.write_text(GOOD); write_contract(con)
            result=M.verify_spice_transient(net,con,root/'evidence')
            self.assertEqual(result['status'],'PASS',result)
            self.assertGreaterEqual(result['simulation']['dataRows'],400)
            self.assertEqual(result['simulation']['measurements']['vmax']['status'],'PASS')

    def test_malformed_netlist_fails_closed(self):
        self.require_tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); net=root/'bad.cir'; con=root/'contract.json'; net.write_text(BAD); write_contract(con)
            result=M.verify_spice_transient(net,con,root/'evidence')
            self.assertEqual(result['status'],'FAIL')
            self.assertIn('ngspice batch simulation failed',result['failures'])

    def test_numeric_contract_divergence_fails_closed(self):
        self.require_tool()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); net=root/'good.cir'; con=root/'contract.json'; net.write_text(GOOD); write_contract(con,too_tight=True)
            result=M.verify_spice_transient(net,con,root/'evidence')
            self.assertEqual(result['status'],'FAIL')
            self.assertIn('ngspice measurement vmax is absent or outside contract bounds',result['failures'])


if __name__=='__main__': unittest.main()
