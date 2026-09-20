from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evidence/data-lifecycle/data-products-r1'

def load(name):
    return json.loads((BASE/name).read_text())

def test_governance_is_fail_closed_not_falsely_resolved():
    a=load('acceptance.json')
    g=a['governance']
    assert g['standing']=='PASS_FAIL_CLOSED_TWO_DOMAIN_RIGHTS_RETENTION_PRIVACY_BOUND'
    assert g['rightsPolicyModel']=='w3c-odrl-2.2-2018'
    assert g['privacyRiskBaseline']=='nist-privacy-framework-1.0'
    assert g['recordsManagementAuthority']=='iso-15489-1-2016'
    assert g['sourceRightsResolved'] is False
    assert g['formalPrivacyAssessmentComplete'] is False
    assert g['retentionSchedulesAssigned'] is False

def test_each_catalog_dataset_links_exactly_one_policy_and_stays_local():
    d=load('federated-catalog.dcat.jsonld')
    assert d['@context']['odrl']=='http://www.w3.org/ns/odrl/2/'
    for ds in d['dcat:dataset']:
        assert 'odrl:Asset' in ds['@type']
        assert ds['odrl:hasPolicy']['@id']==ds['dct:rights']['@id']
        distributions=ds['dcat:distribution']
        assert distributions
        for dist in distributions:
            assert dist['dcat:accessURL']['@id'].startswith('file://')

def test_domain_governance_references_are_revision_bound():
    a=load('acceptance.json')
    assert a['research']['repositoryRevision']=='6cfa97c3a2c4f71dc161744301b3dbcdd334f058'
    assert a['finance']['repositoryRevision']=='1746897f45d6326e1732c804007b57c550987bd0'
    for key in ['research','finance']:
        d=a[key]
        assert d['governancePolicyUid'].startswith('urn:uuid:')
        assert len(d['governancePolicySha256'])==64
        assert d['sourceLicenseStatus']=='UNRESOLVED'
        assert d['redistributionStatus']=='NOT_AUTHORIZED_BY_PRODUCT_METADATA'
        assert d['retentionScheduleStatus']=='UNASSIGNED'

def test_r4_moves_safe_binding_out_of_p0_without_claiming_resolution():
    r4=json.loads((ROOT/'planning/data-lifecycle-census-r4.json').read_text())
    assert {x['id'] for x in r4['p0Queue']}=={'semantic-provenance','decision-outcome-feedback'}
    fabric=next(x for x in r4['fabrics'] if x['name']=='governance-rights-retention')
    assert fabric['standing']=='PASS_FAIL_CLOSED_TWO_DOMAIN_BOUND_RESOLUTION_PENDING'
    assert fabric['priority']=='P1'
    p1={x['id'] for x in r4['p1Queue']}
    assert {'source-rights-resolution','formal-privacy-assessment','retention-schedule-assignment'} <= p1
