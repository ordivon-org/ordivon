#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

SITE = os.environ.get("ORDIVON_WARCIO_SITE", "/opt/ordivon/external/warcio-py/1.8.1/site-packages")
sys.path.insert(0, SITE)
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter


def main() -> int:
    p=argparse.ArgumentParser(description="Write one bounded WARC/1.1 HTTP response record.")
    p.add_argument('--output',required=True,type=Path); p.add_argument('--payload',required=True,type=Path)
    p.add_argument('--target-uri',required=True); p.add_argument('--warc-date',required=True); p.add_argument('--record-id',required=True)
    p.add_argument('--status',default='200 OK'); p.add_argument('--content-type',required=True)
    a=p.parse_args(); body=a.payload.read_bytes(); a.output.parent.mkdir(parents=True,exist_ok=True)
    headers=StatusAndHeaders(a.status,[('Content-Type',a.content_type),('Content-Length',str(len(body)))],protocol='HTTP/1.1')
    with a.output.open('wb') as f:
        writer=WARCWriter(f,gzip=False); writer.warc_version='WARC/1.1'; bio=BytesIO(body)
        record=writer.create_warc_record(a.target_uri,'response',payload=bio,http_headers=headers,warc_headers_dict={'WARC-Date':a.warc_date,'WARC-Record-ID':a.record_id})
        try: writer.write_record(record)
        finally:
            rs=getattr(record,'raw_stream',None)
            if rs is not None and hasattr(rs,'close'): rs.close()
            bio.close()
    return 0
if __name__=='__main__': raise SystemExit(main())
