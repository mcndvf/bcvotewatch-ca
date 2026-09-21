#!/usr/bin/env python3
"""Build BC Vote Watch pages, hreflang groups and sitemap.

Run with a Python that has opencc-python-reimplemented installed (used only for
the Traditional Chinese versions):

    python3 scripts/build_site.py

Every factual claim below carries a dated source. Update FACTS and the page copy
together, and bump TODAY so the visible date, JSON-LD dateModified and sitemap
lastmod all move at once.
"""
import html
import json
import os
import re

from opencc import OpenCC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://bcvotewatch.ca"
TODAY = "2026-09-20"
TODAY_EN = "September 20, 2026"
TODAY_ZH = "2026年9月20日"
S2HK = OpenCC("s2hk")

# ---------------------------------------------------------------- sources
SRC = {
    "ebc_next": "https://elections.bc.ca/voting/bcs-next-election/",
    "ebc_cal": "https://elections.bc.ca/docs/fall-2026-election-calendars.pdf",
    "ebc_byel": "https://elections.bc.ca/resources/results/provincial-by-elections-results",
    "ebc_id": "https://elections.bc.ca/voting/what-you-need-to-vote/voter-id/",
    "ebc_ways": "https://elections.bc.ca/voting/what-you-need-to-vote/ways-to-vote",
    "ebc_who": "https://elections.bc.ca/voting/who-can-vote/",
    "ebc_reg": "https://eregister.electionsbc.gov.bc.ca/ovr/",
    "ebc_maps": "https://elections.bc.ca/resources/maps/",
    "ebc_results": "https://elections.bc.ca/resources/results/provincial-election-results",
    "ebc_nom": "https://elections.bc.ca/provincial-elections/provincial-candidates/candidate-nominations/",
    "ipsos": "https://www.ipsos.com/en-ca/bc-conservative-support-scatters-under-kerry-lynne-findlay",
    "research": "https://researchco.ca/2026/08/18/bcpoli-aug2026/",
    "angus": "https://angusreid.org/election-speculation-bcndp-conservative-eby-klf/",
    "tyee": "https://thetyee.ca/News/2026/09/17/David-Eby-Fuels-Early-Election-Speculation/",
    "ctv": "https://www.ctvnews.ca/vancouver/article/bc-premier-says-ndp-is-election-ready-further-fueling-speculation-on-early-call/",
    "wiki_lead": "https://en.wikipedia.org/wiki/2026_Conservative_Party_of_British_Columbia_leadership_election",
    "wiki_2024": "https://en.wikipedia.org/wiki/44th_British_Columbia_general_election",
    "wiki_43": "https://en.wikipedia.org/wiki/43rd_Parliament_of_British_Columbia",
    "leg": "https://www.leg.bc.ca/",
}


def a(key, text):
    return f'<a href="{SRC[key]}" rel="noopener">{text}</a>'


# ---------------------------------------------------------------- page shell
NAV_EN = [
    ("/bc-election-2026", "BC Election"),
    ("/bc-election-polls", "Polls"),
    ("/bc-party-leaders", "Party Leaders"),
    ("/bc-election-candidates-2026", "Candidates"),
    ("/bc-election-ridings", "Ridings"),
    ("/how-to-vote-bc", "How to Vote"),
    ("/sources", "Sources"),
]
NAV_ZH = [
    ("bc-election-2026", "省选2026"),
    ("bc-election-polls", "民调"),
    ("how-to-vote-bc", "如何投票"),
]
HREFLANG = {"en": "en-CA", "zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}
HTML_LANG = {"en": "en-CA", "zh-cn": "zh-Hans-CA", "zh-tw": "zh-Hant-CA"}


def url_for(lang, slug):
    if slug == "":
        return "/"
    return f"/{slug}" if lang == "en" else f"/{lang}/{slug}"


def conv(lang, s):
    return S2HK.convert(s) if lang == "zh-tw" else s


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def breadcrumb(lang, trail):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
            for i, (n, u) in enumerate(trail)
        ],
    }


def faq_schema(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", ans)}}
            for q, ans in items
        ],
    }


def faq_html(items, heading):
    out = f'<section class="section soft"><div class="wrap faq"><h2>{heading}</h2>'
    for i, (q, ans) in enumerate(items):
        out += f'<details{" open" if i == 0 else ""}><summary>{q}</summary><p>{ans}</p></details>'
    return out + "</div></section>"


def render(lang, slug, title, desc, body, group=None, schemas=(), og_image=None):
    """group: dict lang->slug of the same page in other languages (for hreflang)."""
    path = url_for(lang, slug)
    canonical = SITE + (path if path != "/" else "/")
    alt = ""
    if group:
        for l, sl in group.items():
            alt += f'<link rel="alternate" hreflang="{HREFLANG[l]}" href="{SITE}{url_for(l, sl)}">'
        alt += f'<link rel="alternate" hreflang="x-default" href="{SITE}{url_for("en", group["en"])}">'
    schema_html = "".join(jsonld(s) for s in schemas)
    if lang == "en":
        nav = "".join(f'<a href="{h}">{t}</a>' for h, t in NAV_EN)
        if group and "zh-cn" in group:
            nav += f'<a class="lang" href="{url_for("zh-cn", group["zh-cn"])}" hreflang="zh-Hans">简体</a><a class="lang" href="{url_for("zh-tw", group["zh-tw"])}" hreflang="zh-Hant">繁體</a>'
        footer = f"Primary source: Elections BC. Last reviewed {TODAY_EN}. BC Vote Watch is independent and not affiliated with Elections BC, any party or any campaign."
        site_name = "BC Vote Watch"
    else:
        nav = "".join(f'<a href="{url_for(lang, s)}">{conv(lang, t)}</a>' for s, t in NAV_ZH)
        nav += f'<a class="lang" href="{url_for("en", group["en"])}" hreflang="en-CA">English</a>'
        other = "zh-tw" if lang == "zh-cn" else "zh-cn"
        nav += f'<a class="lang" href="{url_for(other, group[other])}" hreflang="{HREFLANG[other]}">{"繁體" if other == "zh-tw" else "简体"}</a>'
        footer = conv(lang, f"主要来源：Elections BC。最后核对：{TODAY_ZH}。BC Vote Watch 为独立网站，与 Elections BC、任何政党或竞选团队无隶属关系。")
        site_name = "BC Vote Watch"
    page = (
        f'<!DOCTYPE html><html lang="{HTML_LANG[lang]}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title, quote=False)} | {site_name}</title>"
        f'<meta name="description" content="{html.escape(desc)}">'
        f'<link rel="canonical" href="{canonical}">{alt}'
        f'<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">'
        f'<meta property="og:type" content="website"><meta property="og:url" content="{canonical}"><meta property="og:site_name" content="{site_name}">'
        '<link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script>'
        f"{schema_html}</head><body>"
        '<div class="topline"></div><header><div class="wrap nav"><a class="brand" href="/"><b>BC</b> VOTE WATCH</a>'
        f"<nav>{nav}</nav></div></header><main>{body}</main>"
        f'<footer class="footer"><div class="wrap">{footer}</div></footer></body></html>'
    )
    out = os.path.join(ROOT, path.lstrip("/") or "index")
    out = out + ".html" if path != "/" else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf8") as f:
        f.write(conv(lang, page) if lang == "zh-tw" else page)
    return path


