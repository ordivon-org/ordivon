# finance-okx consumer profile

This directory contains the network policy and migration artifacts for the `finance-okx` consumer. It is deliberately outside generic Network core.

Consumer-specific semantics include:

- two admitted provider paths;
- no direct fallback;
- exact destination fencing for the OKX public endpoint;
- all-provider loss fails closed;
- persistent non-production shadow lifecycle.

Current production consumer authority has **not** been transferred by this structural refactor. Finance migration remains frozen until explicitly resumed.

Historical R5/R6/R7 evidence is preserved under `history/`.
