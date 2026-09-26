# AI Red-Team Foundry R9 — Vulnerability Family Ledger

Status: EXPERIMENTAL SECURITY STUDY / STACKED SUCCESSOR TO R8 / NOT PRODUCTION SECURITY AUTHORITY
Date: 2026-09-27

## Objective

R9 separates provider taxonomy from root-cause research taxonomy. PyRIT techniques, garak probes, benchmark
behavior IDs, and community jailbreak names remain provider-native labels. A vulnerability family exists only
when an explicit root-cause hypothesis and an evidence-bound assignment connect one or more R8 results.

```text
R8 SearchResultRef(s)
        |
        +--> provider attack labels  (surface taxonomy)
        |
        +--> FamilyAssignment -------+
                                     v
                              FamilyHypothesis
                                     |
                                     v
                           VulnerabilityFamilyLedger
                                     |
                                     v
                              DiscoveryFrontier
```

## Core invariants

- provider `attack_family` never becomes a vulnerability family automatically;
- one result may have at most one active family assignment in one ledger build;
- assignment method and method reference are explicit (`manual_analysis`, `deterministic_rule`, or `external_clusterer`);
- assignment evidence is digest-bound;
- family identity is derived from the root-cause hypothesis, not from provider labels or current member count;
- adding another member to the same hypothesis does not rename the family;
- different provider attack labels may belong to one family, and identical provider labels may be assigned to different families;
- provider-positive count and observer-bound count are descriptive evidence metadata, not Security standing;
- unassigned results remain visible instead of being silently forced into a cluster;
- the per-search discovery frontier is deterministic and monotone by first-seen root-cause family.

R9 deliberately does not implement a bespoke clustering algorithm. Mature external clusterers may be used via
`external_clusterer`, but the exact method/config/evidence must remain referenced. This keeps Ordivon focused
on identity, provenance, falsifiability, and replay rather than owning generic clustering mechanics.

## Verification

```bash
python3 -m unittest discover -s studies/security/ai-redteam-foundry-r9/tests -p 'test_*.py' -v
python3 studies/security/ai-redteam-foundry-r9/scripts/run_family_ledger_fixture.py
python3 -m compileall -q studies/security/ai-redteam-foundry-r9
```
