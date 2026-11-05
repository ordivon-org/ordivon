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