def hero(eyebrow, h1, lede, extra=""):
    return f'<section class="hero"><div class="wrap"><div class="eyebrow">{eyebrow}</div><h1>{h1}</h1><p class="lede">{lede}</p>{extra}</div></section>'


def article_schema(headline, desc, lang, path):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": headline,
        "description": desc,
        "inLanguage": HTML_LANG[lang],
        "datePublished": "2026-09-20",
        "dateModified": TODAY,
        "mainEntityOfPage": SITE + path,
        "author": {"@type": "Organization", "name": "BC Vote Watch", "url": SITE + "/"},
        "publisher": {"@type": "Organization", "name": "BC Vote Watch", "url": SITE + "/"},
    }


STATUS_BOX_EN = (
    '<div class="status" data-election-status><span class="badge" data-status-label>Possible early election — not yet called</span>'
    "<strong>Current official status</strong><span data-status-detail></span><small data-status-checked></small></div>"
)
STATUS_BOX_ZH = (
    '<div class="status" data-election-status><span class="badge" data-status-label>可能提前省选 · 尚未正式宣布</span>'
    "<strong>目前官方状态</strong><span data-status-detail></span><small data-status-checked></small></div>"
)

# ---------------------------------------------------------------- shared data
CALENDAR = [
    ("Sep 16–22", "Oct 16–21", "Oct 24"),
    ("Sep 23–29", "Oct 23–28", "Oct 31"),
    ("Sep 30–Oct 6", "Oct 30–Nov 4", "Nov 7"),
    ("Oct 7–13", "Nov 5–10", "Nov 14"),
    ("Oct 14–20", "Nov 13–18", "Nov 21"),
    ("Oct 21–27", "Nov 20–25", "Nov 28"),
]


