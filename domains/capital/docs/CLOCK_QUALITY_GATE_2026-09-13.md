# Market Capital Clock Quality Gate

## Standing

`FAIL_PRIVATE_EXECUTION_CLOCK_GATE`

Market Capital public/shadow observation may continue because timing comparisons use monotonic request intervals and exchange/server timestamps. Private account access and every order-capable lane remain blocked.

## Evidence

Three independent one-shot NTP queries agreed that the local WSL clock is ahead of external time by roughly 2.65–2.68 seconds, with less than 30 ms spread between sources. Earlier OKX/Binance server-time measurements showed about 2.20 seconds of local-ahead offset, so the drift is not assumed stable.

WSL is configured with mirrored networking and has no independent NTP daemon. `systemd-timesyncd` is inactive because of the virtualization condition. A read-only attempt to inspect Windows Time through Ordivon Runtime's `windows_native` target failed before dispatch because the WSL/Windows VSOCK runtime-context probe timed out.

## Authority decision

The Windows host / WSL virtual clock remains the system clock authority. Market Capital will **not**:

- start chrony/ntpsec inside mirrored WSL as a competing system time authority;
- call `date -s`, `hwclock`, or equivalent to mutate system time as a trading workaround;
- forge application timestamps to conceal a failing host clock gate.

Graduation requires a supported Windows time path plus a fresh multi-source absolute offset <= 1000 ms, repeated immediately before any future private/demo execution session.
