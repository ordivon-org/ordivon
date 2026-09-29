# LEGO Theory Foundations R1

Date: 2026-09-18
Status: SOURCE-GROUNDED FOUNDATION SNAPSHOT

## Purpose

Record the mature external lineages used by LEGO Theory Layer R1. This is a source map, not a claim that Ordivon invented or subsumes these disciplines.

## Systems Engineering / Systems Thinking

Primary use in LEGO:
- whole-system framing;
- environment, boundaries and interfaces;
- decomposition while preserving relationships;
- lifecycle awareness;
- avoidance of local-component optimization being mistaken for system optimization.

Authoritative starting points:
- INCOSE, About Systems Engineering: https://www.incose.org/about-systems-engineering/
- INCOSE Systems Engineering principles/resources.

Key adoption rule:
A system is not merely a bag of nodes. Relationships with other elements and the environment are first-class.

## Design Structure Matrix (DSM)

Primary use in LEGO:
- compact dependency representation;
- clustering;
- exposing cycles, integrative elements and missing interfaces;
- checking whether a human decomposition matches interaction structure.

Authoritative starting points:
- Steven D. Eppinger and Tyson R. Browning, Design Structure Matrix Methods and Applications, MIT Press.
- MIT Sloan, The Design Structure Matrix: Helping to See Complexity in Systems.
- MIT OpenCourseWare, System Project Management, DSM lecture.

Key adoption rule:
Use DSM as a derived diagnostic model. A cluster suggests a candidate module; it does not itself own architecture truth.

## Feedback Control / State-Space Thinking

Primary use in LEGO:
- dynamic state;
- feedback;
- state estimation/observation;
- controllers and actuators;
- delay, disturbances, model uncertainty and robustness.

Authoritative starting points:
- MIT OpenCourseWare 16.30 Feedback Control Systems.
- Karl J. Åström and Richard M. Murray, Feedback Systems.

Key adoption rule:
For dynamic systems, input/output edges are insufficient. Explicitly model state, observation and feedback.

## STAMP / STPA

Primary use in LEGO:
- system-level loss/hazard reasoning;
- unsafe interactions among otherwise functioning components;
- control structure;
- safety/security constraints;
- causal scenarios beyond single root-cause thinking.

Authoritative starting points:
- MIT Partnership for Systems Approaches to Safety and Security.
- Nancy Leveson and John Thomas, STPA Handbook.

Key adoption rule:
Component correctness does not imply system safety. Analyze control actions and constraints at the system level.

## Evidence boundary

These disciplines are adopted as external intellectual substrates.

Ordivon may:
- encode compact task procedures;
- produce compatible derived models;
- combine outputs across lenses.

Ordivon must not:
- rename mature concepts to create fake novelty;
- treat summaries as replacements for the disciplines;
- claim equivalence to professional analysis without sufficient rigor;
- force every project through every lens.

## R1 hypothesis

The first-wave combination is intentionally complementary:

Systems Engineering -> frame the system.
DSM -> test the decomposition.
Feedback Control -> model dynamic regulation.
STPA -> test unsafe control/interactions.

The hypothesis must be tested on real Ordivon domains before any part is promoted into the shared planning schema.
