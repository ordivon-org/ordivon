import pytest
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

pytestmark = pytest.mark.integration

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('artifact_geospatial',ROOT/'scripts/artifact_geospatial.py')
MODULE=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(MODULE)
BASE=ROOT/'artifact-delivery/shadow-contracts/geospatial-geopackage-point-smoke-r1.json'
OGR2OGR=Path('/usr/bin/ogr2ogr')
SQLITE=Path('/opt/ordivon/external/sqlite/3.53.4-1/sqlite3')


def build_gpkg(root: Path, rows=None) -> Path:
    rows=rows or [
      {'code':1,'name':'alpha','score':1.25,'xy':[117.2272,31.8206]},
      {'code':2,'name':'beta','score':None,'xy':[118.4331,31.3525]},
      {'code':3,'name':'gamma','score':-4.5,'xy':[116.9841,31.7535]},
    ]
    gj={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'code':r['code'],'name':r['name'],'score':r['score']},'geometry':{'type':'Point','coordinates':r['xy']}} for r in rows]}
    src=root/'places.geojson'; dst=root/'places.gpkg'; src.write_text(json.dumps(gj))
    p=subprocess.run([str(OGR2OGR),'-f','GPKG',str(dst),str(src),'-nln','places','-a_srs','EPSG:4326','-dsco','VERSION=1.4','-lco','GEOMETRY_NAME=geom'],text=True,capture_output=True)
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    return dst


class ArtifactGeospatialTests(unittest.TestCase):
    def require_tools(self):
        for p in (MODULE.GDAL,MODULE.SQLITE,MODULE.OGRINFO,MODULE.OGR2OGR):
            if not p.is_file(): self.skipTest(f'required mature external tool unavailable: {p}')

    def test_local_binding_tool_digests_match_proven_substrate(self):
        import hashlib
        binding=json.loads((ROOT/'artifact-delivery/shadow-bindings/geospatial-geopackage-point-local-r1.json').read_text())
        checks=[
          ('/usr/bin/gdal',binding['bindings']['ogcConformance']['hostGdalBinarySha256']),
          ('/usr/bin/ogrinfo',binding['bindings']['geospatialInterpretation']['ogrinfoSha256']),
          ('/usr/bin/ogr2ogr',binding['bindings']['geospatialInterpretation']['ogr2ogrSha256']),
          ('/opt/ordivon/external/sqlite/3.53.4-1/rootfs/usr/bin/sqlite3',binding['bindings']['sqliteContainer']['binarySha256']),
        ]
        for path,want in checks:
            p=Path(path)
            if not p.is_file(): self.skipTest(f'proven substrate path unavailable: {path}')
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),want,path)

    def test_geopackage_point_contract_passes(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); gpkg=build_gpkg(root)
            value=MODULE.verify_geopackage(gpkg,BASE,root/'evidence')
            self.assertEqual(value['status'],'PASS',value)
            self.assertEqual(value['ogcConformance']['status'],'PASS')
            self.assertTrue(value['attributeCrossView']['exactMatch'])
            self.assertEqual(value['featureBounds']['featureCount'],3)

    def test_sqlite_validity_does_not_launder_bad_geopackage_application_id(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); gpkg=build_gpkg(root)
            p=subprocess.run([str(SQLITE),str(gpkg),'PRAGMA application_id=0;'],text=True,capture_output=True); self.assertEqual(p.returncode,0,p.stderr)
            p=subprocess.run([str(SQLITE),str(gpkg),'PRAGMA integrity_check;'],text=True,capture_output=True); self.assertEqual(p.stdout.strip(),'ok')
            value=MODULE.verify_geopackage(gpkg,BASE,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['sqliteContainer']['status'],'FAIL')
            self.assertEqual(value['ogcConformance']['status'],'FAIL')

    def test_valid_geopackage_does_not_launder_wrong_crs_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); gpkg=build_gpkg(root); contract=root/'contract.json'
            c=json.loads(BASE.read_text()); c['layer']['geometry']['srs']['code']=3857; contract.write_text(json.dumps(c))
            value=MODULE.verify_geopackage(gpkg,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['ogcConformance']['status'],'PASS')
            self.assertTrue(any('CRS' in x or 'srs' in x for x in value['failures']),value)

    def test_valid_geopackage_does_not_launder_wrong_geometry_contract(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); gpkg=build_gpkg(root); contract=root/'contract.json'
            # schema itself restricts R1 to POINT; verify rejection occurs before evidence promotion.
            c=json.loads(BASE.read_text()); c['layer']['geometry']['type']='LINESTRING'; contract.write_text(json.dumps(c))
            value=MODULE.verify_geopackage(gpkg,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('geospatial contract schema invalid' in x for x in value['failures']))
            self.assertNotIn('ogcConformance',value)

    def test_duplicate_logical_primary_key_fails_after_conformance(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); rows=[
              {'code':1,'name':'alpha','score':1.0,'xy':[117.0,31.0]},
              {'code':1,'name':'other','score':2.0,'xy':[118.0,32.0]},
            ]; gpkg=build_gpkg(root,rows)
            value=MODULE.verify_geopackage(gpkg,BASE,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertEqual(value['ogcConformance']['status'],'PASS')
            self.assertIn('declared logical primary key is not unique',value['failures'])

    def test_contract_primary_key_must_reference_attribute(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); gpkg=build_gpkg(root); contract=root/'contract.json'
            c=json.loads(BASE.read_text()); c['primaryKey']=['missing']; contract.write_text(json.dumps(c))
            value=MODULE.verify_geopackage(gpkg,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertIn('primaryKey references undeclared attribute field(s): missing',value['failures'])
            self.assertNotIn('ogcConformance',value)

if __name__=='__main__': unittest.main()
