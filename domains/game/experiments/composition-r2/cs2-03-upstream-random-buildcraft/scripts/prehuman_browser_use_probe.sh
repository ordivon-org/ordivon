#!/usr/bin/env bash
set -euo pipefail

: "${BU_CDP_URL:?Set BU_CDP_URL to an already-authorized Chromium CDP endpoint}"
export BU_NAME="${BU_NAME:-game-cs2-03-probe}"
export BH_TAB_MARKER=0

browser-use <<'PY'
import json

URL='http://127.0.0.1:8765/web/'

def study_tab():
    tabs=list_tabs()
    tab=next((t for t in tabs if t.get('url')==URL),None)
    if tab is None:
        new_tab(URL)
        wait_for_load()
        tabs=list_tabs()
        tab=next(t for t in tabs if t.get('url')==URL)
    switch_tab(tab['targetId'])


def interactives():
    rows=[]
    for n in cdp('Accessibility.getFullAXTree')['nodes']:
        role=(n.get('role') or {}).get('value')
        name=(n.get('name') or {}).get('value') or ''
        bid=n.get('backendDOMNodeId')
        if role in {'button','textbox','slider'} and bid:
            rows.append({'role':role,'name':name,'backendDOMNodeId':bid})
    return rows


def click_observed(row):
    q=cdp('DOM.getBoxModel', backendNodeId=row['backendDOMNodeId'])['model']['content']
    click_at_xy(sum(q[0::2])/4, sum(q[1::2])/4)

study_tab()
js('location.reload()')
wait_for_load()
before=interactives()
begin=next((r for r in before if r['role']=='button' and r['name']=='Begin'),None)
assert begin, {'wanted':'Begin','observed':before}
click_observed(begin)
after=interactives()
text=js("document.getElementById('app').innerText")
assert ('Current challenge visible' in text) ^ ('Current challenge concealed' in text)
module_buttons=[r['name'] for r in after if r['role']=='button' and 'stats ' in r['name']]
assert len(module_buttons)>=2
print(json.dumps({
  'standing':'PASS_BROWSER_USE_PERCEPTION_PROBE',
  'humanEvidence':'UNASSESSED_NONHUMAN_ONLY',
  'page':page_info(),
  'before':before,
  'moduleButtons':module_buttons,
  'condition':'UPSTREAM' if 'Current challenge visible' in text else 'DOWNSTREAM',
  'visibleText':text,
  'boundary':'Agentic perception/action evidence only; no Human Player Value or condition-effect claim is authorized.'
},indent=2))
PY
