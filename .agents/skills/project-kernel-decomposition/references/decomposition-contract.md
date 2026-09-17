# Project Kernel Decomposition — report contract

Use this structure unless the target requires a clearly better equivalent.

## 0. Subject / evidence freeze
- project/product:
- exact repo revision or service/docs date:
- scope:
- primary sources:
- unknown/private implementation boundaries:

## 1. One-sentence model
**<one sentence>**

Not primarily: <misleading framing>.

## 2. Product shell / transferable kernel / mature substrates
| class | elements | evidence/notes |
|---|---|---|

## 3. Kernel graph
```text
<small architecture graph>
```

## 4. Responsibility map
| module | responsibility | durable truth | input | output | replaceable by |
|---|---|---|---|---|---|

## 5. State and identity model
| object | identity | lifecycle | persistence | owner | relations |
|---|---|---|---|---|---|

## 6. End-to-end control/effect flow
Show at least one complete vertical path.

## 7. Protocol and interface contracts
List minimal request/event APIs and standard protocol mappings.

## 8. Failure / durability / security boundaries
Include retry, cancellation, isolation, identity, policy, ambiguous effects, and recovery.

## 9. Mechanisms worth retaining
Explain each mechanism independently of product branding.

## 10. What not to copy
Name overlapping product shell, private ontology, duplicated substrates, and accidental complexity.

## 11. Minimal clone
```text
<minimum modules>
```

### Minimal build order
1. ...

### Behavioral acceptance
1. ...

## 12. Mapping to the local architecture
For every module: ADOPT / ADAPT / EXTRACT / ON_DEMAND / REJECT.

## 13. Project-study acceptance
- ONE-SENTENCE TEST:
- MODULE-COMPLETENESS TEST:
- MINIMAL-CLONE SPEC TEST:
- BEHAVIORAL-ACCEPTANCE TEST:

## Verdict
One concise sentence describing what remains after decomposition.
