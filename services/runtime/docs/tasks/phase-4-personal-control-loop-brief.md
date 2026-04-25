# Phase 4 Brief: Personal Control Loop

> **Date**: 2026-04-24
> **Goal**: Establish a functional, high-discipline control loop for personal financial trading decisions, without delegating execution to the AI.

## Objectives

Phase 4 focuses on using financial trading discipline as the first high-stress test for the AegisOS (PFIOS) generic control loop. The objective is to force every impulsive trade idea into a structured intake process, subject it to governance checks, track its outcome, and force a review to generate knowledge.

The system should act as a strict risk manager and journal, NOT an automated trading bot.

## Scope & Deliverables

1.  **Decision Intake (Batch 1)**
    - Complete the `domains/decision_intake` domain.
    - Implement strict validation for trading theses, stop losses, and risk units.
    - Capture psychological states (e.g., revenge trading, chasing).
2.  **Governance Gate (Batch 2)**
    - Implement `trading_discipline.py` policy within the `RiskEngine`.
    - Handle rejection, escalation, and execution paths based on intake parameters.
3.  **Action Plan Receipt (Batch 3)**
    - Generate a "plan-only" receipt.
    - Clearly separate the intention to act from the actual broker execution.
4.  **Outcome + Review Checklist (Batch 4)**
    - Define a finance-specific outcome overlay (did they move the stop loss? did they size up a loser?).
    - Enforce a strict review checklist to close out trades.
5.  **Knowledge Feedback + Candidate Rules (Batch 5)**
    - Track recurring mistakes (e.g., "moved stop loss twice this month").
    - Generate `CandidateRule`s based on these recurring patterns for user review.
6.  **30-Day Real Use Protocol (Batch 6)**
    - Finalize the testing protocol and usage tracking metrics.

## Strict Boundaries (What we are NOT doing)

-   **NO Broker Integration**: We are not connecting to Binance, Interactive Brokers, or any other exchange. Execution remains manual.
-   **NO Automated Action**: The system does not place orders. It only validates the *intention* to place an order.
-   **NO Multi-Agent Swarms**: The system remains a single-agent orchestrator managing discrete workflows.
-   **NO Auto-Promotion of Rules**: Candidate rules remain advisory and cannot automatically mutate system policies without explicit human approval.
-   **NO Repository Renaming**: We will use "AegisOS" in docs, but the repo stays `financial-ai-os` and code imports stay as-is to avoid merge conflict hell.
