#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'source' / 'creative-library-catalog-v1.json'
OUT = ROOT / 'render'
WEB = ROOT / 'interactive'
OUT.mkdir(parents=True, exist_ok=True)
WEB.mkdir(parents=True, exist_ok=True)
cat = json.loads(SRC.read_text(encoding='utf-8'))
works = list(cat.get('works', []))
relations = list(cat.get('relations', []))

owners = sorted({w.get('owner') or 'Unknown' for w in works})
owner_counts = Counter(w.get('owner') or 'Unknown' for w in works)
palette = {'Media':'#58a6ff','Game':'#f2cc60','Web':'#7ee787','Workstation':'#d2a8ff'}
base_anchors = {'Media':(-500.0,120.0),'Game':(40.0,260.0),'Web':(530.0,100.0),'Workstation':(190.0,-300.0)}
anchors = {}
for i, owner in enumerate(owners):
    if owner in base_anchors:
        anchors[owner] = base_anchors[owner]
    else:
        a = 2*math.pi*i/max(1,len(owners)); anchors[owner]=(560*math.cos(a),360*math.sin(a))

by_owner = defaultdict(list)
for w in works: by_owner[w.get('owner') or 'Unknown'].append(w)

# Stable, conceptually positioned island layout. Hashing controls angular placement only;
# catalog identity and owner remain the semantic facts.
positions = {}
for owner, rows in by_owner.items():
    cx, cy = anchors[owner]
    rows = sorted(rows, key=lambda w: w['workId'])
    for idx, w in enumerate(rows):
        h = hashlib.sha256(w['workId'].encode()).digest()
        theta = (int.from_bytes(h[:4],'big') / 2**32) * math.tau
        r = 18 + 14*math.sqrt(idx+1) + (h[4]/255.0)*18
        positions[w['workId']] = (round(cx+r*math.cos(theta),3), round(cy+0.78*r*math.sin(theta),3))

# Relation normalization and degree.
rel_features=[]; degree=Counter(); neighbors=defaultdict(list)
for r in relations:
    a=r.get('child_work_id') or r.get('childWorkId') or r.get('from')
    b=r.get('parent_work_id') or r.get('parentWorkId') or r.get('to')
    typ=r.get('relation_type') or r.get('relationType') or r.get('type') or 'RELATED'
    if a in positions and b in positions:
        rel_features.append({'from':a,'to':b,'type':typ})
        degree[a]+=1; degree[b]+=1
        neighbors[a].append({'workId':b,'type':typ,'direction':'out'})
        neighbors[b].append({'workId':a,'type':typ,'direction':'in'})

# Selective static labels: at most two representative works per owner.
labels=set()
for owner, rows in by_owner.items():
    ranked=sorted(rows,key=lambda w:(not bool(w.get('featured')),-degree[w['workId']],-int(w.get('carrierCount') or 0),w['title'].casefold()))
    labels.update(w['workId'] for w in ranked[:2])

# GeoJSON carriers.
features=[]
for w in works:
    x,y=positions[w['workId']]
    features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[x,y]},'properties':{
        'work_id':w['workId'],'title':w.get('title'),'owner':w.get('owner'),'room':w.get('room'),
        'status':w.get('status'),'series':w.get('series'),'modalities':','.join(w.get('modalities') or []),
        'carrier_count':w.get('carrierCount',0),'evidence_level':w.get('evidenceLevel'),
        'source_revision':w.get('sourceRevision'),'featured':bool(w.get('featured')),'relation_degree':degree[w['workId']]
    }})
