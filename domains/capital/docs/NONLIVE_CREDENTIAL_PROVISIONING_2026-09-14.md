# Non-live Credential Provisioning — 2026-09-14

The user explicitly authorized Demo/Testnet external writes. This authorization does not extend to live or real-money execution.

No independent non-live exchange API credential was found locally. Existing OKX observer and Binance observer/executor credentials are live-account credentials and are forbidden from reuse in Demo/Testnet qualification.

Provisioning status:

- Binance Spot Testnet: an independent Ed25519 keypair is generated under `/root/.config/ordivon/secrets/binance/testnet`. The private key never enters the repository. The public key must be registered on Binance Spot Test Network; Binance then issues the Testnet API key, which must be stored as `api_key` in that directory.
- OKX Demo: `/root/.config/ordivon/secrets/okx/demo` is reserved. OKX requires a Demo Trading API key created in the Demo Trading UI. The resulting demo profile must be stored as `config.toml` with `demo=true` and mode 0600.

Until at least one server-issued non-live credential exists and passes environment verification, no demo/testnet order is submitted.
## Local secure install

After the exchange-side key exists, install it without putting credentials on the command line:

- `./scripts/install-nonlive-credential okx-demo`
- `./scripts/install-nonlive-credential binance-testnet`

The script uses hidden terminal input and writes only to the isolated `.config/ordivon/secrets/...` non-live roots with mode 0600. It has no live mode.