def calendar_table_en():
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in CALENDAR)
    return (
        '<div class="tablewrap"><table><thead><tr><th>If election is called</th><th>Advance voting</th><th>Final Voting Day</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


def calendar_table_zh():
    def z(s):
        return re.sub(r"([A-Z][a-z]{2}) (\d+)", lambda m: f"{ {'Sep':9,'Oct':10,'Nov':11}[m.group(1)] }月{m.group(2)}日", s).replace("–", "至")

    rows = "".join(f"<tr><td>{z(a)}</td><td>{z(b)}</td><td>{z(c)}</td></tr>" for a, b, c in CALENDAR)
    return (
        '<div class="tablewrap"><table><thead><tr><th>若在此期间宣布选举</th><th>提前投票</th><th>最终投票日</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


POLL_ROWS = [
    # pollster key, name, field, sample, ndp, con, grn, ctr, one, note
    ("ipsos", "Ipsos", "Sep 8–14, 2026 (released Sep 15)", "800 adults, online panel; ±4.0 credibility interval", 45, 35, 10, 4, 2, "Other 4%. 28% undecided or no preference."),
    ("research", "Research Co.", "Aug 12–14, 2026 (published Aug 18)", "801 adults, online; ±3.5", 44, 39, 10, 5, 1, "Decided voters. NDP regained the lead after trailing in June."),
]

# =============================================================== ENGLISH PAGES
HUB_FAQ_EN = [
    ("Is there a BC election in 2026?",
     f"Not yet. As of {TODAY_EN}, no BC provincial general election has been called. Elections BC still lists October 21, 2028 as the next scheduled election, while it has published calendars for an unscheduled Fall 2026 election. See the {a('ebc_next', 'Elections BC page')}."),
    ("When is the next BC provincial election?",
     "The next scheduled BC provincial election is Saturday, October 21, 2028, according to Elections BC. It could happen earlier if the government decides to call one or loses the confidence of the Legislative Assembly."),
    ("Can Premier Eby call an early election?",
     f"Elections BC says an early election can happen if the government decides to call one. On September 17, 2026 Premier David Eby said he had no election announcement to make, and that the NDP and Elections BC have been told to be “election ready” ({a('tyee', 'The Tyee')}; {a('ctv', 'CTV News')})."),
    ("What would the 2026 BC election dates be?",
     f"They depend on the day the election is called. Elections BC's scenarios put Final Voting Day on October 24 if called September 16–22, October 31 if called September 23–29, and later Saturdays after that. Full table below, and the {a('ebc_cal', 'official calendar PDF')}."),
    ("Who leads in BC election polls?",
     "In the two most recent polls with published methodology, the BC NDP leads the BC Conservatives: 45% to 35% in Ipsos (Sept 8–14) and 44% to 39% in Research Co. (Aug 12–14). See the <a href=\"/bc-election-polls\">BC election polls page</a>."),
    ("Who are the BC party leaders?",
     "David Eby leads the BC NDP, Kerry-Lynne Findlay the BC Conservatives, Emily Lowan the BC Greens, Mike Bernier CentreBC and Dallas Brodie OneBC. See <a href=\"/bc-party-leaders\">BC party leaders</a>."),
]


def page_hub_en():
    latest = (
        "<ul>"
        f"<li><strong>Sep 17, 2026</strong> — Premier David Eby said he had no election announcement to make, while saying the NDP and Elections BC have been told to be “election ready” ({a('tyee','The Tyee')}; {a('ctv','CTV News')}).</li>"
        f"<li><strong>Sep 15–17, 2026</strong> — New polls: Ipsos has the NDP at 45% and the Conservatives at 35% (Sept 8–14). {a('angus','Angus Reid')} published a survey on Sept 17. <a href=\"/bc-election-polls\">All polls</a>.</li>"
        f"<li><strong>Sep 26, 2026</strong> — Abbotsford-Mission by-election. {a('ebc_byel','Elections BC lists it as scheduled')}; The Tyee gives the Sept 26 date.</li>"
        f"<li><strong>May 30, 2026</strong> — Kerry-Lynne Findlay elected leader of the BC Conservatives ({a('wiki_lead','summary of the result')}). <a href=\"/bc-party-leaders\">Party leaders</a>.</li>"
        "</ul>"
    )
    body = (
        hero("BC Election 2026", "Is there a BC election in 2026?",
             "No election has been called as of September 20, 2026, but an early election is possible. Elections BC still lists October 21, 2028 as the next scheduled provincial election and has published calendars for an unscheduled Fall 2026 vote.",
             STATUS_BOX_EN)
        + f'<section class="section"><div class="wrap"><h2>Latest developments</h2>{latest}<p class="source-note">Each item links to its source. Nothing here is a confirmed election call; this site treats timing as confirmed only when the writ is issued.</p></div></section>'
        + '<section class="section soft"><div class="wrap"><h2>How an early BC election would happen</h2>'
        f"<p>BC has a fixed election date, but {a('ebc_next','Elections BC explains')} that an election can come earlier if the government decides to call one or loses the confidence of the Legislative Assembly. Elections BC also says a Fall 2026 election would run slightly longer than a scheduled one, to allow more time for nominations, voter registration and office setup, while keeping voting day on a Saturday. It has promised an updated calendar in early 2027.</p>"
        f"<p>At the 2024 general election (October 19, 2024) the NDP won 47 of 93 seats, a one-seat majority, ({a('wiki_2024','results summary')}). Party standings in the Legislature have changed since, and two new parties, CentreBC and OneBC, now appear in polling. For current seat standings use the {a('leg','Legislative Assembly of BC')}.</p></div></section>"
        + '<section class="section"><div class="wrap"><h2>Possible Fall 2026 BC election dates</h2><p>These are Elections BC scenarios, not an announcement that an election has been called. Advance voting is six days.</p>'
        + calendar_table_en()
        + f'<p class="source-note">For later scenarios and notes use the {a("ebc_cal","Elections BC Fall 2026 calendar")}.</p></div></section>'
        + faq_html(HUB_FAQ_EN, "BC election 2026 FAQ")
        + '<section class="section"><div class="wrap"><h2>Keep going</h2><div class="linkgrid">'
        '<a class="linkcard" href="/bc-election-polls"><strong>BC election polls 2026</strong><span>NDP vs Conservatives with field dates and sample sizes.</span></a>'
        '<a class="linkcard" href="/bc-party-leaders"><strong>BC party leaders</strong><span>Who leads each party heading into a possible election.</span></a>'
        '<a class="linkcard" href="/how-to-vote-bc"><strong>How to vote in BC</strong><span>Eligibility, ID, advance voting and vote by mail.</span></a>'
        '<a class="linkcard" href="/bc-election-candidates-2026"><strong>BC election candidates 2026</strong><span>How nominations work and where official records will appear.</span></a>'
        "</div></div></section>"
    )
    title = "BC Election 2026: Is There an Early Election?"
    desc = "Has a BC provincial election been called for 2026? Official status, possible Fall 2026 election dates, latest Eby news and polls, sourced to Elections BC."
    schemas = [article_schema(title, desc, "en", "/bc-election-2026"),
               breadcrumb("en", [("Home", "/"), ("BC Election 2026", "/bc-election-2026")]),
               faq_schema(HUB_FAQ_EN)]
    return render("en", "bc-election-2026", title, desc, body, GROUPS["hub"], schemas)


def page_polls_en():
    def row(p):
        _, name, field, sample, n, c, g, ct, o, note = p
        return f"<tr><td><strong>{name}</strong></td><td>{field}</td><td>{sample}</td><td>{n}%</td><td>{c}%</td><td>{g}%</td><td>{ct}%</td><td>{o}%</td><td>{note}</td></tr>"

    rows = "".join(row(p) for p in POLL_ROWS)
    body = (
        hero("Polling monitor", "BC election polls 2026: NDP vs Conservatives",
             "Latest published BC provincial polls with field dates, sample sizes and methods. In the two most recent polls with full method details, the BC NDP leads the BC Conservatives by 5 to 10 points. A poll measures respondents at one point in time; it is not a forecast or a result.")
        + '<section class="section"><div class="wrap"><h2>Vote intention (decided voters)</h2><div class="tablewrap"><table><thead><tr><th>Pollster</th><th>Field dates</th><th>Sample</th><th>NDP</th><th>Cons.</th><th>Green</th><th>CentreBC</th><th>OneBC</th><th>Notes</th></tr></thead><tbody>'
        + rows
        + f'</tbody></table></div><p class="source-note">Sources: {a("ipsos","Ipsos")} and {a("research","Research Co.")}. Ipsos reports the Conservatives down 8 points from their 2024 result (43.3% in 2024).</p></div></section>'
        + '<section class="section soft"><div class="wrap"><h2>Leader ratings</h2><div class="grid">'
        '<div class="card"><div class="kicker">Ipsos · favourable / unfavourable</div><p>David Eby (NDP): <strong>41% / 30%</strong><br>Kerry-Lynne Findlay (Cons.): <strong>17% / 46%</strong><br>Emily Lowan (Green): 12% / 15%<br>Dallas Brodie (OneBC): 10% / 24%<br>Mike Bernier (CentreBC): 9% / 19%</p></div>'
        '<div class="card"><div class="kicker">Research Co. · approval</div><p>Eby: <strong>49%</strong><br>Lowan: 38%<br>Findlay: 34%<br>Bernier: 24%<br>Brodie: 18%</p></div>'
        f'<div class="card"><div class="kicker">Angus Reid · published Sep 17</div><p>Eby approval <strong>41%</strong>. 51% say they feel like a “political orphan” with no party to enthusiastically support. Field dates, sample and vote-intention tables are in the {a("angus","Angus Reid release")}.</p></div>'
        "</div><p class=\"source-note\">These are three different measures (favourability, approval, and a party-support sentiment) from different firms; they are not directly comparable.</p></div></section>"
        + '<section class="section"><div class="wrap"><h2>How to read these polls</h2><ul>'
        "<li><strong>Undecided voters matter.</strong> Ipsos reports 28% undecided or with no preference; the table shows decided voters only.</li>"
        "<li><strong>Regions matter more than the provincial number.</strong> Research Co. found the Conservatives dominant in Northern BC and the Fraser Valley and Metro Vancouver tight, while the NDP leads on Vancouver Island. BC uses first-past-the-post in 93 ridings, so seats depend on where votes fall.</li>"
        "<li><strong>New parties can split the vote.</strong> CentreBC and OneBC are new parties that now appear alongside the Greens in polling (Ipsos describes them as two new parties).</li>"
        "<li><strong>Margins of error.</strong> A ±3.5 to ±4.0 point margin means a 5-point gap can be within combined uncertainty for a single poll.</li></ul>"
        '<p class="source-note">Polls are added only with pollster, field dates, sample and source link. Ridings, candidates and seat projections are not covered here. See <a href="/bc-election-2026">the election guide</a> for status and <a href="/sources">our sourcing rules</a>.</p></div></section>'
    )
    title = "BC Election Polls 2026: NDP vs Conservatives"
    desc = "Latest BC provincial polls: Ipsos NDP 45, Conservatives 35; Research Co. NDP 44, Conservatives 39. Field dates, samples, margins and leader ratings."
    schemas = [article_schema(title, desc, "en", "/bc-election-polls"),
               breadcrumb("en", [("Home", "/"), ("BC Election Polls", "/bc-election-polls")])]
    return render("en", "bc-election-polls", title, desc, body, GROUPS["polls"], schemas)


HOW_FAQ_EN = [
    ("Who can vote in a BC provincial election?",
     f"You must be a Canadian citizen, at least 18 years old, and a resident of BC for at least six months ({a('ebc_who','Elections BC')})."),
    ("Do I need ID to vote in BC?",
     f"Yes. You show one document with your name, photo and address, or two documents with your name (at least one with your current address), or have someone vouch for you. See the full list at {a('ebc_id','Elections BC voter ID')}."),
    ("Can I vote by mail in BC?",
     f"Yes. Elections BC says vote by mail is available to all voters. The package must reach Elections BC before 8 p.m. Pacific time on Final Voting Day ({a('ebc_ways','ways to vote')})."),
    ("Can I vote before voting day in BC?",
     f"Yes. Elections BC provides six days of advance voting (8 a.m. to 8 p.m. local time), and you can vote at any district electoral office from the day an election is called until 4 p.m. on Final Voting Day ({a('ebc_ways','ways to vote')})."),
    ("What are the voting hours on Final Voting Day?",
     "Voting places are open from 8 a.m. to 8 p.m. Pacific time on Final Voting Day, according to Elections BC."),
]


def page_how_en():
    body = (
        hero("Voting information", "How to vote in a BC provincial election",
             "Who can vote, how to register, what ID to bring and the ways to vote, summarised from Elections BC. No BC election has been called yet, so dates depend on when one is; rules below are Elections BC's current published rules.")
        + '<section class="section"><div class="wrap"><h2>Who can vote</h2>'
        f"<p>To vote in a BC provincial election you must be a Canadian citizen, 18 or older, and a BC resident for at least six months ({a('ebc_who','Elections BC')}).</p>"
        f"<h2>Register to vote</h2><p>Check or update your registration online at {a('ebc_reg','Elections BC online voter registration')}, or phone Elections BC at 1-800-661-8683.</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>What ID do I need?</h2>'
        f"<p>Elections BC accepts any one of three approaches ({a('ebc_id','full rules')}):</p><ol>"
        "<li><strong>One document</strong> showing your name, photo and address: for example a BC driver’s licence, BC Identification Card, or BC Services Card with photo.</li>"
        "<li><strong>Two documents</strong> showing your name, with at least one showing your current address: for example a passport, birth certificate, utility bill, bank statement or lease. Electronic versions such as e-bills are acceptable.</li>"
        "<li><strong>Voter vouching</strong>: a registered voter or approved authority can vouch for your identity, with the required declarations.</li></ol></div></section>"
        '<section class="section"><div class="wrap"><h2>Ways to vote</h2><ul>'
        "<li><strong>Final Voting Day:</strong> 8 a.m. to 8 p.m. Pacific time.</li>"
        "<li><strong>Advance voting:</strong> six days, 8 a.m. to 8 p.m. local time, open to all eligible voters.</li>"
        "<li><strong>Vote by mail:</strong> available to all voters; the package must reach Elections BC before 8 p.m. Pacific time on Final Voting Day.</li>"
        "<li><strong>District electoral office:</strong> from when an election is called until 4 p.m. on Final Voting Day.</li>"
        "<li><strong>Assisted telephone voting</strong> and <strong>mobile or special voting</strong> (hospitals, long-term care) for those who qualify.</li></ul>"
        f"<p class=\"source-note\">Source: {a('ebc_ways','Elections BC — Ways to vote')}. Possible Fall 2026 dates are on the <a href=\"/bc-election-2026\">BC election 2026 guide</a>.</p></div></section>"
        + faq_html(HOW_FAQ_EN, "Voting FAQ")
    )
    title = "How to Vote in BC: ID, Advance and Mail Voting"
    desc = "How to vote in a BC provincial election: who can vote, how to register, what ID to bring, advance voting, vote by mail and voting hours, from Elections BC."
    schemas = [article_schema(title, desc, "en", "/how-to-vote-bc"),
               breadcrumb("en", [("Home", "/"), ("How to Vote in BC", "/how-to-vote-bc")]),
               faq_schema(HOW_FAQ_EN)]
    return render("en", "how-to-vote-bc", title, desc, body, GROUPS["how"], schemas)


def page_leaders_en():
    body = (
        hero("Party leaders", "BC party leaders 2026",
             "Who leads each party in British Columbia as a possible early election approaches, with the source for each claim.")
        + '<section class="section"><div class="wrap"><div class="tablewrap"><table><thead><tr><th>Party</th><th>Leader</th><th>Notes</th></tr></thead><tbody>'
        f"<tr><td><strong>BC NDP</strong></td><td>David Eby</td><td>Premier. Won a one-seat majority (47 of 93) in October 2024 ({a('wiki_2024','results summary')}).</td></tr>"
        f"<tr><td><strong>Conservative Party of BC</strong></td><td>Kerry-Lynne Findlay</td><td>Elected leader on May 30, 2026 with 51.0% of weighted points in the fourth round over Caroline Elliott (49.0%). Not currently an MLA ({a('wiki_lead','summary')}).</td></tr>"
        f"<tr><td><strong>BC Greens</strong></td><td>Emily Lowan</td><td>Named as Green leader in the {a('ipsos','Ipsos')} and {a('research','Research Co.')} polls. Two seats won in 2024.</td></tr>"
        f"<tr><td><strong>CentreBC</strong></td><td>Mike Bernier</td><td>New party that now appears in polling (4% Ipsos, 5% Research Co.).</td></tr>"
        f"<tr><td><strong>OneBC</strong></td><td>Dallas Brodie</td><td>New party that now appears in polling (2% Ipsos, 1% Research Co.).</td></tr>"
        "</tbody></table></div>"
        f"<p class=\"source-note\">The composition of the 43rd Parliament has shifted since 2024 as members changed parties or sat as independents ({a('wiki_43','overview')}). For current standings use the {a('leg','Legislative Assembly of BC')}; BC Vote Watch will publish seat standings once each figure is confirmed against the Assembly.</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>How voters rate them</h2>'
        "<p>Ipsos (Sept 8–14, 2026) found Eby 41% favourable / 30% unfavourable and Findlay 17% / 46%. Research Co. (Aug 12–14) recorded approval of 49% for Eby, 38% for Lowan and 34% for Findlay. Full numbers and methods are on the <a href=\"/bc-election-polls\">BC election polls page</a>.</p>"
        '<p>Is an election coming? See the <a href="/bc-election-2026">BC election 2026 guide</a>.</p></div></section>'
    )
    title = "BC Party Leaders 2026: Eby, Findlay, Lowan"
    desc = "Who leads the BC NDP, BC Conservatives, BC Greens, CentreBC and OneBC in 2026. Kerry-Lynne Findlay elected Conservative leader May 30, 2026; poll ratings."
    schemas = [article_schema(title, desc, "en", "/bc-party-leaders"),
               breadcrumb("en", [("Home", "/"), ("BC Party Leaders", "/bc-party-leaders")])]
    return render("en", "bc-party-leaders", title, desc, body, None, schemas)


def page_candidates_en():
    body = (
        hero("Candidates", "BC election candidates 2026",
             "There is no official candidate list yet because no BC provincial election has been called. Official candidates appear only after nominations close. Here is how the process works and where the record will be.")
        + '<section class="section"><div class="wrap"><h2>Where things stand</h2>'
        f"<p>Under Elections BC's process, candidates are nominated once an election is called and confirmed against the official record; see {a('ebc_nom','Elections BC candidate nominations')}. Until then, parties may announce or nominate people, but those are party announcements and not Elections BC records.</p>"
        "<p>BC Vote Watch will keep the two apart: <strong>official candidates</strong> (Elections BC record, dated) and <strong>announced or expected candidates</strong> (party or candidate statement, dated and linked).</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>Who is leading the parties</h2>'
        "<p>The party leaders are the people voters will see on every ballot campaign. See <a href=\"/bc-party-leaders\">BC party leaders 2026</a>. For polling see <a href=\"/bc-election-polls\">BC election polls</a>, and for how a 2026 election could unfold see the <a href=\"/bc-election-2026\">BC election 2026 guide</a>.</p>"
        f"<p class=\"source-note\">There are 93 electoral districts in BC; each elects one MLA. Riding information is on the <a href=\"/bc-election-ridings\">BC ridings page</a>.</p></div></section>"
    )
    title = "BC Election Candidates 2026: Nominations and List"
    desc = "BC election candidates 2026: no official list exists until an election is called. How nominations work and where official Elections BC candidate records appear."
    schemas = [article_schema(title, desc, "en", "/bc-election-candidates-2026"),
               breadcrumb("en", [("Home", "/"), ("BC Election Candidates 2026", "/bc-election-candidates-2026")])]
    return render("en", "bc-election-candidates-2026", title, desc, body, None, schemas)


def page_ridings_en():
    body = (
        hero("Ridings", "BC electoral districts (ridings)",
             "British Columbia elects 93 MLAs, one per electoral district (riding), by first-past-the-post. The riding-by-riding results and candidate pages will be published as the data is verified.")
        + '<section class="section"><div class="wrap"><h2>How BC ridings work</h2>'
        f"<p>Each of the 93 electoral districts elects one member of the Legislative Assembly; the candidate with the most votes wins. Official district maps and boundaries are published by {a('ebc_maps','Elections BC')}, and official past results by {a('ebc_results','Elections BC results')}.</p>"
        "<p>The NDP won 47 of 93 ridings in 2024, a one-seat majority. Because seats are won riding by riding, a provincial poll lead does not translate directly into seats. See <a href=\"/bc-election-polls\">how to read the polls</a>.</p>"
        "<p>Next: <a href=\"/bc-election-2026\">BC election 2026 guide</a> · <a href=\"/how-to-vote-bc\">How to vote</a>.</p></div></section>"
    )
    title = "BC Election Ridings: 93 Electoral Districts"
    desc = "BC has 93 electoral districts (ridings), each electing one MLA. How ridings work, official Elections BC maps and results, and why polls do not equal seats."
    schemas = [article_schema(title, desc, "en", "/bc-election-ridings"),
               breadcrumb("en", [("Home", "/"), ("BC Ridings", "/bc-election-ridings")])]
    return render("en", "bc-election-ridings", title, desc, body, None, schemas)


def page_home_en():
    body = (
        hero("British Columbia · Provincial election", "BC election 2026: early election watch, polls and how to vote",
             "Independent, source-backed tracking of a possible early BC provincial election: official status and dates, polls, party leaders, candidates, ridings and voting information. Official records, reported developments and analysis are labelled separately.",
             STATUS_BOX_EN.replace("Current official status", "Fall 2026 election watch"))
        + '<section class="section"><div class="wrap"><div class="grid">'
        '<div class="card"><div class="kicker">Official scheduled date</div><div class="big">Oct 21, 2028</div><p class="muted">The fixed date currently published by Elections BC.</p></div>'
        '<div class="card"><div class="kicker">Latest poll (Ipsos, Sep 8–14)</div><div class="big">NDP 45 · Cons. 35</div><p class="muted">Decided voters; Research Co. (Aug 12–14) has 44–39. <a href="/bc-election-polls">All polls</a></p></div>'
        '<div class="card"><div class="kicker">Fall 2026 status</div><div class="big">Not called</div><p class="muted">Premier Eby says the NDP is “election ready”; no announcement as of Sept 17.</p></div>'
        "</div></div></section>"
        '<section class="section soft"><div class="wrap"><h2>Track the possible 2026 BC election</h2><div class="linkgrid">'
        '<a class="linkcard" href="/bc-election-2026"><strong>BC Election 2026 Guide</strong><span>Is there an early election? Status, possible dates and latest news.</span></a>'
        '<a class="linkcard" href="/bc-election-polls"><strong>BC Election Polls</strong><span>NDP vs Conservatives with field dates, samples and margins.</span></a>'
        '<a class="linkcard" href="/bc-party-leaders"><strong>BC Party Leaders</strong><span>Eby, Findlay, Lowan, Bernier and Brodie.</span></a>'
        '<a class="linkcard" href="/how-to-vote-bc"><strong>How to Vote in BC</strong><span>Eligibility, ID, advance voting and vote by mail.</span></a>'
        '<a class="linkcard" href="/bc-election-candidates-2026"><strong>BC Election Candidates 2026</strong><span>How nominations work and where official records appear.</span></a>'
        '<a class="linkcard" href="/bc-election-ridings"><strong>BC Ridings</strong><span>93 electoral districts and how they decide seats.</span></a>'
        "</div></div></section>"
        '<section class="section"><div class="wrap"><h2>Official-source first</h2>'
        "<p>Election timing is not treated as confirmed until the writ is issued. Candidate status is not treated as final until it appears in the relevant Elections BC record. Polls are presented as measurements at the field dates, not as election results.</p>"
        f"<p class=\"source-note\">Primary source: {a('ebc_next','Elections BC — B.C.’s Next Election')}. Fall 2026 scenario calendar: {a('ebc_cal','Elections BC PDF')}. 中文：<a href=\"/zh-cn/bc-election-2026\" hreflang=\"zh-Hans\">简体</a> · <a href=\"/zh-tw/bc-election-2026\" hreflang=\"zh-Hant\">繁體</a></p></div></section>"
    )
    title = "BC Election 2026: Early Election Watch and Polls"
    desc = "Independent tracking of a possible 2026 BC provincial election: status and dates, latest polls, party leaders, candidates, ridings and voting information."
    schemas = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "BC Vote Watch", "url": SITE + "/", "inLanguage": ["en-CA", "zh-Hans", "zh-Hant"]},
        {"@context": "https://schema.org", "@type": "Organization", "name": "BC Vote Watch", "url": SITE + "/"},
    ]
    return render("en", "", title, desc, body, None, schemas)


