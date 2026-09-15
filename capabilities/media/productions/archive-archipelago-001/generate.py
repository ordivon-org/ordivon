#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, html
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT/'source'/'creative-library-catalog-v1.json'
OUT = ROOT/'render'
OUT.mkdir(parents=True, exist_ok=True)
cat = json.loads(SRC.read_text(encoding='utf-8'))
works = list(cat.get('works', []))
relations = list(cat.get('relations', []))

owners = sorted({w.get('owner') or 'Unknown' for w in works})
owner_counts = Counter(w.get('owner') or 'Unknown' for w in works)
# Stable hand-tuned archipelago anchors; all coordinates are conceptual, not geographic.
base_anchors = {
    'Media': (-500.0, 120.0),
    'Game': (40.0, 260.0),
    'Web': (530.0, 100.0),
    'Workstation': (190.0, -300.0),
}
anchors = {}
for i,o in enumerate(owners):
    if o in base_anchors:
        anchors[o] = base_anchors[o]
    else:
        a = 2*math.pi*i/max(1,len(owners))
        anchors[o] = (560*math.cos(a), 360*math.sin(a))

positions = {}
by_owner = defaultdict(list)
for w in works:
    by_owner[w.get('owner') or 'Unknown'].append(w)

for owner, rows in by_owner.items():
    cx, cy = anchors[owner]
    rows = sorted(rows, key=lambda w: w['workId'])
    for idx,w in enumerate(rows):
        h = hashlib.sha256(w['workId'].encode()).digest()
        theta = (int.from_bytes(h[:4],'big') / 2**32) * math.tau
        # golden-angle radial distribution with digest jitter: stable, dense, non-overlapping enough for atlas-scale view
        r = 18 + 14*math.sqrt(idx+1) + (h[4]/255.0)*18
        x = cx + r*math.cos(theta)
        y = cy + 0.78*r*math.sin(theta)
        positions[w['workId']] = (round(x,3), round(y,3))

# Point features.
features=[]
for w in works:
    x,y=positions[w['workId']]
    features.append({
      'type':'Feature','geometry':{'type':'Point','coordinates':[x,y]},
      'properties':{
        'work_id':w['workId'],'title':w.get('title'),'owner':w.get('owner'),
        'room':w.get('room'),'status':w.get('status'),'series':w.get('series'),
        'modalities':','.join(w.get('modalities') or []),'carrier_count':w.get('carrierCount',0),
        'evidence_level':w.get('evidenceLevel'),'source_revision':w.get('sourceRevision')
      }
    })
(OUT/'works.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Owner centroid features.
owners_features=[]
for owner in owners:
    x,y=anchors[owner]
    owners_features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[x,y]},'properties':{'owner':owner,'work_count':owner_counts[owner]}})
(OUT/'owners.geojson').write_text(json.dumps({'type':'FeatureCollection','features':owners_features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Relation features only when both endpoints are current works.
rel_features=[]
for r in relations:
    a=r.get('child_work_id') or r.get('childWorkId') or r.get('from')
    b=r.get('parent_work_id') or r.get('parentWorkId') or r.get('to')
    if a in positions and b in positions:
        rel_features.append({'type':'Feature','geometry':{'type':'LineString','coordinates':[list(positions[a]),list(positions[b])]},'properties':{'from_id':a,'to_id':b,'relation_type':r.get('relation_type') or r.get('relationType') or r.get('type')}})
(OUT/'relations.geojson').write_text(json.dumps({'type':'FeatureCollection','features':rel_features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# SVG render.
W,H=1600,1000
minx,maxx=-850,850; miny,maxy=-560,560
def sx(x): return 90+(x-minx)/(maxx-minx)*(W-180)
def sy(y): return 130+(maxy-y)/(maxy-miny)*(H-220)
palette={'Media':'#58a6ff','Game':'#f2cc60','Web':'#7ee787','Workstation':'#d2a8ff'}
svg=[]
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
svg.append('<rect width="100%" height="100%" fill="#0b0f14"/>')
svg.append('<text x="90" y="70" fill="#f0f6fc" font-family="Inter,Segoe UI,sans-serif" font-size="38" font-weight="700">Archive Archipelago 001</text>')
svg.append('<text x="90" y="104" fill="#8b949e" font-family="Inter,Segoe UI,sans-serif" font-size="18">A cartographic portrait of the Ordivon Creative Library · conceptual coordinates, not geography</text>')
# relations first
for f in rel_features:
    (x1,y1),(x2,y2)=f['geometry']['coordinates']
    svg.append(f'<line x1="{sx(x1):.1f}" y1="{sy(y1):.1f}" x2="{sx(x2):.1f}" y2="{sy(y2):.1f}" stroke="#30363d" stroke-width="1" opacity="0.55"/>')
# owner halo + label
for owner in owners:
    x,y=anchors[owner]; c=palette.get(owner,'#8b949e'); n=owner_counts[owner]
    rr=60+min(120, math.sqrt(n)*7)
    svg.append(f'<ellipse cx="{sx(x):.1f}" cy="{sy(y):.1f}" rx="{rr:.1f}" ry="{rr*0.72:.1f}" fill="{c}" opacity="0.055" stroke="{c}" stroke-opacity="0.22"/>')
    svg.append(f'<text x="{sx(x):.1f}" y="{sy(y)-rr*0.78:.1f}" fill="{c}" text-anchor="middle" font-family="Inter,Segoe UI,sans-serif" font-size="19" font-weight="650">{html.escape(owner)} · {n}</text>')
# works
for w in works:
    x,y=positions[w['workId']]; c=palette.get(w.get('owner'),'#8b949e')
    radius=2.2+min(4.8, math.log2(1+max(1,w.get('carrierCount',1))))*0.52
    title=html.escape(f"{w['workId']} — {w.get('title','')}")
    svg.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{radius:.2f}" fill="{c}" opacity="0.82"><title>{title}</title></circle>')
# legend / footer
lx=1120; ly=780
svg.append(f'<rect x="{lx-24}" y="{ly-42}" width="390" height="150" rx="18" fill="#161b22" stroke="#30363d"/>')
for i,owner in enumerate(owners[:6]):
    c=palette.get(owner,'#8b949e'); y=ly+i*24
    svg.append(f'<circle cx="{lx}" cy="{y}" r="6" fill="{c}"/>')
    svg.append(f'<text x="{lx+18}" y="{y+6}" fill="#c9d1d9" font-family="Inter,Segoe UI,sans-serif" font-size="15">{html.escape(owner)} — {owner_counts[owner]} works</text>')
summary=f"{len(works)} works · {len(rel_features)} mapped relations · source catalog {cat.get('catalogDigest','unknown')}"
svg.append(f'<text x="90" y="956" fill="#6e7681" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14">{html.escape(summary)}</text>')
svg.append('</svg>')
(OUT/'archive-archipelago-001.svg').write_text('\n'.join(svg)+'\n',encoding='utf-8')

manifest={
 'schemaVersion':1,'kind':'ordivon.media.cartographic-work-build',
 'workId':'media:archive-archipelago-001','title':'Archive Archipelago 001',
 'sourceCatalogDigest':cat.get('catalogDigest'),'sourceWorkCount':len(works),
 'ownerCounts':dict(sorted(owner_counts.items())),'mappedRelationCount':len(rel_features),
 'coordinateSemantics':'conceptual Cartesian archive plane; no geographic location claim',
 'outputs':['render/works.geojson','render/owners.geojson','render/relations.geojson','render/archive-archipelago-001.svg','render/archive-archipelago-001.gpkg','render/archive-archipelago-001.png']
}
(OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,sort_keys=True))
