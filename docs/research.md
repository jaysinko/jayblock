# Research notes

Access date for all URLs below unless noted: **2026-09-18**.

## Little Snitch 6 blocklists

Authoritative documentation:

- Blocklist concepts: https://help.obdev.at/littlesnitch6/concepts-blocklists
- Managing blocklists (UI): https://help.obdev.at/littlesnitch6/lsc-blocklists
- `.lsrules` format: https://help.obdev.at/littlesnitch6/adv-lsrules-file-format
- Rule matching: https://help.obdev.at/littlesnitch6/concepts-rules
- DNS encryption: https://help.obdev.at/littlesnitch6/concepts-dnsencryption
- Release notes: https://www.obdev.at/products/littlesnitch/releasenotes6.html

### Formats Little Snitch 6 accepts

From the concepts page:

1. **hosts** — `/etc/hosts` style. Treated as a blocklist of **computer names** (exact host match).
2. **domains** — many computer names separated by newlines (or other separators). Treated as **domain names**. Quote: "The domains themselves and all computer names in the domains are blocked."
3. **IP addresses** — ranges or CIDR.
4. **`.lsrules`** — JSON rule groups. If the file only denies hosts/domains/IPs for any process, it appears under Blocklists. Official recommendation: **avoid `.lsrules` when another format exists, because the others are more compact.**
5. **Limited Adblock format** — added in Little Snitch 6 (release notes). Not documented as complete uBO/ABP parity.

Linux Little Snitch docs (useful extra detail, not a substitute for the macOS pages): https://help.obdev.at/littlesnitch-linux/blocklists

- Prefer domain lists over host lists.
- Simple `*.domain.com` is the only wildcard form called out as supported on Linux. JayBlock still emits **bare domains** so macOS autodetection stays in domain mode.

### Matching semantics (collapsing)

Verified: a domain-format entry `tracker.example.com` blocks `metrics.tracker.example.com`.

JayBlock therefore collapses redundant descendants **only** when emitting a domain list. It does not invent parent domains. Public suffixes (`com`, `github.io`, `co.uk`, `amazonaws.com`, `cloudfront.net`) are rejected using the Mozilla Public Suffix List.

Hosts-format output would make collapsing **unsafe**, so JayBlock never emits `0.0.0.0` lines.

### Size / performance

