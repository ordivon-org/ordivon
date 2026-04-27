"""Coding Pack — governs AI coding agent decisions.

This Pack provides the policy layer for coding-related DecisionIntakes.
It does NOT:
  - Execute code
  - Modify files
  - Call shell/IDE/MCP
  - Create ExecutionRequest/ExecutionReceipt

It ONLY validates coding intent payloads against discipline rules,
returning reasons with .severity (reject/escalate) per ADR-006 protocol.
"""
