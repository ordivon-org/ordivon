from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=Path('/root/.local/share/ordivon-workstation/artifact-openxml-v1/current/bin/validate-openxml')
PYTHON=Path('/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python')
def validator()->Path:return Path(os.environ.get('ARTIFACT_OPENXML_VALIDATOR',str(DEFAULT)))
def run(path:Path):return subprocess.run([str(validator()),str(path)],text=True,capture_output=True,check=False,timeout=60)
def make_pptx(path:Path,*,off_canvas:bool=False):
    code="""from pptx import Presentation\nfrom pptx.util import Inches\nimport sys\np=Presentation();p.slide_width=Inches(13.333333);p.slide_height=Inches(7.5);s=p.slides.add_slide(p.slide_layouts[6]);x=Inches(20 if sys.argv[2]=='1' else 1);s.shapes.add_textbox(x,Inches(1),Inches(3),Inches(1)).text='Artifact OpenXML';p.save(sys.argv[1])\n"""
    r=subprocess.run([str(PYTHON),'-c',code,str(path),'1' if off_canvas else '0'],text=True,capture_output=True,check=False,timeout=60);assert r.returncode==0,(r.stdout,r.stderr)
def rewrite_zip(path:Path,mutate):
    original=path.with_suffix('.source.pptx');path.rename(original)
    with zipfile.ZipFile(original) as zin,zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data=zin.read(info.filename);out=mutate(info.filename,data)
            if out is not None:zout.writestr(info,out)
def make_docx(path:Path):
    ct='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    doc='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Artifact OpenXML</w:t></w:r></w:p></w:body></w:document>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ct);z.writestr('_rels/.rels',rels);z.writestr('word/document.xml',doc)
def make_xlsx(path:Path):
    code="import xlsxwriter,sys;w=xlsxwriter.Workbook(sys.argv[1]);s=w.add_worksheet();s.write('A1','Artifact OpenXML');w.close()"
    r=subprocess.run([str(PYTHON),'-c',code,str(path)],text=True,capture_output=True,check=False,timeout=60);assert r.returncode==0,(r.stdout,r.stderr)
class ArtifactOpenXmlAssuranceTests(unittest.TestCase):
    def setUp(self):
        if not validator().is_file():self.skipTest('stable OpenXML validator is not production-current')
        if not PYTHON.is_file():self.skipTest('stable Artifact Python is not production-current')
    def test_claim_and_fault_taxonomy_preserve_nonclaims(self):
        claim=json.loads((ROOT/'artifact-delivery/openxml-assurance-method-v1.json').read_text());faults=json.loads((ROOT/'artifact-delivery/openxml-assurance-fault-taxonomy-v1.json').read_text())
        self.assertEqual(claim['methodId'],faults['methodId']);self.assertIn('Microsoft Office application behavior or target rendering is correct',claim['nonClaims']);self.assertTrue(any(x['claimBoundary']=='explicit non-claim' for x in faults['classes']))
    def test_known_good_pptx_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'good.pptx';make_pptx(p);r=run(p);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'PASS')
    def test_known_good_docx_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'good.docx';make_docx(p);r=run(p);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(json.loads(r.stdout)['artifact']['documentType'],'wordprocessing')
    def test_known_good_xlsx_passes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'good.xlsx';make_xlsx(p);r=run(p);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(json.loads(r.stdout)['artifact']['documentType'],'spreadsheet')
    def test_unreadable_package_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.pptx';p.write_bytes(b'not an OOXML package');r=run(p);self.assertEqual(r.returncode,1);self.assertEqual(json.loads(r.stdout)['status'],'FAIL')
    def test_missing_office_document_relationship_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad-rel.pptx';make_pptx(p);rewrite_zip(p,lambda n,b: None if n=='_rels/.rels' else b);r=run(p);self.assertEqual(r.returncode,1,r.stdout+r.stderr)
    def test_schema_invalid_slide_markup_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad-schema.pptx';make_pptx(p)
            def mutate(n,b):
                if n=='ppt/slides/slide1.xml':return b.replace(b'</p:sld>',b'<p:bogus/></p:sld>')
                return b
            rewrite_zip(p,mutate);r=run(p);self.assertEqual(r.returncode,1,r.stdout+r.stderr);self.assertGreater(json.loads(r.stdout)['validationErrorCount'],0)
    def test_schema_valid_off_canvas_visual_defect_may_pass_but_is_explicit_nonclaim(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'off-canvas.pptx';make_pptx(p,off_canvas=True);r=run(p);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            result=json.loads(r.stdout);self.assertEqual(result['status'],'PASS');claim=json.loads((ROOT/'artifact-delivery/openxml-assurance-method-v1.json').read_text());self.assertIn('PowerPoint/Word layout is visually correct',claim['nonClaims'])
if __name__=='__main__':unittest.main()
