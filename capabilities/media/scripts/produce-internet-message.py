#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path


def main() -> int:
    p=argparse.ArgumentParser(description="Compose one bounded RFC5322/MIME UTF-8 text/plain message.")
    p.add_argument('--output',required=True,type=Path); p.add_argument('--from-address',required=True); p.add_argument('--from-name',default='')
    p.add_argument('--to-address',required=True); p.add_argument('--to-name',default=''); p.add_argument('--subject',required=True)
    p.add_argument('--message-id',required=True); p.add_argument('--date',required=True); p.add_argument('--body-file',required=True,type=Path)
    a=p.parse_args(); dt=datetime.fromisoformat(a.date.replace('Z','+00:00')); body=a.body_file.read_text(encoding='utf-8')
    msg=EmailMessage(policy=policy.SMTPUTF8.clone(linesep='\r\n',max_line_length=998))
    msg['Date']=format_datetime(dt); msg['From']=f'{a.from_name} <{a.from_address}>' if a.from_name else a.from_address
    msg['To']=f'{a.to_name} <{a.to_address}>' if a.to_name else a.to_address; msg['Subject']=a.subject; msg['Message-ID']=a.message_id
    msg.set_content(body,subtype='plain',charset='utf-8',cte='8bit')
    raw=msg.as_bytes(policy=msg.policy)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(raw)
    return 0
if __name__=='__main__': raise SystemExit(main())
