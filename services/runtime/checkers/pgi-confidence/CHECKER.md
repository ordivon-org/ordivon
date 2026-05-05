---
gate_id: pgi_confidence_assessment
display_name: PGI Confidence Assessment Validator
layer: L9F
hardness: escalation
purpose: Validate PGI confidence assessments: calibration, base rate, uncertainty quantification
protects_against: "Overconfidence, missing base rate, confidence without evidence window"
profiles: ['full']
timeout: 30
tags: [governance, verification]
---

# PGI Confidence Assessment Validator

## Purpose

Validate PGI confidence assessments: calibration, base rate, uncertainty quantification

## Protects Against

Overconfidence, missing base rate, confidence without evidence window

## Usage

```bash
python -m ordivon_verify run pgi_confidence_assessment
```
