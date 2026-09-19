# Architecture

## Network layer vs browser layer

Little Snitch is the machine-wide **network** layer. It can deny connections to hostnames and addresses for any process.

It cannot:

- Hide DOM nodes
- Strip first-party ads that share the site's own hostname
- Reliably remove YouTube in-player ads

Those remain a browser content-filter job. See [browser-layer.md](browser-layer.md).

## Pipeline

```
upstream HTTPS fetch (untrusted)
        ↓
format parsing (only understood syntax)
        ↓
IDNA / lowercase / validation
        ↓
public-suffix rejection
        ↓
deduplication
        ↓
allowlist (always wins)
        ↓
descendant collapse (Little Snitch domain matching)
        ↓
deterministic sort
        ↓
dist/<profile>.txt + provenance + stats
```

`python3 tools/build.py` runs this for `balanced`, `aggressive`, and `nuclear`.

## Output format

Plain domain list, `#` comments in the header only, one LDH/punycode name per line, sorted. Little Snitch autodetects this as a **domain** blocklist, so each line blocks the name and every hostname under it.

The file is intentionally **not**:

- `/etc/hosts`
- Adblock Plus
- `.lsrules`

`.lsrules` remains available for the optional application template in `dist/optional/local-apps.lsrules`.

## Profiles

| Profile | Sources | Intent |
| --- | --- | --- |
| balanced | Multi NORMAL, TIF mini, extras | Low drama |
| aggressive | Multi PRO, TIF medium, Fake, extras | Default daily driver |
| nuclear | Multi PRO++, TIF medium, Fake, Pop-Up Ads, extras | Experimental |

Ultimate is omitted because HaGeZi documents Facebook/Messenger breakage.

## Allowlist

`config/allowlist.txt` is first-class. A listed name and all descendants are removed from every profile. It is small on purpose. Shared providers (`cloudflare.com`, `amazonaws.com`, `google.com`) are not allowlisted just because one customer uses them; specific playback or developer hosts are.

## Provenance

`dist/provenance.json.gz` maps each **emitted** domain to source indexes. `python3 tools/explain.py example.com` walks ancestors so a collapsed child still explains as blocked via its parent.

## Supply chain

Upstream is untrusted:

- HTTPS only
- HTML/empty bodies fail
- Per-source byte floors/ceilings
- Unexpected shrink/growth vs the previous fetch fails
- Required source failure aborts the build
- Final domain-count collapse vs last `dist/stats.json` aborts publish
- GitHub Actions only commits after tests pass, so `main`'s `dist/` stays last-known-good

## Application policy (optional)

The subscription is domain-based and process-agnostic (`any` process), which is what Little Snitch blocklists are.

Application containment is a **different** control:

- Browsers: allow the Internet; the blocklist still applies.
- Dev tools: allow the Internet; do not punch holes through the blocklist for ads.
- Unknown binaries: leave Little Snitch on **Ask**. Do not pre-allow "any connection".
- Local-only apps: optional deny-any template, all rules `disabled: true` until reviewed.

Do not encode brittle per-app hostname allowlists in the generator. Paths and bundle IDs change.

## DNS privacy

JayBlock does not install a resolver. If you want encrypted DNS, use Little Snitch's own DNS Encryption with a non-filtering resolver. Do not stack a second DNS-proxy app. See [research.md](research.md).
