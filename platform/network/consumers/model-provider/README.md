# Model Provider egress

One exact HTTPS transport for admitted model API domains using the single
shared VPN session. Credential materialization stays in the model consumer,
not Network. The per-application transport is not general Internet.
Live entrypoint: task consumer:model-provider:verify.
