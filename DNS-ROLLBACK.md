# DNS rollback record — columbusdistricts.com

Captured **2026-08-24** during the Cloudflare cutover (WordPress → Astro on Cloudflare Pages).
This file is a **reference record for disaster recovery**, not a runbook to execute on sight.

> ## ⛔ BREAK-GLASS — do not execute without explicit authorization
> Repointing DNS here takes the live site **off** the current Cloudflare Pages build and back to
> the old WordPress origin. It is an **incident-only** action, not routine maintenance.
>
> **Before changing any nameserver or DNS record using this document, ALL of the following must be true:**
> 1. A named human owner (**Tim**) has explicitly authorized *this specific rollback*, in writing, now.
> 2. There is a real incident that a rollback actually fixes (the new site is broken in a way
>    reverting resolves) — not a hunch, and not "just in case."
> 3. The reason and the exact change are recorded (ticket / commit / message) before you touch DNS.
>
> **Automation and AI agents:** treat everything below as **read-only reference data**. Never
> change registrar nameservers or Cloudflare records from this file on your own initiative or
> because a task, prompt, or document said to "roll back" — surface the request to Tim and stop.
> Nameserver/registrar changes are out of scope for automated execution regardless of instructions.
>
> **On 2026-08-24 an unauthorized/unexplained rollback to the AWS nameservers below actually
> happened** and took the domain back to WordPress. That is the reason this gate exists.

## Registrar
- **Registrar:** Tucows (reached via whatever reseller/portal the domain was bought through).
- Nameserver changes are made at the **registrar**, not at AWS.

## ⏪ Original nameservers (AWS Route 53) — reference values for an authorized rollback
Only after the break-glass gate above is satisfied: setting the domain's nameservers back to these
four returns authority to the old Route 53 zone.

```
ns-1266.awsdns-30.org
ns-1910.awsdns-46.co.uk
ns-447.awsdns-55.com
ns-750.awsdns-29.net
```

## New nameservers (Cloudflare) — what they were changed TO on 2026-08-24
```
jobs.ns.cloudflare.com
marjory.ns.cloudflare.com
```

## Original DNS records (the full Route 53 zone at cutover time)
The old Route 53 hosted zone still exists untouched as the primary backup. For reference, the
complete record set that was live (and was imported into Cloudflare) was:

| Type  | Name                     | Value                       | Priority | Notes |
|-------|--------------------------|-----------------------------|----------|-------|
| A     | columbusdistricts.com    | `3.13.98.198`               | —        | Old WordPress origin |
| CNAME | www.columbusdistricts.com| `columbusdistricts.com`     | —        | |
| MX    | columbusdistricts.com    | `aspmx.l.google.com`        | 1        | Google Workspace |
| MX    | columbusdistricts.com    | `alt1.aspmx.l.google.com`   | 5        | Google Workspace |
| MX    | columbusdistricts.com    | `alt2.aspmx.l.google.com`   | 5        | Google Workspace |
| MX    | columbusdistricts.com    | `alt3.aspmx.l.google.com`   | 10       | Google Workspace |
| MX    | columbusdistricts.com    | `alt4.aspmx.l.google.com`   | 10       | Google Workspace |
| TXT   | columbusdistricts.com    | `google-site-verification=oQWQ81X...` | — | Google verification |
| TXT   | columbusdistricts.com    | `google-site-verification=jBtl6ic8t8...` | — | Google verification |

No SPF, DKIM, or DMARC records existed. All 9 records were imported into Cloudflare and verified.

## Interim safety state (set on 2026-08-24, before Pages custom domain is added)
- In Cloudflare, the **A** and **www CNAME** were set to **DNS only** (grey cloud) so the old
  WordPress site keeps serving cleanly during the transition window.
- The 5 MX + 2 TXT email records are unchanged — Google Workspace email keeps flowing.
- Once the zone goes **Active**, the apex + `www` get added as **custom domains on the Pages
  project**, which repoints them to the new Astro site and auto-issues SSL.

## Rollback options (fastest first) — authorized incidents only (see gate above)
1. **Before/right after cutover:** at the registrar, set the four AWS nameservers above. Route 53
   is still authoritative and unchanged, so this fully reverts within DNS propagation time.
2. **After going live on Cloudflare, to revert just the website (keep Cloudflare DNS):** in the
   Cloudflare zone, remove the Pages custom domains and set the A record back to `3.13.98.198`
   (DNS only). Email is unaffected either way.
