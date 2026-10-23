# Muse Staging Enrollment R3

Status: PACKET ONLY — DO NOT ENROLL PRODUCTION YET

## Preconditions

1. R3 candidate is integrated/requalified against exact current main.
2. Gateway staging deployment enables a durable external-worker DB.
3. A non-browser H3 edge path reaches only the worker HTTP routes.
4. Operator creates a short-lived enrollment bootstrap credential.
5. Muse retains its R2 private key locally; only the public key is enrolled.

## First admitted capability

Use only muse.shell.echo.

Do not enroll browser/native-agent capabilities in R3.

## Gateway configuration

~~~text
ORDIVON_GATEWAY_EXTERNAL_WORKER_DB=<durable gateway state path>
ORDIVON_GATEWAY_WORKER_ENROLLMENT_TOKEN_FILE=<operator-owned bootstrap file>
~~~

The bootstrap file is not a worker runtime credential. Disable/rotate it after enrollment.

## Muse sequence

~~~text
generate/load persistent Ed25519 identity
-> POST /v1/workers/enroll once
-> signed heartbeat
-> signed claim
-> execute fixed capability dispatcher only
-> signed started/events/artifacts/complete
~~~

ONE_SHOT is the first staging mode. LOOP/long-poll follows only after one-shot E2E passes.
Do not create Muse cron until the real staging one-shot path is proven.

## Not included

- no secret values;
- no production hostname;
- no Cloudflare admin credential;
- no Gateway master token;
- no browser capability;
- no cron creation.