# ================================================================ CHINESE PAGES
HUB_FAQ_ZH = [
    ("2026年BC省有省选吗？",
     f"目前没有。截至{TODAY_ZH}，BC省尚未宣布举行省选。Elections BC 仍列明下一次固定省选日期为2028年10月21日，同时已发布2026年秋季提前省选的日期情景表。详见{a('ebc_next', 'Elections BC官方页面')}。"),
    ("BC省下一次省选是什么时候？",
     "Elections BC 列明，下一次定期省选为2028年10月21日（星期六）。如果政府决定提前宣布，或政府失去立法会信任，选举可能提前举行。"),
    ("Eby可以提前宣布省选吗？",
     f"Elections BC 表示，政府决定宣布时可以提前举行选举。2026年9月17日，省长David Eby表示没有选举公告要宣布，同时表示已告知NDP和Elections BC要做好选举准备（“election ready”）（{a('tyee','The Tyee')}；{a('ctv','CTV News')}）。"),
    ("2026年提前省选可能是哪几天？",
     f"取决于选举宣布的日期。按 Elections BC 的情景：9月16至22日宣布，最终投票日为10月24日；9月23至29日宣布，则为10月31日；再晚则顺延至后面的星期六。完整表格见下方及{a('ebc_cal','官方日历PDF')}。"),
    ("目前民调谁领先？",
     "在两项公开方法细节的最新民调中，BC NDP 领先BC保守党：Ipsos（9月8至14日）为45%对35%，Research Co.（8月12至14日）为44%对39%。见<a href=\"/zh-cn/bc-election-polls\">BC省选民调</a>。"),
]


