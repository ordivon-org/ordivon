# Windows Real Chrome Provider — Authority R1

## Purpose

This provider attaches Browser Harness to the operator's already-running Windows Google Chrome.
It reuses the existing user profile/session in place. It does not export cookies, clone the profile,
launch a substitute browser, or bypass browser/provider security controls.

## Natural owners

- Chrome owns the user profile, authenticated web state, and explicit remote-debugging consent.
- Workstation owns the pinned Browser Harness 0.1.13 realization; Windows Runtime admits PowerShell under active_user and the provider binding resolves the exact Workstation-managed Browser Harness path.
- Windows Runtime active_user owns physical Browser Harness execution.
- Browser Capability Router owns only pre-execution route selection.
- The caller/domain owner remains responsible for browser-control and external-effect authority.
- Runtime Job/Attempt evidence proves physical execution only.
- Provider/domain readback proves external outcome when an external effect is attempted.

## Authority separation

ChromeRemoteDebuggingConsent != BrowserControlAuthority != ProviderEffectAuthority.

Chrome consent permits an attached controller to exist. It does not authorize a task, click,
submission, message SEND, purchase, deletion, or other external effect.

A route plan is discovery/composition evidence only. It never grants BrowserControlAuthority or
ProviderEffectAuthority.

## Action classes

| class | examples | minimum authority / verifier |
| --- | --- | --- |
| observe | doctor, page_info, current_tab, list_tabs, accessibility-tree read | admitted read-only browser control; no external effect claim |
| local-control | switch attached tab, local deterministic test-page manipulation | explicit browser-control authority; verify exact local state transition |
| navigation | new tab, URL navigation, back, scroll that may trigger lazy network | browser-control authority plus target/network policy; verify destination/state |
| interaction | click, text entry, select | browser-control authority and task-specific policy; ambiguous completion remains UNKNOWN |
| commit | submit, send, purchase, delete, publish, irreversible account mutation | exact ProviderEffectAuthority + EffectIdentity + provider/domain readback + reconciliation |

A lower class never implies a higher class.

## Readiness

The route may report READY only when:

- Workstation reports an exact Browser Harness 0.1.13 realization and its managed Windows path exists;
- Windows Chrome is running;
- the human-owned DevToolsActivePort consent state is present;
- the corresponding loopback DevTools /json/version endpoint is currently reachable as Chrome.

A live Browser Harness daemon is current state, not a prerequisite for bootstrap readiness.

## Recovery

Before an external effect, loss of Chrome, consent, Browser Harness daemon, Windows Runtime, or
current route binding is PRE_EFFECT_HOLD and requires reacquire/rebind/reverify.

After an ambiguous external effect, do not redispatch. Reconcile using the provider/domain natural
owner before retry.

## Network binding

Browser network identity is orthogonal to browser control. VPN/split-tunnel policy belongs to the
Windows network/VPN owner, not Browser Harness. A VPN binding must be independently observed and
must not be inferred from Browser Harness readiness.
