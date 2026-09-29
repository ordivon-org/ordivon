from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .owner_authority import validate_delegation_grant_document

OFFICE_ROLE_SCHEMA_SHA256 = "08a057ed40c99e8b4d84cf0a34290315557406fd56e5c8c43fbb42d87a4c53b1"
OFFICE_ASSIGNMENT_SCHEMA_SHA256 = "4dde4b27bdc45aafd7f88a3bdf94a354c85ac259256a8db31432950ff532ad79"
OFFICE_VERDICT_SCHEMA_SHA256 = "98b98448d8f46d3e8ccea4060c3c8ac55912ad98c8308d33c38f41111e802df4"
REVIEW_TOPOLOGY_SCHEMA_SHA256 = "1e0ad47e4d7b38b0442fd95cd19a2e5c3e6eece02af4e7fb28f0d143b5c11dbd"
_LEVELS=("L0_OBSERVE","L1_ANALYZE","L2_RECOMMEND","L3_PREPARE","L4_EXECUTE_BOUNDED","L5_CHANGE_CONSTITUTION")
_DUTIES={"MAKER","CHECKER","EFFECT_OWNER","RECONCILER","ASSURANCE"}
_LINES={"GOVERNING_BODY","FIRST_LINE","SECOND_LINE","THIRD_LINE"}
_ROLE_IDS={"GOVERNING_BODY","CAPITAL_ALLOCATION_COMMITTEE","CHIEF_CAPITAL_OFFICE","RESEARCH_OFFICE","ALLOCATION_OFFICE","RISK_OFFICE","TREASURY_OFFICE","EFFECT_OFFICE","CONTROLLER","PERFORMANCE_ATTRIBUTION","MODEL_DATA_GOVERNANCE","EXTERNAL_PROFESSIONAL_LIAISON","INDEPENDENT_ASSURANCE"}
_DATETIME_RE=re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
_VERDICTS={"APPROVE","CONDITIONAL","REJECT","ABSTAIN","ESCALATE"}
_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_DIGEST=re.compile(r"^sha256:[0-9a-f]{64}$")

class InstitutionalTopologyError(ValueError):
    pass

def _schema_identity(path: Path, expected: str, label: str) -> None:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise InstitutionalTopologyError(f"{label} schema changed; requalification required")

def assert_w3_schema_identities(schema_root: Path) -> None:
    _schema_identity(schema_root/'capital-office-role-v1.schema.json',OFFICE_ROLE_SCHEMA_SHA256,'office role')
    _schema_identity(schema_root/'capital-office-assignment-v1.schema.json',OFFICE_ASSIGNMENT_SCHEMA_SHA256,'office assignment')
    _schema_identity(schema_root/'capital-office-verdict-v1.schema.json',OFFICE_VERDICT_SCHEMA_SHA256,'office verdict')
    _schema_identity(schema_root/'capital-review-topology-v1.schema.json',REVIEW_TOPOLOGY_SCHEMA_SHA256,'review topology')

def canonical_digest(value: Any) -> str:
    payload=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return "sha256:"+hashlib.sha256(payload).hexdigest()