def page_hub_zh(lang):
    L = lambda s: conv(lang, s)
    latest = (
        "<ul>"
        f"<li><strong>2026年9月17日</strong> — 省长David Eby表示没有选举公告要宣布，同时说NDP和Elections BC已被告知要做好选举准备（{a('tyee','The Tyee')}；{a('ctv','CTV News')}）。</li>"
        f"<li><strong>2026年9月15至17日</strong> — 新民调：Ipsos显示NDP 45%、保守党35%（9月8至14日）；{a('angus','Angus Reid')}于9月17日发布调查。<a href=\"{url_for(lang,'bc-election-polls')}\">查看全部民调</a>。</li>"
        f"<li><strong>2026年9月26日</strong> — Abbotsford-Mission补选。{a('ebc_byel','Elections BC列为已排定')}；The Tyee给出9月26日的日期。</li>"
        f"<li><strong>2026年5月30日</strong> — Kerry-Lynne Findlay当选BC保守党党魁（{a('wiki_lead','结果摘要')}）。</li>"
        "</ul>"
    )
    body = (
        hero("BC省选 2026", L("2026年BC省会提前省选吗？"),
             L("截至2026年9月20日尚未宣布省选，但有可能提前举行。Elections BC 目前列出的下一次固定省选日期仍是2028年10月21日，同时已经发布2026年秋季提前省选的日期情景表。"),
             STATUS_BOX_ZH)
        + f'<section class="section"><div class="wrap"><h2>{L("最新动态")}</h2>{L(latest)}<p class="source-note">{L("每一条都附有来源。这里没有任何一项是已确认的选举公告；本站只在选举令状正式发出后才把状态改为“已宣布”。")}</p></div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{L("提前省选会怎样发生")}</h2>'
        + L(f"<p>BC省有固定选举日期，但{a('ebc_next','Elections BC说明')}，如果政府决定提前宣布，或政府失去立法会信任，选举可以提前。Elections BC 还表示，2026年秋季的选举会比定期选举稍长，以便有更多时间处理提名、选民登记和办事处设置，投票日仍安排在星期六；更新后的日历预计2027年初发布。</p>")
        + L(f"<p>2024年10月19日省选中，NDP在93个议席中赢得47席，以一席优势组成多数政府（{a('wiki_2024','结果摘要')}）。此后立法会的政党构成已有变化，民调中也出现了两个新政党 CentreBC 和 OneBC。最新议席分布请查看{a('leg','BC省立法会')}。</p>")
        + "</div></section>"
        + f'<section class="section"><div class="wrap"><h2>{L("2026年秋季省选可能的日期")}</h2><p>{L("以下是 Elections BC 的情景表，并非选举已宣布。提前投票为六天。")}</p>'
        + L(calendar_table_zh())
        + f'<p class="source-note">{L("更后期的情景与说明请见")}{a("ebc_cal", L("Elections BC 2026年秋季日历"))}。</p></div></section>'
        + L(faq_html(HUB_FAQ_ZH, "BC省选2026常见问题"))
        + f'<section class="section"><div class="wrap"><h2>{L("继续了解")}</h2><div class="linkgrid">'
        f'<a class="linkcard" href="{url_for(lang,"bc-election-polls")}"><strong>{L("BC省选民调")}</strong><span>{L("NDP与保守党，附调查日期和样本量。")}</span></a>'
        f'<a class="linkcard" href="{url_for(lang,"how-to-vote-bc")}"><strong>{L("BC省如何投票")}</strong><span>{L("资格、身份证明、提前投票和邮寄投票。")}</span></a>'
        "</div></div></section>"
    )
    title = L("BC省选2026：会提前选举吗？日期与最新状态")
    desc = L("2026年BC省是否已宣布省选？官方状态、可能的秋季投票日期、Eby最新表态和民调，来源均为Elections BC及公开报道。")
    path = url_for(lang, "bc-election-2026")
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [(L("首页"), "/"), (L("BC省选2026"), path)]),
               faq_schema([(L(q), L(a_)) for q, a_ in HUB_FAQ_ZH])]
    return render(lang, "bc-election-2026", title, desc, body, GROUPS["hub"], schemas)


