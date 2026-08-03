# Station Zero v3 DeepSeek Credential Pool

## Purpose

Station Zero does not bind its live Agent Provider to one API key. It discovers a local pool of independent DeepSeek credentials, assigns separate concurrency limits, routes work toward healthy capacity, and retains strict Candidate admission after every response.

The default credential source is:

```text
/root/.config/ordivon/secrets
```

Every regular file whose name starts with `deepseek` and ends with `.json` is considered. Existing files are additive. Adding `deepseek2.json` does not replace `deepseek.json` or `deepseek1.json`.

## Add another API key

Create a new file such as:

```text
/root/.config/ordivon/secrets/deepseek2.json
```

Use this schema:

```json
{
  "schemaVersion": 1,
  "id": "deepseek-2",
  "enabled": true,
  "apiKey": "REPLACE_WITH_THE_NEW_KEY",
  "baseUrl": "https://api.deepseek.com/v1",
  "model": "deepseek-v4-flash",
  "provider": "deepseek",
  "maximumConcurrency": 2,
  "weight": 1
}
```

Then restrict the file:

```bash
chmod 600 /root/.config/ordivon/secrets/deepseek2.json
```

`apiKey`, `baseUrl`, `model`, and `provider` are required. The remaining fields are optional:

- `id`: stable, non-secret evidence identity. The filename stem is used when omitted.
- `enabled`: set to `false` to keep a credential file present but excluded.
- `maximumConcurrency`: independent in-flight request limit for this key. When omitted, the process-wide per-credential default is used.
- `weight`: relative scheduling weight among otherwise equally healthy credentials. It does not bypass concurrency limits.

Do not copy one key into several files to simulate capacity. The pool fingerprints API keys in memory and counts a repeated key only once.

## Discovery and reload

The running service checks credential sources before Agent decisions. The default reload interval is 15 seconds. A newly created valid `deepseek*.json` file is admitted on a later decision after that interval; a restart is not normally required.

Reload is additive but fail-closed per credential:

- a valid new credential is added without historical catch-up traffic;
- a removed or disabled credential stops receiving new work after reload;
- a malformed, insecure, or incompatible new file is skipped while unrelated valid credentials remain available;
- if no valid credential remains, the pool becomes unavailable instead of using cached secret material;
- one missing source does not suppress valid credentials discovered from other configured sources;
- in-flight calls continue on the credential object with which they started.

## Scheduling and health

Credential selection is not fixed round-robin. The score considers:

- active, queued, and reserved work relative to that key's concurrency;
- consecutive failures;
- moving-average latency;
- weighted virtual runtime, initialized at the current pool position when a key is hot-added;
- temporary cooldown or permanent quarantine.

Failure handling:

- HTTP `429`: cool down only that key, respecting `Retry-After` within the configured maximum cooldown;
- HTTP `401` or `403`: quarantine that key until the API key changes or the process restarts;
- timeout, transport failure, or HTTP `5xx`: exponential per-key cooldown;
- malformed model output: reject the response and try other capacity, without treating the key as invalid;
- reported-model mismatch: quarantine the incompatible credential.

The default retry limit is automatic: `max(4, usable credential count × 2)`. Quarantined credentials do not inflate the retry budget. `ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS` overrides it when explicitly set.

## Runtime configuration

Enable the live Provider:

```bash
ORDIVON_GAME_V3_PROVIDER=deepseek pnpm start
```

Relevant variables:

```text
ORDIVON_GAME_V3_DEEPSEEK_SOURCES
ORDIVON_GAME_V3_DEEPSEEK_SECRETS
ORDIVON_GAME_V3_DEEPSEEK_CONCURRENCY
ORDIVON_GAME_V3_DEEPSEEK_RELOAD_INTERVAL_MS
ORDIVON_GAME_V3_DEEPSEEK_RETRY_BASE_DELAY_MS
ORDIVON_GAME_V3_DEEPSEEK_COOLDOWN_MAXIMUM_MS
ORDIVON_GAME_V3_DEEPSEEK_MAX_ATTEMPTS
ORDIVON_GAME_V3_DEEPSEEK_TIMEOUT_MS
ORDIVON_GAME_V3_DEEPSEEK_MAX_TOKENS
ORDIVON_GAME_V3_DEEPSEEK_THINKING
ORDIVON_GAME_V3_DEEPSEEK_TEMPERATURE
```

`ORDIVON_GAME_V3_DEEPSEEK_SOURCES` accepts a comma-separated mixture of files and directories. `ORDIVON_GAME_V3_DEEPSEEK_SECRETS` remains a compatibility alias. When neither is set, the default secrets directory is scanned.

Example with two directories and one explicit file:

```bash
ORDIVON_GAME_V3_DEEPSEEK_SOURCES=/root/.config/ordivon/secrets,/mnt/private/deepseek,/run/secrets/deepseek-emergency.json
```

## Security and evidence

Credential files must not be readable by group or other users. The pool never includes API keys or key fingerprints in Provider evidence. Evidence exposes only operational identities and health data such as credential ID, source filename, concurrency, call counts, latency, cooldown, and quarantine state.
