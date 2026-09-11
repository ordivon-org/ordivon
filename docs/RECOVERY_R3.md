# R3 live data-plane recovery

Date: 2026-09-11

## Failure discovered during the first recovery attempt

The first crash test killed the permanent `network-v2-singbox.service` process and correctly observed a new PID plus an incremented systemd restart counter. An immediate HTTPS request still failed.

Journal timing showed why: systemd declared the replacement process started before sing-box had completed route discovery and opened `127.0.0.1:28080`. In the observed run, the restart delay was about two seconds and the listener became ready roughly 0.68 seconds after the new service start event.

Therefore `ActiveState=active` is not application readiness.

## R3 correction

Recovery admission now requires functional readiness, not process state:

1. establish a working HTTPS request through the live sing-box proxy;
2. record the current PID and restart counter;
3. kill the exact sing-box process with SIGKILL;
4. observe a real request failure window;
5. wait for a different PID **and** a successful HTTPS request through the proxy;
6. prove the systemd restart counter increased;
7. prove blackbox_exporter reports `probe_success=1` for `127.0.0.1:28080` using the standard `tcp_connect` module;
8. prove Prometheus ingests that sing-box-specific probe.

The Prometheus configuration now has a dedicated `blackbox-singbox` job. This closes a prior observability gap where the monitoring plane could remain green while the sing-box proxy itself was unavailable.

Run:

```sh
task smoke:recovery-live
```

## Semantic correction

`verify:live` no longer requires `NRestarts=0`. A non-zero restart history is not current drift if the exact source generation is installed and the service is currently functional. Recovery history belongs in evidence/operations, not in the definition of live currentness.

R3 proves automatic recovery of the local R0 sing-box process. It does not yet prove machine reboot recovery, provider-tunnel recovery, multi-path failover, or long-running soak.
