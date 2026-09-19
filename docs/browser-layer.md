# Browser layer

Little Snitch / JayBlock will not reproduce uBlock Origin. That is a limitation of **network hostname policy**, not a missing feature in this repository.

## What the network layer already does

Third-party ad, tracker, analytics, fingerprinting, and malware **hostnames** are denied for every app, including browsers. Many sites become quieter before the page even paints.

## What still needs a content filter

- **YouTube in-player ads.** Ads and the video are served from the same `googlevideo.com` edges. Blocking that domain stops playback. JayBlock therefore allowlists YouTube delivery hosts and does not pretend to strip those ads.
- **Cosmetic filtering.** Cookie banners, leftover empty ad slots, in-page promo cards.
- **First-party advertising.** When `/ads` is served from `www.the-site.com`, a domain list cannot see it.
- **Annoyance filtering.** Newsletter modals, anti-adblock overlays, some cookie nags.

## Minimal recommendation

Use **one** browser extension, with **default lists**, nothing else until a specific gap appears.

### Firefox or Chromium

Install [uBlock Origin](https://github.com/gorhill/uBlock#installation). Leave the default filter lists enabled. Do not stack additional "mega" lists on top of JayBlock; you will mostly add breakage.

That default set is what currently does the best job on YouTube without extra configuration. When YouTube changes anti-adblock behavior, follow uBlock Origin's own releases rather than adding random filter URLs.

### Safari

Safari cannot run uBlock Origin. Use **AdGuard for Safari** with its default/base filters, or another maintained Safari content blocker. Do not also subscribe that tool to HaGeZi Pro; JayBlock already covers the network layer.

## What not to do

- Do not add YouTube ad domains to JayBlock.
- Do not run a second system-wide filter (AdGuard Hosts, another Little Snitch list of EasyList, NextDNS filtering) unless you are prepared to debug overlapping allowlists.
- Do not install "YouTube ad skipper" malware.

## How to tell which layer failed

If Little Snitch's log shows a denied hostname, JayBlock (or another blocklist) did it: `python3 tools/explain.py that.host`.

If the connection is allowed but an element is still visible on the page, that is cosmetic/first-party and belongs in uBlock Origin.
