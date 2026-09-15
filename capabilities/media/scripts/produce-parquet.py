#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
TYPE_MAP={'int64':pa.int64(),'string':pa.string(),'float64':pa.float64(),'boolean':pa.bool_()}
def main()->int:
 p=argparse.ArgumentParser(description='Write a flat primitive Parquet file with explicit schema/nullability.')
 p.add_argument('--output',required=True,type=Path); p.add_argument('--schema',required=True,type=Path); p.add_argument('--rows',required=True,type=Path)
 a=p.parse_args(); spec=json.loads(a.schema.read_text()); rows=json.loads(a.rows.read_text())
 fields=[]
 for col in spec['columns']:
  typ=TYPE_MAP.get(col['type'])
  if typ is None: raise ValueError('unsupported flat type: '+str(col['type']))
  fields.append(pa.field(col['name'],typ,nullable=bool(col['nullable'])))
 table=pa.Table.from_pylist(rows,schema=pa.schema(fields)); a.output.parent.mkdir(parents=True,exist_ok=True)
 pq.write_table(table,a.output,compression='zstd',version='2.6'); return 0
if __name__=='__main__': raise SystemExit(main())
