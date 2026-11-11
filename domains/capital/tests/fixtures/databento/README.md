These are upstream open-source **decoder conformance inputs**, NOT authorized
financial market data, not proof of ETF/US-equity execution, and not a source of
historically available quotes for Ordivon investment decisions.

- mbp-1.v3.dbn.zst and definition.v3.dbn.zst: exact files from
  https://github.com/databento/dbn/tree/a77693030595b8f29f6b4c58e63b1b1a9d899b3f/tests/data
  (Databento DBN repository, Apache-2.0).
- publishers-rc9.json: exact publisher metadata file from
  https://github.com/nautechsystems/nautilus_trader/blob/v2.0.0rc9/crates/adapters/databento/publishers.json
  (NautilusTrader project LGPL-3.0; project source tag v2.0.0rc9).

The original files are bound by SHA-256 in test_native_dbn.py; the DBN fixture's
quotes refer to CME ESH21 futures rather than SPY, and the definition fixture
contains MSFT, so the two sources must not be silently joined.
Runtime code never automatically promotes these bytes to authorized data.

Redistribution notices: the upstream publisher metadata derives from the
NautilusTrader v2.0.0rc9 source release; its verbatim GNU LGPL version 3 text
is included as `LICENSE-LGPL-3.0.txt` in this directory. The DBN fixture's
Apache-2.0 source license is identified above; the repository root `LICENSE`
contains the Apache-2.0 license text. These notices do not establish market
data entitlement, vendor endorsement or use rights for financial execution.
