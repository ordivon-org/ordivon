# Windows Real Chrome Network consumer

This consumer projects the existing Linux Network v2 provider-egress to Windows through WSL mirrored
localhost. It owns only browser web egress. Browser control, Chrome remote-debugging consent, and
ProviderEffect authority remain separate owners.

Current realization:
- namespace-local mixed proxy: 127.0.0.1:19780 inside nv2-browserless-prod;
- Windows-visible host relay: 127.0.0.1:19781;
- public IPv4 web egress only;
- private-address destinations rejected;
- IPv6 egress rejected for the current qualification envelope;
- no direct fallback.

The historical Browserless physical namespace name is a compatibility identifier for provider-egress,
not semantic Browserless ownership.
