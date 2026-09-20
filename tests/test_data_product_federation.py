from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'evidence/data-lifecycle/data-products-r1'

def load(name):
    return json.loads((P/name).read_text())

def test_two_domain_catalog_is_dcat_projection():
    d=load('federated-catalog.dcat.jsonld')
    assert d['@type']=='dcat:Catalog'
    assert d['dct:conformsTo']['@id']=='https://www.w3.org/TR/vocab-dcat-3/'
    assert len(d['dcat:dataset'])==2
    ids={x['dct:identifier'] for x in d['dcat:dataset']}
    assert ids=={
      '94d0bf2c-036b-53b1-b733-14d3a5536a74',
      'd14d7457-c9aa-59e0-8bf5-7783cea39c1c',
    }
    assert sum(len(x['dcat:distribution']) for x in d['dcat:dataset'])==2

def test_prov_keeps_research_derivation_and_finance_boundary():
    p=load('product-provenance.prov.jsonld')
    graph=p['@graph']
    research_result='urn:sha256:37a092e36c0d31bad0e66f7992812537b3e99abc7037d685182743df62b1e10c'
    entity=next(x for x in graph if x.get('@id')==research_result)
    assert entity['prov:wasDerivedFrom']['@id']=='urn:sha256:6c2066eb1bf1824887a72c6f6df3cb5106894efde206686eb564287fe6547e50'
    a=load('acceptance.json')
    assert a['finance']['consumerBinding']=='NOT_YET_PROVEN_AFTER_PRODUCT_REGISTRATION'
    assert a['finance']['externalFinancialWritesAttempted'] is False

def test_acceptance_and_census_do_not_overclaim():
    a=load('acceptance.json')
    assert a['standing']=='PASS_TWO_DOMAIN_ODPS_ODCS_DCAT_PROV'
    assert a['rdfValidation']['standing']=='PASS'
    r3=json.loads((ROOT/'planning/data-lifecycle-census-r3.json').read_text())
    by={x['name']:x for x in r3['lifecycle']}
    assert by['metadata-catalog']['standing']=='PASS_TWO_DOMAIN_FEDERATED_DCAT'
    assert by['data-contract-product']['standing']=='PASS_TWO_DOMAIN_ODPS_1_1_ODCS_3_2'
    assert by['decision-action']['priority']=='P0'
    assert {x['id'] for x in r3['p0Queue']}=={
      'semantic-provenance','rights-privacy-retention','decision-outcome-feedback'
    }
