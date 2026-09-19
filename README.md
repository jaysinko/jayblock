# JayBlock

Machine-wide privacy, advertising, tracking, telemetry, and malware blocking for [Little Snitch 6](https://www.obdev.at/products/littlesnitch/index.html).

JayBlock is a **generated domain subscription**, not a pile of public lists glued together. The default **aggressive** profile is meant to stay on all the time on a Mac used for software development and business.

## Little Snitch subscription URL

```
https://raw.githubusercontent.com/jaysinko/jayblock/main/dist/aggressive.txt
```

GitHub Pages mirror (same file):

```
https://jaysinko.github.io/jayblock/aggressive.txt
```

Install in Little Snitch 6:

1. Open **Little Snitch**.
2. Open the **Rules** window.
3. If you have no blocklists yet, click **Add Blocklists…** in the sidebar. Otherwise click **+** next to the **Blocklists** heading.
4. Paste the subscription URL into the field for adding a list by URL.
5. Click **Add**. Name it `JayBlock Aggressive`.
6. Double-click the new blocklist and set the update interval to **Daily** (Hourly is optional).
7. Leave it enabled.

Full UI notes: [docs/little-snitch.md](docs/little-snitch.md).

## What it blocks

Where a destination is identifiable as its own hostname, JayBlock blocks:

- Advertising and ad measurement
- Cross-site and behavioral tracking
- Analytics and unnecessary application telemetry
- Fingerprinting and identity-resolution services
- Session replay / behavioral monitoring beacons
- App advertising SDK backends
- Known malware, phishing, scam, adware, cryptominer, and C2 infrastructure

It applies to **every process on the Mac**, not just the browser.

## What it deliberately does not block

- YouTube ads. Video ads share `googlevideo.com` with the video itself. See [docs/browser-layer.md](docs/browser-layer.md).
- First-party ads that are served from the same hostname as the site.
- Cosmetic junk (cookie banners, in-page placeholders). That needs a browser content filter.
- Entire cloud providers, CDNs, certificate infrastructure, or public suffixes.
- Facebook, Messenger, Gmail, GitHub, npm, PyPI, Docker, Stripe, OpenAI, Anthropic, or Apple/iCloud service roots.
- Anonymity. This is destination blocking, not Tor.

## Privacy boundaries

| Layer | What JayBlock does |
| --- | --- |
| Unwanted outbound destinations | Yes. This is the product. |
| Encrypted websites (HTTPS) | Unrelated. HTTPS is the browser/OS. |
| DNS privacy | Complementary. Use Little Snitch DNS Encryption if you want it; see [docs/research.md](docs/research.md). |
| Anonymity | No. |
| Browser fingerprint resistance | No. Use a hardened browser separately. |

## Profiles

| File | Role |
| --- | --- |
| `dist/aggressive.txt` | **Default.** HaGeZi Multi PRO + TIF medium + Fake + extras. |
| `dist/balanced.txt` | Lower false-positive tolerance. Multi NORMAL + TIF mini. |
| `dist/nuclear.txt` | Experimental. Multi PRO++ and pop-up extras. Breakage is acceptable. Never the default. |

HaGeZi Multi ULTIMATE is not used. It documents Facebook/Messenger breakage.

## Updates

GitHub Actions rebuilds daily, fetches upstream lists, runs tests, and only commits if validation passes. A failed or empty build leaves the last known-good `dist/` artifacts in place.

Rebuild locally:

```bash
python3 -m pip install -r requirements.txt
python3 tools/build.py
python3 -m unittest discover -s tests -v
```

## Debugging a domain

```bash
python3 tools/explain.py doubleclick.net
python3 tools/explain.py github.com
```

False positives: open a GitHub issue with the domain, the app or site that broke, and the `explain.py` output. Do not disable the whole list if you can disable one entry in Little Snitch (select the entry in the blocklist and disable it; Little Snitch applies that across lists).

## Temporarily disable

In Little Snitch’s Rules window, uncheck **JayBlock Aggressive**, or uncheck **All Blocklists**. Re-enable after you finish debugging.

## Browser complement

Little Snitch cannot hide DOM elements or separate YouTube ads from YouTube video. Use **uBlock Origin** with its default lists in Firefox or Chromium. Details: [docs/browser-layer.md](docs/browser-layer.md).

## Source philosophy

- Quality over quantity. One curated compiler plus a threat feed, not twenty overlapping lists.
- HaGeZi already incorporates EasyList, EasyPrivacy, AdGuard DNS filter, OISD, and StevenBlack. Those are not ingested again.
- The allowlist is small and evidence-backed. It always wins.
- Upstream lists are untrusted input. Empty bodies, HTML error pages, and huge size swings fail the build.

## Optional application rules

The domain list is the product. Application containment is separate and optional. See `config/optional-local-apps.lsrules` and [docs/architecture.md](docs/architecture.md). Keep Little Snitch’s interactive alert for unknown executables.

## License

GPL-3.0. The published lists are derived from [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) and must stay under GPL-3.0. See [NOTICE](NOTICE).
