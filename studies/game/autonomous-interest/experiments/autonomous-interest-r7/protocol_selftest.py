#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))

import evaluator_reference as er
import selection_reference as sr
import renderer_reference as rr
import study_runner_reference as hr
import build_manifest_reference as bm

SCHEMA=ROOT/'domains/game/game-autonomous-interest-model-r7.schema.json'
PROTOCOL=ROOT/'domains/game/game-autonomous-interest-protocol-r7.json'
MODEL=HERE/'selftest_model.json'
CHECK_JSONSCHEMA='/root/.local/bin/check-jsonschema'


def schema_validate(path=MODEL):
    return subprocess.run([CHECK_JSONSCHEMA,'--schemafile',str(SCHEMA),str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)


def behavioral_projection(r):
    return {k:r[k] for k in ('policySuccess','scores','complexityMeasured','hardCorePass','antiGoodhart','eligibleForTournament','diagnostics')}


def make_eligible_fixture(cid='R7SELFTEST01'):
    actions=['a0','a1','a2']; couplings=['c0','c1','c2']; states={}; contexts={}; starts=[]
    k=0
    for c in range(4):
        train=[]; ev=[]
        for j in range(4):
            sid=f't{c}_{j}'; train.append(sid); starts.append((sid,c,j,k)); k+=1
        for j in range(8):
            sid=f'e{c}_{j}'; ev.append(sid); starts.append((sid,c,j,k)); k+=1
        contexts[str(c)]={'trainInitialStates':train,'evalInitialStates':ev}
    for sid,c,j,k in starts:
        win=actions[(j+c)%3]
        trans={a:{'next':'win' if a==win else 'loss'} for a in actions}
        if k<3:
            trans[win]={'next':'win','couplingId':f'c{k}','withoutCouplingNext':'loss'}
        states[sid]={'observationClass':(j+c)%3,'status':'ONGOING','transitions':trans}
    states['win']={'observationClass':250,'status':'WIN','transitions':{}}
    states['loss']={'observationClass':251,'status':'LOSS','transitions':{}}
    return {'schemaVersion':1,'kind':'selftest','candidateId':cid,'humanSignalUsed':False,'actions':actions,'causalCouplings':couplings,'contexts':contexts,'states':states}


def permute_observation_labels(model):
    m=copy.deepcopy(model)
    used={st['observationClass'] for st in m['states'].values()}
    mapping={x:(x*17+23)%256 for x in used}
    assert len(set(mapping.values()))==len(mapping)
    for st in m['states'].values(): st['observationClass']=mapping[st['observationClass']]
    return m


def rename_state_ids_and_reverse_contexts(model):
    m=copy.deepcopy(model); mapping={old:f'z{i:03d}' for i,old in enumerate(sorted(m['states']))}; ns={}
    for old,st in m['states'].items():
        st=copy.deepcopy(st); nt={}
        for a,tr in st['transitions'].items():
            tr=dict(tr); tr['next']=mapping[tr['next']]
            if 'withoutCouplingNext' in tr: tr['withoutCouplingNext']=mapping[tr['withoutCouplingNext']]
            nt[a]=tr
        st['transitions']=nt; ns[mapping[old]]=st
    m['states']=ns
    for ctx in m['contexts'].values():
        ctx['trainInitialStates']=[mapping[x] for x in reversed(ctx['trainInitialStates'])]
        ctx['evalInitialStates']=[mapping[x] for x in reversed(ctx['evalInitialStates'])]
    return m


def test_schema_and_semantic_class_only():
    model=er.load_model(str(MODEL)); assert schema_validate().returncode==0; er.validate_model(model,allow_selftest=True)
    for bad_value in ('CONTINUE',256,[0]*12):
        bad=copy.deepcopy(model); bad['states'][next(iter(bad['states']))]['observationClass']=bad_value
        tmp=HERE/'.bad-r7-model.json'; tmp.write_text(json.dumps(bad))
        try:
            assert schema_validate(tmp).returncode!=0
            try: er.validate_model(bad,allow_selftest=True)
            except (ValueError,TypeError): pass
            else: raise AssertionError('invalid observationClass admitted')
        finally: tmp.unlink(missing_ok=True)
    bad=copy.deepcopy(model); sid=next(iter(bad['states'])); bad['states'][sid]['observation']=[0]*12
    tmp=HERE/'.bad-r7-extra-observation.json'; tmp.write_text(json.dumps(bad))
    try:
        assert schema_validate(tmp).returncode!=0
        try: er.validate_model(bad,allow_selftest=True)
        except ValueError as exc: assert 'state keys invalid' in str(exc)
        else: raise AssertionError('R6 pixel observation channel survived semantic validation')
    finally: tmp.unlink(missing_ok=True)


def test_observation_label_invariance():
    m=make_eligible_fixture(); p=permute_observation_labels(m)
    a=er.evaluate_model(m,allow_selftest=True); b=er.evaluate_model(p,allow_selftest=True)
    assert er.canonical_json(behavioral_projection(a))==er.canonical_json(behavioral_projection(b))
    assert er.semantic_model_fingerprint(m)==er.semantic_model_fingerprint(p)
    assert er.canonical_observation_classes(m)==er.canonical_observation_classes(p)


def test_state_id_context_order_invariance():
    m=make_eligible_fixture(); p=rename_state_ids_and_reverse_contexts(m)
    assert er.semantic_model_fingerprint(m)==er.semantic_model_fingerprint(p)
    for disabled in [None,*m['causalCouplings']]:
        a=er.evaluate_model(m,allow_selftest=True,disabled_coupling=disabled)
        b=er.evaluate_model(p,allow_selftest=True,disabled_coupling=disabled)
        assert er.canonical_json(behavioral_projection(a))==er.canonical_json(behavioral_projection(b)),disabled
    for coupling in m['causalCouplings']:
        assert sr.coupling_effect_fingerprint(m,coupling)==sr.coupling_effect_fingerprint(p,coupling)


def make_r6_ablation_order_witness():
    m=make_eligible_fixture()
    src='t0_0'; twin='t0_1'
    m['states'][twin]['observationClass']=m['states'][src]['observationClass']
    m['states'][twin]['transitions']=copy.deepcopy(m['states'][src]['transitions'])
    for a,tr in list(m['states'][twin]['transitions'].items()):
        if 'couplingId' in tr:
            m['states'][twin]['transitions'][a]={'next':tr['next']}
    # preserve c1 usage elsewhere without changing the tied normal-world pair.
    es='e0_0'; win=next(a for a,tr in m['states'][es]['transitions'].items() if tr['next']=='win')
    m['states'][es]['transitions'][win]={'next':'win','couplingId':'c1','withoutCouplingNext':'loss'}
    er.validate_model(m,allow_selftest=True)
    assert er.semantic_state_identity(m,src,None)==er.semantic_state_identity(m,twin,None)
    assert er.semantic_state_identity(m,src,'c0')!=er.semantic_state_identity(m,twin,'c0')
    return m


def test_r6_ablation_initial_order_regression():
    m=make_r6_ablation_order_witness(); p=copy.deepcopy(m); p['contexts']['0']['trainInitialStates']=list(reversed(p['contexts']['0']['trainInitialStates']))
    assert [er.semantic_state_identity(m,s,'c0') for s in er.initial_states(m,'train',0,'c0')]==[er.semantic_state_identity(p,s,'c0') for s in er.initial_states(p,'train',0,'c0')]
    a=er.evaluate_model(m,allow_selftest=True,disabled_coupling='c0'); b=er.evaluate_model(p,allow_selftest=True,disabled_coupling='c0')
    assert er.canonical_json(behavioral_projection(a))==er.canonical_json(behavioral_projection(b))
    assert sr.choose_ablation(m,allow_selftest=True)['couplingId']==sr.choose_ablation(p,allow_selftest=True)['couplingId']


def test_duplicate_action_state_keying():
    m=er.load_model(str(MODEL)); ag=er.agency_and_duplicates(m)
    assert ['a0','a1'] in ag['duplicateActionPairs']
    row=ag['pairRates']['a0|a1']; assert row['coObserved']>0 and row['equivalent']==row['coObserved'] and row['rate']==1.0


def test_candidate_slot_invariance():
    base=make_eligible_fixture(); rows=[]
    for cid in ('R7SELFTEST01','R7SELFTEST02','R7SELFTEST03'):
        m=copy.deepcopy(base); m['candidateId']=cid; rows.append(behavioral_projection(er.evaluate_model(m,allow_selftest=True)))
    assert er.canonical_json(rows[0])==er.canonical_json(rows[1])==er.canonical_json(rows[2])


def candidate_models():
    return [make_eligible_fixture(x) for x in ('R7SELFTEST01','R7SELFTEST02','R7SELFTEST03')]


def test_build_manifest_order_and_blinding_seed():
    models=candidate_models()
    for m in models: assert er.evaluate_model(m,allow_selftest=True)['eligibleForTournament'] is True
    a=bm.make_manifest(models,allow_selftest=True); b=bm.make_manifest(list(reversed(models)),allow_selftest=True)
    assert er.canonical_json(a)==er.canonical_json(b)
    assert a['presentationSeed']==bm.presentation_seed(models)
    changed=[copy.deepcopy(x) for x in models]; changed[1]=permute_observation_labels(changed[1])
    assert bm.presentation_seed(changed)==a['presentationSeed']
    renamed=[copy.deepcopy(x) for x in models]; renamed[2]=rename_state_ids_and_reverse_contexts(renamed[2])
    assert bm.presentation_seed(renamed)==a['presentationSeed']
    checked=bm.validate_manifest(a,list(reversed(models)),allow_selftest=True)
    winner=bm.winner_model_for_manifest(checked,models,allow_selftest=True)
    assert checked['selectedCouplingId'] in winner['causalCouplings']
    assert checked['armBindings']['winner']['disabledCoupling'] is None
    assert checked['armBindings']['ablation']['disabledCoupling']==checked['selectedCouplingId']


def test_blinded_renderer_closes_r6_bitmap_channel():
    models=candidate_models(); manifest=bm.make_manifest(models,allow_selftest=True); winner=bm.winner_model_for_manifest(manifest,models,allow_selftest=True); seed=manifest['presentationSeed']
    rr.conformance_report(winner,None,presentation_seed=seed)
    sid=rr.scheduled_start(winner,0,0)[1]
    html=rr.render_html(winner,sid,presentation_seed=seed,participant_ordinal=0)
    assert winner['candidateId'] not in html and sid not in html and 'observationClass' not in html and 'grid-template-columns' not in html and 'level-' not in html
    assert 'State token' in html and html.count('class="token ')==1
    tokens={rr.blinded_token_id(winner,sid,seed,p) for p in range(24)}
    assert len(tokens)>1
    # Raw observation-label renaming cannot steer either semantic seed or token mapping.
    perm=permute_observation_labels(winner)
    assert er.canonical_observation_class(winner,sid)==er.canonical_observation_class(perm,sid)
    assert rr.blinded_token_id(winner,sid,seed,0)==rr.blinded_token_id(perm,sid,seed,0)


def test_selection_uses_models_not_caller_scores():
    forged={'candidateId':'R7C01','eligibleForTournament':True,'scores':{f:1.0 for f in sr.SCALAR_FAMILIES}}
    try: sr.tournament_select([forged])
    except Exception: pass
    else: raise AssertionError('caller score mapping reached selection')
    m=make_eligible_fixture(); rows=sr.ablation_rows(m,allow_selftest=True)
    for row in rows:
        direct=er.evaluate_model(m,allow_selftest=True,disabled_coupling=row['couplingId'])
        assert er.canonical_json(row['ablationEvaluation'])==er.canonical_json(direct)


def _meaningful_action_ordinal(model,state_id,disabled=None):
    classes=er.all_state_semantic_classes(model,disabled)
    for action in er.ordered_legal(model,state_id):
        after=er.next_state(model,state_id,action,disabled)
        if classes[state_id]!=classes[after]: return model['actions'].index(action)
    raise AssertionError('no meaningful action')


def _new_study(enrollment=0,disabled=None):
    model=make_eligible_fixture(); study=hr.StudyMachine(enrollment); game=rr.Session(model,study.participant_ordinal_within_arm,disabled); study.bind_initial_game_state(model,game.state_id); return model,study,game


def _meaningful_event(model,study,game,disabled,t):
    before=game.state_id
    if model['states'][before]['status']=='ONGOING':
        o=_meaningful_action_ordinal(model,before,disabled); after=rr.apply_action_ordinal(model,before,o,disabled); ev=study.record_gameplay_action(model,disabled,t,before_state=before,action_ordinal=o,after_state=after); game.state_id=after; return ev
    next_episode=game.episode_index+1; _,after=rr.scheduled_start(model,game.participant_ordinal,next_episode); ev=study.record_next_round(model,disabled,t,before_state=before,after_state=after,episode_index=next_episode); game.episode_index=next_episode; game.state_id=after; return ev


def _drive(study,model,game,target,start=0,optional=False):
    field='active_optional_play_ms' if optional else 'active_mandatory_play_ms'; study.record_heartbeat(start,visible=True,focused=True); _meaningful_event(model,study,game,None,start); t=start
    while getattr(study,field)<target:
        prev=t; t+=20_000
        for hb in range(prev+5_000,t+1,5_000): study.record_heartbeat(hb,visible=True,focused=True)
        _meaningful_event(model,study,game,None,t)
    return t


def test_focused_idle_and_explicit_presence_loss():
    model,s,g=_new_study();
    for t in range(0,hr.MANDATORY_MS+1,5_000): s.record_heartbeat(t,visible=True,focused=True)
    assert s.active_mandatory_play_ms==0 and s.phase(hr.MANDATORY_MS)=='MANDATORY'
    model,s,g=_new_study(); s.record_heartbeat(0,visible=True,focused=True); _meaningful_event(model,s,g,None,0); s.record_heartbeat(5_000,visible=True,focused=True); s.record_presence_loss(6_000,reason='hidden'); s.record_heartbeat(10_000,visible=True,focused=True); _meaningful_event(model,s,g,None,10_000)
    assert s.active_mandatory_play_ms==0
    script=hr.heartbeat_script(); assert '/presence-loss' in script and 'visibilitychange' in script and "addEventListener('blur'" in script and 'pagehide' in script


def test_endpoint_requires_interaction():
    model,s,g=_new_study(); done=_drive(s,model,g,hr.MANDATORY_MS); assert s.phase(done)=='CHOICE'; s.record_continue(done)
    for t in range(done,done+hr.CONTINUATION_TARGET_MS+1,5_000): s.record_heartbeat(t,visible=True,focused=True)
    assert s.active_optional_play_ms==0 and not s.voluntary_continuation_3m
    end=_drive(s,model,g,hr.CONTINUATION_TARGET_MS,start=done+hr.CONTINUATION_TARGET_MS,optional=True)
    assert s.active_optional_play_ms==hr.CONTINUATION_TARGET_MS and s.voluntary_continuation_3m
    assert end<=s.continue_elapsed_ms+hr.OPTIONAL_MAX_MS


def test_noop_illegal_and_phase_reject():
    model,s,g=_new_study(); s.record_heartbeat(0,visible=True,focused=True)
    noop=copy.deepcopy(model); s2=hr.StudyMachine(0); g2=rr.Session(noop,s2.participant_ordinal_within_arm,None); sid=g2.state_id; action=er.ordered_legal(noop,sid)[0]; ordinal=noop['actions'].index(action); noop['states'][sid]['transitions'][action]={'next':sid}; s2.bind_initial_game_state(noop,sid); s2.record_heartbeat(0,visible=True,focused=True); ev=s2.record_gameplay_action(noop,None,0,before_state=sid,action_ordinal=ordinal,after_state=sid); assert not ev['qualified'] and ev['accruedPlayMs']==0
    model,s,g=_new_study(); done=_drive(s,model,g,hr.MANDATORY_MS); before=g.state_id; ep=g.episode_index
    try:
        if model['states'][before]['status']=='ONGOING': hr.prepare_gameplay_action(s,g,model,None,done,_meaningful_action_ordinal(model,before,None))
        else: hr.prepare_next_round(s,g,model,None,done)
    except ValueError: pass
    else: raise AssertionError('CHOICE phase mutated gameplay')
    assert g.state_id==before and g.episode_index==ep and s._expected_game_state_id==before


def test_assignment_and_arm_symmetry():
    arms=[hr.arm_for(i) for i in range(24)]; assert arms.count('winner')==12 and arms.count('ablation')==12
    assert sorted(hr.within_arm_ordinal(i) for i in range(24) if hr.arm_for(i)=='winner')==list(range(12))
    assert sorted(hr.within_arm_ordinal(i) for i in range(24) if hr.arm_for(i)=='ablation')==list(range(12))


def sha256_file(path): return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_reference_digest_bindings_if_frozen():
    p=json.loads(PROTOCOL.read_text())
    if not p.get('state',{}).get('protocolFrozen',False): return
    paths={'evaluator':HERE/'evaluator_reference.py','selection':HERE/'selection_reference.py','renderer':HERE/'renderer_reference.py','studyRunner':HERE/'study_runner_reference.py','buildManifest':HERE/'build_manifest_reference.py','selftest':HERE/'protocol_selftest.py','selftestModel':MODEL,'modelSchema':SCHEMA,'protocolMarkdown':ROOT/'domains/game/GAME_AUTONOMOUS_INTEREST_PROTOCOL_R7.md'}
    assert set(p['referenceImplementationDigests'])==set(paths)
    for k,path in paths.items(): assert p['referenceImplementationDigests'][k]==sha256_file(path),(k,p['referenceImplementationDigests'][k],sha256_file(path))


def test_protocol_zero_slots():
    p=json.loads(PROTOCOL.read_text()); assert p['state']['candidateGenerationStarted'] is False and p['state']['candidateSemanticSlotsConsumed']==0 and p['state']['productSelected'] is False and p['state']['g0Entered'] is False


def main():
    test_schema_and_semantic_class_only(); test_observation_label_invariance(); test_state_id_context_order_invariance(); test_r6_ablation_initial_order_regression(); test_duplicate_action_state_keying(); test_candidate_slot_invariance(); test_build_manifest_order_and_blinding_seed(); test_blinded_renderer_closes_r6_bitmap_channel(); test_selection_uses_models_not_caller_scores(); test_focused_idle_and_explicit_presence_loss(); test_endpoint_requires_interaction(); test_noop_illegal_and_phase_reject(); test_assignment_and_arm_symmetry(); test_reference_digest_bindings_if_frozen(); test_protocol_zero_slots()
    print('R7_PROTOCOL_SELFTEST=PASS')
    print('R7_R6_TERMINAL_REGRESSIONS=PASS')
    print('R7_BLINDED_PRESENTATION=PASS')
    print('R7_EXPLICIT_PRESENCE_LOSS=PASS')
    print('R7_CANDIDATE_GENERATION_STARTED=false')
    print('R7_SEMANTIC_SLOTS_CONSUMED=0')

if __name__=='__main__': main()
