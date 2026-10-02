# BrowserControlPort R1

BrowserControlPort is a stable operation vocabulary and adapter-binding boundary beneath the Browser
Capability Router. The Router still selects Browser routes. BrowserControlPort does not rerank
routes and does not execute operations.

R1 deliberately qualifies only the read-only Windows Real Chrome baseline:

- readiness
- tabs.list
- page.observe-structured

The current Browser Harness transport may internally use Chrome DevTools Protocol, but raw CDP
methods are not the Browser-domain API. Existing Jev, Browser Use/Browserless and CFT routes are
catalogued as implementation support only; F6 does not independently re-certify their effectful
operations. WebDriver BiDi is represented only as a future, not-materialized adapter.

Operation support, operation qualification and authority are independent:

implementation support != qualification != BrowserControlAuthority != ProviderEffectAuthority.

A QUALIFIED_OPERATION projection therefore still has authorityGranted=false,
browserEffectAuthorized=false, providerEffectAuthorized=false and executionDispatched=false.
