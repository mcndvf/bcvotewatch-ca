# BC Vote Watch — bootstrap release

Static, no-build HTML/CSS/JS starter designed for the same simple deployment model used by SmartRichmond: Git-backed static pages suitable for Cloudflare Pages.

## Initial SEO pages
- `/` — BC election watch hub
- `/bc-election-2026` — early-election status + date scenarios
- `/bc-election-candidates-2026` — candidate tracker contract
- `/bc-election-ridings` — riding hub
- `/bc-election-polls` — polling monitor stub
- `/bc-election-party-poll-2026` — reader poll (party choice, not candidates — nominations aren't final until Oct 3)
- `/how-to-vote-bc` — official-source voting links
- `/sources` — evidence/source rules
- `/zh-cn/bc-election-2026`
- `/zh-tw/bc-election-2026`

## Election status switch
Update `data/election-status.json` when Elections BC formally changes the status. Do not mark the election called based only on media speculation.

## Reader poll (Cloudflare Pages Function + KV)
`/bc-election-party-poll-2026` posts votes to `functions/api/party-poll.js`, which needs a Cloudflare KV namespace bound to the Pages project. This mirrors how SmartRichmond wires its `/api/mayor-poll` function. One-time setup in the Cloudflare Pages dashboard for the `bcvotewatch-ca` project:
1. Workers & Pages → KV → create a namespace (e.g. `party-poll`).
2. Pages project → Settings → Functions → KV namespace bindings → add binding `PARTY_POLL_KV` pointing at that namespace (bind it for both Production and Preview).
3. Settings → Environment variables → add a secret `POLL_IP_SALT` (any random string) for both Production and Preview — it's used to hash voter IPs for one-vote-per-person dedup, never stored in plaintext.
4. If the Pages project's `*.pages.dev` subdomain differs from `bcvotewatch-ca.pages.dev` / `bcvotewatch.pages.dev`, update `ALLOWED_ORIGINS` in `functions/api/party-poll.js` to match.
Without this KV binding the poll page loads but voting will fail with a server error.

## Domain / deployment
1. Put these files at repository root.
2. Connect repository to Cloudflare Pages with no framework preset and no build command; output directory is repository root (or the matching static output directory if your existing SmartRichmond setup uses one).
3. Add `bcvotewatch.ca` and `www.bcvotewatch.ca` as custom domains in Cloudflare Pages.
4. At Porkbun, add the exact DNS records Cloudflare Pages requests. Do not guess the target before Cloudflare creates the project hostname.
5. Verify HTTPS, canonical URLs, `robots.txt`, `sitemap.xml`, and submit the property/sitemap in Google Search Console.

## Current election status
As of 2026-09-25, Elections BC confirms a provincial general election for October 24, 2026. Candidate nominations close October 3. Update the source in `scripts/build_site.py`, then regenerate the HTML pages whenever election information changes.

Official source: https://elections.bc.ca/2026-provincial-election/
