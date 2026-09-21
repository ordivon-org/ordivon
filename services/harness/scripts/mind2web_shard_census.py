import collections
import json
import sys
import zipfile

zip_path, shard = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(zip_path) as z, z.open(shard, pwd=b"mind2web") as f:
    data = json.load(f)

ops = collections.Counter()
cards = []
websites = set()
domains = set()
actions = pos_empty = pos_multi = 0

for task in data:
    websites.add(task.get("website"))
    domains.add(task.get("domain"))
    for action in task.get("actions", []):
        actions += 1
        ops[(action.get("operation") or {}).get("op")] += 1
        pos = action.get("pos_candidates") or []
        neg = action.get("neg_candidates") or []
        pos_empty += int(not pos)
        pos_multi += int(len(pos) > 1)
        cards.append(len(pos) + len(neg))

print(json.dumps({
    "shard": shard,
    "tasks": len(data),
    "actions": actions,
    "ops": dict(ops),
    "posEmpty": pos_empty,
    "posMulti": pos_multi,
    "candidateCards": cards,
    "websites": sorted(x for x in websites if x is not None),
    "domains": sorted(x for x in domains if x is not None),
}, separators=(",", ":")))