- Little Snitch 6 release notes advertise improved filtering performance for large blocklists and a curated picker with daily updates.
- Older community reports (StevenBlack hosts issue #739) mention a historical ~200k rule concern for `.lsrules`. That format is no longer recommended for this use.
- HaGeZi full TIF is about **2.1 million entries / 44 MB** (`wildcard/tif-onlydomains.txt`, HTTP Content-Length 44777734 on 2026-09-18). Too large for a comfortable Little Snitch subscription and UI. JayBlock uses **TIF medium** instead.
- Measured 2026-09-18: `wildcard/tif.medium-onlydomains.txt` header reports **858694** domains. The README's ~319k figure is the Adblock-format rule count, which compresses coverage via `||domain^`. After merge with Multi PRO and descendant collapse, aggressive is about **1.03 million** suffix-matching domains and **18 MB**. Little Snitch 6 documents improved large-list performance; use balanced if the Rules UI feels heavy.
- No current official maximum is published.

### Subscription transport

Little Snitch loads remote lists over **HTTPS with a trusted certificate**. Insecure HTTP is not supported for remote rule groups; blocklist URLs from GitHub are HTTPS.

`raw.githubusercontent.com` served HaGeZi files as `text/plain; charset=utf-8` (verified with HEAD, 2026-09-18). That is the correct Content-Type for a domain list.

GitHub Pages also serves `.txt` as text/plain and is a reasonable mirror. jsDelivr can lag daily rebuilds, so it is not the primary URL.

### UI for adding a custom list (Little Snitch 6)

From https://help.obdev.at/littlesnitch6/lsc-blocklists:

- First list: **Add Blocklists…** in the Rules window sidebar.
- Later lists: **+** beside the Blocklists section header.
- Picker item 4: paste a URL for a list that is not in the curated catalog.
- After add, the blocklist editor asks for a name.
- Double-click a blocklist to change name and update interval.
- Individual false positives can be disabled; a disable applies to every list that contains that entry.
- Update intervals: daily historically, **hourly added in Little Snitch 6**.

## Upstream evaluation

### HaGeZi DNS Blocklists (selected)

- Repo: https://github.com/hagezi/dns-blocklists
- FAQ: https://github.com/hagezi/dns-blocklists/blob/main/FAQ.md
- Cheat sheet: https://github.com/hagezi/dns-blocklists/blob/main/CHEATSHEET.md
- Sources: https://github.com/hagezi/dns-blocklists/blob/main/sources.md
- License: GPL-3.0
- Maintenance: daily on GitHub/GitLab/Codeberg; extra build mirror every 4–8 hours.

HaGeZi is not a concatenation. The maintainer states there is no 1:1 transfer of sources; lists are compiled, extended, and cleaned.

Discussion confirming OISD / StevenBlack / AdGuard DNS filter are **not required** on top of HaGeZi: https://github.com/hagezi/dns-blocklists/discussions/8909 (maintainer, 2026-01-25: "No, it is not required. Similarly, Steven Black and AdGuard DNS filter are not required.")

Recommended starter: **Multi PRO + Threat Intelligence Feeds**.

| Version | Breakage | Notes |
| --- | --- | --- |
| Light | Minimal | Top 1M/10M only. No crash reporters. |
| Normal | Low | All-round. No crash reporters. Balanced profile. |
| Pro | Low–moderate | Maintainer default. Aggressive profile foundation. Crash reporters included. |
| Pro++ | Moderate | Nuclear foundation. |
| Ultimate | High | Documents Facebook/Messenger/WhatsApp tracker breakage. **Not used.** |

Wildcard domains format (plain names, software treats as suffix/wildcard), verified 2026-09-18:

- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/pro-onlydomains.txt (200, 4387981 bytes)
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/multi-onlydomains.txt (Normal)
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/pro.plus-onlydomains.txt
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/tif.medium-onlydomains.txt
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/tif.mini-onlydomains.txt
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/fake-onlydomains.txt
- https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/popupads-onlydomains.txt

`wildcard/pro.txt` is the asterisk form (`*.example.com`), which JayBlock can parse, but **`-onlydomains.txt` is the better input**.

Lists investigated and **not** ingested:

- OISD big (`https://big.oisd.nl/`) — already a HaGeZi input; adding it is redundant.
- StevenBlack hosts — same.
- AdGuard DNS filter — same.
- EasyList / EasyPrivacy — ABP path/cosmetic rules cannot be faithfully converted; HaGeZi already extracts the DNS-useful parts.
- HaGeZi Ultimate — Facebook/Messenger breakage.
- HaGeZi native.apple — would attack macOS/iCloud telemetry in ways that break the OS.
- HaGeZi DoH/VPN/TOR bypass — fights encrypted DNS.
- HaGeZi URL shortener — known to break `t.co` and similar redirects.
- HaGeZi social — would block Facebook.
- HaGeZi badware hoster — blocks entire shared hosts, including legitimate tenants.
- HaGeZi abused TLDs — blocks whole TLDs.
- NRD/DGA — huge, unfiltered, high false-positive rate by design.
- Full TIF — size, as above.

### Other candidates

- Peter Lowe's list: historically blocks `t.co`. Little Snitch's own docs use that as a false-positive example. Not added.
- URLhaus / Phishing Army / OpenPhish: covered in spirit by HaGeZi TIF medium.

## Encrypted DNS on current macOS

Little Snitch 6 implements system-wide DoT/DoH/DoQ via a DNS Proxy network extension.

Implications:

- macOS allows **only one** DNS proxy extension. Another VPN/DNS app can make Little Snitch encryption unavailable.
- Split-horizon / router-local DNS names need exceptions.
- Apps that do DNSBL-style lookups against a private DNS server can fail.
- SNI still leaks hostnames on HTTPS connections, so DNS encryption is not anonymity.
- A **filtering** resolver (NextDNS, AdGuard DNS) would duplicate JayBlock and make provenance harder. Prefer a **non-filtering** resolver if you enable this.

Little Snitch's own docs mention Quad9's logging stance without making it a hard recommendation: https://help.obdev.at/littlesnitch6/concepts-dnsencryption

JayBlock does **not** force DNS settings. If used: Little Snitch → DNS Encryption → Quad9 (DoT or DoH) or Cloudflare `cloudflare-dns.com` only if you accept Cloudflare as the lookup party. Keep the JayBlock allowlist entries for those resolvers.

A Sequoia-era DNS proxy bypass was specific to Little Snitch 6.1 and fixed in 6.1.1: https://www.obdev.at/en/blog/warning-macos-sequoia-15-may-bypass-dns-encryption/

## YouTube

YouTube advertisements and video segments are served from the same `googlevideo.com` edge hostnames. DNS/network blocking cannot separate them. Blocking `youtube.com`, `ytimg.com`, `ggpht.com`, `youtubei.googleapis.com`, or `jnn-pa.googleapis.com` breaks playback (PoToken / SABR). JayBlock allowlists those names and does not claim YouTube ad removal.

## Public Suffix List

https://publicsuffix.org/list/public_suffix_list.dat (vendored 2026-09-18, VERSION 2026-09-17). Used so collapsing never turns `foo.github.io` into a block on all of `github.io`.
