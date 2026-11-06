#!/usr/bin/env python3
"""Source-cut and reference integrity for a bounded external LEGO candidate.

Catalog evidence is never an install, permission, registry or promotion authority.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path

STATES = ("INCOMPLETE_CANDIDATE", "DECLARED", "ADMITTED")
DECISIONS = ("HOLD", "REFERENCE_ONLY", "KEEP_NATIVE", "ADOPT_SCOPED", "REJECT")
COORDS = {"I","O","S","pre","post","inv","eff","c","epsilon","prov","unfold"}
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def check(root: Path, packet: Path) -> list[str]:
    errors: list[str] = []
    try:
        item = json.loads(packet.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ["invalid packet: " + str(exc)]
    if item.get("kind") != "ordivon.external-lego-evidence" or item.get("schemaVersion") != "r1":
        errors.append("invalid kind/version")
    if item.get("standing") not in STATES or item.get("decision") not in DECISIONS:
        errors.append("invalid candidate standing or disposition")
    if item.get("standing") == "INCOMPLETE_CANDIDATE" and item.get("productionActivated") is not False:
        errors.append("candidate cannot claim production activation")
    if item.get("decision") == "ADOPT_SCOPED" and not item.get("ownerApprovalEvidence"):
        errors.append("adoption requires independent owner approval evidence")
    cap = item.get("capability", {})
    if not cap.get("name") or cap.get("kind") not in ("capability", "method", "mixed"):
        errors.append("invalid capability classification")
    if item.get("standing") in ("DECLARED","ADMITTED") and set(cap.get("r21", {})) != COORDS:
        errors.append("formal LEGO declaration missing 11 typed coordinates")
    source = item.get("source", {})
    cut = source.get("ordivonSourceCut", "")
    if not SHA.fullmatch(cut):
        errors.append("invalid SourceCut")
    elif subprocess.run(["git","-C",str(root),"cat-file","-t",cut],capture_output=True,text=True).stdout.strip() != "commit":
        errors.append("SourceCut is not a commit")
    up = source.get("upstream", {})
    if not SHA.fullmatch(up.get("observedHeadCommit", "")):
        errors.append("missing exact upstream commit")
    if not DIGEST.fullmatch(up.get("releaseArchiveSha256","")):
        errors.append("missing exact release digest")
    for field in ("repository","licenseExpression","licenseEvidence","releaseTag","observationTime"):
        if not up.get(field):
            errors.append("missing upstream field " + field)
    refs = item.get("references",{})
    required = ("provider","knowledge","skills","research","composition","experiment")
    for key in required:
        if key not in refs:
            errors.append("missing ref " + key)
    consumers = refs.get("consumerSources",[])
    if not isinstance(consumers,list) or not consumers:
        errors.append("missing consumer source references")
        consumers=[]
    paths = [v for k,v in refs.items() if k != "consumerSources"] + consumers
    for path in paths:
        if not isinstance(path,str) or not path or path.startswith("/"):
            errors.append("invalid ref path")
            continue
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            errors.append("missing or escaping ref: " + path)
    if SHA.fullmatch(cut):
        for path in consumers:
            p = subprocess.run(["git","-C",str(root),"cat-file","-e",cut+":"+path],capture_output=True)
            if p.returncode:
                errors.append("not in bound original SourceCut: " + path)
    if "experiment" in refs and (root/refs["experiment"]).is_file():
        try:
            test=json.loads((root/refs["experiment"]).read_text())
            if test.get("candidate") != up.get("repository","").removeprefix("https://github.com/"):
                errors.append("mismatched experiment upstream")
            if test.get("productionSwitched") is not False or not test.get("negativeControls"):
                errors.append("experiment lacks explicit no-switch boundary or negative tests")
        except (ValueError,OSError) as exc:
            errors.append("invalid experiment: "+str(exc))
    return errors


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("packet",type=Path)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[3])
    a=p.parse_args()
    errs=check(a.root.resolve(),a.packet.resolve())
    print(json.dumps({"standing":"PASS" if not errs else "FAIL","issues":errs},indent=2))
    return 1 if errs else 0


if __name__=="__main__":
    raise SystemExit(main())
