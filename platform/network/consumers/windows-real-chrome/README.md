# Windows Real Chrome egress

A public-web HTTP proxy inside the Gluetun namespace with host loopback relay.
Private addresses and private domains are excluded by the policy. Browser
identity, login, user interaction and WSL bootstrap belong to Workstation /
Browser consumers. Live entrypoint: task consumer:windows-real-chrome:verify.
