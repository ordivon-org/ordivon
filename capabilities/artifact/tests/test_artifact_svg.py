import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SPEC=importlib.util.spec_from_file_location('artifact_svg',ROOT/'scripts/artifact_svg.py');M=importlib.util.module_from_spec(SPEC);assert SPEC.loader;SPEC.loader.exec_module(M)
class ArtifactSvgTests(unittest.TestCase):
 def require_tools(self):
  for p in (M.XMLLINT,M.RSVG,M.NODE,M.BROWSER_PROBE):
   if not p.is_file():self.skipTest(str(p))
 def write(self,p:Path,body:str):p.write_text(body)
 def test_bounded_static_svg_passes_reference_and_browser_matrix(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a.svg';self.write(p,'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="24" viewBox="0 0 32 24"><rect x="1" y="1" width="20" height="10" rx="2" fill="#369"/><circle cx="24" cy="12" r="5" fill="none" stroke="#fff" stroke-width="2"/></svg>');v=M.verify_svg(p,r/'e');self.assertEqual(v['status'],'PASS',v);self.assertEqual(v['referenceRender']['render']['width'],32);self.assertTrue(v['browserTargetMatrix']['intrinsicDimensionAgreement']);self.assertGreater(v['browserTargetMatrix']['browsers']['chromium']['nonTransparentPixels'],0)
 def test_script_fails_bounded_profile_before_render(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a.svg';self.write(p,'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><script>alert(1)</script><rect width="10" height="10"/></svg>');v=M.verify_svg(p,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['boundedStaticProfile']['status'],'FAIL');self.assertTrue(any('element outside' in x for x in v['failures']))
 def test_external_image_reference_fails_bounded_profile(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a.svg';self.write(p,'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><image href="https://example.com/x.png" width="10" height="10"/></svg>');v=M.verify_svg(p,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['boundedStaticProfile']['status'],'FAIL')
 def test_mismatched_viewbox_fails_profile(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a.svg';self.write(p,'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 20 20"><rect width="10" height="10"/></svg>');v=M.verify_svg(p,r/'e');self.assertEqual(v['status'],'FAIL');self.assertIn('R1 requires viewBox exactly 0 0 width height',v['failures'])
 def test_doctype_is_rejected_even_if_xml_is_well_formed(self):
  self.require_tools()
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/'a.svg';self.write(p,'<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>');v=M.verify_svg(p,r/'e');self.assertEqual(v['status'],'FAIL');self.assertEqual(v['xmlWellFormedness']['status'],'FAIL')
if __name__=='__main__':unittest.main()
