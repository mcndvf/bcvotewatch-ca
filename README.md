# BC Vote Watch — bootstrap release

Static, no-build HTML/CSS/JS starter designed for the same simple deployment model used by SmartRichmond: Git-backed static pages suitable for Cloudflare Pages.

## Initial SEO pages
- `/` — BC election watch hub
- `/bc-election-2026` — early-election status + date scenarios
- `/bc-election-candidates-2026` — candidate tracker contract
- `/bc-election-ridings` — riding hub
- `/bc-election-polls` — polling monitor stub
- `/how-to-vote-bc` — official-source voting links
- `/sources` — evidence/source rules
- `/zh-cn/bc-election-2026`
- `/zh-tw/bc-election-2026`

## Election status switch
Update `data/election-status.json` when Elections BC formally changes the status. Do not mark the election called based only on media speculation.

## Domain / deployment
1. Put these files at repository root.
2. Connect repository to Cloudflare Pages with no framework preset and no build command; output directory is repository root (or the matching static output directory if your existing SmartRichmond setup uses one).
3. Add `bcvotewatch.ca` and `www.bcvotewatch.ca` as custom domains in Cloudflare Pages.
4. At Porkbun, add the exact DNS records Cloudflare Pages requests. Do not guess the target before Cloudflare creates the project hostname.
5. Verify HTTPS, canonical URLs, `robots.txt`, `sitemap.xml`, and submit the property/sitemap in Google Search Console.

## Current factual status at bootstrap
As of 2026-09-20, Elections BC lists the next scheduled provincial election as 2028-10-21 and publishes Fall 2026 possible-date scenarios for an unscheduled election.

Official source: https://elections.bc.ca/voting/bcs-next-election/
Scenario PDF: https://elections.bc.ca/docs/fall-2026-election-calendars.pdf
