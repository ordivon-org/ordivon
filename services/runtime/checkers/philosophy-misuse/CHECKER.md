---
gate_id: philosophy_misuse
display_name: Philosophy Misuse Detection
layer: L9A
hardness: hard
purpose: Detect philosophical language rationalizing overwork, gambling, evidence bypass, emotional suppression, or responsibility avoidance
protects_against: "Long-termism→overwork, freedom→gambling, discipline→suppression, meaning→bypass, non-attachment→avoidance, pragmatism→shortcuts"
profiles: ['pr-fast', 'full']
timeout: 60
tags: [governance, verification]
---

# Philosophy Misuse Detection

## Purpose

Detect philosophical language rationalizing overwork, gambling, evidence bypass, emotional suppression, or responsibility avoidance

## Protects Against

Long-termism→overwork, freedom→gambling, discipline→suppression, meaning→bypass, non-attachment→avoidance, pragmatism→shortcuts

## Usage

```bash
python -m ordivon_verify run philosophy_misuse
```
