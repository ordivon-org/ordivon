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
