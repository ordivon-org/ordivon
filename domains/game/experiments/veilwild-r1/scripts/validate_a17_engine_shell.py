#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
project=(ROOT/'godot/project.godot').read_text()
scene=(ROOT/'godot/main.tscn').read_text()
contract=json.loads((ROOT/'contracts/F17_ENGINE_INTEGRATION_CONTRACT_R1.json').read_text())
required_mounts={m['name'] for m in contract['mounts']}
missing=[name for name in sorted(required_mounts) if f'name="{name}"' not in scene]
assert 'run/main_scene="res://main.tscn"' in project
assert 'VeilwildEventBus="*res://integration/event_bus.gd"' in project
assert not missing, f'missing mounts: {missing}'
assert contract['producer']=={'agentId':'A17','frontId':'F17','closureId':'V-R1'}
assert contract['compatibility'].startswith(('PROVISIONAL_', 'PARTIAL_RUNTIME_INTEGRATION'))
if contract['compatibility'].startswith('PARTIAL_RUNTIME_INTEGRATION'):
    bindings = contract.get('sourceBindings', [])
    assert any(b.get('producer') == 'A13/F13' for b in bindings), 'partial integration must identify consumed F13 source binding'
    assert 'not a frozen playable candidate' in contract['compatibility']
print('VEILWILD_A17_ENGINE_SHELL_VALID mounts=%d modules=%d' % (len(required_mounts), len(contract['moduleSettings'])))
