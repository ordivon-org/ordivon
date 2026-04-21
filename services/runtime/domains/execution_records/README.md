# Execution Records Domain

`domains/execution_records/` owns the persisted request/receipt objects used by the Execution layer.

## Owns

- `ExecutionRequest`
- `ExecutionReceipt`
- execution record repository/service logic

## Does Not Own

- action-family semantics
- governance approval
- product-facing responses
