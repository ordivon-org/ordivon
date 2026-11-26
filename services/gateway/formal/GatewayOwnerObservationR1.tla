---------------- MODULE GatewayOwnerObservationR1 ----------------
EXTENDS TLC

\* Gateway B03 models transient Owner status and source inventory qualification.
\* External availability, authentication, and real MCP effects are NOT modeled.
\* Stringified statuses stand for the JSON value classes, not Python booleans.
\* Inventory shape, target multiplicity, and optional context-list shape are
\* additional independent evidence obligations before a Ready projection.

Flags == {"true", "false", "string-false", "int-one", "missing"}
BooleanFlags == {"true", "false"}
InventoryShapes == {"list", "missing", "not-list"}
TargetCounts == {"none", "one", "duplicate"}
ContextShapes == {"missing", "list", "canonical-empty", "canonical-nonempty", "invalid"}

VARIABLES phase, observedConfigured, observedAvailable,
          inventoryShape, matchingTargets, contextShape,
          projectedAvailable, observationError
vars == <<phase, observedConfigured, observedAvailable,
          inventoryShape, matchingTargets, contextShape,
          projectedAvailable, observationError>>

Init ==
  /\ phase = "start"
  /\ observedConfigured = "missing"
  /\ observedAvailable = "missing"
  /\ inventoryShape = "missing"
  /\ matchingTargets = "none"
  /\ contextShape = "missing"
  /\ projectedAvailable = FALSE
  /\ observationError = FALSE

Observe ==
  /\ phase = "start"
  /\ \E c \in Flags:
       \E a \in Flags:
         \E inventory \in InventoryShapes:
           \E matches \in TargetCounts:
             \E contexts \in ContextShapes:
               /\ observedConfigured' = c
               /\ observedAvailable' = a
               /\ inventoryShape' = inventory
               /\ matchingTargets' = matches
               /\ contextShape' = contexts
  /\ phase' = "observed"
  /\ UNCHANGED <<projectedAvailable, observationError>>

ValidObservation ==
  /\ observedConfigured \in BooleanFlags
  /\ observedAvailable \in BooleanFlags
  /\ ~(observedConfigured = "false" /\ observedAvailable = "true")
  /\ inventoryShape = "list"
  /\ matchingTargets = "one"
  /\ contextShape # "invalid"
  /\ ~(contextShape = "canonical-empty" /\ observedAvailable = "true")

Project ==
  /\ phase = "observed"
  /\ phase' = "projected"
  /\ projectedAvailable' =
       (ValidObservation /\ observedConfigured = "true" /\ observedAvailable = "true")
  /\ observationError' = ~ValidObservation
  /\ UNCHANGED <<observedConfigured, observedAvailable,
                  inventoryShape, matchingTargets, contextShape>>

Stop ==
  /\ phase = "projected"
  /\ UNCHANGED vars

Next == Observe \/ Project \/ Stop
Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ phase \in {"start", "observed", "projected"}
  /\ observedConfigured \in Flags
  /\ observedAvailable \in Flags
  /\ inventoryShape \in InventoryShapes
  /\ matchingTargets \in TargetCounts
  /\ contextShape \in ContextShapes
  /\ projectedAvailable \in BOOLEAN
  /\ observationError \in BOOLEAN

NoFalsePositive ==
  (phase = "projected" /\ projectedAvailable) =>
    /\ observedConfigured = "true"
    /\ observedAvailable = "true"
    /\ ValidObservation
    /\ observationError = FALSE

MalformedObservationReported ==
  (phase = "projected" /\ ~ValidObservation) =>
    /\ projectedAvailable = FALSE
    /\ observationError = TRUE

NoAmbiguousOrInvalidInventoryReady ==
  (phase = "projected" /\
    (inventoryShape # "list" \/ matchingTargets # "one" \/ contextShape = "invalid" \/
     (contextShape = "canonical-empty" /\ observedAvailable = "true"))) =>
    /\ projectedAvailable = FALSE
    /\ observationError = TRUE

NeverAvailable ==
  ~(phase = "projected" /\ projectedAvailable)

\* Negative controls: truthiness coercion or legacy fallback over empty canonical inventory.
UnsafeProject ==
  /\ phase = "observed"
  /\ observedConfigured = "true"
  /\ (observedAvailable = "string-false" \/
       (observedAvailable = "true" /\ inventoryShape = "list" /\
        matchingTargets = "one" /\ contextShape = "canonical-empty"))
  /\ phase' = "projected"
  /\ projectedAvailable' = TRUE
  /\ observationError' = FALSE
  /\ UNCHANGED <<observedConfigured, observedAvailable,
                  inventoryShape, matchingTargets, contextShape>>

UnsafeNext == Next \/ UnsafeProject
UnsafeSpec == Init /\ [][UnsafeNext]_vars
===============================================================