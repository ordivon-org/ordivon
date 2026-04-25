# PHASE 5 DEFERRED — not implemented

     1|> **Status: Not implemented — placeholder only. The models.py and service.py described below do not exist yet. Trace logic currently lives in `apps/api/app/api/v1/traces.py`.**
     2|
     3|# State Trace
     4|
     5|`state/trace/` owns main-chain query bundles and trace resolution rules.
     6|
     7|## Current Focus
     8|
     9|- workflow trace
    10|- recommendation trace
    11|- review trace
    12|- honest `present / missing / unlinked` relation semantics
    13|
    14|## Read These Files First
    15|
    16|- `models.py`
    17|  - `TraceReference`
    18|  - `TraceBundle`
    19|- `service.py`
    20|  - trace root entrypoints
    21|