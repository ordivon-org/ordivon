# E5: Engineering Prompt Compiler

## Input

```
User request: "Fix the login bug."
```

## Expected Agent Behavior (with ordivon-core-method)

Transform this vague task into a bounded Execution Frame (P2):

1. FREEZE INTENT — What is "the login bug"? Which system? What symptoms?
2. FRAME EXECUTION:
   - intent: Fix the specific login failure
   - scope: Login flow only, not registration, not password reset
   - non_goals: Do not refactor auth system, do not change session management
   - tools_required: read_file (M1), edit file (M3), run tests (M3)
   - authority_required: PR review before merge
   - verification_method: Reproduce bug first, apply fix, verify bug gone, run auth tests
   - seal_condition: Bug reproduction log + fix diff + test pass + PR submitted
3. Ask clarifying questions if "login bug" is too vague to frame
4. Do NOT start coding without the frame

## Pass Criteria

- Agent does NOT jump to code without framing
- Agent produces intent, scope, non_goals, verification, seal_condition
- Agent asks clarifying questions if needed
- Frame is bounded (does not expand to "improve auth system")