def page_polls_zh(lang):
    L = lambda s: conv(lang, s)
    rows = ""
    for _, name, field, sample, n, c, g, ct, o, note in POLL_ROWS:
        if name == "Ipsos":
            f_, s_, nt = "2026年9月8至14日（9月15日发布）", "800名成年人，线上样本；可信区间±4.0", "其他4%；28%未决定或无偏好。"
        else:
            f_, s_, nt = "2026年8月12至14日（8月18日发布）", "801名成年人，线上；误差±3.5", "已决定选民；NDP在6月落后后重新领先。"
        rows += f"<tr><td><strong>{name}</strong></td><td>{f_}</td><td>{s_}</td><td>{n}%</td><td>{c}%</td><td>{g}%</td><td>{ct}%</td><td>{o}%</td><td>{nt}</td></tr>"
    body = (
        hero("民调追踪", L("BC省选民调 2026：NDP对保守党"),
             L("最新公开的BC省民调，附调查日期、样本量和方法。在两项方法细节完整的最新民调中，BC NDP领先BC保守党5至10个百分点。民调只反映某一时间点的受访者意见，不是预测，也不是选举结果。"))
        + f'<section class="section"><div class="wrap"><h2>{L("政党支持度（已决定选民）")}</h2><div class="tablewrap"><table><thead><tr><th>{L("调查机构")}</th><th>{L("调查日期")}</th><th>{L("样本")}</th><th>NDP</th><th>{L("保守党")}</th><th>{L("绿党")}</th><th>CentreBC</th><th>OneBC</th><th>{L("备注")}</th></tr></thead><tbody>'
        + L(rows)
        + f'</tbody></table></div><p class="source-note">{L("来源：")}{a("ipsos","Ipsos")}、{a("research","Research Co.")}。{L("Ipsos指出保守党较2024年结果（43.3%）下降8个百分点。")}</p></div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{L("党魁评价")}</h2><div class="grid">'
        + L('<div class="card"><div class="kicker">Ipsos · 好感／反感</div><p>David Eby（NDP）：<strong>41%／30%</strong><br>Kerry-Lynne Findlay（保守党）：<strong>17%／46%</strong><br>Emily Lowan（绿党）：12%／15%<br>Dallas Brodie（OneBC）：10%／24%<br>Mike Bernier（CentreBC）：9%／19%</p></div>')
        + L('<div class="card"><div class="kicker">Research Co. · 支持率</div><p>Eby：<strong>49%</strong><br>Lowan：38%<br>Findlay：34%<br>Bernier：24%<br>Brodie：18%</p></div>')
        + L(f'<div class="card"><div class="kicker">Angus Reid · 9月17日发布</div><p>Eby支持率<strong>41%</strong>。51%的人表示自己是“政治孤儿”，没有能热情支持的政党。调查日期、样本和政党支持表见{a("angus","Angus Reid报告")}。</p></div>')
        + f'</div><p class="source-note">{L("这是不同机构的三种不同指标（好感度、支持率和政治情绪），不能直接互相比较。")}</p></div></section>'
        + f'<section class="section"><div class="wrap"><h2>{L("如何解读这些民调")}</h2><ul>'
        + L("<li><strong>未决定选民很重要。</strong>Ipsos显示28%未决定或无偏好；上表只列已决定选民。</li>")
        + L("<li><strong>地区比全省数字更重要。</strong>Research Co.发现保守党在北部BC占优，菲沙河谷和大温哥华竞争激烈，NDP则在温哥华岛领先。BC采用单一选区得票最多者当选（first-past-the-post）的93个选区，所以议席取决于选票分布。</li>")
        + L("<li><strong>新政党可能分流选票。</strong>CentreBC和OneBC是新政党，现在与绿党一起出现在民调中（Ipsos称之为两个新政党）。</li>")
        + L("<li><strong>误差范围。</strong>±3.5至±4.0个百分点的误差意味着单项民调中5个百分点的差距可能仍在综合不确定性之内。</li></ul>")
        + f'<p class="source-note">{L("民调只有在附上调查机构、调查日期、样本和来源链接后才会收录。查看")}<a href="{url_for(lang,"bc-election-2026")}">{L("省选指南")}</a>{L("了解选举状态。")}</p></div></section>'
    )
    title = L("BC省选民调 2026：NDP对保守党最新民调")
    desc = L("BC省最新民调：Ipsos显示NDP 45%、保守党35%；Research Co.显示44%对39%。附调查日期、样本、误差和党魁评价。")
    path = url_for(lang, "bc-election-polls")
    schemas = [article_schema(title, desc, lang, path), breadcrumb(lang, [(L("首页"), "/"), (L("BC省选民调"), path)])]
    return render(lang, "bc-election-polls", title, desc, body, GROUPS["polls"], schemas)


