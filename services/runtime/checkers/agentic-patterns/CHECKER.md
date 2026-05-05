---
gate_id: agentic_patterns
display_name: Agentic Pattern Detection
layer: L7C
hardness: hard
purpose: Detect ADP-1 agentic pattern risks: capability-authority collapse, evidence laundering, READY overclaim
protects_against: "Capability-as-authorization, READY-as-approval, evidence laundering, CandidateRule promotion, MCP confused deputy, benchmark overclaim"
profiles: ['full']
timeout: 180
tags: [governance, verification]
---

# Agentic Pattern Detection

## Purpose

Detect ADP-1 agentic pattern risks: capability-authority collapse, evidence laundering, READY overclaim

## Protects Against

Capability-as-authorization, READY-as-approval, evidence laundering, CandidateRule promotion, MCP confused deputy, benchmark overclaim

## Usage

```bash
python -m ordivon_verify run agentic_patterns
```
