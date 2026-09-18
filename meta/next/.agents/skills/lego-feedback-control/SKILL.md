---
name: lego-feedback-control
description: Apply feedback-control and state-space thinking to a LEGO system whose behavior evolves over time. Identify state, observations, reference goals, controllers, actuators/effects, feedback paths, disturbances, delays, estimation gaps, and robustness questions. Use for runtimes, agents, autonomous loops, recovery, resource regulation, adaptive systems, and other dynamic processes. Do not force control terminology onto static architecture.
compatibility: Cross-platform. This is a modeling/analysis lens, not a numeric controller-design package.
metadata:
  source-authority: MIT feedback control / standard control theory
  lego-theory-layer: docs/LEGO_THEORY_LAYER_R1.md
---

# LEGO Feedback Control Lens

Static nodes and edges are not enough when behavior depends on time and feedback.

## Procedure

1. Define the regulated outcome or reference signal.
2. Identify state variables that determine future behavior.
3. Separate true state from observable measurements.
4. Identify observers/estimators when state is only partially visible.
5. Identify controllers/decision makers.
6. Identify actuators/effect channels.
7. Trace feedback paths from effects back to observations.
8. Record delays, sampling cadence, stale observations and asynchronous boundaries.
9. Identify disturbances and model uncertainty.
10. Ask robustness questions:
    - what happens when observations are late or wrong?
    - what happens when an actuator fails?
    - can controllers fight each other?
    - can positive feedback produce runaway behavior?
    - what stabilizes recovery?
11. Propose bounded perturbation tests instead of assuming stability.

## Output

Produce:
- state inventory;
- observation map;
- controller/effect map;
- feedback loops;
- delay/disturbance list;
- stability/robustness hypotheses;
- candidate perturbation tests.

## Promotion law

Promote a result only when it reveals a durable responsibility, observation boundary, controller ownership, or contract needed by the architecture.

## Non-claims

A conceptual feedback diagram does not establish mathematical stability.

## Stop condition

Stop when the dynamic variables and feedback paths that affect the current design decision are explicit and testable.

Canonical local reference:
- docs/LEGO_THEORY_LAYER_R1.md
- knowledge/lessons/lego-theory-foundations-r1.md
