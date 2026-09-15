import json, tempfile, unittest
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cad',ROOT/'scripts/artifact_cad_step.py'); cad=importlib.util.module_from_spec(spec); spec.loader.exec_module(cad)
class ArtifactCadStepTests(unittest.TestCase):
 def test_positive_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   r=cad.verify_step_solid(ROOT/'tests/fixtures/cad/block-through-hole.step',ROOT/'tests/fixtures/cad/block-through-hole-contract.json',Path(td))
   self.assertEqual('PASS',r['status'],r.get('failures')); self.assertEqual(15,r['occtReadback']['edges']); self.assertEqual(15,r['freecadReadback']['edges'])
 def test_truncated_step_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   bad=Path(td)/'bad.step'; bad.write_bytes((ROOT/'tests/fixtures/cad/block-through-hole.step').read_bytes()[:1200]); r=cad.verify_step_solid(bad,ROOT/'tests/fixtures/cad/block-through-hole-contract.json',Path(td)/'e'); self.assertEqual('FAIL',r['status'])
 def test_malformed_nested_contract_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   c=json.loads((ROOT/'tests/fixtures/cad/block-through-hole-contract.json').read_text()); del c['topology']['edges']; cp=Path(td)/'c.json'; cp.write_text(json.dumps(c)); r=cad.verify_step_solid(ROOT/'tests/fixtures/cad/block-through-hole.step',cp,Path(td)/'e'); self.assertEqual('FAIL',r['status']); self.assertTrue(any('topology.edges' in x for x in r['failures']))
 def test_contract_divergence_fails_after_read(self):
  with tempfile.TemporaryDirectory() as td:
   c=json.loads((ROOT/'tests/fixtures/cad/block-through-hole-contract.json').read_text()); c['bboxMm']['xmax']=41.0; cp=Path(td)/'c.json'; cp.write_text(json.dumps(c)); r=cad.verify_step_solid(ROOT/'tests/fixtures/cad/block-through-hole.step',cp,Path(td)/'e'); self.assertEqual('FAIL',r['status']); self.assertTrue(any('bbox xmax' in x for x in r['failures']))
if __name__=='__main__': unittest.main()
