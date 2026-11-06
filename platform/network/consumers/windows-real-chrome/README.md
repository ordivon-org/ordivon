# Windows Real Chrome egress

A public-web HTTP proxy inside the Gluetun namespace with host loopback relay.
Private addresses and private domains are excluded by the policy. Browser
identity, login, user interaction and WSL bootstrap belong to Workstation /
Browser consumers. Live entrypoint: task consumer:windows-real-chrome:verify.

## Windows-side proof, not browser process proof

Windows PowerShell 5.1 can drop standalone empty-string arguments to native
programs. For an explicit browser/Chrome proxy observation, invoke curl.exe
with single-token `--noproxy=` and `--proxy=http://127.0.0.1:19781`
arguments. Require `%{http_connect} == 200` and the expected origin status,
then compare IPinfo egress with `task provider:gluetun:observe-exit`.
Never infer that the Windows Chrome or Codex **process** inherited this proxy
from a successful manually proxied request; that is a separate consumer
property. The public unauthenticated IPinfo endpoint has shared rate limits,
so this is a one-shot diagnostic, not a continuous health gate.

## Native Chrome enterprise policy and real browser witness

Windows Chrome's built-in user-scoped policy `ProxySettings` with
`ProxyMode=fixed_servers` and `ProxyServer=http://127.0.0.1:19781`
is the mature browser-side mechanism. The policy is owned by **Workstation**;
Network owns only the Linux public-web proxy and the scoped relay. Its
source/installed/loaded readback is distinct from the Linux Network
`consumer:windows-real-chrome:verify` result. Do not copy this policy into
the generic Linux core or create an additional Chrome VPN launcher.

On the Windows interactive desktop, inspect `chrome://policy`, then open
`https://ipinfo.io` in the real browser. For a reproducible one-shot
browser witness, Chrome itself supports `--headless=new --dump-dom` in a
disposable `--user-data-dir`; leave `--proxy-server` **unset** so that
the browser's actual Windows policy is the factor under test. Compare its
public IP and country with `task provider:gluetun:observe-exit`, and delete
only the newly created throwaway browser profile. No browser login,
credentials or production profile should be touched.

A successful browser HTTPS request is a sampled consequence, not a
permanent IP promise or a universal WebRTC, IPv6, DNS or extension-traffic
no-bypass verdict. Do not retain the transient IPinfo observation in
source-controlled documentation.
