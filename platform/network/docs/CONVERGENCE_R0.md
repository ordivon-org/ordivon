# R0 live convergence

Date: 2026-09-11

R0 previously had a source-green/live-red failure: commit `6bec498` granted `AF_NETLINK` to the sing-box systemd sandbox, while the installed unit still lacked that address family. The permanent service therefore restarted continuously even though isolated smoke tests passed.

The R0 convergence boundary now requires all of the following in one explicit host operation:

1. validate source configuration before installation;
2. install exact config and systemd bytes from the repository;
3. reload systemd and restart the four permanent R0 services;
4. keep Toxiproxy disabled outside deliberate fault tests;
5. prove live bytes equal source bytes;
6. prove DNS, sing-box, blackbox exporter and Prometheus are active;
7. prove the permanent sing-box data plane can carry HTTPS;
8. prove a live black-box probe returns `probe_success=1`;
9. prove Prometheus contains successful probe evidence.

Run:

```sh
task converge:r0
```

This closes only host-generation convergence for R0. It does not admit provider VPN paths, packet-level netem, containerlab, multi-path failover, reboot recovery, soak, external-vantage corroboration or legacy workload migration.