HOW_FAQ_ZH = [
    ("谁可以在BC省省选投票？",
     f"你必须是加拿大公民、年满18岁，并在BC省居住至少六个月（{a('ebc_who','Elections BC')}）。"),
    ("在BC省投票需要带身份证明吗？",
     f"需要。你可以出示一份载有姓名、照片和地址的证件，或两份载有姓名的证件（至少一份显示现居地址），或由他人为你担保身份。完整名单见{a('ebc_id','Elections BC选民身份证明')}。"),
    ("BC省可以邮寄投票吗？",
     f"可以。Elections BC 表示邮寄投票对所有选民开放，选票包必须在最终投票日太平洋时间晚上8点前送达 Elections BC（{a('ebc_ways','投票方式')}）。"),
    ("BC省可以在投票日之前投票吗？",
     f"可以。Elections BC 提供六天提前投票（当地时间上午8点至晚上8点），并且从选举宣布之日起至最终投票日下午4点止，你可以在任何选区选举办事处投票（{a('ebc_ways','投票方式')}）。"),
    ("最终投票日的投票时间是几点？",
     "根据 Elections BC，最终投票日的投票站开放时间为太平洋时间上午8点至晚上8点。"),
]


def page_how_zh(lang):
    L = lambda s: conv(lang, s)
    body = (
        hero("投票资讯", L("如何在BC省省选投票"),
             L("谁可以投票、如何登记、需要带什么证件以及投票方式，均摘自 Elections BC。BC省目前尚未宣布省选，所以日期取决于宣布的时间；以下是 Elections BC 目前公布的规则。"))
        + f'<section class="section"><div class="wrap"><h2>{L("谁可以投票")}</h2>'
        + L(f"<p>要在BC省省选投票，你必须是加拿大公民、年满18岁，并在BC省居住至少六个月（{a('ebc_who','Elections BC')}）。</p>")
        + f"<h2>{L('登记投票')}</h2>"
        + L(f"<p>可在{a('ebc_reg','Elections BC网上选民登记')}查看或更新登记，也可致电 Elections BC：1-800-661-8683。</p>")
        + "</div></section>"
        + f'<section class="section soft"><div class="wrap"><h2>{L("需要什么身份证明？")}</h2>'
        + L(f"<p>Elections BC 接受以下三种方式之一（{a('ebc_id','完整规则')}）：</p><ol>")
        + L("<li><strong>一份证件</strong>，载有姓名、照片和地址：例如BC省驾照、BC身份证或带照片的BC Services Card。</li>")
        + L("<li><strong>两份证件</strong>，载有姓名，其中至少一份显示现居地址：例如护照、出生证明、水电费账单、银行对账单或租约。电子版（如电子账单）也可接受。</li>")
        + L("<li><strong>选民担保</strong>：已登记选民或获认可的人员可在作出规定声明后为你担保身份。</li></ol></div></section>")
        + f'<section class="section"><div class="wrap"><h2>{L("投票方式")}</h2><ul>'
        + L("<li><strong>最终投票日：</strong>太平洋时间上午8点至晚上8点。</li>")
        + L("<li><strong>提前投票：</strong>六天，当地时间上午8点至晚上8点，对所有合资格选民开放。</li>")
        + L("<li><strong>邮寄投票：</strong>对所有选民开放；选票包须在最终投票日太平洋时间晚上8点前送达 Elections BC。</li>")
        + L("<li><strong>选区选举办事处：</strong>从选举宣布之日起至最终投票日下午4点。</li>")
        + L("<li><strong>电话协助投票</strong>以及<strong>流动或特别投票</strong>（医院、长期护理院），供符合条件者使用。</li></ul>")
        + f'<p class="source-note">{L("来源：")}{a("ebc_ways",L("Elections BC — 投票方式"))}。{L("2026年秋季可能的日期见")}<a href="{url_for(lang,"bc-election-2026")}">{L("BC省选2026指南")}</a>。</p></div></section>'
        + L(faq_html(HOW_FAQ_ZH, "投票常见问题"))
    )
    title = L("BC省如何投票：资格、身份证明、提前投票与邮寄")
    desc = L("如何在BC省省选投票：谁可以投票、如何登记、需要什么证件、提前投票、邮寄投票和投票时间，资料来自Elections BC。")
    path = url_for(lang, "how-to-vote-bc")
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [(L("首页"), "/"), (L("如何投票"), path)]),
               faq_schema([(L(q), L(a_)) for q, a_ in HOW_FAQ_ZH])]
    return render(lang, "how-to-vote-bc", title, desc, body, GROUPS["how"], schemas)


