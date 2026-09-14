# Clock Quality Repair — 2026-09-14

Clock quality is now qualified for private-execution timing, without changing execution authority.

Windows Time was repaired through an explicit UAC-approved administrator PowerShell flow. Before mutation, the complete `W32Time` registry subtree was exported to `C:\ProgramData\Ordivon\backups\w32time-before-20260914-102212.reg`. `w32time` remains the Windows authority, starts automatically, and now uses the observed-working peers `time.cloudflare.com`, `time.apple.com`, and `time.aws.com` in NTP client mode. Windows reported leap indicator 0, stratum 4, and a successful synchronized source instead of Local CMOS Clock. Windows-native stripchart measurements were within roughly ±9 ms.

WSL was separately found to remain about 1.02 seconds ahead of the repaired Windows host. The kernel already exposes `/dev/ptp_hyperv`, a Hyper-V host PTP clock, so no second NTP authority was introduced. The mature `linuxptp` package was installed and `phc2sys` is now enabled as `ordivon-wsl-host-clock-sync.service`, continuously synchronizing `CLOCK_REALTIME` from `/dev/ptp_hyperv`. Direct host-PTP versus WSL system-clock difference fell from about 1022 ms to about 2 ms.

Fresh external validation after the repair produced six successful measurements across three batches using Cloudflare, Apple, and AWS NTP sources. The maximum observed absolute offset was 47.1 ms, far inside the frozen 1000 ms gate. UDP/123 timeouts remain transport noise and do not alter the successful measurements.

This graduates clock timing only. `config/execution_authority.json` remains NON_LIVE, external financial writes remain NOT_ADMITTED, and no private/demo/live execution is authorized by this repair.
