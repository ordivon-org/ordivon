# Network N03/N04 Supply-Chain Readiness R1

Natural owner: Network NS2. Concrete consumer:
consumers/supply-chain/ready.sh. This is a small bounded official TLA+/TLC
model through Runtime's already digest-verified public upstream tool, not
a new stack, checker, proxy, authority, or LEGO registry.

The five required origins each demand CONNECT=200 and an allowed HTTP status
from one curl attempt. Separately the unknown destination must yield an
explicit proxy-level CONNECT=403; HTTP 403 after successful CONNECT=200,
proxy-auth 407, and transport-error CONNECT=000 must not be conflated.
One shared deadline applies to all probes. The five negative reachability
probes show the model admits READY and the independent failure modes, so
the safety proof is not vacuous.

The concrete consumer tests/test_readiness_shared_budget.py and other
Network owner tests still run independently; symbolic status labels do
not prove actual curl behavior or live network policy. No proof is claimed
about DNS, cross-namespace bypass, malicious processes, proxy identity,
real upstream/TLS, Windows/WSL, or user-domain success. NS2 stays PROPOSED.

Under CEGAR, inspect whether an abstract counterexample is a real
consumer behavior before fixing implementation or refining the model.
