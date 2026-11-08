---------------- MODULE GatewayOwnerObservationR1 ----------------
EXTENDS TLC

\* Gateway B03 only models transient Owner status normalization.
\* External availability, authentication, and real MCP effects are NOT modeled.
\* Stringified statuses stand for the JSON value classes, not Python booleans.

Flags == {"true", "false", "string-false", "int-one", "missing"}
BooleanFlags == {"true", "false"}

VARIABLES phase, observedConfigured, observedAvailable,
          projectedAvailable, observationError
vars == <<phase, observedConfigured, observedAvailable,
          projectedAvailable, observationError>>

Init ==
  /\ phase = "start"
  /\ observedConfigured = "missing"
  /\ observedAvailable = "missing"
  /\ projectedAvailable = FALSE
  /\ observationError = FALSE

Observe ==
  /\ phase = "start"
  /\ \E c \in Flags:
       \E a \in Flags:
         /\ observedConfigured' = c
         /\ observedAvailable' = a
  /\ phase' = "observed"
  /\ UNCHANGED <<projectedAvailable, observationError>>

ValidObservation ==
  /\ observedConfigured \in BooleanFlags
  /\ observedAvailable \in BooleanFlags
  /\ ~(observedConfigured = "false" /\ observedAvailable = "true")

Project ==
  /\ phase = "observed"
  /\ phase' = "projected"
  /\ projectedAvailable' =
       (observedConfigured = "true" /\ observedAvailable = "true")
  /\ observationError' = ~ValidObservation
  /\ UNCHANGED <<observedConfigured, observedAvailable>>

Stop ==
  /\ phase = "projected"
  /\ UNCHANGED vars

Next == Observe \/ Project \/ Stop
Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ phase \in {"start", "observed", "projected"}
  /\ observedConfigured \in Flags
  /\ observedAvailable \in Flags
  /\ projectedAvailable \in BOOLEAN
  /\ observationError \in BOOLEAN

NoFalsePositive ==
  (phase = "projected" /\ projectedAvailable) =>
    /\ observedConfigured = "true"
    /\ observedAvailable = "true"
    /\ observationError = FALSE

MalformedObservationReported ==
  (phase = "projected" /\ ~ValidObservation) =>
    /\ projectedAvailable = FALSE
    /\ observationError = TRUE

NeverAvailable ==
  ~(phase = "projected" /\ projectedAvailable)

\* Negative control: model accidental Python truthiness coercion of "false".
UnsafeProject ==
  /\ phase = "observed"
  /\ observedConfigured = "true"
  /\ observedAvailable = "string-false"
  /\ phase' = "projected"
  /\ projectedAvailable' = TRUE
  /\ observationError' = FALSE
  /\ UNCHANGED <<observedConfigured, observedAvailable>>

UnsafeNext == Next \/ UnsafeProject
UnsafeSpec == Init /\ [][UnsafeNext]_vars
===============================================================