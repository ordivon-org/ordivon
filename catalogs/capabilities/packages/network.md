# Package: Network

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Provide or restore communication that satisfies the real workload's reachability, identity, path, performance, isolation and reliability requirements, with enough evidence to distinguish a genuine fix from a false green.

Network normally acts as an enabling capability. It becomes the entity of interest only when the network/service itself is what is being engineered or evaluated.

## Mature external knowledge/capability owners

- IETF Internet Standards, Best Current Practices and protocol RFCs for DNS, IP, transport, HTTP/TLS/QUIC and related concerns;
- operating-system/native routing, DNS, firewall, VPN/tunnel and proxy implementations;
- provider/VPN/cloud/network-native mechanisms;
- standard diagnostic tools such as DNS queries, route/path probes, packet/throughput tests and protocol-specific clients;
- RIPE Atlas or equivalent external vantage-point measurements when outside-network evidence is needed.

Do not build a custom network stack merely to compose or diagnose these mechanisms.

## Observed local capability

- Network v2 (`/root/projects/ordivon@dac057c6668c83e085bb3ae3b910866fd349b4eb`, owner path `platform/network`) with `LOCAL_WSL_GRADUATED` standing and an independent standard-Linux reference lane;
- `dig`, `nslookup`;
- `ping`, `tracepath`, `mtr`;
- `ip`, `iperf3`;
- `curl`, `wget`, OpenSSL;
- Windows/WSL/VPN/proxy/tunnel experience and existing falsification cases;
- Runtime evidence capture for exact probes.

## Concrete current gaps

No generic network capability gap is proven.

Packet capture, BGP/ASN analysis, external probes, protocol-specific tooling, alternate VPN transports or cloud network tooling remain on-demand.

## Acceptance workload

The next real network failure is the acceptance case:

`workload requirement -> classify failure -> select minimum mature mechanism -> reproduce -> repair/route -> falsify likely false greens -> verify the actual workload`

When relevant, test DNS, path identity, IPv4/IPv6, Windows/WSL divergence, MTU, HTTP/TLS behavior, throughput, sustained transfer/resume and ambient-state dependency rather than relying on a single successful ping or small request.

## External references

- RFC Editor / Internet standards corpus: https://www.rfc-editor.org/
- IETF Datatracker: https://datatracker.ietf.org/
- RIPE Atlas: https://www.ripe.net/analyse/internet-measurements/ripe-atlas/
