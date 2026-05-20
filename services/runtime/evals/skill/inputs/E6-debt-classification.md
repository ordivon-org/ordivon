# E6: Debt Classification

## Input

Classify these four issues found during code review:

1. A typo in an error message: "conection" instead of "connection"
2. A checker script hardcodes a list of document IDs, requiring edits in
   two places when a new document is added
3. Infrastructure health checks only run manually, with no scheduled automation
4. The AOS subsystem has no integration tests, and adding them would require
   restructuring the test harness

## Task

Classify each as A1 (direct fix), A2 (logic refinement), A3 (system redesign),
or A4 (debt formalize). Give brief reasoning for each.
