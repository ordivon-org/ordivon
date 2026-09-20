# Multi-region configuration repair

Repair `pipeline.py` so that:

- `DEFAULT_TIMEOUT_SECONDS` is `30` instead of `15`.
- `retry_limit()` returns `3` instead of `1`.
- `execution_mode()` remains exactly `"safe"`.

Preserve all public names and modify only `pipeline.py`.
