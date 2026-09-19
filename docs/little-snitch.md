# Little Snitch 6 installation

Instructions follow the current Little Snitch 6 documentation:

- https://help.obdev.at/littlesnitch6/lsc-blocklists
- https://help.obdev.at/littlesnitch6/concepts-blocklists

They are **not** Little Snitch 5 / Mini instructions.

## Subscribe to JayBlock Aggressive

1. Open **Little Snitch**.
2. Open the **Rules** window.
3. In the left sidebar, if there is no Blocklists section yet, click **Add Blocklists…**. If Blocklists already exists, click the **+** control to the right of that heading.
4. The blocklist picker opens. Ignore the curated catalog unless you want it. Use the control described as adding a list **by URL**.
5. Paste:

   `https://raw.githubusercontent.com/jaysinko/jayblock/main/dist/aggressive.txt`

6. Click **Add**. When asked for a name, use `JayBlock Aggressive`.
7. Double-click the new sidebar entry. Set the update interval to **Daily**. Hourly is available in Little Snitch 6 if you want faster uptake after a GitHub Actions rebuild.
8. Confirm the checkbox next to the list is enabled.

Little Snitch will download a plain domain list over HTTPS and apply it to all processes.

## Mirror URL

If `raw.githubusercontent.com` is unreachable:

`https://jaysinko.github.io/jayblock/aggressive.txt`

Do not subscribe to both; they are the same list.

## Other profiles

- Balanced: replace `aggressive.txt` with `balanced.txt`.
- Nuclear: `nuclear.txt`. Expect breakage. Not recommended as the standing configuration.

## Disable one false positive

Select the Blocklist in the sidebar, find the domain, and disable that entry. Little Snitch 6 applies that disable across every blocklist that contains it.

## Disable everything temporarily

Uncheck **JayBlock Aggressive**, or uncheck **All Blocklists**.

## Optional encrypted DNS

Little Snitch → **DNS Encryption**. Pick DoT or DoH to a **non-filtering** resolver (Quad9 is the example discussed in Objective Development's docs). macOS allows only one DNS proxy extension; a VPN that also installs one will conflict. JayBlock does not require this.

## Optional application template

`dist/optional/local-apps.lsrules` is a **remote-rule-group style** JSON file with deny rules marked `"disabled": true`. Import it only after reviewing process paths. It is not a blocklist subscription.

Keep connection alerts enabled for unknown executables. The domain list is not a substitute for that.
