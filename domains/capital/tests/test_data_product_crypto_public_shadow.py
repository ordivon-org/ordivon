from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data-products/crypto-public-shadow-r2'
SRC=ROOT/'evidence/crypto-public-shadow-r2-20260914.json'
EXPECTED='ed5fba6227a5d997adefb6bf63717463dc75fdc8b62cfb0005804109eb0a2d7e'

def load(name):
    return json.loads((P/name).read_text())

def test_product_contract_source_binding():
    prod,con,a=load('odps.json'),load('odcs.json'),load('acceptance.json')
    assert prod['apiVersion']=='v1.1.0' and prod['type']=='consumerAligned'
    assert con['apiVersion']=='v3.2.0'
    assert prod['outputPorts'][0]['contractId']==con['id']==a['contractId']
    assert prod['id']==a['productId']
    assert hashlib.sha256(SRC.read_bytes()).hexdigest()==EXPECTED==a['sourceSha256']
    assert a['standing']=='PASS_ODPS_1_1_ODCS_3_2_SOURCE_BOUND_READ_ONLY'

def test_public_shadow_no_effect_boundary_and_shape():
    d=json.loads(SRC.read_text())
    assert d['brokerCredentialsUsed'] is False
    assert d['privateAccountDataUsed'] is False
    assert d['externalFinancialWritesAttempted'] is False
    s=d['streaming']
    assert s['acceptedSnapshotCount']==4
    assert len(s['measured'])==3
    assert sorted({q['venue'] for m in s['measured'] for q in m['quotes'].values()})==['BINANCE','OKX']
    assert sorted({q['asset'] for m in s['measured'] for q in m['quotes'].values()})==['BTC','ETH']

def test_product_context_keeps_observation_separate_from_execution():
    prod=load('odps.json')
    constraints=' '.join(x['constraint'] for x in prod['context']['constraints'])
    assert 'Do not use this product as authorization or instruction to place a trade.' in constraints
    assert 'Do not turn bounded cross-venue observations into an alpha' in constraints

def test_fail_closed_governance_policy_and_unresolved_rights():
    prod=load('odps.json')
    acc=load('acceptance.json')
    policy=json.loads((P/'governance-policy.odrl.jsonld').read_text())
    assert policy['@context']=='http://www.w3.org/ns/odrl.jsonld'
    assert policy['@type']=='Set'
    assert policy['uid']==acc['governancePolicyUid']
    assert {x['action'] for x in policy['prohibition']}=={'distribute','grantUse','delete'}
    cp={x['property']:x['value'] for x in prod['customProperties']}
    assert cp['sourceLicenseStatus']=='UNRESOLVED'
    assert cp['redistributionStatus']=='NOT_AUTHORIZED_BY_PRODUCT_METADATA'
    assert cp['retentionScheduleStatus']=='UNASSIGNED'
    assert cp['automaticDeletionStatus']=='NOT_AUTHORIZED_UNTIL_RECORDS_REQUIREMENT_ASSIGNED'
    assert cp['privacyFrameworkBaseline']=='NIST_PRIVACY_FRAMEWORK_1_0'
    assert cp['privacyAssessmentStatus']=='BOUNDED_NO_PRIVATE_ACCOUNT_DATA_PROVEN_FORMAL_ASSESSMENT_NOT_COMPLETE'

def test_public_access_is_not_promoted_to_redistribution_license():
    prod=load('odps.json')
    serialized=json.dumps(prod).lower()
    assert '"license":' not in serialized
    a=load('acceptance.json')
    assert a['sourceLicenseStatus']=='UNRESOLVED'
    assert a['redistributionStatus']=='NOT_AUTHORIZED_BY_PRODUCT_METADATA'
    assert a['brokerCredentialsUsed'] is False
    assert a['privateAccountDataUsed'] is False
    assert a['externalFinancialWritesAttempted'] is False


def test_domain_owner_is_not_provider_rights_claim():
    prod=load("odps.json")
    assert prod["team"]["name"]=="Ordivon Capital market-observation domain"
    cp={x["property"]:x["value"] for x in prod["team"]["customProperties"]}
    assert cp["ownershipScope"]=="PRODUCT_METADATA_AND_LIFECYCLE_NOT_PROVIDER_IP"
