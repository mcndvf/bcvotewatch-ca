# One-shot deployment prompt for the local browser agent

Work only on launching BCVoteWatch.ca. Do not modify SmartRichmond.ca or unrelated repositories.

Goal: deploy BCVoteWatch.ca using the same GitHub + Cloudflare Pages/static-site pattern as the existing SmartRichmond.ca site, while preserving the BCVoteWatch bootstrap files and URLs.

1. Inspect the local SmartRichmond repository only to identify its exact static-site deployment conventions (repo layout, Cloudflare Pages build/output settings, reusable shared header/footer implementation, Search Console verification pattern). Do not change SmartRichmond.
2. Create or use a dedicated `bcvotewatch-ca` Git repository under the same GitHub account used for SmartRichmond.
3. Copy the BCVoteWatch bootstrap release into that repository. If SmartRichmond uses a specific static directory/layout, make the minimum path-only adaptation required; do not change the published URL contract.
4. Preserve these SEO URLs exactly: `/`, `/bc-election-2026.html`, `/bc-election-candidates-2026.html`, `/bc-election-ridings.html`, `/bc-election-polls.html`, `/how-to-vote-bc.html`, `/sources.html`, `/zh-cn/bc-election-2026.html`, `/zh-tw/bc-election-2026.html`.
5. Deploy through Cloudflare Pages using the same account/settings pattern as SmartRichmond. Configure `bcvotewatch.ca` as primary and `www.bcvotewatch.ca` consistently with SmartRichmond's canonical-host convention.
6. In the already logged-in Porkbun account, apply only the DNS records explicitly requested by Cloudflare for BCVoteWatch.ca. Do not alter nameservers or unrelated DNS records unless the existing SmartRichmond architecture demonstrably requires it.
7. Verify HTTPS and HTTP 200 for the homepage and all listed SEO pages; verify `/robots.txt` and `/sitemap.xml`.
8. If Google Search Console is already logged in, add the new domain/property using the same verified method used by SmartRichmond and submit `https://bcvotewatch.ca/sitemap.xml`.
9. Final report only: repository URL, commit SHA, Cloudflare Pages project/production URL, DNS records changed, custom-domain status, Search Console status, and any blocker. Do not add new features.

Accuracy gate: keep the site wording that a Fall 2026 early provincial election is possible but not formally called unless Elections BC itself has changed the official status at execution time. If it has changed, update `data/election-status.json` and the affected page copy using the official Elections BC source before deploy.
