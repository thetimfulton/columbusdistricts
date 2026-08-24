# DNS rollback record — columbusdistricts.com

Captured **2026-08-24** during the Cloudflare cutover (WordPress → Astro on Cloudflare Pages).
Keep this file. If anything goes wrong, this is how to put DNS back exactly as it was.

## Registrar
- **Registrar:** Tucows (reached via whatever reseller/portal the domain was bought through).
- Nameserver changes are made at the **registrar**, not at AWS.

## ⏪ Original nameservers (AWS Route 53) — restore these to roll back
Set the domain's nameservers back to these four to return authority to the old Route 53 zone:

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

## Rollback options (fastest first)
1. **Before/right after cutover:** at the registrar, set the four AWS nameservers above. Route 53
   is still authoritative and unchanged, so this fully reverts within DNS propagation time.
2. **After going live on Cloudflare, to revert just the website (keep Cloudflare DNS):** in the
   Cloudflare zone, remove the Pages custom domains and set the A record back to `3.13.98.198`
   (DNS only). Email is unaffected either way.
