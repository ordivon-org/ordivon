# ZTE U30 Pro (MU5358): read-only performance observation

This is a vendor-specific Network Provider adapter, NOT a new network
controller, packet stack, QoS scheduler or firmware replacement.

Evidence target: ZTE U30 Pro, MU5358, U30ProHW1.0, B24.
The source GET API follows the device's normal same-origin HTTPS AJAX
request. Only a strict performance-field allowlist is projected. No radio
writes, no admin login, no AP password/SSID queries, no SIM or IMEI data.

## Use

    cd platform/network
    python3 providers/zte-u30pro/observe.py
    python3 providers/zte-u30pro/observe.py --no-probes
    python3 -m pytest -q tests/test_zte_u30pro_observer.py

The default low-impact probes use 10 gateway ICMP pings plus two DNS queries.
There is NO cellular throughput load. The observer explicitly reports UNKNOWN
for unavailable values and refuses to attest to a different device.

## Evaluation method (external mature tools)

1. Verify the actual USB, Wi-Fi and route interfaces independently.
   These interfaces use the same 192.168.0.0/24 gateway, not separate WANs.
2. Use iperf3 for a controlled LAN/host path, keeping the test endpoint
   separate from the gateway's management service.
3. Use Flent RRUL with a consenting remote server to measure sustained
   end-to-end loaded latency vs idle, not only headline speed.
4. Obtain actual channel width, neighbor airtime and 5G NR band/quality.
   Compare two 5 GHz channel blocks by paired measurements when OEM UI
   permits a normal reversible channel change.
5. Only after proven loaded queueing at the actual forwarding bottleneck,
   consider existing CAKE and CAKE-autorate. Host fq_codel does not govern
   5G router queues or devices that bypass the host.
6. Preserve firmware provenance and compare before/after. Never assert
   UNKNOWN means false, no data, or confirmed improvement.

References: RFC 6349 TCP throughput methodology; Cisco Meraki RRM;
Flent RRUL; RFC 8290 fq_codel; OpenWrt SQM / CAKE-autorate.

No live device configuration, authentication or installation is performed.
