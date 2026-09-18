#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "knowledge/registries/lego-lens-registry-r1.json"

def fail(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    raise SystemExit(1)

data = json.loads(PATH.read_text())
if data.get("schemaVersion") != 1:
    fail("schemaVersion must be 1")
if data.get("kind") != "ordivon.lego-lens-registry":
    fail("unexpected kind")

lenses = data.get("lenses")
if not isinstance(lenses, list) or not lenses:
    fail("lenses must be a non-empty list")

required = {
    "id", "kind", "standing", "sourceSubstrate", "decisionQuestion",
    "activationSignals", "prerequisites", "contraindications",
    "overlapGroup", "consumes", "defaultCost", "validatedEvidence"
}
ids = set()
for lens in lenses:
    missing = sorted(required - set(lens))
    if missing:
        fail(f"{lens.get('id','<unknown>')} missing {missing}")
    lid = lens["id"]
    if lid in ids:
        fail(f"duplicate lens id: {lid}")
    ids.add(lid)
    if lens["kind"] not in {"discipline_lens", "composite_profile"}:
        fail(f"{lid}: invalid kind")
    if lens["defaultCost"] not in {"LOW", "MEDIUM", "HIGH"}:
        fail(f"{lid}: invalid defaultCost")
    for field in ("activationSignals", "prerequisites", "contraindications", "overlapGroup", "consumes", "validatedEvidence"):
        if not isinstance(lens[field], list):
            fail(f"{lid}: {field} must be list")
    if lens["kind"] == "discipline_lens" and not lens.get("skillRef"):
        fail(f"{lid}: discipline_lens requires skillRef")
    if lens["kind"] == "composite_profile" and not lens.get("profileRef"):
        fail(f"{lid}: composite_profile requires profileRef")

for lens in lenses:
    unknown = sorted(set(lens["consumes"]) - ids)
    if unknown:
        fail(f"{lens['id']}: consumes unknown lenses {unknown}")


reserve = data.get("reservePool", [])
if not isinstance(reserve, list):
    fail("reservePool must be a list")
reserve_ids = set()
reserve_required = {
    "id", "status", "family", "sourceSubstrate", "uniqueQuestion",
    "discoverySignals", "requiredAssumptions", "nearestActiveLenses",
    "promotionTrigger", "currentBlocker"
}
for item in reserve:
    missing = sorted(reserve_required - set(item))
    if missing:
        fail(f"reserve {item.get('id','<unknown>')} missing {missing}")
    rid = item["id"]
    if rid in ids:
        fail(f"reserve id collides with active lens: {rid}")
    if rid in reserve_ids:
        fail(f"duplicate reserve id: {rid}")
    reserve_ids.add(rid)
    if item["status"] not in {"RESERVE_ONLY", "RESERVE_SHADOW_TESTED"}:
        fail(f"{rid}: invalid reserve status")
    if "skillRef" in item:
        fail(f"{rid}: reserve entries must not carry skillRef")
    for field in ("discoverySignals", "requiredAssumptions", "nearestActiveLenses"):
        if not isinstance(item[field], list):
            fail(f"{rid}: {field} must be list")

all_known = ids | reserve_ids
for item in reserve:
    unknown = sorted(set(item["nearestActiveLenses"]) - all_known)
    if unknown:
        fail(f"{item['id']}: nearestActiveLenses unknown {unknown}")

reserve_policy = data.get("reservePoolPolicy", {})
if reserve_policy.get("routerMaySelectReserve") is not False:
    fail("reservePoolPolicy.routerMaySelectReserve must be false")
if reserve_policy.get("reserveMayHaveSkillRef") is not False:
    fail("reservePoolPolicy.reserveMayHaveSkillRef must be false")

policy = data.get("selectionPolicy", {})
if policy.get("allowNoLens") is not True:
    fail("selectionPolicy.allowNoLens must be true")
if policy.get("keywordActivationForbidden") is not True:
    fail("selectionPolicy.keywordActivationForbidden must be true")

print(json.dumps({
    "ok": True,
    "path": str(PATH.relative_to(ROOT)),
    "lenses": len(lenses),
    "disciplineLenses": sum(x["kind"] == "discipline_lens" for x in lenses),
    "compositeProfiles": sum(x["kind"] == "composite_profile" for x in lenses),
    "defaultMaxSelected": policy.get("defaultMaxSelected"),
    "reservePool": len(reserve)
}, ensure_ascii=False))
