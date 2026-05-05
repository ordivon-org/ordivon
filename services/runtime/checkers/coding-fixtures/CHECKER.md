---
gate_id: coding_fixtures
display_name: Coding Discipline Fixtures
layer: L5D
hardness: hard
purpose: Validate coding intake test fixtures — task_description, file_paths, required fields
protects_against: "Missing intake fields, invalid fixture JSON, forbidden path fixtures without reject expectation"
profiles: ['full']
timeout: 30
tags: [coding, fixtures, intake, discipline]
---

# Coding Discipline Fixtures Checker

## Purpose

Validates that coding discipline test fixtures are well-formed.
Each fixture exercises the CodingDisciplinePolicy gates.

## Governed Objects

`tests/unit/packs/test_coding_policy.py` — Coding Pack policy tests.