def _exact(value: Any, required: set[str], optional: set[str], label: str) -> dict[str,Any]:
    if not isinstance(value,dict): raise InstitutionalTopologyError(f"{label} must be an object")
    missing=required-set(value); extra=set(value)-required-optional
    if missing or extra: raise InstitutionalTopologyError(f"{label} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    return value

def _text(value: Any,label: str,max_bytes: int=12000) -> str:
    if not isinstance(value,str) or not value or value!=value.strip(): raise InstitutionalTopologyError(f"{label} must be non-empty and trimmed")
    if len(value.encode())>max_bytes: raise InstitutionalTopologyError(f"{label} exceeds {max_bytes} bytes")
    return value

def _id(value: Any,label: str) -> str:
    value=_text(value,label,1024)
    if not _ID.fullmatch(value): raise InstitutionalTopologyError(f"{label} must be an identifier")
    return value

def _digest(value: Any,label: str) -> str:
    value=_text(value,label,128)
    if not _DIGEST.fullmatch(value): raise InstitutionalTopologyError(f"{label} must be sha256")
    return value

def _dt(value: Any,label: str) -> str:
    value=_text(value,label,128)
    if not _DATETIME_RE.fullmatch(value): raise InstitutionalTopologyError(f"{label} must be RFC3339 date-time with timezone")
    try: parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc: raise InstitutionalTopologyError(f"{label} must be RFC3339") from exc
    if parsed.tzinfo is None: raise InstitutionalTopologyError(f"{label} must include timezone")
    return value

def _uniq_strings(value: Any,label: str) -> list[str]:
    if not isinstance(value,list): raise InstitutionalTopologyError(f"{label} must be an array")
    rows=[_text(item,f"{label}[]",2048) for item in value]
    if len(rows)!=len(set(rows)): raise InstitutionalTopologyError(f"{label} must be unique")
    return rows

def validate_office_role_document(doc: Any) -> dict[str,Any]:
    root=_exact(doc,{'schemaVersion','kind','roleId','line','mandate','allowedDelegationLevels','vetoClasses','prohibitedAuthorities','incompatibleSameDecisionRoles','independenceRequired'},set(),'office role')
    if root['schemaVersion']!=1 or isinstance(root['schemaVersion'],bool): raise InstitutionalTopologyError('office role schemaVersion must equal 1')
    if root['kind']!='ordivon.capital.office-role': raise InstitutionalTopologyError('unexpected office role kind')
    _id(root['roleId'],'roleId')
    if root['roleId'] not in _ROLE_IDS: raise InstitutionalTopologyError('invalid office roleId')
    if root['line'] not in _LINES: raise InstitutionalTopologyError('invalid office line')
    _text(root['mandate'],'mandate')
    levels=_uniq_strings(root['allowedDelegationLevels'],'allowedDelegationLevels')
    if not levels or any(x not in _LEVELS for x in levels): raise InstitutionalTopologyError('invalid allowed delegation level')
    _uniq_strings(root['vetoClasses'],'vetoClasses'); _uniq_strings(root['prohibitedAuthorities'],'prohibitedAuthorities')
    incompatible=_uniq_strings(root['incompatibleSameDecisionRoles'],'incompatibleSameDecisionRoles')
    if any(role not in _ROLE_IDS for role in incompatible): raise InstitutionalTopologyError('invalid incompatible Office role')
    if root['roleId'] in incompatible: raise InstitutionalTopologyError('role cannot be incompatible with itself')
    if not isinstance(root['independenceRequired'],bool): raise InstitutionalTopologyError('independenceRequired must be boolean')
    if root['line']=='THIRD_LINE' and not root['independenceRequired']: raise InstitutionalTopologyError('third line must require independence')
    return root

def validate_office_registry(doc: Any) -> dict[str,Any]:
    root=_exact(doc,{'schemaVersion','kind','standing','referencePatterns','roles'},set(),'office registry')
    if root['schemaVersion']!=1 or root['kind']!='ordivon.capital.office-registry': raise InstitutionalTopologyError('invalid office registry identity')
    _text(root['standing'],'standing'); _uniq_strings(root['referencePatterns'],'referencePatterns')
    if not isinstance(root['roles'],list) or not root['roles']: raise InstitutionalTopologyError('office registry roles must be non-empty')
    roles=[validate_office_role_document(x) for x in root['roles']]
    ids=[x['roleId'] for x in roles]
    if len(ids)!=len(set(ids)): raise InstitutionalTopologyError('duplicate office roleId')
    known=set(ids)
    for row in roles:
        unknown=set(row['incompatibleSameDecisionRoles'])-known
        if unknown: raise InstitutionalTopologyError(f"unknown incompatible role(s): {sorted(unknown)}")
    return root

def _role_map(registry: dict[str,Any]) -> dict[str,dict[str,Any]]:
    validate_office_registry(registry)
    return {row['roleId']:row for row in registry['roles']}

def validate_office_assignment_shape(doc: Any) -> dict[str,Any]:
    root=_exact(doc,{'schemaVersion','kind','assignmentId','roleId','actorRef','agentId','delegationGrantDigest','validFrom','revocable','evidenceDigest'},{'validUntil','workRef'},'office assignment')
    if root['schemaVersion']!=1 or isinstance(root['schemaVersion'],bool) or root['kind']!='ordivon.capital.office-assignment': raise InstitutionalTopologyError('invalid office assignment identity')
    _id(root['assignmentId'],'assignmentId'); _id(root['roleId'],'roleId')
    if root['roleId'] not in _ROLE_IDS: raise InstitutionalTopologyError('invalid office assignment roleId')
    actor=_text(root['actorRef'],'actorRef',512)
    if not actor.startswith('actor:') or any(c.isspace() for c in actor): raise InstitutionalTopologyError('actorRef must be a Host ActorRef-shaped opaque reference')
    _text(root['agentId'],'agentId',128); _digest(root['delegationGrantDigest'],'delegationGrantDigest'); _dt(root['validFrom'],'validFrom')
    if root.get('validUntil') is not None: _dt(root['validUntil'],'validUntil')
    if root['revocable'] is not True: raise InstitutionalTopologyError('office assignments must be revocable')
    _digest(root['evidenceDigest'],'evidenceDigest')
    if root.get('workRef') is not None: _text(root['workRef'],'workRef',1024)
    return root

def validate_office_assignment_document(doc: Any, *, registry: dict[str,Any], delegation: dict[str,Any]) -> dict[str,Any]:
    root=validate_office_assignment_shape(doc)
    roles=_role_map(registry)
    if root['roleId'] not in roles: raise InstitutionalTopologyError('assignment role is not registered')
    grant=validate_delegation_grant_document(delegation)
    if canonical_digest(grant)!=root['delegationGrantDigest']: raise InstitutionalTopologyError('assignment delegation digest mismatch')
    grantee=grant['grantee']
    if grantee['granteeType']=='OFFICE_ROLE':
        if grantee['granteeId']!=root['roleId']: raise InstitutionalTopologyError('office-role delegation does not target assignment role')
    elif grantee['granteeType']=='AGENT_IDENTITY':
        if grantee['granteeId']!=root['agentId']: raise InstitutionalTopologyError('agent delegation does not target assignment agent')
    else:
        raise InstitutionalTopologyError('CAPABILITY_PROFILE grant cannot by itself staff an Office role')
    if grant['level'] not in roles[root['roleId']]['allowedDelegationLevels']:
        raise InstitutionalTopologyError('delegated level exceeds/violates office role eligibility')
    return root

def project_agent_birth_role_binding(assignment: dict[str,Any], *, registry: dict[str,Any], delegation: dict[str,Any]) -> dict[str,Any]:
    assignment=validate_office_assignment_document(assignment,registry=registry,delegation=delegation)
    role=_role_map(registry)[assignment['roleId']]
    digest=canonical_digest(assignment)
    role_card="\n".join([
        f"OFFICE_ROLE={role['roleId']}",f"CONTROL_LINE={role['line']}",f"AGENT_ID={assignment['agentId']}",f"ACTOR_REF={assignment['actorRef']}",
        f"OFFICE_ASSIGNMENT_DIGEST={digest}",f"DELEGATION_GRANT_DIGEST={assignment['delegationGrantDigest']}",f"MANDATE={role['mandate']}",
        "AUTHORITY_BOUNDARY=Role card and ActorRef are context/binding only; authority remains the explicit DelegationGrant plus downstream owner/provider policy.",
        "TRUTH_BOUNDARY=Host social identity, Agent Birth materialization, Harness completion and Runtime success do not establish resource/provider truth or external effect authority."
    ])
    return {'schemaVersion':1,'kind':'ordivon.capital.agent-birth-role-binding','agentId':assignment['agentId'],'actorRef':assignment['actorRef'],'roleId':role['roleId'],'line':role['line'],'officeAssignmentDigest':digest,'delegationGrantDigest':assignment['delegationGrantDigest'],'roleCard':role_card,'hostAuthorizationGranted':False,'providerAuthorityGranted':False,'credentialAuthorityGranted':False,'externalEffectAuthorityGranted':False}

def validate_office_verdict_shape(doc: Any) -> dict[str,Any]:
    root=_exact(doc,{'schemaVersion','kind','verdictId','decisionRef','decisionDigest','assignmentDigest','roleId','actorRef','agentId','phase','verdict','assertedVetoClasses','rationale','evidenceRefs','unresolvedUnknowns','frozenAt','frozen'},set(),'office verdict')
    if root['schemaVersion']!=1 or isinstance(root['schemaVersion'],bool) or root['kind']!='ordivon.capital.office-verdict': raise InstitutionalTopologyError('invalid office verdict identity')
    _id(root['verdictId'],'verdictId'); _text(root['decisionRef'],'decisionRef',1024); _digest(root['decisionDigest'],'decisionDigest'); _digest(root['assignmentDigest'],'assignmentDigest')
    if root['roleId'] not in _ROLE_IDS: raise InstitutionalTopologyError('invalid Office verdict roleId')
    actor=_text(root['actorRef'],'actorRef',512)
    if not actor.startswith('actor:') or any(c.isspace() for c in actor): raise InstitutionalTopologyError('verdict actorRef must be Host ActorRef-shaped')
    _text(root['agentId'],'agentId',128)
    if root['phase'] not in {'INDEPENDENT_INITIAL','POST_DISCUSSION'}: raise InstitutionalTopologyError('invalid verdict phase')
    if root['verdict'] not in _VERDICTS: raise InstitutionalTopologyError('invalid verdict')
    _uniq_strings(root['assertedVetoClasses'],'assertedVetoClasses'); _text(root['rationale'],'rationale'); _uniq_strings(root['evidenceRefs'],'evidenceRefs'); _uniq_strings(root['unresolvedUnknowns'],'unresolvedUnknowns'); _dt(root['frozenAt'],'frozenAt')
    if root['frozen'] is not True: raise InstitutionalTopologyError('Office verdict must be frozen')
    return root

def validate_office_verdict_document(doc: Any, *, registry: dict[str,Any], assignment: dict[str,Any]) -> dict[str,Any]:
    root=validate_office_verdict_shape(doc)
    if root['assignmentDigest']!=canonical_digest(assignment): raise InstitutionalTopologyError('verdict assignment digest mismatch')
    if root['roleId']!=assignment['roleId'] or root['actorRef']!=assignment['actorRef'] or root['agentId']!=assignment['agentId']: raise InstitutionalTopologyError('verdict identity differs from Office assignment')
    veto=root['assertedVetoClasses']; role=_role_map(registry)[root['roleId']]
    if set(veto)-set(role['vetoClasses']): raise InstitutionalTopologyError('verdict asserts veto class not owned by role')
    if veto and root['verdict']!='REJECT': raise InstitutionalTopologyError('veto classes require REJECT verdict')
    return root

def validate_review_topology_document(doc: Any) -> dict[str,Any]:
    root=_exact(doc,{'schemaVersion','kind','reviewId','decisionRef','decisionDigest','materiality','externalEffectPlanned','dutyBindings','verdictRefs'},set(),'review topology')
    if root['schemaVersion']!=1 or isinstance(root['schemaVersion'],bool) or root['kind']!='ordivon.capital.review-topology': raise InstitutionalTopologyError('invalid review topology identity')
    _id(root['reviewId'],'reviewId'); _text(root['decisionRef'],'decisionRef',1024); _digest(root['decisionDigest'],'decisionDigest')
    if root['materiality'] not in {'ROUTINE','SENSITIVE','HIGH_CONSEQUENCE'}: raise InstitutionalTopologyError('invalid materiality')
    if not isinstance(root['externalEffectPlanned'],bool): raise InstitutionalTopologyError('externalEffectPlanned must be boolean')
    if not isinstance(root['dutyBindings'],list) or len(root['dutyBindings'])<2: raise InstitutionalTopologyError('review requires duty bindings')
    duties=[]
    for i,b in enumerate(root['dutyBindings']):
        b=_exact(b,{'duty','assignmentDigest','roleId','actorRef','agentId'},set(),f'dutyBindings[{i}]')
        if b['duty'] not in _DUTIES: raise InstitutionalTopologyError('invalid duty')
        _digest(b['assignmentDigest'],'assignmentDigest'); _id(b['roleId'],'roleId')
        if b['roleId'] not in _ROLE_IDS: raise InstitutionalTopologyError('invalid duty Office roleId')
        actor=_text(b['actorRef'],'actorRef',512)
        if not actor.startswith('actor:') or any(c.isspace() for c in actor): raise InstitutionalTopologyError('duty actorRef must be Host ActorRef-shaped')
        _text(b['agentId'],'agentId',128); duties.append(b['duty'])
    if not isinstance(root['verdictRefs'],list): raise InstitutionalTopologyError('verdictRefs must be array')
    seen=set()
    for i,r in enumerate(root['verdictRefs']):
        r=_exact(r,{'verdictId','digest'},set(),f'verdictRefs[{i}]'); _id(r['verdictId'],'verdictId'); _digest(r['digest'],'verdict digest')
        key=(r['verdictId'],r['digest'])
        if key in seen: raise InstitutionalTopologyError('duplicate verdictRef')
        seen.add(key)
    return root

def evaluate_review_topology(topology: dict[str,Any], *, registry: dict[str,Any], assignments: list[dict[str,Any]], delegations: dict[str,dict[str,Any]], verdicts: list[dict[str,Any]]) -> dict[str,Any]:
    topology=validate_review_topology_document(topology); roles=_role_map(registry)
    duties=[row['duty'] for row in topology['dutyBindings']]
    if len(duties)!=len(set(duties)): raise InstitutionalTopologyError('duplicate review duty')
    assignment_by_digest={}
    assignment_ids=set()
    for assignment in assignments:
        aid=assignment.get('assignmentId') if isinstance(assignment,dict) else None
        if not isinstance(aid,str) or aid not in delegations: raise InstitutionalTopologyError('missing delegation for Office assignment')
        if aid in assignment_ids: raise InstitutionalTopologyError('duplicate Office assignmentId')
        assignment_ids.add(aid)
        validated=validate_office_assignment_document(assignment,registry=registry,delegation=delegations[aid])
        assignment_by_digest[canonical_digest(validated)]=validated
    bound={}
    for b in topology['dutyBindings']:
        if b['assignmentDigest'] not in assignment_by_digest: raise InstitutionalTopologyError('duty binding references unknown assignment')
        a=assignment_by_digest[b['assignmentDigest']]
        if (b['roleId'],b['actorRef'],b['agentId'])!=(a['roleId'],a['actorRef'],a['agentId']): raise InstitutionalTopologyError('duty binding identity differs from assignment')
        bound[b['duty']]=a
    required={'MAKER','CHECKER'}
    if topology['externalEffectPlanned']: required|={'EFFECT_OWNER','RECONCILER'}
    missing=sorted(required-set(bound))
    role_errors=[]
    expected_lines={'MAKER':'FIRST_LINE','CHECKER':'SECOND_LINE','EFFECT_OWNER':'FIRST_LINE','RECONCILER':'SECOND_LINE','ASSURANCE':'THIRD_LINE'}
    for duty,a in bound.items():
        if roles[a['roleId']]['line']!=expected_lines[duty]: role_errors.append(f"{duty} requires {expected_lines[duty]}")
    if 'EFFECT_OWNER' in bound and bound['EFFECT_OWNER']['roleId']!='EFFECT_OFFICE': role_errors.append('EFFECT_OWNER must bind EFFECT_OFFICE')
    if 'RECONCILER' in bound and bound['RECONCILER']['roleId']!='CONTROLLER': role_errors.append('RECONCILER must bind CONTROLLER')
    if 'ASSURANCE' in bound and bound['ASSURANCE']['roleId']!='INDEPENDENT_ASSURANCE': role_errors.append('ASSURANCE must bind INDEPENDENT_ASSURANCE')
    conflict_pairs=[('MAKER','CHECKER'),('CHECKER','EFFECT_OWNER'),('EFFECT_OWNER','RECONCILER'),('MAKER','ASSURANCE'),('CHECKER','ASSURANCE'),('EFFECT_OWNER','ASSURANCE'),('RECONCILER','ASSURANCE')]
    identity_conflicts=[]
    for left,right in conflict_pairs:
        if left in bound and right in bound:
            a,b=bound[left],bound[right]
            if a['actorRef']==b['actorRef'] or a['agentId']==b['agentId']: identity_conflicts.append(f"{left}/{right} must be independently staffed")
            if b['roleId'] in roles[a['roleId']]['incompatibleSameDecisionRoles'] or a['roleId'] in roles[b['roleId']]['incompatibleSameDecisionRoles']: pass
    verdict_by_digest={canonical_digest(v):v for v in verdicts}
    validated_verdicts=[]
    ref_digests={r['digest'] for r in topology['verdictRefs']}
    if set(verdict_by_digest)!=ref_digests: raise InstitutionalTopologyError('verdict documents differ from verdictRefs')
    verdict_id_by_digest={canonical_digest(v): v.get('verdictId') for v in verdicts if isinstance(v,dict)}
    for ref in topology['verdictRefs']:
        if verdict_id_by_digest.get(ref['digest']) != ref['verdictId']: raise InstitutionalTopologyError('verdictRef id/digest mismatch')
    for digest,v in verdict_by_digest.items():
        ad=v.get('assignmentDigest') if isinstance(v,dict) else None
        if ad not in assignment_by_digest: raise InstitutionalTopologyError('verdict references unknown assignment')
        vv=validate_office_verdict_document(v,registry=registry,assignment=assignment_by_digest[ad])
        if vv['decisionRef']!=topology['decisionRef'] or vv['decisionDigest']!=topology['decisionDigest']: raise InstitutionalTopologyError('verdict targets another decision')
        validated_verdicts.append(vv)
    checker=bound.get('CHECKER')
    checker_initial=[] if checker is None else [v for v in validated_verdicts if v['assignmentDigest']==canonical_digest(checker) and v['phase']=='INDEPENDENT_INITIAL']
    if len(checker_initial)>1: raise InstitutionalTopologyError('multiple frozen initial checker verdicts')
    vetoes=[v for v in validated_verdicts if v['verdict']=='REJECT' and v['assertedVetoClasses']]
    checker_reject=bool(checker_initial and checker_initial[0]['verdict']=='REJECT')
    checker_escalate=bool(checker_initial and checker_initial[0]['verdict'] in {'CONDITIONAL','ABSTAIN','ESCALATE'})
    if missing: standing='REVIEW_OPEN'
    elif role_errors or identity_conflicts: standing='BLOCKED_ROLE_CONFLICT'
    elif vetoes: standing='BLOCKED_BY_VETO'
    elif not checker_initial: standing='REVIEW_OPEN'
    elif checker_reject: standing='REVIEW_REJECTED'
    elif checker_escalate: standing='ESCALATION_REQUIRED'
    else: standing='READY_FOR_DOWNSTREAM_POLICY'
    return {'schemaVersion':1,'kind':'ordivon.capital.review-disposition','reviewId':topology['reviewId'],'decisionRef':topology['decisionRef'],'decisionDigest':topology['decisionDigest'],'standing':standing,'missingDuties':missing,'roleErrors':role_errors,'identityConflicts':identity_conflicts,'vetoClasses':sorted({x for v in vetoes for x in v['assertedVetoClasses']}),'checkerInitialVerdict':None if not checker_initial else checker_initial[0]['verdict'],'policyGateRequired':True,'assuranceIsOperatingApproval':False,'majorityVoteMayOverrideVeto':False,'authorityGranted':False,'providerAuthorityGranted':False,'credentialAuthorityGranted':False,'externalEffectAuthorityGranted':False,'domainAcceptanceEstablished':False}

__all__=['InstitutionalTopologyError','assert_w3_schema_identities','canonical_digest','validate_office_role_document','validate_office_registry','validate_office_assignment_shape','validate_office_assignment_document','project_agent_birth_role_binding','validate_office_verdict_shape','validate_office_verdict_document','validate_review_topology_document','evaluate_review_topology']
