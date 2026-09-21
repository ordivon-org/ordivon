# QuickFIX/n 1.14.1 qualification oracle

This directory is not part of the canonical Ordivon Capital runtime.

QuickFIX/n 1.14.1 is retained as the current differential oracle for the bounded,
sessionless FIX 4.4 NewOrderSingle TagValue projection. A 2026-09-21 matrix of
120 cases covering BUY/SELL, DAY/GTC/IOC, multiple decimal scales, symbols,
destinations, sequence numbers, and timestamps matched the local projector byte
for byte (120/120, zero mismatches).

The canonical local projector does not implement a FIX session, transport,
BodyLength/CheckSum wire framing, resend logic, sequence recovery, dictionary
negotiation, or broader message types. Any such future contract must reopen
qualification and should prefer a mature FIX engine unless a new comparison
shows otherwise.
