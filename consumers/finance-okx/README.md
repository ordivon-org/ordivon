# finance-okx consumer profile

This directory contains the network policy and migration artifacts for the `finance-okx` consumer. It is deliberately outside generic Network core.

Consumer-specific semantics include:

- two admitted provider paths;
- no direct fallback;
- exact destination fencing for the OKX public endpoint;
- all-provider loss fails closed;
- persistent production systemd lifecycle after explicit authority cutover.

Network v2 is the intended production network authority. Consumer cutover is explicit and must bind the exact source-owned authority contract before legacy transport retirement.

Historical R5/R6/R7 evidence is preserved under `history/`.
