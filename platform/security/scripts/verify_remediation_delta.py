#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.remediation import verify_remediation_delta

p = argparse.ArgumentParser()
p.add_argument("--package", required=True)
p.add_argument("--before-sbom", type=Path, required=True)
p.add_argument("--before-report", type=Path, required=True)
p.add_argument("--after-sbom", type=Path, required=True)
p.add_argument("--after-report", type=Path, required=True)
a = p.parse_args()
print(json.dumps(verify_remediation_delta(
    package=a.package,
    before_sbom_path=a.before_sbom,
    before_report_path=a.before_report,
    after_sbom_path=a.after_sbom,
    after_report_path=a.after_report,
), sort_keys=True))
