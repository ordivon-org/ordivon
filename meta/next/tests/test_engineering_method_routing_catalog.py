import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / 'catalogs/capabilities/packages/engineering-method-routing-r1.json'
CARD = ROOT / 'catalogs/capabilities/packages/engineering.md'

EXPECTED_SOURCE_COUNTS = {
    'ecc-native': 311,
    'matt-native': 38,
    'obra-superpowers': 14,
    'ordivon-native-tools': 2,
    'project-ordivon-next': 30,
    'rea-native': 1,
    'spec-kit-native': 10,
}

def load_catalog():
    return json.loads(CATALOG.read_text())

def test_catalog_shape_and_complete_native_supply():
    payload = load_catalog()
    inventory = payload['inventory']
    assert payload['schemaVersion'] == 1
    assert len(inventory) == 406
    assert Counter(item['sourceId'] for item in inventory) == Counter(EXPECTED_SOURCE_COUNTS)
    assert payload['sourceCounts'] == dict(sorted(EXPECTED_SOURCE_COUNTS.items()))
    assert len({item['skillId'] for item in inventory}) == len(inventory)

def test_every_inventory_item_is_routable_without_claiming_authority():
    payload = load_catalog()
    for item in payload['inventory']:
        assert item['nativeCategories']
        assert item['capabilityClasses']
        assert item['phases']
        assert item['standing']
    assert 'routing guidance only' in payload['standingSemantics']
    assert any('Skills provide procedure' in p for p in payload['principles'])
    assert any('Host owns durable collaboration truth' in p for p in payload['principles'])

def test_ecc_preserves_native_module_coverage():
    ecc = [i for i in load_catalog()['inventory'] if i['sourceId'] == 'ecc-native']
    assert len(ecc) == 311
    assert all(i['nativeCategories'] for i in ecc)
    assert all(i['capabilityClasses'] for i in ecc)

def test_deprecated_spec_kit_compatibility_skill_is_not_default_routed():
    items = {i['skillId']: i for i in load_catalog()['inventory']}
    item = items['spec-kit-native/speckit-taskstoissues']
    assert item['standing'] == 'RETIRED_EXPLICIT'
    assert item['description'].startswith('Deprecated:')

def test_default_routing_keeps_thin_waist_and_separate_owners():
    payload = load_catalog()
    routes = payload['routing']
    assert set(routes) == {'FRAME', 'PLAN', 'EXECUTE', 'VERIFY', 'DELIVER', 'MULTI_AGENT', 'RESOURCE'}
    verify = json.dumps(routes['VERIFY'])
    execute = json.dumps(routes['EXECUTE'])
    assert 'obra-superpowers/verification-before-completion' in verify
    assert 'obra-superpowers/subagent-driven-development' in execute
    assert 'services/runtime' in execute

def test_engineering_card_points_to_current_method_supply_without_becoming_a_lifecycle():
    text = CARD.read_text()
    assert 'Last census: 2026-10-16' in text
    assert 'engineering-method-routing-r1.md' in text
    assert '406-Skill census' in text
    assert 'not another workflow engine or authority layer' in text
