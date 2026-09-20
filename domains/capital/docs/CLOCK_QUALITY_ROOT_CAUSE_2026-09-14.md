# Clock Quality Root Cause — 2026-09-14

The private-execution clock gate remains failed, but the diagnosis is now narrower than the initial WSL-only observation.

Windows-native inspection is functional. `w32time` is configured for `time.windows.com,0x9` and uses the built-in trigger-start model, but the service is currently stopped. Windows Time event history records NtpClient receiving invalid time data from `time.windows.com`; operational state has fallen back to `Local CMOS Clock` and shows no successful synchronized source. The built-in `ForceSynchronizeTime` task exists under `LOCAL SERVICE / Highest`, but the Runtime limited Windows token cannot start `w32time` or trigger that task. Runtime also correctly refuses `windowsAuthority=elevated` because the current provider token has no already-elevated authority to select.

Fresh external NTP evidence shows the clock problem is not a stable application offset. The 2026-09-13 audit observed the local clock ahead by roughly 2.65–2.68 seconds. The 2026-09-14 audit observed the local clock behind by roughly 2.90–2.92 seconds across Cloudflare, Google, Apple, and AWS sources. Some UDP/123 probes also time out intermittently. The sign reversal means application timestamp compensation is specifically rejected.

The safe remediation boundary is therefore an administrator-authorized Windows Time repair followed by fresh multi-source validation. Market Capital must not start a competing WSL NTP daemon, mutate WSL time directly, or loosen the 1000 ms private-execution gate.
