import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_dataset", ROOT / "scripts/artifact_dataset.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
BASE_CONTRACT = ROOT / "artifact-delivery/shadow-contracts/dataset-parquet-flat-smoke-r1.json"
PYARROW = Path("/opt/ordivon/external/pyarrow/25.0.1/python")

WRITER = r'''
import json,sys
import pyarrow as pa
import pyarrow.parquet as pq
rows=json.loads(sys.argv[2])
nullable_score=sys.argv[3]=='1'
schema=pa.schema([
 pa.field('id',pa.int64(),nullable=False),
 pa.field('name',pa.string(),nullable=False),
 pa.field('score',pa.float64(),nullable=nullable_score),
 pa.field('active',pa.bool_(),nullable=False),
])
t=pa.Table.from_pylist(rows,schema=schema)
pq.write_table(t,sys.argv[1],compression='zstd',version='2.6')
'''


def write_parquet(path: Path, rows: list[dict], nullable_score: bool = True) -> None:
    p=subprocess.run([str(PYARROW),'-c',WRITER,str(path),json.dumps(rows,separators=(',',':')), '1' if nullable_score else '0'],text=True,capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout+p.stderr)


class ArtifactDatasetTests(unittest.TestCase):
    def require_tools(self):
        for p in (PYARROW, MODULE.PYARROW_PYTHON, MODULE.DUCKDB):
            if not p.is_file(): self.skipTest(f"required mature external tool unavailable: {p}")

    def valid_rows(self):
        return [
            {"id":2,"name":"beta","score":None,"active":False},
            {"id":1,"name":"alpha","score":1.25,"active":True},
            {"id":3,"name":"gamma","score":-4.5,"active":True},
        ]

    def test_flat_parquet_contract_passes_two_reader_matrix(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'data.parquet'; evidence=root/'evidence'
            write_parquet(parquet,self.valid_rows())
            value=MODULE.verify_parquet(parquet,BASE_CONTRACT,evidence)
            self.assertEqual(value['status'],'PASS',value)
            self.assertTrue(value['readerAgreement']['exactCanonicalRowsMatch'])
            self.assertEqual(value['readerAgreement']['rowCount'],3)
            self.assertEqual(value['keyIntegrity']['status'],'PASS')
            self.assertEqual(value['parquetSchema']['status'],'PASS')

    def test_valid_parquet_does_not_launder_contract_schema_mismatch(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'data.parquet'; contract=root/'contract.json'
            write_parquet(parquet,self.valid_rows())
            c=json.loads(BASE_CONTRACT.read_text()); c['columns'][2]['nullable']=False
            contract.write_text(json.dumps(c))
            value=MODULE.verify_parquet(parquet,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('score' in x and ('nullability' in x or 'repetition' in x) for x in value['failures']),value)

    def test_duplicate_primary_key_fails_closed_after_valid_decode(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'duplicate.parquet'
            rows=self.valid_rows(); rows.append({"id":1,"name":"other","score":9.0,"active":False})
            write_parquet(parquet,rows)
            value=MODULE.verify_parquet(parquet,BASE_CONTRACT,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertIn('declared primary key is not unique',value['failures'])
            self.assertTrue(value['readerAgreement']['exactCanonicalRowsMatch'])

    def test_corrupt_parquet_fails_reader_evidence(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'corrupt.parquet'
            write_parquet(parquet,self.valid_rows())
            data=parquet.read_bytes(); parquet.write_bytes(data[:-8])
            value=MODULE.verify_parquet(parquet,BASE_CONTRACT,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertTrue(any('rejected' in x or 'decode' in x for x in value['failures']),value)

    def test_non_finite_float_is_outside_profile_and_fails_closed(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'nonfinite.parquet'
            rows=self.valid_rows(); rows[0]['score']=float('nan')
            write_parquet(parquet,rows)
            value=MODULE.verify_parquet(parquet,BASE_CONTRACT,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertIn('PyArrow rejected or could not decode the Parquet artifact',value['failures'])

    def test_contract_rejects_nullable_primary_key_before_readers(self):
        self.require_tools()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parquet=root/'data.parquet'; contract=root/'bad-contract.json'
            write_parquet(parquet,self.valid_rows())
            c=json.loads(BASE_CONTRACT.read_text()); c['columns'][0]['nullable']=True
            contract.write_text(json.dumps(c))
            value=MODULE.verify_parquet(parquet,contract,root/'evidence')
            self.assertEqual(value['status'],'FAIL')
            self.assertIn('primary-key column(s) must be non-nullable in the contract: id',value['failures'])
            self.assertNotIn('parquetSchema',value)


if __name__ == '__main__': unittest.main()
