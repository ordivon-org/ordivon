# Portfolio Risk Budget Registration R1

P4 now consumes one explicit owner-principal registration at `config/portfolio_risk_budget.json`.
The registration is validated by JSON Schema before OPA evaluates any limits.

`UNSET` is the canonical current state. All five limits must remain null in that state, so Market Capital cannot infer risk tolerance from account size, past trades, model outputs, or assistant judgement.

`ACTIVE` is admitted only when the Owner Principal explicitly supplies all five values:

- `maxGrossToEquity`
- `maxLargestPositionGrossShare`
- `minAvailableEquityRatio`
- `shockMagnitudePct`
- `maxEquityLossPctAtShock`

The JSON registration owns declared preferences only. OPA remains the policy decision owner. Portfolio calculations remain read-only and do not size or submit orders.