(OUT/'works.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
owner_features=[{'type':'Feature','geometry':{'type':'Point','coordinates':list(anchors[o])},'properties':{'owner':o,'work_count':owner_counts[o]}} for o in owners]
(OUT/'owners.geojson').write_text(json.dumps({'type':'FeatureCollection','features':owner_features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
relation_features=[]
for r in rel_features:
    relation_features.append({'type':'Feature','geometry':{'type':'LineString','coordinates':[list(positions[r['from']]),list(positions[r['to']])]},'properties':{'from_id':r['from'],'to_id':r['to'],'relation_type':r['type']}})
(OUT/'relations.geojson').write_text(json.dumps({'type':'FeatureCollection','features':relation_features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Shared projection for editorial still + web canvas.
W,H=1600,1000; minx,maxx=-850,850; miny,maxy=-560,560
def sx(x): return 84+(x-minx)/(maxx-minx)*(W-168)
def sy(y): return 160+(maxy-y)/(maxy-miny)*(H-300)
def owner_radius(owner): return 62+min(122, math.sqrt(owner_counts[owner])*7)

def relation_path(a,b,typ):
    x1,y1=positions[a]; x2,y2=positions[b]
    X1,Y1,X2,Y2=sx(x1),sy(y1),sx(x2),sy(y2)
    # deterministic shallow bend avoids the dead-straight network look without adding semantics.
    h=hashlib.sha256((a+'|'+b+'|'+typ).encode()).digest(); sign=-1 if h[0]%2 else 1
    mx,my=(X1+X2)/2,(Y1+Y2)/2; dx,dy=X2-X1,Y2-Y1; ln=max(1,math.hypot(dx,dy))
    bend=min(34,ln*0.06)*sign; cx=mx-dy/ln*bend; cy=my+dx/ln*bend
    return f'M {X1:.1f},{Y1:.1f} Q {cx:.1f},{cy:.1f} {X2:.1f},{Y2:.1f}'

# Editorial still.
svg=[]
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
svg.append('<rect width="100%" height="100%" fill="#090d12"/>')
svg.append('<rect x="52" y="52" width="1496" height="896" rx="28" fill="none" stroke="#30363d" stroke-width="2"/>')
svg.append('<text x="86" y="116" fill="#f0f6fc" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="40" font-weight="700" letter-spacing="4">ARCHIVE / ARCHIPELAGO 001</text>')
svg.append('<text x="86" y="148" fill="#7d8590" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14" letter-spacing="1.4">303 FROZEN CREATIVE WORKS · 45 CATALOGUED RELATIONS · CONCEPTUAL ARCHIVE PLANE</text>')
svg.append('<line x1="86" y1="176" x2="1514" y2="176" stroke="#21262d"/>')
# island contours
for owner in owners:
    x,y=anchors[owner]; X,Y=sx(x),sy(y); c=palette.get(owner,'#8b949e'); rr=owner_radius(owner)
    for mul,op in [(1.0,.18),(.72,.10),(.46,.07)]:
        svg.append(f'<ellipse cx="{X:.1f}" cy="{Y:.1f}" rx="{rr*mul:.1f}" ry="{rr*.72*mul:.1f}" fill="none" stroke="{c}" stroke-opacity="{op}" stroke-dasharray="5 8"/>')
    svg.append(f'<ellipse cx="{X:.1f}" cy="{Y:.1f}" rx="{rr:.1f}" ry="{rr*.72:.1f}" fill="{c}" fill-opacity="0.035"/>')
# relation routes behind nodes
for r in rel_features:
    typ=r['type']; col='#6e7681' if typ=='DERIVATIVE_OF' else '#8b949e'; dash='3 7' if typ=='DERIVATIVE_OF' else 'none'
    svg.append(f'<path d="{relation_path(r["from"],r["to"],typ)}" fill="none" stroke="{col}" stroke-opacity="0.28" stroke-width="1.15" stroke-dasharray="{dash}"/>')
# owner headings
for owner in owners:
    x,y=anchors[owner]; X,Y=sx(x),sy(y); c=palette.get(owner,'#8b949e'); rr=owner_radius(owner)
    svg.append(f'<text x="{X:.1f}" y="{Y-rr*.80:.1f}" fill="{c}" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14" font-weight="700" letter-spacing="1.3">{html.escape(owner.upper())} / {owner_counts[owner]}</text>')
# works + selected labels
work_map={w['workId']:w for w in works}
for w in works:
    wid=w['workId']; x,y=positions[wid]; X,Y=sx(x),sy(y); c=palette.get(w.get('owner'),'#8b949e')
    radius=2.0+min(5.0,math.log2(1+max(1,int(w.get('carrierCount') or 1)))*0.52)
    if w.get('featured'):
        svg.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{radius+4:.2f}" fill="none" stroke="{c}" stroke-width="1.2" stroke-opacity="0.55"/>')
    svg.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{radius:.2f}" fill="{c}" opacity="0.88"><title>{html.escape(wid+" — "+str(w.get("title") or ""))}</title></circle>')
for wid in sorted(labels):
    w=work_map[wid]; x,y=positions[wid]; X,Y=sx(x),sy(y); ox,oy=anchors[w.get('owner')]; side=1 if x>=ox else -1
    tx=X+side*16; anchor='start' if side>0 else 'end'; c=palette.get(w.get('owner'),'#8b949e')
    title=str(w.get('title') or wid); title=title if len(title)<=27 else title[:26]+'…'
    svg.append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X+side*11:.1f}" y2="{Y-8:.1f}" stroke="{c}" stroke-opacity="0.45"/>')
    svg.append(f'<text x="{tx:.1f}" y="{Y-11:.1f}" fill="#d0d7de" text-anchor="{anchor}" font-family="Inter,Segoe UI,sans-serif" font-size="11.5">{html.escape(title)}</text>')
# editorial legend
lx,ly=1120,720
svg.append(f'<rect x="{lx}" y="{ly}" width="392" height="160" rx="18" fill="#11161d" stroke="#30363d"/>')
svg.append(f'<text x="{lx+22}" y="{ly+30}" fill="#f0f6fc" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" font-weight="700" letter-spacing="1">READING THE MAP</text>')
svg.append(f'<line x1="{lx+22}" y1="{ly+54}" x2="{lx+72}" y2="{ly+54}" stroke="#6e7681" stroke-width="1.4" stroke-dasharray="3 7"/><text x="{lx+88}" y="{ly+59}" fill="#8b949e" font-family="Inter,Segoe UI,sans-serif" font-size="13">DERIVATIVE_OF — 35</text>')
svg.append(f'<line x1="{lx+22}" y1="{ly+82}" x2="{lx+72}" y2="{ly+82}" stroke="#8b949e" stroke-width="1.4"/><text x="{lx+88}" y="{ly+87}" fill="#8b949e" font-family="Inter,Segoe UI,sans-serif" font-size="13">CONSUMER_OF — 10</text>')
svg.append(f'<circle cx="{lx+30}" cy="{ly+112}" r="5" fill="#58a6ff"/><circle cx="{lx+30}" cy="{ly+112}" r="9" fill="none" stroke="#58a6ff" stroke-opacity=".55"/><text x="{lx+50}" y="{ly+117}" fill="#8b949e" font-family="Inter,Segoe UI,sans-serif" font-size="13">ring = featured work · size ≈ carrier count</text>')
svg.append(f'<text x="{lx+22}" y="{ly+145}" fill="#6e7681" font-family="Inter,Segoe UI,sans-serif" font-size="11">proximity is composition, not semantic similarity</text>')
# footer
short=(cat.get('catalogDigest') or 'unknown').replace('sha256:','')[:16]
svg.append('<line x1="86" y1="906" x2="1514" y2="906" stroke="#21262d"/>')
svg.append(f'<text x="86" y="934" fill="#6e7681" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12">SOURCE CATALOG {html.escape(short)}… · frozen snapshot · exact details in GeoPackage / interactive companion</text>')
svg.append('<text x="1514" y="934" fill="#6e7681" text-anchor="end" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12">NO GEOGRAPHY · NO DEPENDENCY INFERENCE</text>')
svg.append('</svg>')
(OUT/'archive-archipelago-001.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')

# Self-contained interaction dataset (rendered from the frozen source snapshot).
interactive_works=[]
for w in works:
    interactive_works.append({
        'id':w['workId'],'title':w.get('title'),'owner':w.get('owner'),'room':w.get('room'),'status':w.get('status'),
        'series':w.get('series'),'modalities':w.get('modalities') or [],'carriers':w.get('carrierCount',0),
        'featured':bool(w.get('featured')),'evidenceLevel':w.get('evidenceLevel'),'sourceRevision':w.get('sourceRevision'),
        'x':sx(positions[w['workId']][0]),'y':sy(positions[w['workId']][1]),'degree':degree[w['workId']],
        'neighbors':sorted(neighbors[w['workId']],key=lambda n:(n['type'],n['workId']))
    })
idata={'schemaVersion':1,'workId':'media:archive-archipelago-001','catalogDigest':cat.get('catalogDigest'),
       'works':interactive_works,'relations':[{'from':r['from'],'to':r['to'],'type':r['type'],'path':relation_path(r['from'],r['to'],r['type'])} for r in rel_features],
       'owners':[{'name':o,'count':owner_counts[o],'x':sx(anchors[o][0]),'y':sy(anchors[o][1]),'radius':owner_radius(o),'color':palette.get(o,'#8b949e')} for o in owners]}
(WEB/'data.js').write_text('window.ARCHIVE_ARCHIPELAGO_DATA='+json.dumps(idata,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')

manifest={'schemaVersion':1,'kind':'ordivon.media.cartographic-work-build','workId':'media:archive-archipelago-001','title':'Archive Archipelago 001',
 'sourceCatalogDigest':cat.get('catalogDigest'),'sourceWorkCount':len(works),'ownerCounts':dict(sorted(owner_counts.items())),
 'mappedRelationCount':len(rel_features),'relationTypes':dict(sorted(Counter(r['type'] for r in rel_features).items())),
 'staticLabelCount':len(labels),'coordinateSemantics':'conceptual Cartesian archive plane; no geographic location or semantic-distance claim',
 'outputs':['render/works.geojson','render/owners.geojson','render/relations.geojson','render/archive-archipelago-001.svg','render/archive-archipelago-001.gpkg','render/archive-archipelago-001.png','interactive/index.html']}
(OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,sort_keys=True))
