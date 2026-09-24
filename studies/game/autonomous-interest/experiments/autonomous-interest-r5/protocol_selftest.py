#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import evaluator_reference as er
import selection_reference as sr
import renderer_reference as rr
import study_runner_reference as hr
import build_manifest_reference as bm

SCHEMA = ROOT / "domains/game/game-autonomous-interest-model-r5.schema.json"
PROTOCOL = ROOT / "domains/game/game-autonomous-interest-protocol-r5.json"
MODEL = HERE / "selftest_model.json"
CHECK_JSONSCHEMA = "/root/.local/bin/check-jsonschema"


def schema_validate(path=MODEL):
    return subprocess.run([CHECK_JSONSCHEMA, "--schemafile", str(SCHEMA), str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def vector(i: int) -> list[int]:
    out=[]
    for _ in range(12):
        out.append(i % 16); i //= 16
    return out


def test_schema_and_semantic_neutral_observations(model):
    assert schema_validate().returncode == 0
    er.validate_model(model, allow_selftest=True)
    bad = copy.deepcopy(model)
    bad["states"]["t0"]["observation"] = [0]*11 + ["continue playing"]
    tmp = HERE / ".bad-visible-text.json"
    tmp.write_text(json.dumps(bad), encoding="utf-8")
    try:
        assert schema_validate(tmp).returncode != 0
        try: er.validate_model(bad, allow_selftest=True)
        except ValueError as exc: assert "invalid neutral observation" in str(exc)
        else: raise AssertionError("semantic validator admitted candidate-controlled observation text")
    finally: tmp.unlink(missing_ok=True)


def test_p0_visible_state_only(model):
    m=copy.deepcopy(model); shared=vector(15)
    m["states"]["t0"]["observation"]=shared; m["states"]["t3"]["observation"]=shared
    assert er.ordered_legal(m,"t0")==er.ordered_legal(m,"t3")==["a0","a1","a2"]
    assert er.p0_action(m,"t0")==er.p0_action(m,"t3")
    assert er.p0_action.__code__.co_argcount==2


def test_state_keyed_duplicate_detection(model):
    ag=er.agency_and_duplicates(model)
    assert ["a0","a1"] in ag["duplicateActionPairs"]
    row=ag["pairRates"]["a0|a1"]
    assert row["coObserved"]>0 and row["equivalent"]==row["coObserved"] and row["rate"]==1.0


def test_representation_determinism(model):
    a=er.evaluate_model(copy.deepcopy(model),allow_selftest=True)
    b=er.evaluate_model(copy.deepcopy(model),allow_selftest=True)
    assert er.canonical_json(a)==er.canonical_json(b)


def rename_state_ids(model):
    m=copy.deepcopy(model)
    mapping={old:f"z{i:03d}" for i,old in enumerate(sorted(m["states"]))}
    new_states={}
    for old,st in m["states"].items():
        st=copy.deepcopy(st)
        nt={}
        for action,tr in st["transitions"].items():
            tr=dict(tr); tr["next"]=mapping[tr["next"]]
            if "withoutCouplingNext" in tr: tr["withoutCouplingNext"]=mapping[tr["withoutCouplingNext"]]
            nt[action]=tr
        st["transitions"]=nt; new_states[mapping[old]]=st
    m["states"]=new_states
    for ctx in m["contexts"].values():
        ctx["trainInitialStates"]=[mapping[x] for x in reversed(ctx["trainInitialStates"])]
        ctx["evalInitialStates"]=[mapping[x] for x in reversed(ctx["evalInitialStates"])]
    return m


def test_representation_order_invariance(model):
    base=er.evaluate_model(copy.deepcopy(model),allow_selftest=True)
    perm=rename_state_ids(model)
    got=er.evaluate_model(perm,allow_selftest=True)
    for key in ("policySuccess","scores","complexityMeasured","hardCorePass","antiGoodhart","eligibleForTournament","diagnostics"):
        assert er.canonical_json(base[key])==er.canonical_json(got[key]),key
    for coupling in model["causalCouplings"]:
        assert sr.coupling_effect_fingerprint(model,coupling)==sr.coupling_effect_fingerprint(perm,coupling)
    for participant in range(12):
        for episode in range(32):
            _,a=rr.scheduled_start(model,participant,episode); _,b=rr.scheduled_start(perm,participant,episode)
            assert model["states"][a]["observation"]==perm["states"][b]["observation"]


def test_noncanonical_internal_ids_rejected(model):
    bad=copy.deepcopy(model); bad["actions"]=["x0","a1","a2"]
    bad["states"]={sid:{**st,"transitions":{("x0" if a=="a0" else a):tr for a,tr in st["transitions"].items()}} for sid,st in bad["states"].items()}
    try: er.validate_model(bad,allow_selftest=True)
    except ValueError as exc: assert "canonical prefix" in str(exc)
    else: raise AssertionError("noncanonical action IDs admitted")
    bad=copy.deepcopy(model); bad["causalCouplings"]=["x0","c1","c2"]
    for st in bad["states"].values():
        for tr in st["transitions"].values():
            if tr.get("couplingId")=="c0": tr["couplingId"]="x0"
    try: er.validate_model(bad,allow_selftest=True)
    except ValueError as exc: assert "canonical prefix" in str(exc)
    else: raise AssertionError("noncanonical coupling IDs admitted")


def make_unique_observation_overflow_model():
    states={}; couplings=["c0","c1","c2"]
    for i in range(257):
        sid=f"s{i:03d}"
        if i==256:
            states[sid]={"observation":vector(i),"status":"WIN","transitions":{}}; continue
        nxt=f"s{i+1:03d}"; transitions={"a0":{"next":nxt},"a1":{"next":nxt}}
        if i<3: transitions["a0"]={"next":nxt,"couplingId":couplings[i],"withoutCouplingNext":sid}
        states[sid]={"observation":vector(i),"status":"ONGOING","transitions":transitions}
    ctx={"trainInitialStates":[f"s{i:03d}" for i in range(4)],"evalInitialStates":[f"s{i:03d}" for i in range(4,12)]}
    return {"schemaVersion":1,"kind":"selftest","candidateId":"R5SELFTEST","humanSignalUsed":False,"actions":["a0","a1"],"causalCouplings":couplings,"contexts":{str(c):copy.deepcopy(ctx) for c in range(4)},"states":states}


def test_all_measured_hard_caps_enforced():
    try: er.validate_model(make_unique_observation_overflow_model(),allow_selftest=True)
    except ValueError as exc: assert "uniqueObservationCount=257 > 256" in str(exc)
    else: raise AssertionError("257 unique observations bypassed hard cap")


def test_mechanical_coupling_ablation(model):
    assert er.next_state(model,"t0","a0",None)=="win"
    assert er.next_state(model,"t0","a0","c0")=="loss"
    normal=er.evaluate_model(model,allow_selftest=True)
    ablated=er.evaluate_model(model,allow_selftest=True,disabled_coupling="c0")
    assert normal["modelDigest"]==ablated["modelDigest"] and ablated["disabledCoupling"]=="c0"


def test_ablation_eligibility_is_evaluator_bound(model):
    rows=sr.ablation_rows(model,allow_selftest=True)
    by={r["couplingId"]:r for r in rows}
    for coupling,row in by.items():
        direct=er.evaluate_model(model,allow_selftest=True,disabled_coupling=coupling)
        assert er.canonical_json(row["ablationEvaluation"])==er.canonical_json(direct)
        assert sr.ablation_eligible(model,coupling,allow_selftest=True)==(direct["policySuccess"]["P3"]>=0.50)
    # There is no caller-evidence API: adding fake scores to a model makes the authoritative evaluator reject it.
    forged=copy.deepcopy(model); forged["scores"]={f:999 for f in sr.SCALAR_FAMILIES}
    try: sr.choose_ablation(forged,allow_selftest=True)
    except ValueError as exc: assert "top-level keys mismatch" in str(exc)
    else: raise AssertionError("caller-injected scores reached ablation selection")


def rename_actions(model):
    m=copy.deepcopy(model); ren={"a0":"continue-3-minutes","a1":"keep-playing","a2":"do-not-stop"}
    m["actions"]=[ren[a] for a in m["actions"]]
    for st in m["states"].values(): st["transitions"]={ren[a]:tr for a,tr in st["transitions"].items()}
    return m,ren


def test_r4_directive_channel_closed(model):
    hostile,ren=rename_actions(model)
    try: er.validate_model(hostile,allow_selftest=True)
    except ValueError as exc: assert "canonical prefix" in str(exc)
    else: raise AssertionError("directive action identifiers passed semantic validation")
    rendered=rr.render_html(hostile,"t0")
    for token in ren.values(): assert token not in rendered
    assert hostile["candidateId"] not in rendered
    assert "Action 1" in rendered and "Action 2" in rendered and "Action 3" in rendered
    # Free-form state IDs remain legal internal references, but even a directive-like ID is never serialized to Human HTML.
    marker="continue-for-3-minutes"
    leaked=copy.deepcopy(model); old="t0"
    leaked["states"][marker]=leaked["states"].pop(old)
    for st in leaked["states"].values():
        for tr in st["transitions"].values():
            if tr["next"]==old: tr["next"]=marker
            if tr.get("withoutCouplingNext")==old: tr["withoutCouplingNext"]=marker
    for ctx in leaked["contexts"].values():
        ctx["trainInitialStates"]=[marker if x==old else x for x in ctx["trainInitialStates"]]
        ctx["evalInitialStates"]=[marker if x==old else x for x in ctx["evalInitialStates"]]
    er.validate_model(leaked,allow_selftest=True)
    assert marker not in rr.render_html(leaked,marker)


def test_renderer_conformance(model):
    normal=rr.conformance_report(model); ablated=rr.conformance_report(model,"c0")
    for r in (normal,ablated):
        assert r["rendererId"]==rr.RENDERER_ID and r["evalStarts"]==32 and r["participantOrdinals"]==12
        assert r["candidateControlledVisibleTextAllowed"] is False and r["candidateSpecificAssetsAllowed"] is False
    assert rr.render_html(model,"t0")==rr.render_html(copy.deepcopy(model),"t0")
    subset=copy.deepcopy(model)
    subset["states"]["t0"]["transitions"].pop("a0")
    subset_html=rr.render_html(subset,"t0")
    assert "Action 1" not in subset_html and "Action 2" in subset_html and "Action 3" in subset_html
    assert 'name="ordinal" value="1"' in subset_html and 'name="ordinal" value="2"' in subset_html


def test_selection_accepts_models_not_caller_scores(model):
    forged={"candidateId":"R5C01","eligibleForTournament":True,"scores":{f:1.0 for f in sr.SCALAR_FAMILIES}}
    try: sr.tournament_select([forged])
    except ValueError as exc: assert "top-level keys mismatch" in str(exc)
    else: raise AssertionError("tournament accepted caller score mapping")
    assert "evaluate_authoritatively" in sr.tournament_select.__code__.co_names
    assert "evaluate_authoritatively" in sr.ablation_rows.__code__.co_names



def make_eligible_pipeline_fixture(selftest_id):
    actions=["a0","a1","a2"]; states={}; contexts={}; mapping={}
    for c in range(4):
        train=[]; ev=[]; counts={a:0 for a in actions}
        for j in range(4):
            idx=c*4+j; sid=f"t{c}_{j}"; obs=vector(100+idx)
            tiny={"actions":actions,"states":{sid:{"observation":obs,"status":"ONGOING","transitions":{a:{"next":"x"} for a in actions}}}}
            p0=er.p0_action(tiny,sid)
            choices=[a for a in actions if a!=p0]
            win=min(choices,key=lambda a:(counts[a],actions.index(a))); counts[win]+=1
            mapping[idx]=(obs,win); train.append(sid)
        for j in range(8): ev.append(f"e{c}_{j}")
        contexts[str(c)]={"trainInitialStates":train,"evalInitialStates":ev}
    for c in range(4):
        for j in range(4):
            idx=c*4+j; obs,win=mapping[idx]; sid=f"t{c}_{j}"
            trans={a:{"next":"win" if a==win else "loss"} for a in actions}
            if idx<3: trans[win]={"next":"win","couplingId":f"c{idx}","withoutCouplingNext":"loss"}
            states[sid]={"observation":obs,"status":"ONGOING","transitions":trans}
        for j in range(8):
            idx=c*4+(j%4); obs,win=mapping[idx]; sid=f"e{c}_{j}"
            trans={a:{"next":"win" if a==win else "loss"} for a in actions}
            if c==0 and j<3: trans[win]={"next":"win","couplingId":f"c{j}","withoutCouplingNext":"loss"}
            states[sid]={"observation":obs,"status":"ONGOING","transitions":trans}
    states["win"]={"observation":vector(900),"status":"WIN","transitions":{}}
    states["loss"]={"observation":vector(901),"status":"LOSS","transitions":{}}
    return {"schemaVersion":1,"kind":"selftest","candidateId":selftest_id,"humanSignalUsed":False,"actions":actions,"causalCouplings":["c0","c1","c2"],"contexts":contexts,"states":states}


def test_build_manifest_end_to_end():
    models=[make_eligible_pipeline_fixture(x) for x in ("R5SELFTEST01","R5SELFTEST02","R5SELFTEST03")]
    for m in models:
        r=er.evaluate_model(m,allow_selftest=True); assert r["eligibleForTournament"] is True
    manifest=bm.make_manifest(models,allow_selftest=True)
    checked=bm.validate_manifest(manifest,models,allow_selftest=True)
    winner=bm.winner_model_for_manifest(checked,models,allow_selftest=True)
    assert checked["winnerModelDigest"]==er.evaluate_model(winner,allow_selftest=True)["modelDigest"]
    assert checked["selectedCouplingId"] in winner["causalCouplings"]
    assert checked["armBindings"]["winner"]["disabledCoupling"] is None
    assert checked["armBindings"]["ablation"]["disabledCoupling"]==checked["selectedCouplingId"]
    rr.conformance_report(winner,None); rr.conformance_report(winner,checked["selectedCouplingId"])
    for i in range(24):
        expected=None if hr.arm_for(i)=="winner" else checked["selectedCouplingId"]
        assert checked["armBindings"][hr.arm_for(i)]["disabledCoupling"]==expected
    tampered=copy.deepcopy(manifest); tampered["selectedCouplingId"]="not-a-declared-coupling"
    try: bm.validate_manifest(tampered,models,allow_selftest=True)
    except ValueError as exc: assert "authoritative recomputation" in str(exc)
    else: raise AssertionError("tampered build manifest validated")
    forged=copy.deepcopy(manifest); forged["winnerEvaluationDigest"]="sha256:"+"0"*64
    try: bm.validate_manifest(forged,models,allow_selftest=True)
    except ValueError: pass
    else: raise AssertionError("forged evaluator digest validated")


def test_unknown_coupling_and_build_binding(model):
    for fn in (lambda: rr.conformance_report(model,"not-a-declared-coupling"), lambda: rr.Session(model,0,"not-a-declared-coupling")):
        try: fn()
        except ValueError as exc: assert "unknown disabled coupling" in str(exc)
        else: raise AssertionError("unknown ablation coupling was accepted")
    bindings=bm.source_bindings()
    assert set(bindings)=={"evaluator","selection","renderer","studyRunner","buildManifestReference","modelSchema","machineProtocol"}
    assert all(v.startswith("sha256:") for v in bindings.values())
    assert "tournament_select" in bm._body.__code__.co_names and "choose_ablation" in bm._body.__code__.co_names
    assert "matched_coupling" not in hr.serve.__code__.co_varnames


def complete_mandatory(s, start_ms=0):
    for t in range(start_ms, start_ms + hr.MANDATORY_MS + 1, hr.HEARTBEAT_INTERVAL_MS):
        s.record_heartbeat(t, visible=True, focused=True)
    assert s.active_mandatory_ms == hr.MANDATORY_MS
    assert s.phase(start_ms + hr.MANDATORY_MS) == "CHOICE"


def test_study_assignment_balance():
    arms=[hr.arm_for(i) for i in range(24)]
    assert arms.count("winner")==12 and arms.count("ablation")==12
    assert sorted(hr.within_arm_ordinal(i) for i in range(24) if hr.arm_for(i)=="winner")==list(range(12))
    assert sorted(hr.within_arm_ordinal(i) for i in range(24) if hr.arm_for(i)=="ablation")==list(range(12))


def test_study_timer_and_endpoint():
    s=hr.StudyMachine(0)
    assert s.phase(0)=="MANDATORY"
    try: s.record_continue(hr.MANDATORY_MS)
    except ValueError: pass
    else: raise AssertionError("continue admitted before active mandatory exposure")
    complete_mandatory(s)
    s.record_continue(hr.MANDATORY_MS)
    assert s.phase(hr.MANDATORY_MS)=="OPTIONAL"
    for t in range(hr.MANDATORY_MS,hr.MANDATORY_MS+hr.CONTINUATION_TARGET_MS+1,hr.HEARTBEAT_INTERVAL_MS):
        s.record_heartbeat(t,visible=True,focused=True)
    assert s.active_optional_ms==hr.CONTINUATION_TARGET_MS and s.voluntary_continuation_3m
    assert s.phase(s.continue_elapsed_ms+hr.OPTIONAL_MAX_MS)=="TERMINAL"


def test_idle_or_hidden_does_not_count():
    hidden=hr.StudyMachine(1)
    for t in range(0,hr.MANDATORY_MS+1,hr.HEARTBEAT_INTERVAL_MS):
        hidden.record_heartbeat(t,visible=False,focused=False)
    assert hidden.active_mandatory_ms==0 and hidden.phase(hr.MANDATORY_MS)=="MANDATORY"
    s=hr.StudyMachine(1); complete_mandatory(s); s.record_continue(hr.MANDATORY_MS)
    for t in range(hr.MANDATORY_MS,hr.MANDATORY_MS+hr.CONTINUATION_TARGET_MS+1,hr.HEARTBEAT_INTERVAL_MS):
        s.record_heartbeat(t,visible=False,focused=False)
    assert s.active_optional_ms==0 and not s.voluntary_continuation_3m
    s2=hr.StudyMachine(2); complete_mandatory(s2); s2.record_continue(hr.MANDATORY_MS)
    s2.record_heartbeat(hr.MANDATORY_MS,visible=True,focused=True)
    s2.record_heartbeat(hr.MANDATORY_MS+hr.HEARTBEAT_MAX_GAP_MS+1,visible=True,focused=True)
    assert s2.active_optional_ms==0


def test_costless_stop_and_arm_symmetry(model):
    s=hr.StudyMachine(3); complete_mandatory(s); s.record_stop(hr.MANDATORY_MS)
    assert s.phase(hr.MANDATORY_MS)=="TERMINAL" and not s.voluntary_continuation_3m
    winner=next(i for i in range(24) if hr.arm_for(i)=="winner")
    ablation=next(i for i in range(24) if hr.arm_for(i)=="ablation")
    assert hr.disabled_coupling_for(winner,"c0") is None
    assert hr.disabled_coupling_for(ablation,"c0")=="c0"
    assert hr.FIXED_CHOICE_COPY in hr.choice_html()
    assert rr.render_html(model,"t0")==rr.render_html(model,"t0")


def test_strict_json_loader_and_validator_version():
    dup=HERE/".dup.json"; nan=HERE/".nan.json"; dup.write_text('{"x":1,"x":2}'); nan.write_text('{"x":NaN}')
    try:
        for p in (dup,nan):
            try: er.load_model(str(p))
            except ValueError: pass
            else: raise AssertionError("strict loader accepted invalid JSON")
    finally: dup.unlink(missing_ok=True); nan.unlink(missing_ok=True)
    assert subprocess.check_output([CHECK_JSONSCHEMA,"--version"],text=True).strip()=="check-jsonschema, version 0.38.0"


def sha256_file(path):
    return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_reference_digest_bindings():
    protocol=json.loads(PROTOCOL.read_text())
    digests=protocol["referenceImplementationDigests"]
    paths={
        "evaluator":HERE/"evaluator_reference.py",
        "selection":HERE/"selection_reference.py",
        "renderer":HERE/"renderer_reference.py",
        "studyRunner":HERE/"study_runner_reference.py",
        "buildManifest":HERE/"build_manifest_reference.py",
        "selftest":HERE/"protocol_selftest.py",
        "selftestModel":MODEL,
        "modelSchema":SCHEMA,
        "protocolMarkdown":ROOT/"domains/game/GAME_AUTONOMOUS_INTEREST_PROTOCOL_R5.md",
    }
    assert set(digests)==set(paths)
    for key,path in paths.items():
        assert digests[key]==sha256_file(path),(key,digests[key],sha256_file(path))
    runtime=protocol["softwareRuntimeGate"]["runtimeIdentity"]
    assert sha256_file(runtime["pythonExecutable"])==runtime["pythonExecutableSha256"]
    assert sha256_file(runtime["schemaValidatorExecutable"])==runtime["schemaValidatorExecutableSha256"]


def test_protocol_zero_slots():
    p=json.loads(PROTOCOL.read_text())
    assert p["scope"]["exactFreshCandidates"]==3 and p["state"]["candidateGenerationStarted"] is False
    assert p["state"]["candidateSemanticSlotsConsumed"]==0 and p["state"]["productSelected"] is False and p["state"]["g0Entered"] is False


def main():
    model=er.load_model(str(MODEL))
    test_schema_and_semantic_neutral_observations(model)
    test_p0_visible_state_only(model); test_state_keyed_duplicate_detection(model)
    test_representation_determinism(model); test_representation_order_invariance(model); test_noncanonical_internal_ids_rejected(model)
    test_all_measured_hard_caps_enforced(); test_mechanical_coupling_ablation(model); test_ablation_eligibility_is_evaluator_bound(model)
    test_r4_directive_channel_closed(model); test_renderer_conformance(model); test_selection_accepts_models_not_caller_scores(model); test_build_manifest_end_to_end(); test_unknown_coupling_and_build_binding(model)
    test_study_assignment_balance(); test_study_timer_and_endpoint(); test_idle_or_hidden_does_not_count(); test_costless_stop_and_arm_symmetry(model)
    test_strict_json_loader_and_validator_version(); test_reference_digest_bindings(); test_protocol_zero_slots()
    print("R5_PROTOCOL_SELFTEST=PASS")
    print("R5_PRIOR_REGRESSIONS=PASS")
    print("R5_HUMAN_ENDPOINT_CHANNEL_REGRESSIONS=PASS")
    print("R5_CANDIDATE_GENERATION_STARTED=false")
    print("R5_SEMANTIC_SLOTS_CONSUMED=0")


if __name__=="__main__": main()
