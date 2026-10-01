#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
STUDY=ROOT/"studies/security/dwc-r21-dw11-operator-ux-qualification"
sys.path.insert(0,str(STUDY))
from dwc_dw11_eval.trial import CANDIDATE_REVISION, build_packet, materialize_trial

def main():
    subject,gt=materialize_trial(ROOT,STUDY,CANDIDATE_REVISION)
    packet=build_packet(subject,"agent:chatgpt-daybreak-r21-20261001")
    out=STUDY/"evidence/acceptance"
    out.mkdir(parents=True,exist_ok=True)
    for name,value in [
        ("dw11-agent-reentry-subject-r2.json",subject),
        ("dw11-agent-reentry-ground-truth-r2.json",gt),
        ("dw11-independent-agent-reentry-packet-r2.json",packet),
    ]:
        (out/name).write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "candidateRevision":CANDIDATE_REVISION,
        "subjectDigest":subject["subjectDigest"],
        "groundTruthDigest":gt["groundTruthDigest"],
        "packetDigest":packet["packetDigest"],
        "caseCount":len(subject["trialCases"]),
    },indent=2,sort_keys=True))
if __name__=="__main__":
    main()