# ---------------------------------------------------------------- groups + sitemap
GROUPS = {
    "hub": {"en": "bc-election-2026", "zh-cn": "bc-election-2026", "zh-tw": "bc-election-2026"},
    "polls": {"en": "bc-election-polls", "zh-cn": "bc-election-polls", "zh-tw": "bc-election-polls"},
    "how": {"en": "how-to-vote-bc", "zh-cn": "how-to-vote-bc", "zh-tw": "how-to-vote-bc"},
}
EN_ONLY = ["", "bc-party-leaders", "bc-election-candidates-2026", "bc-election-ridings", "sources"]


def sitemap():
    def loc(l, s):
        return SITE + (url_for(l, s) if s else "/")

    entries = []
    for s in EN_ONLY:
        entries.append(f"<url><loc>{loc('en', s)}</loc><lastmod>{TODAY}</lastmod></url>")
    for g in GROUPS.values():
        for l, s in g.items():
            links = "".join(
                f'<xhtml:link rel="alternate" hreflang="{HREFLANG[ll]}" href="{loc(ll, ss)}"/>' for ll, ss in g.items()
            ) + f'<xhtml:link rel="alternate" hreflang="x-default" href="{loc("en", g["en"])}"/>'
            entries.append(f"<url><loc>{loc(l, s)}</loc><lastmod>{TODAY}</lastmod>{links}</url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(entries) + "\n</urlset>\n"
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf8") as f:
        f.write(xml)
    return len(entries)


def patch_static():
    """sources.html and 404.html keep their body; only the nav gets the new link."""
    nav_old = '<a href="/bc-election-polls">Polls</a><a href="/how-to-vote-bc">How to Vote</a>'
    for name in ("sources.html", "404.html"):
        p = os.path.join(ROOT, name)
        s = open(p, encoding="utf8").read()
        if "/bc-party-leaders" not in s and '<a href="/bc-election-polls">Polls</a>' in s:
            s = s.replace('<a href="/bc-election-polls">Polls</a>', '<a href="/bc-election-polls">Polls</a><a href="/bc-party-leaders">Party Leaders</a>')
            open(p, "w", encoding="utf8").write(s)


if __name__ == "__main__":
    page_home_en()
    page_hub_en()
    page_polls_en()
    page_how_en()
    page_leaders_en()
    page_candidates_en()
    page_ridings_en()
    for lang in ("zh-cn", "zh-tw"):
        page_hub_zh(lang)
        page_polls_zh(lang)
        page_how_zh(lang)
    patch_static()
    print("sitemap urls:", sitemap())
