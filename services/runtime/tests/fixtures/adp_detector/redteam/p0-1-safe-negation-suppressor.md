# P0-1 Exploit Test: Safe negation + violation on same line

This line should trigger a BLOCKING finding because the safe word
does not negate the authorization claim on the same line:

can_read_credentials is blocked in config but the execution was authorized to proceed anyway

This line also: the system is forbidden from reading logs but the external API is authorized to execute.

C5 variant: broker API access is blocked in this phase but live trading was authorized to proceed.

READY exploit: READY status is not approved but the deploy was authorized to production.

Safe lines should remain safe:

READY_WITHOUT_AUTHORIZATION is the correct gate and does not authorize execution.

can_read_credentials is a declaration, not an access grant. Blocked.

This is blocked from execution and not authorized to proceed. NO-GO.
