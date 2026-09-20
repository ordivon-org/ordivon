# Browser Readiness Operations R6

## Purpose

R6 separates normal browser-route operability from benchmark policy.

The generic Browser Use route previously used browser-agent-21 as a boot-warm lane. The operator
later masked that lane to remove resident Chromium memory. The Router correctly treated the mask as
POLICY_DISABLED, but the only generic lane then became impossible to wake.

R6 does not unmask or repurpose browser-agent-21. It migrates generic Browser Use to a new,
independent browser-agent-22 lane with explicit cold-on-demand lifecycle.

## Lane ownership

- browser-agent-21 remains operator-retired/masked and is not changed by the migration;
- browser-agent-22 is the new generic Browser Use lane;
- ChatGPT carriers 11/12/13 remain a separate authenticated pool and are never reused for generic
  browsing or benchmark traffic.

The rendered Browser Use configuration binds only browser-agent-22.

## Cold-on-demand lifecycle

browser-agent-22 carries three explicit lifecycle commitments:

- serviceUnit: ordivon-browserless@22.service
- activationUnit: ordivon-browser-agent.target
- idleStopUnits:
  - ordivon-browser-agent.target
  - ordivon-browserless@22.service
  - ordivon-browserless-operator-proxy@22.service

The target requires the carrier and loopback operator proxy. It has no multi-user WantedBy
installation and deployment explicitly leaves it disabled/cold.

Starting the target therefore materializes the carrier only for a real generic Browser Use request.

## Router semantics

A masked exact lane remains POLICY_DISABLED.

An inactive generic endpoint whose activation unit is loaded and unmasked is now
READY_ON_DEMAND. This is a readiness claim about the declared lifecycle path, not a claim that a
browser process is already healthy.

An active carrier is still health-probed and reports READY only when Browserless health succeeds.

Router readiness never starts the carrier.

## Browser Use execution

Before Browser Use creates/attaches its named daemon, it calls the endpoint's explicit lifecycle
activation. The lifecycle implementation:

1. rechecks service/activation masks;
2. starts only the configured activation unit when needed;
3. polls Browserless health within a bounded start timeout;
4. fails closed if activation or health does not converge.

The generated action process still receives no persisted token-bearing CDP environment.

## Reclaim behavior

On explicit Browser Use session close, a lifecycle-managed endpoint checks Browserless sessions.

- if another session exists, it returns SKIP_ACTIVE_SESSION and leaves the carrier running;
- if session observation fails, it returns HOLD_SESSION_OBSERVATION_FAILED and leaves the carrier
  running;
- only when the session list is observed empty does it stop the explicitly configured idleStopUnits.

This preserves the fail-closed rule: uncertain ownership never stops another consumer's browser.

## Deployment boundary

R6 source deployment does not unmask browser-agent-21.

It installs browser-agent-22's empty data directory/configuration, replaces the generic target with
the cold-on-demand target, leaves generic display/proxy units disabled at boot, and keeps only the
small ChatGPT operator proxies enabled as before.

The source-level deployment plan and Browser-focused tests must pass before any workstation apply.

The live first-activation witness exposed one dependency-closure omission: the immutable
browserless-display-auth release allowlist still admitted 21 but not the new 22 instance. R6.1
retains 21 for rollback compatibility, adds 22 to the bounded production display-auth set, and
requires the commit-addressed Agent Automation release to advance before the live retry. The
systemd mask remains the authority that keeps retired 21 unavailable.

## Jev standing

R6 does not invent or extract a Jev credential.

The current host has no TYPESAFE_API_KEY or TEXT_MODEL_API_KEY in the executing environment, and a
name-only search of the normal Ordivon configuration roots found no existing binding source for
those names. Jev therefore remains a separate credential-provisioning blocker.

No secret value is read or emitted by this readiness work.


## Live verification — 2026-09-18

R6.1 was promoted through the commit-addressed Agent Automation release at commit
ae0938168df227e2075653d73517d9a2fc161e72. Browser Security qualification returned
NO_OBSERVED_DRIFT before activation.

A fresh Browser Use benchmark trial then exercised the normal cold-on-demand path:

- Runtime executionDisposition: succeeded;
- Runtime deliveryDisposition: committed;
- route standing: EXECUTED;
- semantic witness: PASS;
- actionCount: 2;
- modelRequestCount: 0;
- bootstrapElapsedMs: 3962;
- taskElapsedMs: 959;
- totalElapsedMs: 4921.

S4 reconciliation independently returned BENCHMARK_EXECUTED / PASS.

After session close, browser-agent target 22, carrier 22, Xvfb display 22, and operator proxy 22 were
all inactive; no browser-agent-22 container or 3022/13122 listener remained. Router immediately
returned READY_ON_DEMAND again.

The legacy 21 carrier/display/proxy masks remained unchanged throughout.

The S5 live gate now has exactly one blocker: Jev remains CREDENTIAL_MISSING while Browser Use is
READY_ON_DEMAND. No paired trials are materialized until both routes are normally ready.
