# Compatibility

Reliability is a product requirement. A privacy rule that wrecks daily work is a bad rule.

## Known compromises

### YouTube advertising

Not blocked at the network layer. Playback hosts are allowlisted. Use uBlock Origin for in-player ads. Details in [browser-layer.md](browser-layer.md).

### Crash reporters vs developer platforms

HaGeZi Multi PRO starts blocking Sentry, Bugsnag, Crashlytics, and similar. On this machine those hosts are also **products used for development**. JayBlock allowlists `sentry.io`, `bugsnag.com`, `datadoghq.com`, `newrelic.com`, `grafana.com`, and `honeycomb.io`. Other apps therefore keep their crash beacons to those vendors. That is intentional.

Firebase platform hosts (`firebaseio.com`, `firebase.google.com`, …) are allowlisted. Firebase *analytics* hosts that are separate domains can still be blocked.

### Google Tag Manager

`googletagmanager.com` is blocked in aggressive. Sites that dump essential logic into GTM can look "broken". That is a site architecture problem; disable the one domain in Little Snitch if you depend on a specific GTM-only site.

### Affiliate and click wrappers

Some click-tracking hosts are blocked. The destination shop or article should still load if you paste the canonical URL. Referral shorteners that are also tracking domains may need a one-off disable.

### Facebook pixel vs Facebook the product

`facebook.net` (the third-party pixel/SDK) is blocked. `facebook.com`, `messenger.com`, `fbcdn.net`, WhatsApp, and Instagram service roots are protected in tests and must not appear as blocked ancestors.

### Cloudflare

`cloudflare.com` / `cloudflare.net` are protected. `cloudflareinsights.com` (RUM beacon) is not, and may be blocked. Sites keep working; Cloudflare's analytics beacon does not.

### Encrypted DNS

DoH/VPN bypass lists are not included, so Little Snitch DNS Encryption and Quad9/Cloudflare resolvers keep working.

### Native Apple telemetry lists

HaGeZi's `native.apple` list is not included. Blocking Apple's own telemetry hostnames from a dedicated "native tracker" list is a common way to break iCloud, push, and updates.

### Nuclear profile

PRO++ plus pop-up extras. Expect more false positives. Do not subscribe to nuclear as the daily driver.

## How tests think about "don't break GitHub"

Tests do **not** allowlist every `*.github.com` name. They fail the build if a **protected hostname** would match under Little Snitch domain semantics — meaning the hostname itself or any ancestor is in the published list. `collector.github.com` could still be blocked without failing `github.com`. If that ever breaks `gh`, add that exact host to the allowlist with a reason.

## Reporting a false positive

1. `python3 tools/explain.py the.domain.com`
2. Disable that single entry in Little Snitch to confirm the fix.
3. Open an issue with the explain output and what broke.

If a whole class of development infrastructure is hit (a package registry, a CA, an identity provider), that is a build-breaking bug, not a personal preference.
