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
TODAY = "2026-09-22"
TODAY_EN = "September 22, 2026"
TODAY_ZH = "2026年9月22日"
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
    "sov": "https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf",
    "byel": "https://elections.bc.ca/2026-abbotsford-mission-by-election/",
    "byel_cands": "https://elections.bc.ca/news/abbotsford-mission-by-election-candidates-confirmed/",
    "byel_writ": "https://elections.bc.ca/news/writ-issued-for-2026-abbotsford-mission-by-election/",
    "leger": "https://leger360.com/in-the-news-bc-politics-ndp-narrow-lead-april-2026-leger/",
    "centrebc": "https://www.centrebc.ca/",
    "ctv_milobar": "https://www.ctvnews.ca/vancouver/article/peter-milobar-named-centrebc-party-leader-mike-bernier-stepping-down/",
    "ebc_2026": "https://elections.bc.ca/2026-provincial-election/",
    "ebc_2026_cands": "https://elections.bc.ca/2026-provincial-election/candidate-list/",
    "infonews_call": "https://infonews.ca/news/7880776/bc-premier-eby-calls-early-election-for-oct-24-says-trump-is-existential-threat/",
    "ctv_findlay_resign": "https://www.ctvnews.ca/vancouver/article/kerry-lynne-findlay-resigns-as-bc-conservative-leader/",
    "comox_doerkson": "https://comoxvalleyrecord.com/2026/09/21/b-c-conservatives-appoint-lorne-doerkson-interim-leader/",
    "wiki_byel_cancel": "https://en.wikipedia.org/wiki/2026_Abbotsford-Mission_provincial_by-election",
    "leger_jun": "https://leger360.com/in-the-news-bc-conservatives-take-narrow-lead/",
}


def a(key, text):
    return f'<a href="{SRC[key]}" rel="noopener">{text}</a>'


# ---------------------------------------------------------------- page shell
ICONS = (
    '<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/favicon.svg" type="image/svg+xml" sizes="any">'
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">'
    '<meta name="theme-color" content="#b5121b">'
)
NAV_EN = [
    ("/bc-election-2026", "BC Election"),
    ("/bc-election-polls", "Polls"),
    ("/bc-party-leaders", "Party Leaders"),
    ("/bc-election-issues", "Issues"),
    ("/abbotsford-mission-by-election-2026", "Abbotsford-Mission"),
    ("/bc-election-results-2024", "2024 Results"),
    ("/bc-election-candidates-2026", "Candidates"),
    ("/bc-election-ridings", "Ridings"),
    ("/how-to-vote-bc", "How to Vote"),
    ("/sources", "Sources"),
]
NAV_ZH = [
    ("bc-election-2026", "省选2026"),
    ("bc-election-polls", "民调"),
    ("bc-party-leaders", "党魁"),
    ("bc-election-issues", "议题"),
    ("abbotsford-mission-by-election-2026", "Abbotsford-Mission"),
    ("bc-election-results-2024", "2024结果"),
    ("bc-election-ridings", "选区"),
    ("how-to-vote-bc", "如何投票"),
]
HREFLANG = {"en": "en-CA", "zh-cn": "zh-Hans", "zh-tw": "zh-Hant"}
OG_LOCALE = {"en": "en_CA", "zh-cn": "zh_CN", "zh-tw": "zh_TW"}
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
        f'<meta property="og:locale" content="{OG_LOCALE[lang]}">'
        f'<meta property="og:image" content="{SITE}/assets/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title)}"><meta name="twitter:description" content="{html.escape(desc)}"><meta name="twitter:image" content="{SITE}/assets/og-image.png">'
        + ICONS +
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
    '<div class="status" data-election-status><span class="badge" data-status-label>Provincial election called — vote October 24, 2026</span>'
    '<strong>Current official status</strong><span data-status-detail>Premier David Eby called the election on September 22, 2026. '
    'Voting day is Saturday, October 24, 2026.</span><small data-status-checked>Last checked September 22, 2026</small></div>'
)
STATUS_BOX_ZH = (
    '<div class="status" data-election-status><span class="badge" data-status-label>省选已宣布 · 2026年10月24日投票</span>'
    '<strong>目前官方状态</strong><span data-status-detail>省长David Eby于2026年9月22日宣布举行省选，投票日为2026年10月24日（星期六）。'
    '</span><small data-status-checked>最后核对 2026年9月22日</small></div>'
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


KEY_DATES = [
    ("Writ Day (campaign begins)", "September 22, 2026"),
    ("Nomination deadline", "October 3, 2026, 1 p.m."),
    ("Advance voting", "October 16\u201321, 2026, 8 a.m.\u20138 p.m."),
    ("Vote-by-mail request deadline (online/phone)", "October 18, 2026"),
    ("Final Voting Day", "Saturday, October 24, 2026, 8 a.m.\u20138 p.m."),
    ("Final count", "November 6\u201310, 2026"),
    ("Return Day (result becomes official)", "November 18, 2026"),
]
KEY_DATES_ZH = [
    ("提名令状日（竞选期开始）", "2026年9月22日"),
    ("提名截止", "2026年10月3日下午1点"),
    ("提前投票", "2026年10月16至21日，上午8点至晚上8点"),
    ("邮寄选票申请截止（网上／电话）", "2026年10月18日"),
    ("最终投票日", "2026年10月24日（星期六），上午8点至晚上8点"),
    ("最终点票", "2026年11月6至10日"),
    ("结果确认日（Return Day）", "2026年11月18日"),
]


def key_dates_table_en():
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in KEY_DATES)
    return f'<div class="tablewrap"><table><tbody>{rows}</tbody></table></div>'


def key_dates_table_zh():
    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in KEY_DATES_ZH)
    return f'<div class="tablewrap"><table><tbody>{rows}</tbody></table></div>'


def general_election_event(lang):
    return {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "British Columbia 2026 provincial general election" if lang == "en" else conv(lang, "2026年BC省省选"),
        "startDate": "2026-10-24T08:00-07:00",
        "endDate": "2026-10-24T20:00-07:00",
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {"@type": "Place", "name": "British Columbia, Canada",
                     "address": {"@type": "PostalAddress", "addressRegion": "BC", "addressCountry": "CA"}},
        "organizer": {"@type": "Organization", "name": "Elections BC", "url": "https://elections.bc.ca/"},
        "description": "British Columbia provincial general election, called September 22, 2026.",
        "image": SITE + "/assets/og-image.png",
    }


POLL_ROWS = [
    # pollster key, name, field, sample, ndp, con, grn, ctr, one, note
    ("angus", "Angus Reid", "Sep 8–15, 2026 (released Sep 17)", "749 adults, online; comparable probability sample ±4.0", 41, 37, None, None, None, "Only the NDP/Conservative vote-intention figures found in the release; see the full report for other parties. 51% said they feel like a “political orphan.”"),
    ("ipsos", "Ipsos", "Sep 8–14, 2026 (released Sep 15)", "800 adults, online panel; ±4.0 credibility interval", 45, 35, 10, 4, 2, "Other 4%. 28% undecided or no preference."),
    ("research", "Research Co.", "Aug 12–14, 2026 (published Aug 18)", "801 adults, online; ±3.5", 44, 39, 10, 5, 1, "Decided voters. NDP regained the lead after trailing in June."),
    ("leger_jun", "Leger", "Jun 1–2, 2026 (published Jun 5)", "1,002 adults, online panel; comparable probability sample ±3.1", 41, 45, 8, None, None, "Conservatives led just after Findlay became leader; only 26% said they were familiar with her."),
    ("leger", "Leger", "Apr 3–6, 2026 (published May 4)", "1,003 adults, online panel; comparable probability sample ±3.1", 44, 40, None, None, None, "Only NDP and Conservative figures shown here; see the release for other parties. 54% said the province is on the wrong track."),
]

# =============================================================== ENGLISH PAGES
HUB_FAQ_EN = [
    ("Is there a BC election in 2026?",
     f"Yes. Premier David Eby called a provincial general election on September 22, 2026. Voting day is Saturday, October 24, 2026 ({a('infonews_call', 'iNFOnews')}; {a('ebc_2026', 'Elections BC')})."),
    ("When is the BC election?",
     "Saturday, October 24, 2026. Advance voting runs October 16–21, and the nomination deadline for candidates is October 3 at 1 p.m., according to Elections BC."),
    ("Why did Eby call an early election?",
     f"Eby cited the trade war with the United States, calling it an “existential” issue for BC that voters should have a say on ({a('infonews_call', 'iNFOnews')}). BC's fixed election date was not due until October 21, 2028; the {a('ebc_next', 'Election Act')} lets the government call one earlier."),
    ("Does the BC election overlap with municipal elections?",
     "Yes. BC municipal elections are October 17, 2026, one week before the October 24 provincial vote. Some municipal leaders raised concerns about the two campaigns overlapping."),
    ("Who leads in BC election polls?",
     "The most recent pre-writ polls (Ipsos, Sept 8–14, and Angus Reid, Sept 8–15) had the NDP ahead of the Conservatives, 45%–35% and 41%–37%. Earlier in the campaign year Leger had the Conservatives ahead in June. See the <a href=\"/bc-election-polls\">BC election polls page</a>."),
    ("Who are the BC party leaders?",
     "David Eby leads the BC NDP, Lorne Doerkson is interim leader of the BC Conservatives (after Kerry-Lynne Findlay resigned September 20, 2026), Emily Lowan leads the BC Greens, Peter Milobar leads CentreBC and Dallas Brodie leads OneBC. See <a href=\"/bc-party-leaders\">BC party leaders</a>."),
    ("What happened to the Abbotsford-Mission by-election?",
     f"It was cancelled. Elections BC says the general election call on September 22 cancelled the by-election that had been scheduled for September 26, and folded the riding into the province-wide vote; ballots already cast do not count ({a('byel', 'Elections BC')}; {a('wiki_byel_cancel', 'Wikipedia summary')})."),
]


def page_hub_en():
    latest = (
        "<ul>"
        f"<li><strong>Sep 22, 2026</strong> — Premier David Eby called a provincial election, citing the U.S. trade war as an “existential” issue for BC. Voting day is Saturday, October 24, 2026 ({a('infonews_call','iNFOnews')}). The pending Abbotsford-Mission by-election was cancelled and folded into the general vote ({a('byel','Elections BC')}).</li>"
        f"<li><strong>Sep 21, 2026</strong> — The Conservative caucus named Lorne Doerkson (Cariboo-Chilcotin) interim leader by unanimous vote, after Findlay's resignation ({a('comox_doerkson','Comox Valley Record')}).</li>"
        f"<li><strong>Sep 20, 2026</strong> — Kerry-Lynne Findlay resigned as Conservative leader after 14 MLAs left the caucus since August ({a('ctv_findlay_resign','CTV News')}).</li>"
        f"<li><strong>Sep 15–17, 2026</strong> — Pre-writ polls: Ipsos had the NDP at 45% and the Conservatives at 35% (Sept 8–14); {a('angus','Angus Reid')} had the NDP at 41% and the Conservatives at 37% (Sept 8–15). <a href=\"/bc-election-polls\">All polls</a>.</li>"
        "</ul>"
    )
    body = (
        hero("BC Election 2026", "BC votes October 24, 2026",
             f"Premier David Eby called a provincial general election on September 22, 2026. British Columbians elect all 93 MLAs on Saturday, October 24, 2026. See the {a('ebc_2026','official Elections BC election page')} for the current, authoritative record.",
             STATUS_BOX_EN)
        + f'<section class="section"><div class="wrap"><h2>Latest developments</h2>{latest}<p class="source-note">Each item links to its source. Party standings and candidates are changing quickly during the campaign; see <a href="/bc-party-leaders">party leaders</a> and <a href="/bc-election-candidates-2026">candidates</a>.</p></div></section>'
        + '<section class="section soft"><div class="wrap"><h2>Key dates for the October 24 election</h2>'
        + key_dates_table_en()
        + f'<p class="source-note">Source: {a("ebc_2026","Elections BC — 2026 Provincial Election")}. This matches the Sept 16–22 call-window scenario Elections BC had already published in its {a("ebc_cal","Fall 2026 calendar")}: advance voting Oct 16–21, Final Voting Day Oct 24.</p></div></section>'
        + '<section class="section"><div class="wrap"><h2>Why now</h2>'
        f"<p>Elections BC's fixed-date law lets an election come early if the government decides to call one or loses the confidence of the Legislative Assembly ({a('ebc_next','Elections BC')}). Eby cited the trade war with the United States, calling it an “existential” issue for BC that voters should have a say on ({a('infonews_call','iNFOnews')}).</p>"
        f"<p>At the 2024 general election (October 19, 2024) the NDP won 47 of 93 seats, a one-seat majority ({a('wiki_2024','results summary')}). Since then the Conservative caucus has splintered: eight members left to form CentreBC, others to OneBC or as independents, and leader Kerry-Lynne Findlay resigned September 20 after 14 MLAs departed since August. See <a href=\"/bc-party-leaders\">current party leaders</a> and <a href=\"/bc-election-results-2024\">the 2024 results</a>.</p></div></section>"
        + faq_html(HUB_FAQ_EN, "BC election 2026 FAQ")
        + '<section class="section"><div class="wrap"><h2>Keep going</h2><div class="linkgrid">'
        '<a class="linkcard" href="/bc-election-polls"><strong>BC election polls 2026</strong><span>NDP vs Conservatives with field dates and sample sizes.</span></a>'
        '<a class="linkcard" href="/bc-party-leaders"><strong>BC party leaders</strong><span>Who leads each party as the campaign starts.</span></a>'
        '<a class="linkcard" href="/bc-election-issues"><strong>BC election issues</strong><span>Housing, health care, the budget and tariffs: facts and party positions.</span></a>'
        '<a class="linkcard" href="/bc-election-candidates-2026"><strong>BC election candidates 2026</strong><span>Nomination deadline October 3; where the official list appears.</span></a>'
        '<a class="linkcard" href="/abbotsford-mission-by-election-2026"><strong>Abbotsford-Mission by-election</strong><span>Cancelled Sept 22 and folded into the general election.</span></a>'
        '<a class="linkcard" href="/bc-election-results-2024"><strong>BC 2024 election results</strong><span>Official seats, votes and turnout.</span></a>'
        '<a class="linkcard" href="/how-to-vote-bc"><strong>How to vote in BC</strong><span>Eligibility, ID, advance voting and vote by mail.</span></a>'
        '<a class="linkcard" href="/bc-election-ridings"><strong>BC ridings</strong><span>Find your riding and its 2024 result.</span></a>'
        "</div></div></section>"
    )
    title = "BC Election 2026: Vote October 24"
    desc = "BC's provincial election was called Sept 22, 2026. Voting day is October 24. Key dates, why Eby called it, party leaders and polls, sourced to Elections BC."
    schemas = [article_schema(title, desc, "en", "/bc-election-2026"),
               breadcrumb("en", [("Home", "/"), ("BC Election 2026", "/bc-election-2026")]),
               faq_schema(HUB_FAQ_EN), general_election_event("en")]
    return render("en", "bc-election-2026", title, desc, body, GROUPS["hub"], schemas)


def page_polls_en():
    def row(p):
        _, name, field, sample, n, c, g, ct, o, note = p
        pc = lambda v: f"{v}%" if v is not None else "—"
        return f"<tr><td><strong>{name}</strong></td><td>{field}</td><td>{sample}</td><td>{pc(n)}</td><td>{pc(c)}</td><td>{pc(g)}</td><td>{pc(ct)}</td><td>{pc(o)}</td><td>{note}</td></tr>"

    rows = "".join(row(p) for p in POLL_ROWS)
    body = (
        hero("Polling monitor", "BC election polls 2026: before the October 24 vote",
             "Five published BC polls show a swing: the Conservatives led in June, but every poll since mid-August has put the NDP ahead, as the Conservative caucus lost 14 MLAs and its leader resigned. A poll measures respondents at one point in time; it is not a forecast or a result.")
        + '<section class="section"><div class="wrap"><h2>Vote intention (decided voters)</h2><div class="tablewrap"><table><thead><tr><th>Pollster</th><th>Field dates</th><th>Sample</th><th>NDP</th><th>Cons.</th><th>Green</th><th>CentreBC</th><th>OneBC</th><th>Notes</th></tr></thead><tbody>'
        + rows
        + f'</tbody></table></div><p class="source-note">Sources: {a("angus","Angus Reid")}, {a("ipsos","Ipsos")}, {a("research","Research Co.")} and {a("leger_jun","Leger (June)")} and {a("leger","Leger (April)")}. Ipsos reports the Conservatives down 8 points from their 2024 result (43.3% in 2024). All five polls were taken before the election was called on September 22, 2026.</p></div></section>'
        + '<section class="section soft"><div class="wrap"><h2>Leader ratings</h2><div class="grid">'
        '<div class="card"><div class="kicker">Ipsos · favourable / unfavourable</div><p>David Eby (NDP): <strong>41% / 30%</strong><br>Kerry-Lynne Findlay (Cons.): <strong>17% / 46%</strong><br>Emily Lowan (Green): 12% / 15%<br>Dallas Brodie (OneBC): 10% / 24%<br>Mike Bernier (then CentreBC leader): 9% / 19%</p></div>'
        '<div class="card"><div class="kicker">Research Co. · approval</div><p>Eby: <strong>49%</strong><br>Lowan: 38%<br>Findlay: 34%<br>Bernier (then CentreBC leader): 24%<br>Brodie: 18%</p></div>'
        f'<div class="card"><div class="kicker">Angus Reid · Sep 8–15, released Sep 17</div><p>Eby approval <strong>41%</strong>. 51% say they feel like a “political orphan” with no party to enthusiastically support. Full tables in the {a("angus","Angus Reid release")}.</p></div>'
        "</div><p class=\"source-note\">These are three different measures (favourability, approval, and a party-support sentiment) from different firms; they are not directly comparable. All were taken before CentreBC named Peter Milobar leader (Sept 18), before Kerry-Lynne Findlay resigned as Conservative leader (Sept 20) and before Lorne Doerkson became interim Conservative leader (Sept 21); their ratings refer to Bernier and Findlay respectively. See <a href=\"/bc-party-leaders\">current party leaders</a>.</p></div></section>"
        + '<section class="section"><div class="wrap"><h2>How to read these polls</h2><ul>'
        "<li><strong>The Conservative number moved fast.</strong> Leger had the Conservatives ahead 45–41 in June; by September, Ipsos had the NDP ahead 45–35. In between, 14 Conservative MLAs left caucus, Findlay resigned as leader, and Lorne Doerkson was named interim leader. See <a href=\"/bc-party-leaders\">party leaders</a>.</li>"
        "<li><strong>Undecided voters matter.</strong> Ipsos reports 28% undecided or with no preference; the table shows decided voters only.</li>"
        "<li><strong>Regions matter more than the provincial number.</strong> Research Co. found the Conservatives dominant in Northern BC and the Fraser Valley and Metro Vancouver tight, while the NDP leads on Vancouver Island. BC uses first-past-the-post in 93 ridings, so seats depend on where votes fall.</li>"
        "<li><strong>New parties can split the vote.</strong> CentreBC and OneBC are new parties that now appear alongside the Greens in polling (Ipsos describes them as two new parties).</li>"
        "<li><strong>Margins of error.</strong> A ±3.1 to ±4.0 point margin means a close race can be within combined uncertainty for a single poll.</li></ul>"
        '<p class="source-note">Polls are added only with pollster, field dates, sample and source link. No poll has been published with field dates after the September 22 election call as of this writing. Ridings, candidates and seat projections are not covered here. See <a href="/bc-election-2026">the election guide</a> for status and <a href="/sources">our sourcing rules</a>.</p></div></section>'
    )
    title = "BC Election Polls 2026: Before the Oct 24 Vote"
    desc = "BC election polls ahead of the Oct 24, 2026 vote: Conservatives led in June (45–41), NDP led by September (45–35). Field dates, samples and margins."
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
        hero("Voting information", "How to vote in the BC provincial election",
             f"Who can vote, how to register, what ID to bring and the ways to vote, for the October 24, 2026 general election. Advance voting is October 16–21; the nomination deadline is October 3. Rules below are Elections BC's current published rules ({a('ebc_2026','official election page')}).")
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
    title = "How to Vote in BC: ID, Advance, Mail Voting"
    desc = "How to vote in a BC provincial election: who can vote, how to register, what ID to bring, advance voting, vote by mail and voting hours, from Elections BC."
    schemas = [article_schema(title, desc, "en", "/how-to-vote-bc"),
               breadcrumb("en", [("Home", "/"), ("How to Vote in BC", "/how-to-vote-bc")]),
               faq_schema(HOW_FAQ_EN)]
    return render("en", "how-to-vote-bc", title, desc, body, GROUPS["how"], schemas)


def page_leaders_en():
    body = (
        hero("Party leaders", "BC party leaders 2026",
             "Who leads each party in British Columbia heading into the October 24, 2026 election, with the source for each claim.")
        + '<section class="section"><div class="wrap"><div class="tablewrap"><table><thead><tr><th>Party</th><th>Leader</th><th>Notes</th></tr></thead><tbody>'
        f"<tr><td><strong>BC NDP</strong></td><td>David Eby</td><td>Premier. Won a one-seat majority (47 of 93) in October 2024 ({a('wiki_2024','results summary')}). Called the October 24, 2026 election on September 22 ({a('infonews_call','iNFOnews')}).</td></tr>"
        f"<tr><td><strong>Conservative Party of BC</strong></td><td>Lorne Doerkson <em>(interim)</em></td><td>Named interim leader September 21, 2026 by unanimous caucus vote ({a('comox_doerkson','Comox Valley Record')}); MLA for Cariboo-Chilcotin, elected as a Conservative in 2024. Kerry-Lynne Findlay, elected leader May 30, 2026, resigned September 20 after 14 MLAs left the caucus since August ({a('ctv_findlay_resign','CTV News')}). Her candidacy in the October 24 general election was not confirmed by Elections BC as of {TODAY_EN}; the by-election she had been running in was cancelled when the general election was called.</td></tr>"
        f"<tr><td><strong>BC Greens</strong></td><td>Emily Lowan</td><td>Named as Green leader in the {a('ipsos','Ipsos')} and {a('research','Research Co.')} polls. Two seats won in 2024.</td></tr>"
        f"<tr><td><strong>CentreBC</strong></td><td>Peter Milobar</td><td>Named leader on September 18, 2026, replacing Mike Bernier ({a('ctv_milobar','CTV News')}). CentreBC lists eight MLAs, with Milobar as leader and MLA for Kamloops Centre ({a('centrebc','CentreBC')}). New party that appears in polling (4% Ipsos, 5% Research Co., 8% Leger in June).</td></tr>"
        f"<tr><td><strong>OneBC</strong></td><td>Dallas Brodie</td><td>New party that now appears in polling (2% Ipsos, 1% Research Co.).</td></tr>"
        "</tbody></table></div>"
        f"<p class=\"source-note\">The composition of the 43rd Parliament shifted repeatedly through 2025–26 as members changed parties or sat as independents ({a('wiki_43','overview')}), and the Legislature has now been dissolved for the election. For the pre-dissolution record use the {a('leg','Legislative Assembly of BC')}; BC Vote Watch will publish seat standings once each figure is confirmed against the Assembly.</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>How voters rated them before the writ</h2>'
        "<p>Ipsos (Sept 8–14, 2026) found Eby 41% favourable / 30% unfavourable and Findlay 17% / 46%. Research Co. (Aug 12–14) recorded approval of 49% for Eby, 38% for Lowan and 34% for Findlay. These ratings predate Findlay's resignation and Doerkson's appointment. Full numbers and methods are on the <a href=\"/bc-election-polls\">BC election polls page</a>.</p>"
        '<p>See the <a href="/bc-election-2026">BC election 2026 guide</a> for key dates.</p></div></section>'
    )
    title = "BC Party Leaders 2026: Eby, Doerkson, Lowan"
    desc = "Who leads the BC NDP, BC Conservatives, BC Greens, CentreBC and OneBC ahead of the Oct 24, 2026 election. Doerkson interim Conservative leader since Sept 21."
    schemas = [article_schema(title, desc, "en", "/bc-party-leaders"),
               breadcrumb("en", [("Home", "/"), ("BC Party Leaders", "/bc-party-leaders")])]
    return render("en", "bc-party-leaders", title, desc, body, GROUPS["leaders"], schemas)


def page_candidates_en():
    body = (
        hero("Candidates", "BC election candidates 2026",
             f"Nominations for the October 24, 2026 general election close October 3 at 1 p.m. Elections BC publishes accepted nominations as they are confirmed; the list is not final until the deadline. See the {a('ebc_2026_cands','official candidate list')}.")
        + '<section class="section"><div class="wrap"><h2>Where things stand</h2>'
        f"<p>Under Elections BC's process, a nomination is only official once Elections BC accepts it; see {a('ebc_nom','Elections BC candidate nominations')} and the {a('ebc_2026_cands','current candidate list')}, which Elections BC says “does not show all candidates that have declared publicly that they are running” — only those it has accepted.</p>"
        "<p>BC Vote Watch will keep the two apart: <strong>official candidates</strong> (Elections BC record, dated) and <strong>announced or expected candidates</strong> (party or candidate statement, dated and linked). The Abbotsford-Mission by-election, which had five confirmed candidates, was cancelled September 22 when the general election was called; see the <a href=\"/abbotsford-mission-by-election-2026\">Abbotsford-Mission page</a>.</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>Who is leading the parties</h2>'
        "<p>The party leaders are the people voters will see across the campaign. See <a href=\"/bc-party-leaders\">BC party leaders 2026</a>. For polling see <a href=\"/bc-election-polls\">BC election polls</a>, and for key dates see the <a href=\"/bc-election-2026\">BC election 2026 guide</a>.</p>"
        f"<p class=\"source-note\">There are 93 electoral districts in BC; each elects one MLA. Riding information, including the 2024 result for each seat, is on the <a href=\"/bc-election-ridings\">BC ridings page</a>.</p></div></section>"
    )
    title = "BC Election Candidates 2026: Nominations"
    desc = "BC election candidates 2026: nominations close October 3 at 1 p.m. How the official Elections BC candidate list works and where to find it."
    schemas = [article_schema(title, desc, "en", "/bc-election-candidates-2026"),
               breadcrumb("en", [("Home", "/"), ("BC Election Candidates 2026", "/bc-election-candidates-2026")])]
    return render("en", "bc-election-candidates-2026", title, desc, body, None, schemas)


def page_home_en():
    body = (
        hero("British Columbia · Provincial election", "BC election 2026: vote October 24",
             "Independent, source-backed tracking of BC's 2026 provincial election: key dates, polls, party leaders, candidates, ridings and voting information. Official records, reported developments and analysis are labelled separately.",
             STATUS_BOX_EN.replace("Current official status", "Election watch"))
        + '<section class="section"><div class="wrap"><div class="grid">'
        '<div class="card"><div class="kicker">Election called</div><div class="big">Sep 22, 2026</div><p class="muted">Premier Eby called the election, citing the U.S. trade war.</p></div>'
        '<div class="card"><div class="kicker">Voting day</div><div class="big">Oct 24, 2026</div><p class="muted">Advance voting Oct 16–21; nominations close Oct 3. <a href="/bc-election-2026">Key dates</a></p></div>'
        '<div class="card"><div class="kicker">Latest pre-writ poll (Ipsos, Sep 8–14)</div><div class="big">NDP 45 · Cons. 35</div><p class="muted">Decided voters; Angus Reid (Sep 8–15) has 41–37. <a href="/bc-election-polls">All polls</a></p></div>'
        "</div></div></section>"
        '<section class="section soft"><div class="wrap"><h2>Track the 2026 BC election</h2><div class="linkgrid">'
        '<a class="linkcard" href="/bc-election-2026"><strong>BC Election 2026 Guide</strong><span>Key dates, why Eby called it, and the latest news.</span></a>'
        '<a class="linkcard" href="/bc-election-polls"><strong>BC Election Polls</strong><span>NDP vs Conservatives with field dates, samples and margins.</span></a>'
        '<a class="linkcard" href="/bc-party-leaders"><strong>BC Party Leaders</strong><span>Eby, Doerkson (interim), Lowan, Milobar and Brodie.</span></a>'
        '<a class="linkcard" href="/bc-election-issues"><strong>BC Election Issues</strong><span>Housing, health care, budget and tariffs with sourced party positions.</span></a>'
        '<a class="linkcard" href="/bc-election-candidates-2026"><strong>BC Election Candidates 2026</strong><span>Nomination deadline October 3; where the official list appears.</span></a>'
        '<a class="linkcard" href="/abbotsford-mission-by-election-2026"><strong>Abbotsford-Mission By-election</strong><span>Cancelled Sept 22 and folded into the general election.</span></a>'
        '<a class="linkcard" href="/bc-election-results-2024"><strong>BC 2024 Election Results</strong><span>Official seats, votes and turnout from Elections BC.</span></a>'
        '<a class="linkcard" href="/how-to-vote-bc"><strong>How to Vote in BC</strong><span>Eligibility, ID, advance voting and vote by mail.</span></a>'
        '<a class="linkcard" href="/bc-election-ridings"><strong>BC Ridings</strong><span>Official 2024 results for all 93 ridings, and the closest races.</span></a>'
        "</div></div></section>"
        '<section class="section"><div class="wrap"><h2>Official-source first</h2>'
        "<p>Election dates and rules follow Elections BC's official record. Candidate status is not treated as final until it appears in the relevant Elections BC record. Polls are presented as measurements at the field dates, not as election results or forecasts.</p>"
        f"<p class=\"source-note\">Primary source: {a('ebc_2026','Elections BC — 2026 Provincial Election')}. 中文：<a href=\"/zh-cn/bc-election-2026\" hreflang=\"zh-Hans\">简体</a> · <a href=\"/zh-tw/bc-election-2026\" hreflang=\"zh-Hant\">繁體</a></p></div></section>"
    )
    title = "BC Election 2026: Vote October 24"
    desc = "Independent tracking of BC's 2026 provincial election, called Sept 22: key dates, polls, party leaders, candidates, ridings and voting information."
    schemas = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "BC Vote Watch", "url": SITE + "/", "inLanguage": ["en-CA", "zh-Hans", "zh-Hant"]},
        {"@context": "https://schema.org", "@type": "Organization", "name": "BC Vote Watch", "url": SITE + "/", "logo": SITE + "/icon-512.png"},
        general_election_event("en"),
    ]
    return render("en", "", title, desc, body, None, schemas)


# ================================================================ CHINESE PAGES
def hub_faq_zh(lang):
    return [
    ("2026年BC省有省选吗？",
     f"有。省长David Eby于2026年9月22日宣布举行省选，投票日为2026年10月24日（星期六）（{a('infonews_call','iNFOnews')}；{a('ebc_2026','Elections BC')}）。"),
    ("BC省省选是什么时候？",
     "2026年10月24日（星期六）。根据 Elections BC，提前投票为10月16至21日，候选人提名截止日为10月3日下午1点。"),
    ("Eby为什么提前宣布省选？",
     f"Eby表示与美国的贸易战对BC省是“生死攸关”（existential）的问题，选民应该有发言权（{a('infonews_call','iNFOnews')}）。BC省原定的固定选举日期是2028年10月21日；{a('ebc_next','选举法')}允许政府提前宣布。"),
    ("BC省选和市选时间重叠吗？",
     "重叠。BC省市选定于2026年10月17日，比10月24日的省选早一周。部分市政官员对两场选举时间相近表示担忧。"),
    ("目前民调谁领先？",
     f"最新的选前民调（Ipsos，9月8至14日；Angus Reid，9月8至15日）都显示NDP领先保守党，分别为45%对35%和41%对37%。更早的6月，Leger曾显示保守党领先。见<a href=\"{url_for(lang,'bc-election-polls')}\">BC省选民调</a>。"),
    ("BC省各党党魁是谁？",
     f"David Eby领导BC NDP；Lorne Doerkson自Kerry-Lynne Findlay于2026年9月20日辞职后出任BC保守党临时党魁；Emily Lowan领导BC绿党；Peter Milobar领导CentreBC；Dallas Brodie领导OneBC。见<a href=\"{url_for(lang,'bc-party-leaders')}\">BC省党魁</a>。"),
    ("Abbotsford-Mission补选怎么样了？",
     f"已取消。Elections BC表示，9月22日宣布的省选取消了原定9月26日举行的补选，该选区并入全省投票；已经投出的选票不计入省选（{a('byel','Elections BC')}；{a('wiki_byel_cancel','维基百科摘要')}）。"),
]


def page_hub_zh(lang):
    L = lambda s: conv(lang, s)
    latest = (
        "<ul>"
        f"<li><strong>2026年9月22日</strong> — 省长David Eby宣布举行省选，并称与美国的贸易战对BC是“生死攸关”的问题；投票日为2026年10月24日（星期六）（{a('infonews_call','iNFOnews')}）。原定的Abbotsford-Mission补选被取消，并入省选（{a('byel','Elections BC')}）。</li>"
        f"<li><strong>2026年9月21日</strong> — 保守党团一致投票，任命Lorne Doerkson（Cariboo-Chilcotin）为临时党魁（{a('comox_doerkson','Comox Valley Record')}）。</li>"
        f"<li><strong>2026年9月20日</strong> — Kerry-Lynne Findlay辞去保守党党魁职务；此前8月以来已有14名议员离开该党团（{a('ctv_findlay_resign','CTV News')}）。</li>"
        f"<li><strong>2026年9月15至17日</strong> — 选前民调：Ipsos显示NDP 45%、保守党35%（9月8至14日）；{a('angus','Angus Reid')}显示NDP 41%、保守党37%（9月8至15日）。<a href=\"{url_for(lang,'bc-election-polls')}\">查看全部民调</a>。</li>"
        "</ul>"
    )
    body = (
        hero("BC省选 2026", L("BC省将于2026年10月24日投票"),
             L(f"省长David Eby于2026年9月22日宣布举行省选。BC省居民将于2026年10月24日（星期六）选出全部93名省议员。详见{a('ebc_2026','Elections BC官方选举页面')}。"),
             STATUS_BOX_ZH)
        + f'<section class="section"><div class="wrap"><h2>{L("最新动态")}</h2>{L(latest)}<p class="source-note">{L("每一条都附有来源。竞选期间政党构成和候选人变化很快，见")}<a href="{url_for(lang,"bc-party-leaders")}">{L("党魁")}</a>{L("和")}<a href="/bc-election-candidates-2026">{L("候选人")}</a>{L("（英文）")}。</p></div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{L("2026年10月24日省选关键日期")}</h2>'
        + L(key_dates_table_zh())
        + f'<p class="source-note">{L("来源：")}{a("ebc_2026", L("Elections BC——2026年省选"))}。{L("这与 Elections BC 此前公布的“9月16至22日宣布”情景吻合：提前投票10月16至21日，最终投票日10月24日，见")}{a("ebc_cal", L("2026年秋季日历"))}。</p></div></section>'
        + f'<section class="section"><div class="wrap"><h2>{L("为什么是现在")}</h2>'
        + L(f"<p>BC省实行固定选举日期，但{a('ebc_next','Elections BC说明')}，如果政府决定提前宣布，或政府失去立法会信任，选举可以提前。Eby称与美国的贸易战对BC是“生死攸关”的问题，选民应该有发言权（{a('infonews_call','iNFOnews')}）。</p>")
        + L(f"<p>2024年10月19日省选中，NDP在93个议席中赢得47席，以一席优势组成多数政府（{a('wiki_2024','结果摘要')}）。此后保守党团出现分裂：八名议员另组CentreBC，另有议员转投OneBC或成为无党派议员，党魁Kerry-Lynne Findlay于9月20日辞职，此前8月以来已有14名议员离开。见<a href=\"{url_for(lang,'bc-party-leaders')}\">现任党魁</a>和<a href=\"{url_for(lang,'bc-election-results-2024')}\">2024年结果</a>。</p></div></section>")
        + L(faq_html(hub_faq_zh(lang), "BC省选2026常见问题"))
        + f'<section class="section"><div class="wrap"><h2>{L("继续了解")}</h2><div class="linkgrid">'
        f'<a class="linkcard" href="{url_for(lang,"bc-election-polls")}"><strong>{L("BC省选民调")}</strong><span>{L("NDP与保守党，附调查日期和样本量。")}</span></a>'
        f'<a class="linkcard" href="{url_for(lang,"bc-party-leaders")}"><strong>{L("BC省党魁")}</strong><span>{L("竞选开始时各党由谁领导。")}</span></a>'
        f'<a class="linkcard" href="{url_for(lang,"abbotsford-mission-by-election-2026")}"><strong>{L("Abbotsford-Mission")}</strong><span>{L("9月22日取消的补选，并入省选。")}</span></a>'
        f'<a class="linkcard" href="{url_for(lang,"how-to-vote-bc")}"><strong>{L("BC省如何投票")}</strong><span>{L("资格、身份证明、提前投票和邮寄投票。")}</span></a>'
        "</div></div></section>"
    )
    title = L("BC省选2026：10月24日投票")
    desc = L("BC省省选已于2026年9月22日宣布，投票日为10月24日。关键日期、Eby为何提前宣布、党魁与民调，来源均为Elections BC及公开报道。")
    path = url_for(lang, "bc-election-2026")
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [(L("首页"), "/"), (L("BC省选2026"), path)]),
               faq_schema([(L(q), L(a_)) for q, a_ in hub_faq_zh(lang)]), general_election_event(lang)]
    return render(lang, "bc-election-2026", title, desc, body, GROUPS["hub"], schemas)


POLL_ZH_META = {
    "angus": ("2026年9月8至15日（9月17日发布）", "749名成年人，线上；相当于概率样本±4.0", "此处仅列NDP和保守党的投票意向数字；其他政党见完整报告。51%表示自己是“政治孤儿”。"),
    "ipsos": ("2026年9月8至14日（9月15日发布）", "800名成年人，线上样本；可信区间±4.0", "其他4%；28%未决定或无偏好。"),
    "research": ("2026年8月12至14日（8月18日发布）", "801名成年人，线上；误差±3.5", "已决定选民；NDP在6月落后后重新领先。"),
    "leger_jun": ("2026年6月1至2日（6月5日发布）", "1,002名成年人，线上样本；相当于概率样本±3.1", "保守党在Findlay刚当选党魁后一度领先；当时只有26%的人认识她。"),
    "leger": ("2026年4月3至6日（5月4日发布）", "1,003名成年人，线上样本；相当于概率样本±3.1", "此处仅列NDP和保守党；其他政党见原报告。54%认为省份走错方向。"),
}


def page_polls_zh(lang):
    L = lambda s: conv(lang, s)
    rows = ""
    for key, name, field, sample, n, c, g, ct, o, note in POLL_ROWS:
        f_, s_, nt = POLL_ZH_META[key]
        pc = lambda v: f"{v}%" if v is not None else "—"
        rows += f"<tr><td><strong>{name}</strong></td><td>{f_}</td><td>{s_}</td><td>{pc(n)}</td><td>{pc(c)}</td><td>{pc(g)}</td><td>{pc(ct)}</td><td>{pc(o)}</td><td>{nt}</td></tr>"
    body = (
        hero("民调追踪", L("BC省选民调 2026：2026年10月24日投票前"),
             L("五项公开的BC省民调显示了一次逆转：保守党在6月领先，但从8月中起的每一项民调都是NDP领先，同期保守党团有14名议员离开、党魁辞职。民调只反映某一时间点的受访者意见，不是预测，也不是选举结果。"))
        + f'<section class="section"><div class="wrap"><h2>{L("政党支持度（已决定选民）")}</h2><div class="tablewrap"><table><thead><tr><th>{L("调查机构")}</th><th>{L("调查日期")}</th><th>{L("样本")}</th><th>NDP</th><th>{L("保守党")}</th><th>{L("绿党")}</th><th>CentreBC</th><th>OneBC</th><th>{L("备注")}</th></tr></thead><tbody>'
        + L(rows)
        + f'</tbody></table></div><p class="source-note">{L("来源：")}{a("angus","Angus Reid")}、{a("ipsos","Ipsos")}、{a("research","Research Co.")}、{a("leger_jun","Leger（6月）")}、{a("leger","Leger（4月）")}。{L("Ipsos指出保守党较2024年结果（43.3%）下降8个百分点。以上五项民调均在2026年9月22日宣布选举之前进行。")}</p></div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{L("党魁评价")}</h2><div class="grid">'
        + L('<div class="card"><div class="kicker">Ipsos · 好感／反感</div><p>David Eby（NDP）：<strong>41%／30%</strong><br>Kerry-Lynne Findlay（保守党）：<strong>17%／46%</strong><br>Emily Lowan（绿党）：12%／15%<br>Dallas Brodie（OneBC）：10%／24%<br>Mike Bernier（当时的CentreBC党魁）：9%／19%</p></div>')
        + L('<div class="card"><div class="kicker">Research Co. · 支持率</div><p>Eby：<strong>49%</strong><br>Lowan：38%<br>Findlay：34%<br>Bernier（当时的CentreBC党魁）：24%<br>Brodie：18%</p></div>')
        + L(f'<div class="card"><div class="kicker">Angus Reid · 9月8至15日，9月17日发布</div><p>Eby支持率<strong>41%</strong>。51%的人表示自己是“政治孤儿”，没有能热情支持的政党。完整数据见{a("angus","Angus Reid报告")}。</p></div>')
        + f'</div><p class="source-note">{L("这是不同机构的三种不同指标（好感度、支持率和政治情绪），不能直接互相比较。三项都在CentreBC于9月18日任命Peter Milobar为党魁、Findlay于9月20日辞去保守党党魁、Doerkson于9月21日出任临时党魁之前进行，因此评价对象分别是Bernier和Findlay。见")}<a href="{url_for(lang,"bc-party-leaders")}">{L("现任党魁")}</a>。</p></div></section>'
        + f'<section class="section"><div class="wrap"><h2>{L("如何解读这些民调")}</h2><ul>'
        + L(f'<li><strong>保守党的数字变化很快。</strong>Leger在6月显示保守党以45%对41%领先；到9月，Ipsos显示NDP以45%对35%领先。其间保守党团有14名议员离开、Findlay辞去党魁、Lorne Doerkson出任临时党魁。见<a href="{url_for(lang,"bc-party-leaders")}">党魁</a>。</li>')
        + L("<li><strong>未决定选民很重要。</strong>Ipsos显示28%未决定或无偏好；上表只列已决定选民。</li>")
        + L("<li><strong>地区比全省数字更重要。</strong>Research Co.发现保守党在北部BC占优，菲沙河谷和大温哥华竞争激烈，NDP则在温哥华岛领先。BC采用单一选区得票最多者当选（first-past-the-post）的93个选区，所以议席取决于选票分布。</li>")
        + L("<li><strong>新政党可能分流选票。</strong>CentreBC和OneBC是新政党，现在与绿党一起出现在民调中（Ipsos称之为两个新政党）。</li>")
        + L("<li><strong>误差范围。</strong>±3.1至±4.0个百分点的误差意味着接近的差距可能仍在综合不确定性之内。</li></ul>")
        + f'<p class="source-note">{L("民调只有在附上调查机构、调查日期、样本和来源链接后才会收录。截至发稿，尚无调查日期在9月22日选举宣布之后的民调发布。查看")}<a href="{url_for(lang,"bc-election-2026")}">{L("省选指南")}</a>{L("了解选举状态。")}</p></div></section>'
    )
    title = L("BC省选民调 2026：10月24日投票前")
    desc = L("BC省选前民调：保守党6月一度领先（45%对41%），NDP到9月领先（45%对35%）。附调查日期、样本、误差与党魁评价。")
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
             L(f"谁可以投票、如何登记、需要带什么证件以及投票方式，适用于2026年10月24日的省选。提前投票为10月16至21日，提名截止日为10月3日。以下是 Elections BC 目前公布的规则（{a('ebc_2026','官方选举页面')}）。"))
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


# ================================================================ BY-ELECTION
BYEL_CANDS = [
    ("Pam Alexis", "BC NDP", "NDP candidate in this riding in 2024 (44.62%, official result)."),
    ("Kerry-Lynne Findlay", "Conservative Party", "Elected leader of the BC Conservatives May 30, 2026; resigned as leader September 20."),
    ("Stephen Fowler", "BC Green Party", ""),
    ("Lakhwinder Jhaj", "CentreBC", ""),
    ("Jeff Monds", "Libertarian", ""),
]
BYEL_FAQ_EN = [
    ("Is the Abbotsford-Mission by-election still happening?",
     f"No. Elections BC cancelled it on September 22, 2026, when Premier Eby called the provincial general election. Abbotsford-Mission voters now take part in the October 24 general election instead ({a('byel','Elections BC')})."),
    ("Why was the by-election cancelled?",
     f"Under the Election Act, calling a general election dissolves the Legislature and cancels any pending by-election; the riding is folded into the province-wide vote ({a('wiki_byel_cancel','Wikipedia summary')})."),
    ("Do votes already cast in the by-election count?",
     f"No. Elections BC says voting in the by-election ended and any ballots cast will not count toward the general election; anyone who voted in the by-election must vote again on October 24 ({a('byel','Elections BC')})."),
    ("Who was running in the cancelled by-election?",
     f"Five candidates had been confirmed: Pam Alexis (BC NDP), Kerry-Lynne Findlay (Conservative Party), Stephen Fowler (BC Green Party), Lakhwinder Jhaj (CentreBC) and Jeff Monds (Libertarian) ({a('byel_cands','Elections BC candidate list')}). The general-election candidate list for Abbotsford-Mission may differ; nominations close October 3."),
    ("Why was there going to be a by-election in Abbotsford-Mission?",
     f"Elections BC said MLA Reann Gasper resigned on August 24, 2026 ({a('byel_writ','Elections BC')}). She had won the seat for the Conservatives in 2024."),
    ("Is Kerry-Lynne Findlay running in the October 24 general election?",
     f"BC Vote Watch could not confirm this from Elections BC as of {TODAY_EN}. Findlay resigned as Conservative leader on September 20, 2026; the by-election she had been contesting in Abbotsford-Mission was cancelled two days later. See <a href=\"/bc-party-leaders\">BC party leaders</a>."),
    ("Who can vote in Abbotsford-Mission on October 24?",
     f"Canadian citizens aged 18 or older who are BC residents; see <a href=\"/how-to-vote-bc\">how to vote in BC</a> for the general rules and ID requirements ({a('ebc_who','Elections BC')})."),
]


def byel_event(lang):
    return {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Abbotsford-Mission by-election (cancelled)" if lang == "en" else conv(lang, "Abbotsford-Mission补选（已取消）"),
        "startDate": "2026-09-26T08:00-07:00",
        "endDate": "2026-09-26T20:00-07:00",
        "eventStatus": "https://schema.org/EventCancelled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "location": {"@type": "Place", "name": "Abbotsford-Mission electoral district, British Columbia",
                     "address": {"@type": "PostalAddress", "addressRegion": "BC", "addressCountry": "CA"}},
        "organizer": {"@type": "Organization", "name": "Elections BC", "url": "https://elections.bc.ca/"},
        "description": "Provincial by-election in Abbotsford-Mission, British Columbia, cancelled September 22, 2026 when a general election was called.",
        "image": SITE + "/assets/og-image.png",
    }


def page_byel_en():
    zparty = {"BC NDP": "BC NDP", "Conservative Party": "Conservative", "BC Green Party": "Green", "CentreBC": "CentreBC", "Libertarian": "Libertarian"}
    rows = "".join(
        f"<tr><td><strong>{n}</strong></td><td>{zparty[p_]}</td><td>{note}</td></tr>" for n, p_, note in BYEL_CANDS
    )
    body = (
        hero("By-election cancelled", "Abbotsford-Mission by-election: cancelled",
             f"Elections BC cancelled the September 26, 2026 by-election on September 22, when Premier Eby called a provincial general election. Abbotsford-Mission voters choose their MLA on October 24, along with the rest of the province ({a('byel','Elections BC')}).")
        + '<section class="section"><div class="wrap"><h2>Quick answers</h2><ul>'
        "<li><strong>Status:</strong> Cancelled September 22, 2026, when the general election was called.</li>"
        "<li><strong>Ballots already cast:</strong> Do not count. Anyone who voted in the by-election must vote again.</li>"
        "<li><strong>What happens now:</strong> Abbotsford-Mission is part of the October 24, 2026 general election; the nomination deadline is October 3.</li>"
        f"<li><strong>By-election candidates (for reference):</strong> Pam Alexis (NDP), Kerry-Lynne Findlay (Conservative), Stephen Fowler (Green), Lakhwinder Jhaj (CentreBC), Jeff Monds (Libertarian); the general-election list may differ ({a('ebc_2026_cands','official candidate list')}).</li></ul></div></section>"
        + '<section class="section"><div class="wrap"><h2>What happened</h2>'
        f"<p>Elections BC says: “A provincial general election has been called. The 2026 Abbotsford-Mission by-election has been cancelled.” Voting in the by-election ended and any ballots cast will not count toward the general election ({a('byel','Elections BC')}). The by-election had been called after Conservative MLA Reann Gasper resigned on August 24, 2026 ({a('byel_writ','Elections BC')}); nominations for it had closed September 5 with five candidates confirmed ({a('byel_cands','Elections BC')}), and advance voting was already under way when the general election was called.</p>"
        f"<p>See <a href=\"/bc-election-2026\">why Eby called the October 24 election</a> and <a href=\"/bc-party-leaders\">current party leaders</a>, including the status of Conservative leader Kerry-Lynne Findlay, who had been the Conservative candidate in this by-election.</p></div></section>"
        + '<section class="section soft"><div class="wrap"><h2>Background: by-election candidates</h2><div class="tablewrap"><table><thead><tr><th>Candidate</th><th>Party</th><th>Notes</th></tr></thead><tbody>'
        + rows
        + f'</tbody></table></div><p class="source-note">This was the confirmed candidate list for the cancelled by-election ({a("byel_cands","Elections BC")}). It is not the general-election ballot; see the {a("ebc_2026_cands","official 2026 candidate list")} once nominations close October 3.</p></div></section>'
        + '<section class="section"><div class="wrap"><h2>How Abbotsford-Mission voted in 2024</h2>'
        f"<p>At the October 19, 2024 general election, Conservative Reann Gasper won Abbotsford-Mission with <strong>13,523 votes (55.38%)</strong>, ahead of NDP candidate Pam Alexis with <strong>10,894 votes (44.62%)</strong>. Source: {a('sov','Elections BC Statement of Votes')}. See the <a href=\"/ridings/abbotsford-mission\">Abbotsford-Mission riding page</a> and the province-wide <a href=\"/bc-election-results-2024\">2024 results</a>.</p>"
        "<p>This is background, not a forecast: general elections often differ from by-elections in turnout and campaign focus, and BC Vote Watch does not publish riding-level predictions.</p></div></section>"
        + faq_html(BYEL_FAQ_EN, "Abbotsford-Mission FAQ")
        + '<section class="section"><div class="wrap"><p class="source-note">Next: <a href="/bc-election-2026">BC election 2026: key dates</a> · <a href="/bc-election-candidates-2026">BC election candidates 2026</a> · <a href="/bc-election-polls">BC election polls</a> · <a href="/how-to-vote-bc">how to vote in BC</a>.</p></div></section>'
    )
    title = "Abbotsford-Mission By-election: Cancelled"
    desc = "The Sept 26, 2026 Abbotsford-Mission by-election was cancelled Sept 22 when a general election was called. What happened, and how the riding votes Oct 24."
    path = "/abbotsford-mission-by-election-2026"
    schemas = [article_schema(title, desc, "en", path),
               breadcrumb("en", [("Home", "/"), ("Abbotsford-Mission By-election", path)]),
               faq_schema(BYEL_FAQ_EN), byel_event("en")]
    return render("en", "abbotsford-mission-by-election-2026", title, desc, body, GROUPS["byel"], schemas)


def byel_faq_zh(lang):
    return [
    ("Abbotsford-Mission补选还会举行吗？",
     f"不会。Elections BC于2026年9月22日在省长Eby宣布举行省选后取消了这次补选。Abbotsford-Mission选民改为参加10月24日的省选（{a('byel','Elections BC')}）。"),
    ("为什么补选被取消？",
     f"根据选举法，宣布省选会解散立法会，任何待举行的补选都会被取消，该选区并入全省投票（{a('wiki_byel_cancel','维基百科摘要')}）。"),
    ("补选中已经投出的选票算数吗？",
     f"不算。Elections BC表示，补选的投票已经结束，任何已投出的选票都不计入省选；曾在补选中投票的人须在10月24日重新投票（{a('byel','Elections BC')}）。"),
    ("被取消的补选原本有哪些候选人？",
     f"原定五名候选人：Pam Alexis（BC NDP）、Kerry-Lynne Findlay（保守党）、Stephen Fowler（BC绿党）、Lakhwinder Jhaj（CentreBC）和Jeff Monds（自由意志党）（{a('byel_cands','Elections BC候选人名单')}）。省选中Abbotsford-Mission的候选人名单可能不同；提名截止日为10月3日。"),
    ("Abbotsford-Mission为什么原本要补选？",
     f"Elections BC表示，保守党议员Reann Gasper于2026年8月24日辞职（{a('byel_writ','Elections BC')}）。她在2024年代表保守党赢得该选区。"),
    ("Kerry-Lynne Findlay会参加10月24日的省选吗？",
     f"截至{TODAY_ZH}，BC Vote Watch未能从Elections BC确认这一点。Findlay于2026年9月20日辞去保守党党魁职务；她原本在Abbotsford-Mission参选的补选两天后被取消。见<a href=\"{url_for(lang,'bc-party-leaders')}\">BC省党魁</a>。"),
    ("10月24日谁可以在Abbotsford-Mission投票？",
     f"年满18岁的加拿大公民，且为BC省居民；一般规则和证件要求见<a href=\"{url_for(lang,'how-to-vote-bc')}\">BC省如何投票</a>（{a('ebc_who','Elections BC')}）。"),
]


def page_byel_zh(lang):
    L = lambda s: conv(lang, s)
    zparty = {"BC NDP": "BC NDP", "Conservative Party": "保守党", "BC Green Party": "BC绿党", "CentreBC": "CentreBC", "Libertarian": "自由意志党"}
    notes_zh = {
        "Pam Alexis": "2024年该选区的NDP候选人（得票44.62%，官方结果）。",
        "Kerry-Lynne Findlay": "2026年5月30日当选保守党党魁；9月20日辞去党魁职务。",
    }
    rows = "".join(
        f"<tr><td><strong>{n}</strong></td><td>{zparty[p_]}</td><td>{notes_zh.get(n, '')}</td></tr>" for n, p_, _ in BYEL_CANDS
    )
    body = (
        hero("补选已取消", L("Abbotsford-Mission补选：已取消"),
             L(f"Elections BC于2026年9月22日取消了原定9月26日举行的补选，原因是省长Eby宣布举行省选。Abbotsford-Mission选民将与全省一起在10月24日选出省议员（{a('byel','Elections BC')}）。"))
        + f'<section class="section"><div class="wrap"><h2>{L("快速答案")}</h2><ul>'
        + L("<li><strong>状态：</strong>2026年9月22日因省选宣布而取消。</li>")
        + L("<li><strong>已投出的选票：</strong>不计入省选。曾在补选中投票的人须重新投票。</li>")
        + L("<li><strong>现状：</strong>Abbotsford-Mission并入2026年10月24日的省选；提名截止日为10月3日。</li>")
        + L(f"<li><strong>补选候选人（仅供参考）：</strong>Pam Alexis（NDP）、Kerry-Lynne Findlay（保守党）、Stephen Fowler（绿党）、Lakhwinder Jhaj（CentreBC）、Jeff Monds（自由意志党）；省选名单可能不同（{a('ebc_2026_cands','官方候选人名单')}）。</li></ul></div></section>")
        + f'<section class="section"><div class="wrap"><h2>{L("发生了什么")}</h2>'
        + L(f"<p>Elections BC表示：“已宣布举行省选，2026年Abbotsford-Mission补选已被取消。”补选的投票已经结束，任何已投出的选票都不计入省选（{a('byel','Elections BC')}）。这次补选原因是保守党议员Reann Gasper于2026年8月24日辞职（{a('byel_writ','Elections BC')}）；提名已于9月5日截止，确认了五名候选人（{a('byel_cands','Elections BC')}），省选宣布时提前投票已经开始。</p>")
        + L(f"<p>见<a href=\"{url_for(lang,'bc-election-2026')}\">Eby为何宣布10月24日的省选</a>和<a href=\"{url_for(lang,'bc-party-leaders')}\">现任党魁</a>，包括曾是本次补选保守党候选人的党魁Kerry-Lynne Findlay目前的情况。</p></div></section>")
        + f'<section class="section soft"><div class="wrap"><h2>{L("背景：补选候选人")}</h2><div class="tablewrap"><table><thead><tr><th>{L("候选人")}</th><th>{L("政党")}</th><th>{L("备注")}</th></tr></thead><tbody>'
        + L(rows)
        + L(f'</tbody></table></div><p class="source-note">这是已取消补选的确认候选人名单（{a("byel_cands","Elections BC")}）。这不是省选的选票名单；提名于10月3日截止后见{a("ebc_2026_cands","官方2026年候选人名单")}。</p></div></section>')
        + f'<section class="section"><div class="wrap"><h2>{L("Abbotsford-Mission在2024年怎么投")}</h2>'
        + L(f"<p>2024年10月19日省选中，保守党的Reann Gasper以<strong>13,523票（55.38%）</strong>赢得Abbotsford-Mission，NDP候选人Pam Alexis得<strong>10,894票（44.62%）</strong>。来源：{a('sov','Elections BC投票统计报告')}。见<a href=\"{url_for(lang,'ridings/abbotsford-mission')}\">Abbotsford-Mission选区页</a>和全省<a href=\"{url_for(lang,'bc-election-results-2024')}\">2024年选举结果</a>。</p>")
        + L("<p>这只是背景，不是预测：大选的投票率和竞选焦点常与补选不同，BC Vote Watch不发布选区层面的预测。</p>")
        + "</div></section>"
        + L(faq_html(byel_faq_zh(lang), "Abbotsford-Mission常见问题"))
    )
    title = L("Abbotsford-Mission补选：已取消")
    desc = L("原定2026年9月26日的Abbotsford-Mission补选已于9月22日因省选宣布而取消。发生了什么，以及该选区如何在10月24日投票。")
    path = url_for(lang, "abbotsford-mission-by-election-2026")
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [(L("首页"), "/"), (L("补选"), path)]),
               faq_schema([(L(q), L(a_)) for q, a_ in byel_faq_zh(lang)]), byel_event(lang)]
    return render(lang, "abbotsford-mission-by-election-2026", title, desc, body, GROUPS["byel"], schemas)


# ================================================================ 2024 RESULTS
RES_ROWS = [
    ("BC NDP", 944579, "44.87%", 47),
    ("Conservative Party", 911153, "43.28%", 44),
    ("BC Green Party", 173377, "8.24%", 2),
    ("Independent", 47117, "2.24%", 0),
    ("Unaffiliated", 25464, "1.21%", 0),
    ("Libertarian", 1380, "0.07%", 0),
    ("Freedom Party of BC", 1267, "0.06%", 0),
    ("Communist Party of BC", 639, "0.03%", 0),
    ("Christian Heritage Party of B.C.", 365, "0.02%", 0),
]
RES_ZH = {"BC NDP": "BC NDP", "Conservative Party": "保守党", "BC Green Party": "BC绿党", "Independent": "无党派候选人（Independent）",
          "Unaffiliated": "无所属（Unaffiliated）", "Libertarian": "自由意志党", "Freedom Party of BC": "BC自由党（Freedom Party）",
          "Communist Party of BC": "BC共产党", "Christian Heritage Party of B.C.": "BC基督教遗产党"}
RES_FAQ_EN = [
    ("Who won the 2024 BC election?",
     f"The BC NDP under David Eby won 47 of 93 seats, a one-seat majority, with 44.87% of the vote. The Conservative Party won 44 seats (43.28%) and the BC Greens 2 seats (8.24%) ({a('sov','Elections BC Statement of Votes')})."),
    ("What was voter turnout in the 2024 BC election?",
     "2,109,658 votes were cast, 58.45% of the 3,609,288 registered voters, according to Elections BC."),
    ("How close was the 2024 BC election?",
     "The NDP finished 33,426 votes and 1.59 percentage points ahead of the Conservatives province-wide. It won exactly the 47 seats needed for a majority in the 93-seat Legislature."),
    ("When did people vote in the 2024 BC election?",
     "About 47.5% of votes were cast at advance voting, 44.0% on Final Voting Day and 3.7% by mail; the rest came from district electoral office, special and assisted telephone voting."),
    ("Are these the current seats in the Legislature?",
     f"No. These are the results on election night in 2024. Party standings have since changed; see <a href=\"/bc-party-leaders\">BC party leaders</a> and the {a('leg','Legislative Assembly of BC')}."),
]
RES_FAQ_ZH = [
    ("谁赢得了2024年BC省选？",
     f"David Eby领导的BC NDP以44.87%的得票赢得93个议席中的47席，以一席优势组成多数政府。保守党赢得44席（43.28%），BC绿党2席（8.24%）（{a('sov','Elections BC投票统计报告')}）。"),
    ("2024年BC省选的投票率是多少？",
     "根据 Elections BC，共有2,109,658张选票，占3,609,288名登记选民的58.45%。"),
    ("2024年BC省选有多接近？",
     "NDP在全省得票上领先保守党33,426票、1.59个百分点，恰好赢得93席立法会中组成多数所需的47席。"),
    ("2024年大家什么时候投票？",
     "约47.5%的选票在提前投票期间投出，44.0%在最终投票日投出，3.7%为邮寄投票；其余来自选区选举办事处、特别投票和电话协助投票。"),
    ("这是立法会目前的议席吗？",
     f"不是。这是2024年选举夜的结果，此后政党构成已有变化。见<a href=\"{{PBL}}\">BC党魁</a>和{a('leg','BC省立法会')}。"),
]


def page_results_en():
    rows = "".join(f"<tr><td>{n}</td><td>{v:,}</td><td>{pc}</td><td>{seats}</td></tr>" for n, v, pc, seats in RES_ROWS)
    body = (
        hero("Results", "BC 2024 election results: seats, votes and turnout",
             "Official results of the October 19, 2024 BC provincial general election from Elections BC. The NDP won 47 of 93 seats with 44.87% of the vote, a one-seat majority; the Conservatives won 44 seats with 43.28%; the Greens won 2.")
        + '<section class="section"><div class="wrap"><h2>Results by party</h2><div class="tablewrap"><table><thead><tr><th>Party</th><th>Valid votes</th><th>% of total</th><th>Seats</th></tr></thead><tbody>'
        + rows
        + '<tr><td><strong>Total</strong></td><td><strong>2,105,341</strong></td><td><strong>100.00%</strong></td><td><strong>93</strong></td></tr></tbody></table></div>'
        f"<p class=\"source-note\">Source: {a('sov','Elections BC — Statement of Votes, 43rd Provincial General Election (October 19, 2024)')}, presented to the Speaker on April 17, 2025. Official results by riding and candidate are in the same document and at {a('ebc_results','Elections BC results')}.</p></div></section>"
        '<section class="section soft"><div class="wrap"><h2>Turnout</h2><div class="grid">'
        '<div class="card"><div class="kicker">Votes cast</div><div class="big">2,109,658</div><p class="muted">Including 4,317 rejected ballots.</p></div>'
        '<div class="card"><div class="kicker">Registered voters</div><div class="big">3,609,288</div><p class="muted">As of the close of voting.</p></div>'
        '<div class="card"><div class="kicker">Turnout</div><div class="big">58.45%</div><p class="muted">Of registered voters.</p></div></div></div></section>'
        '<section class="section"><div class="wrap"><h2>How close it was</h2>'
        "<p>Province-wide the NDP led the Conservatives by <strong>33,426 votes (1.59 percentage points)</strong>. The NDP won exactly the 47 seats needed for a majority in a 93-seat Legislature. Seats are won riding by riding, so a small vote lead can produce a very different seat margin. See <a href=\"/bc-election-ridings\">results for all 93 ridings</a>.</p>"
        "<h2>When British Columbians voted</h2><ul>"
        "<li><strong>Advance voting:</strong> 47.5% of votes (45.17% in district, 2.32% out of district)</li>"
        "<li><strong>Final Voting Day:</strong> 44.0% (42.33% in district, 1.71% out of district)</li>"
        "<li><strong>Vote by mail:</strong> 3.7% (3.24% at headquarters, 0.48% at district offices)</li>"
        "<li><strong>District electoral office voting:</strong> 3.0%; <strong>special voting:</strong> 1.6%; <strong>assisted telephone voting:</strong> 0.2%</li></ul>"
        f"<p class=\"source-note\">Shares are of votes considered (including rejected ballots); source {a('sov','Elections BC')}. Ways to vote today: <a href=\"/how-to-vote-bc\">how to vote in BC</a>.</p></div></section>"
        + faq_html(RES_FAQ_EN, "2024 BC election results FAQ")
        + '<section class="section"><div class="wrap"><p class="source-note">These are 2024 election-night results, not the current standings of the Legislature. What has changed since: <a href="/bc-election-2026">BC election 2026 guide</a> · <a href="/bc-party-leaders">party leaders</a> · <a href="/abbotsford-mission-by-election-2026">Abbotsford-Mission by-election</a>.</p></div></section>'
    )
    title = "BC 2024 Election Results: Seats and Votes"
    desc = "Official BC 2024 election results: NDP 47 seats (44.87%), Conservatives 44 (43.28%), Greens 2. Turnout 58.45%. Source: Elections BC Statement of Votes."
    path = "/bc-election-results-2024"
    schemas = [article_schema(title, desc, "en", path),
               breadcrumb("en", [("Home", "/"), ("BC 2024 Election Results", path)]),
               faq_schema(RES_FAQ_EN)]
    return render("en", "bc-election-results-2024", title, desc, body, GROUPS["results"], schemas)


def page_results_zh(lang):
    L = lambda s: conv(lang, s)
    rows = "".join(f"<tr><td>{RES_ZH[n]}</td><td>{v:,}</td><td>{pc}</td><td>{seats}</td></tr>" for n, v, pc, seats in RES_ROWS)
    faq = [(q, ans.replace("{PBL}", url_for(lang, "bc-party-leaders"))) for q, ans in RES_FAQ_ZH]
    body = (
        hero("选举结果", L("BC省2024年选举结果：议席、得票与投票率"),
             L("BC省2024年10月19日省选的官方结果，来自 Elections BC。NDP以44.87%的得票赢得93席中的47席，以一席优势组成多数政府；保守党赢得44席（43.28%）；绿党2席。"))
        + f'<section class="section"><div class="wrap"><h2>{L("各党结果")}</h2><div class="tablewrap"><table><thead><tr><th>{L("政党")}</th><th>{L("有效票")}</th><th>{L("得票率")}</th><th>{L("议席")}</th></tr></thead><tbody>'
        + L(rows)
        + f'<tr><td><strong>{L("合计")}</strong></td><td><strong>2,105,341</strong></td><td><strong>100.00%</strong></td><td><strong>93</strong></td></tr></tbody></table></div>'
        + L(f"<p class=\"source-note\">来源：{a('sov','Elections BC——第43届省选投票统计报告（2024年10月19日）')}，于2025年4月17日提交议长。分选区、分候选人的官方结果见同一文件及{a('ebc_results','Elections BC结果页')}。</p></div></section>")
        + f'<section class="section soft"><div class="wrap"><h2>{L("投票率")}</h2><div class="grid">'
        + L('<div class="card"><div class="kicker">投出选票</div><div class="big">2,109,658</div><p class="muted">含4,317张废票。</p></div>')
        + L('<div class="card"><div class="kicker">登记选民</div><div class="big">3,609,288</div><p class="muted">截至投票结束时。</p></div>')
        + L('<div class="card"><div class="kicker">投票率</div><div class="big">58.45%</div><p class="muted">占登记选民比例。</p></div>')
        + "</div></div></section>"
        + f'<section class="section"><div class="wrap"><h2>{L("结果有多接近")}</h2>'
        + L(f"<p>全省得票上，NDP领先保守党<strong>33,426票（1.59个百分点）</strong>，恰好赢得93席立法会中组成多数所需的47席。议席是按选区逐个决定的，所以小幅的得票领先可能造成很不同的议席差距。见<a href=\"{url_for(lang,'bc-election-ridings')}\">全部93个选区的结果</a>。</p>")
        + f"<h2>{L('大家什么时候投票')}</h2><ul>"
        + L("<li><strong>提前投票：</strong>47.5%的选票（选区内45.17%，选区外2.32%）</li>")
        + L("<li><strong>最终投票日：</strong>44.0%（选区内42.33%，选区外1.71%）</li>")
        + L("<li><strong>邮寄投票：</strong>3.7%（总部处理3.24%，选区办事处0.48%）</li>")
        + L("<li><strong>选区选举办事处投票：</strong>3.0%；<strong>特别投票：</strong>1.6%；<strong>电话协助投票：</strong>0.2%</li></ul>")
        + L(f"<p class=\"source-note\">比例为计入废票在内的“考虑票数”占比；来源{a('sov','Elections BC')}。目前的投票方式见<a href=\"{url_for(lang,'how-to-vote-bc')}\">BC省如何投票</a>。</p></div></section>")
        + L(faq_html(faq, "2024年BC省选结果常见问题"))
    )
    title = L("BC省2024年选举结果：议席、得票与投票率")
    desc = L("BC省2024年官方选举结果：NDP 47席（44.87%），保守党44席（43.28%），绿党2席，投票率58.45%。来源：Elections BC。")
    path = url_for(lang, "bc-election-results-2024")
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [(L("首页"), "/"), (L("2024年结果"), path)]),
               faq_schema([(L(q), L(a_)) for q, a_ in faq])]
    return render(lang, "bc-election-results-2024", title, desc, body, GROUPS["results"], schemas)


# ================================================================ LEADERS (zh)
def page_leaders_zh(lang):
    L = lambda s: conv(lang, s)
    body = (
        hero("政党党魁", L("BC省政党党魁 2026"), L("2026年10月24日省选前，BC省各政党目前由谁领导，每项说明都附有来源。"))
        + f'<section class="section"><div class="wrap"><div class="tablewrap"><table><thead><tr><th>{L("政党")}</th><th>{L("党魁")}</th><th>{L("说明")}</th></tr></thead><tbody>'
        + L(f"<tr><td><strong>BC NDP</strong></td><td>David Eby</td><td>省长。2024年10月以一席优势（93席中的47席）赢得多数政府（{a('sov','Elections BC官方结果')}）。于9月22日宣布10月24日省选（{a('infonews_call','iNFOnews')}）。</td></tr>")
        + L(f"<tr><td><strong>BC保守党</strong></td><td>Lorne Doerkson（临时党魁）</td><td>2026年9月21日经党团一致投票被任命为临时党魁（{a('comox_doerkson','Comox Valley Record')}）；为Cariboo-Chilcotin省议员，2024年以保守党身份当选。Kerry-Lynne Findlay于2026年5月30日当选党魁，在8月以来已有14名议员离开党团后，于9月20日辞职（{a('ctv_findlay_resign','CTV News')}）。截至{TODAY_ZH}，Elections BC尚未确认她是否为10月24日大选的候选人；她此前参选的补选已因大选宣布而取消。</td></tr>")
        + L(f"<tr><td><strong>BC绿党</strong></td><td>Emily Lowan</td><td>在{a('ipsos','Ipsos')}和{a('research','Research Co.')}民调中被列为绿党党魁。2024年赢得2席。</td></tr>")
        + L(f"<tr><td><strong>CentreBC</strong></td><td>Peter Milobar</td><td>2026年9月18日被任命为党魁，接替Mike Bernier（{a('ctv_milobar','CTV News')}）。CentreBC列出八名议员，Milobar为党魁及Kamloops Centre议员（{a('centrebc','CentreBC官网')}）。新政党，已出现在民调中（Ipsos 4%，Research Co. 5%，6月Leger 8%）。</td></tr>")
        + L("<tr><td><strong>OneBC</strong></td><td>Dallas Brodie</td><td>新政党，现已出现在民调中（Ipsos 2%，Research Co. 1%）。</td></tr>")
        + "</tbody></table></div>"
        + L(f"<p class=\"source-note\">2024年以来第43届立法会的构成反复变化，有议员转党或成为无党派议员（{a('wiki_43','概述')}），立法会现已因选举而解散。解散前的记录请查看{a('leg','BC省立法会')}；BC Vote Watch会在与立法会和权威报道核对一致后再发布议席数字。</p></div></section>")
        + f'<section class="section soft"><div class="wrap"><h2>{L("选举令状前选民如何评价他们")}</h2>'
        + L(f"<p>Ipsos（9月8至14日）显示Eby好感度41%、反感30%，Findlay好感17%、反感46%。Research Co.（8月12至14日）显示Eby支持率49%，Lowan 38%，Findlay 34%。这些评价均早于Findlay辞职和Doerkson出任党魁。完整数字与方法见<a href=\"{url_for(lang,'bc-election-polls')}\">BC省选民调</a>。</p>")
        + L(f"<p>关键日期见<a href=\"{url_for(lang,'bc-election-2026')}\">BC省选2026指南</a>。</p></div></section>")
    )
    title = L("BC省政党党魁 2026：Eby、Doerkson、Lowan")
    desc = L("2026年10月24日省选前，BC NDP、BC保守党、BC绿党、CentreBC和OneBC的党魁。Doerkson自9月21日起任保守党临时党魁；附民调评价。")
    path = url_for(lang, "bc-party-leaders")
    schemas = [article_schema(title, desc, lang, path), breadcrumb(lang, [(L("首页"), "/"), (L("BC党魁"), path)])]
    return render(lang, "bc-party-leaders", title, desc, body, GROUPS["leaders"], schemas)


# ================================================================ RIDINGS (93) + HUB
RIDINGS = json.load(open(os.path.join(ROOT, "data", "ridings-2024.json"), encoding="utf8"))["ridings"]
PROV_PCT = {"BC NDP": 44.87, "Conservative Party": 43.28, "BC Green Party": 8.24}
PROV_TURNOUT = 58.45
PARTY_EN = {"BC NDP": "NDP", "Conservative Party": "Conservative", "BC Green Party": "Green"}
PARTY_ZH = {"BC NDP": "BC NDP", "Conservative Party": "保守党", "BC Green Party": "BC绿党", "Independent": "无党派候选人",
            "Unaffiliated": "无所属", "Libertarian": "自由意志党", "Communist Party of BC": "BC共产党",
            "Freedom Party of BC": "BC自由党", "Christian Heritage Party of B.C.": "BC基督教遗产党"}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _prep():
    for r in RIDINGS:
        r["slug"] = slugify(r["name"])
        w, ru = r["candidates"][0], r["candidates"][1]
        r["winner"], r["runner"] = w, ru
        r["margin"] = w["votes"] - ru["votes"]
        r["margin_pts"] = round(w["pct"] - ru["pct"], 2)
    for i, r in enumerate(sorted(RIDINGS, key=lambda r: r["margin_pts"])):
        r["closest_rank"] = i + 1
    assert len({r["slug"] for r in RIDINGS}) == 93


_prep()
SEATS = {}
for _r in RIDINGS:
    SEATS[_r["winner"]["party"]] = SEATS.get(_r["winner"]["party"], 0) + 1
assert SEATS == {"BC NDP": 47, "Conservative Party": 44, "BC Green Party": 2}, SEATS


def pname(lang, party):
    return PARTY_EN.get(party, party) if lang == "en" else PARTY_ZH.get(party, party)


def page_riding(lang, r):
    L = lambda s: conv(lang, s)
    en = lang == "en"
    w, ru = r["winner"], r["runner"]
    n = r["name"]
    wp, rp = pname(lang, w["party"]), pname(lang, ru["party"])
    flip = r["margin"] // 2 + 1
    diff = round(r["turnout"] - PROV_TURNOUT, 2)
    rank = r["closest_rank"]
    hub = url_for(lang, "bc-election-ridings")
    # candidate table
    def inc_mark(c):
        return " *" if c["incumbent"] else ""
    rows = ""
    for i, c in enumerate(r["candidates"]):
        cn = html.escape(c["name"]) + inc_mark(c)
        badge = ("Elected" if en else "当选") if i == 0 else ""
        rows += f"<tr><td>{cn}</td><td>{pname(lang, c['party'])}</td><td>{c['votes']:,}</td><td>{c['pct']:.2f}%</td><td>{'<strong>'+badge+'</strong>' if badge else ''}</td></tr>"
    if en:
        lede = (f"{html.escape(w['name'])} ({wp}) won {n} in the October 19, 2024 BC election with {w['pct']:.2f}% of the vote, "
                f"{r['margin']:,} votes ahead of {html.escape(ru['name'])} ({rp}). Turnout was {r['turnout']:.2f}%.")
        head_th = "<th>Candidate</th><th>Party</th><th>Votes</th><th>Share</th><th></th>"
        prov_line = ""
        if w["party"] in PROV_PCT:
            prov_line = f" Province-wide the {wp} took {PROV_PCT[w['party']]:.2f}% of the vote, compared with {w['pct']:.2f}% here."
        close = (f"<p>{n} ranks <strong>{rank} of 93</strong> among the closest races in 2024 (1 is the closest). The winning margin was {r['margin']:,} votes "
                 f"({r['margin_pts']:.2f} percentage points); it would have taken {flip:,} voters switching from {html.escape(w['name'])} to {html.escape(ru['name'])} to flip the result.{prov_line}</p>")
        seat = ("<p>These are 2024 election results. The person who holds a seat can change between general elections through resignations, by-elections or a change of party, "
                f"so use the Legislative Assembly’s {a('leg','member directory')} for the current MLA. ")
        if n == "Abbotsford-Mission":
            seat += "This seat was due for a by-election on September 26, 2026, which was cancelled when the general election was called; voters here choose their MLA on October 24 instead. See the <a href=\"/abbotsford-mission-by-election-2026\">Abbotsford-Mission page</a>."
        seat += "</p>"
        faq = [
            (f"Who won {n} in the 2024 BC election?", f"{w['name']} ({wp}) won {n} with {w['votes']:,} votes ({w['pct']:.2f}%), ahead of {ru['name']} ({rp}) with {ru['votes']:,} ({ru['pct']:.2f}%). Source: Elections BC Statement of Votes."),
            (f"What was voter turnout in {n} in 2024?", f"{r['voted']:,} of {r['registered']:,} registered voters voted in {n}, a turnout of {r['turnout']:.2f}%, compared with {PROV_TURNOUT}% province-wide."),
            (f"How close was the race in {n}?", f"The winning margin was {r['margin']:,} votes ({r['margin_pts']:.2f} percentage points), the {ordinal(rank)} closest of BC's 93 ridings."),
        ]
        body = (
            hero("BC provincial riding", f"{n}", lede)
            + f'<section class="section"><div class="wrap"><h2>2024 election results in {n}</h2><div class="tablewrap"><table><thead><tr>{head_th}</tr></thead><tbody>{rows}</tbody></table></div>'
            f"<p class=\"source-note\">Source: {a('sov','Elections BC Statement of Votes')}, October 19, 2024. * Member of the 42nd Parliament (a sitting or former MLA at the time). The winner is the candidate with the most votes.</p></div></section>"
            '<section class="section soft"><div class="wrap"><h2>Key numbers</h2><div class="grid">'
            f'<div class="card"><div class="kicker">Registered voters</div><div class="big">{r["registered"]:,}</div><p class="muted">In {n} at the close of voting.</p></div>'
            f'<div class="card"><div class="kicker">Votes cast</div><div class="big">{r["voted"]:,}</div><p class="muted">{r["valid"]:,} valid and {r["rejected"]:,} rejected ballots.</p></div>'
            f'<div class="card"><div class="kicker">Turnout</div><div class="big">{r["turnout"]:.2f}%</div><p class="muted">{abs(diff):.2f} points {"above" if diff >= 0 else "below"} the province-wide {PROV_TURNOUT}%.</p></div>'
            "</div></div></section>"
            f'<section class="section"><div class="wrap"><h2>How close was it?</h2>{close}<h2>The seat after 2024</h2>{seat}'
            f'<p>More: <a href="{hub}">all 93 BC ridings</a> · <a href="/bc-election-results-2024">2024 results</a> · <a href="/bc-election-polls">BC election polls</a> · <a href="/how-to-vote-bc">how to vote</a>.</p></div></section>'
            + faq_html(faq, f"{n} FAQ")
        )
        title = f"{n} 2024 BC Election Results" if len(n) <= 17 else f"{n}: 2024 Results"
        desc = f"{w['name']} ({wp}) won {n} in 2024 with {w['pct']:.2f}%. Riding results, turnout ({r['turnout']:.2f}%), margin ({r['margin']:,} votes) and how it compares."
        if len(desc) > 160:
            desc = f"{w['name']} ({wp}) won {n} in 2024 with {w['pct']:.2f}%. Results, turnout ({r['turnout']:.2f}%) and margin ({r['margin']:,} votes)."
        crumbs = [("Home", "/"), ("BC Ridings", url_for(lang, "bc-election-ridings")), (n, url_for(lang, "ridings/" + r["slug"]))]
    else:
        lede = (f"{html.escape(w['name'])}（{wp}）在2024年10月19日的BC省选中以{w['pct']:.2f}%的得票赢得{n}选区，领先{html.escape(ru['name'])}（{rp}）{r['margin']:,}票。投票率为{r['turnout']:.2f}%。")
        head_th = "<th>候选人</th><th>政党</th><th>得票</th><th>得票率</th><th></th>"
        prov_line = ""
        if w["party"] in PROV_PCT:
            prov_line = f"全省范围内{wp}的得票率为{PROV_PCT[w['party']]:.2f}%，本选区为{w['pct']:.2f}%。"
        close = (f"<p>在2024年最接近的选区中，{n}排第<strong>{rank}位（共93个）</strong>（1为最接近）。获胜差距为{r['margin']:,}票（{r['margin_pts']:.2f}个百分点）；"
                 f"只要有{flip:,}名选民从{html.escape(w['name'])}改投{html.escape(ru['name'])}，结果就会逆转。{prov_line}</p>")
        seat = ("<p>这是2024年的选举结果。议席持有人可能因辞职、补选或转党在两次大选之间发生变化，"
                f"请查看立法会的{a('leg','议员名录')}了解现任议员。")
        if n == "Abbotsford-Mission":
            seat += f"该选区原定于2026年9月26日举行补选，但在省选宣布后已被取消；选民改为在10月24日选出省议员。见<a href=\"{url_for(lang,'abbotsford-mission-by-election-2026')}\">Abbotsford-Mission页</a>。"
        seat += "</p>"
        faq = [
            (f"2024年BC省选谁赢得了{n}？", f"{w['name']}（{wp}）以{w['votes']:,}票（{w['pct']:.2f}%）赢得{n}，领先{ru['name']}（{rp}）的{ru['votes']:,}票（{ru['pct']:.2f}%）。来源：Elections BC投票统计报告。"),
            (f"2024年{n}的投票率是多少？", f"{n}的{r['registered']:,}名登记选民中有{r['voted']:,}人投票，投票率为{r['turnout']:.2f}%，全省为{PROV_TURNOUT}%。"),
            (f"{n}的选情有多接近？", f"获胜差距为{r['margin']:,}票（{r['margin_pts']:.2f}个百分点），在BC省93个选区中最接近的排第{rank}位。"),
        ]
        body = (
            hero("BC省选区", f"{n}", L(lede))
            + f'<section class="section"><div class="wrap"><h2>{L("2024年选举结果")}：{n}</h2><div class="tablewrap"><table><thead><tr>{L(head_th)}</tr></thead><tbody>{L(rows)}</tbody></table></div>'
            + L(f"<p class=\"source-note\">来源：{a('sov','Elections BC投票统计报告')}（2024年10月19日）。* 第42届省议会议员（当时的现任或前任议员）。得票最多者当选。</p></div></section>")
            + f'<section class="section soft"><div class="wrap"><h2>{L("关键数字")}</h2><div class="grid">'
            + L(f'<div class="card"><div class="kicker">登记选民</div><div class="big">{r["registered"]:,}</div><p class="muted">{n}选区投票结束时。</p></div>')
            + L(f'<div class="card"><div class="kicker">投出选票</div><div class="big">{r["voted"]:,}</div><p class="muted">有效票{r["valid"]:,}张，废票{r["rejected"]:,}张。</p></div>')
            + L(f'<div class="card"><div class="kicker">投票率</div><div class="big">{r["turnout"]:.2f}%</div><p class="muted">比全省{PROV_TURNOUT}%{"高" if diff >= 0 else "低"}{abs(diff):.2f}个百分点。</p></div>')
            + f'</div></div></section><section class="section"><div class="wrap"><h2>{L("选情有多接近？")}</h2>{L(close)}<h2>{L("2024年之后的议席")}</h2>{L(seat)}'
            + L(f'<p>更多：<a href="{hub}">全部93个BC选区</a> · <a href="{url_for(lang,"bc-election-results-2024")}">2024年结果</a> · <a href="{url_for(lang,"bc-election-polls")}">BC省选民调</a> · <a href="{url_for(lang,"how-to-vote-bc")}">如何投票</a>。</p></div></section>')
            + L(faq_html(faq, f"{n}常见问题"))
        )
        title = L(f"{n}选区 2024年BC省选结果")
        desc = L(f"{w['name']}（{wp}）在2024年以{w['pct']:.2f}%赢得{n}选区。附选区完整结果、投票率（{r['turnout']:.2f}%）、得票差距（{r['margin']:,}票）等。")
        crumbs = [(L("首页"), "/"), (L("BC省选区"), url_for(lang, "bc-election-ridings")), (n, url_for(lang, "ridings/" + r["slug"]))]
    path = url_for(lang, "ridings/" + r["slug"])
    schemas = [article_schema(title, desc, lang, path), breadcrumb(lang, crumbs), faq_schema([(L(q), L(a_)) if not en else (q, a_) for q, a_ in faq])]
    return render(lang, "ridings/" + r["slug"], title, desc, body, riding_group(r["slug"]), schemas)


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"


def riding_group(slug):
    return {"en": "ridings/" + slug, "zh-cn": "ridings/" + slug, "zh-tw": "ridings/" + slug}


def page_ridings_hub(lang):
    L = lambda s: conv(lang, s)
    en = lang == "en"
    all_rows = ""
    for r in sorted(RIDINGS, key=lambda r: r["name"]):
        w = r["winner"]
        all_rows += (f'<tr><td><a href="{url_for(lang, "ridings/" + r["slug"])}">{r["name"]}</a></td><td>{html.escape(w["name"])}</td><td>{pname(lang, w["party"])}</td>'
                     f'<td>{r["margin"]:,} ({r["margin_pts"]:.2f})</td><td>{r["turnout"]:.2f}%</td></tr>')
    close_rows = ""
    for r in sorted(RIDINGS, key=lambda r: r["margin_pts"])[:10]:
        w, ru = r["winner"], r["runner"]
        close_rows += (f'<tr><td><a href="{url_for(lang, "ridings/" + r["slug"])}">{r["name"]}</a></td><td>{html.escape(w["name"])} ({pname(lang, w["party"])})</td>'
                       f'<td>{html.escape(ru["name"])} ({pname(lang, ru["party"])})</td><td>{r["margin"]:,}</td><td>{r["margin_pts"]:.2f}</td></tr>')
    if en:
        th_all = "<th>Riding</th><th>2024 winner</th><th>Party</th><th>Margin: votes (pts)</th><th>Turnout</th>"
        th_close = "<th>Riding</th><th>Winner</th><th>Runner-up</th><th>Margin (votes)</th><th>Margin (pts)</th>"
        body = (
            hero("Ridings", "BC ridings: all 93 electoral districts",
                 "British Columbia elects 93 MLAs, one per electoral district (riding), by first-past-the-post. Each riding page has the official 2024 results, turnout and how close the race was.")
            + '<section class="section"><div class="wrap"><h2>2024 seats by party</h2><div class="grid">'
            f'<div class="card"><div class="kicker">BC NDP</div><div class="big">{SEATS["BC NDP"]}</div><p class="muted">44.87% of the vote</p></div>'
            f'<div class="card"><div class="kicker">Conservative</div><div class="big">{SEATS["Conservative Party"]}</div><p class="muted">43.28% of the vote</p></div>'
            f'<div class="card"><div class="kicker">BC Green</div><div class="big">{SEATS["BC Green Party"]}</div><p class="muted">8.24% of the vote</p></div></div>'
            f"<p class=\"source-note\">Election-night 2024 results from {a('sov','Elections BC')}; not the current standings of the Legislature (see <a href=\"/bc-party-leaders\">party leaders</a>). Maps and boundaries: {a('ebc_maps','Elections BC')}.</p></div></section>"
            '<section class="section soft"><div class="wrap"><h2>The 10 closest ridings in 2024</h2><p>These are the ridings a small shift in votes would have changed.</p>'
            f'<div class="tablewrap"><table><thead><tr>{th_close}</tr></thead><tbody>{close_rows}</tbody></table></div></div></section>'
            '<section class="section"><div class="wrap"><h2>All 93 BC ridings</h2>'
            '<p><input type="search" data-filter="#riding-table" placeholder="Filter by riding, candidate or party" aria-label="Filter ridings" style="width:100%;max-width:420px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;font:inherit"></p>'
            f'<div class="tablewrap"><table id="riding-table"><thead><tr>{th_all}</tr></thead><tbody>{all_rows}</tbody></table></div>'
            '<p class="source-note">Next: <a href="/bc-election-2026">BC election 2026 guide</a> · <a href="/bc-election-results-2024">2024 results</a> · <a href="/how-to-vote-bc">how to vote</a>.</p></div></section>'
        )
        title = "BC Ridings: All 93 Districts and Results"
        desc = "All 93 BC provincial ridings with official 2024 election results, winners, turnout and the 10 closest races. Find your riding."
    else:
        th_all = "<th>选区</th><th>2024年当选者</th><th>政党</th><th>差距：票数（百分点）</th><th>投票率</th>"
        th_close = "<th>选区</th><th>当选者</th><th>亚军</th><th>差距（票）</th><th>差距（百分点）</th>"
        body = (
            hero("选区", L("BC省选区：全部93个选区"),
                 L("BC省有93个选区，每个选区以得票最多者当选（first-past-the-post）产生一名省议员。每个选区页都有2024年官方结果、投票率以及选情有多接近。"))
            + f'<section class="section"><div class="wrap"><h2>{L("2024年各党议席")}</h2><div class="grid">'
            + L(f'<div class="card"><div class="kicker">BC NDP</div><div class="big">{SEATS["BC NDP"]}</div><p class="muted">得票率44.87%</p></div>')
            + L(f'<div class="card"><div class="kicker">保守党</div><div class="big">{SEATS["Conservative Party"]}</div><p class="muted">得票率43.28%</p></div>')
            + L(f'<div class="card"><div class="kicker">BC绿党</div><div class="big">{SEATS["BC Green Party"]}</div><p class="muted">得票率8.24%</p></div></div>')
            + L(f"<p class=\"source-note\">2024年选举夜结果，来自{a('sov','Elections BC')}；并非立法会目前的议席分布（见<a href=\"{url_for(lang,'bc-party-leaders')}\">党魁页</a>）。地图与选区边界：{a('ebc_maps','Elections BC')}。</p></div></section>")
            + f'<section class="section soft"><div class="wrap"><h2>{L("2024年最接近的10个选区")}</h2><p>{L("只要少量选票转向，这些选区的结果就会改变。")}</p>'
            + f'<div class="tablewrap"><table><thead><tr>{L(th_close)}</tr></thead><tbody>{L(close_rows)}</tbody></table></div></div></section>'
            + f'<section class="section"><div class="wrap"><h2>{L("全部93个BC选区")}</h2>'
            + f'<p><input type="search" data-filter="#riding-table" placeholder="{L("按选区、候选人或政党筛选")}" aria-label="{L("筛选选区")}" style="width:100%;max-width:420px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;font:inherit"></p>'
            + f'<div class="tablewrap"><table id="riding-table"><thead><tr>{L(th_all)}</tr></thead><tbody>{L(all_rows)}</tbody></table></div>'
            + L(f'<p class="source-note">继续：<a href="{url_for(lang,"bc-election-2026")}">BC省选2026指南</a> · <a href="{url_for(lang,"bc-election-results-2024")}">2024年结果</a> · <a href="{url_for(lang,"how-to-vote-bc")}">如何投票</a>。</p></div></section>')
        )
        title = L("BC省选区：全部93个选区与2024年结果")
        desc = L("BC省全部93个选区的2024年官方选举结果、当选者、投票率和最接近的10个选区。")
    path = url_for(lang, "bc-election-ridings")
    schemas = [article_schema(title, desc, lang, path), breadcrumb(lang, [(L("首页") if not en else "Home", "/"), (L("BC省选区") if not en else "BC Ridings", path)])]
    return render(lang, "bc-election-ridings", title, desc, body, GROUPS["ridings"], schemas)


# ================================================================ ISSUE HUBS
SRC.update({
    "bud_fiscal": "https://www.bcbudget.gov.bc.ca/2026/fiscal/",
    "bud_rel": "https://news.gov.bc.ca/releases/2026FIN0003-000158",
    "rent_rel": "https://news.gov.bc.ca/releases/2026HMA0028-000639",
    "health_rel": "https://news.gov.bc.ca/releases/2026HLTH0018-000361",
    "tyee_docs": "https://thetyee.ca/News/2026/05/31/BC-Family-Doctor-Crisis-Gets-Even-Worse/",
    "softwood": "https://www2.gov.bc.ca/gov/content/industry/forestry/competitive-forest-industry/softwood-lumber-trade-with-the-u-s",
    "cp_soft": "https://canada.constructconnect.com/joc/news/government/2026/04/resolving-softwood-dispute-mutually-beneficial-for-canada-u-s-b-c-premier-says",
    "cons_plat": "https://conservativebc.ca/our-platform/",
    "grn_plat": "https://bcgreens.ca/2024-platform/",
    "onebc": "https://1bc.ca/",
    "cbc_policy": "https://www.centrebc.ca/our-policy/",
})
ISSUE_ORDER = ["housing", "health-care", "budget-deficit", "us-tariffs"]
ASOF_EN, ASOF_ZH = "as of September 20, 2026", "截至2026年9月20日"

# each position row: (party key, EN html, ZH html)
POS_LABEL = {
    "ndp": ("BC NDP (government)", "BC NDP（执政党）"),
    "cons": ("Conservative Party of BC", "BC保守党"),
    "grn": ("BC Greens", "BC绿党"),
    "ctr": ("CentreBC", "CentreBC"),
    "one": ("OneBC", "OneBC"),
}
NOTFOUND_EN = "No concrete position on this topic found in the materials we reviewed (" + ASOF_EN + "); see the party's own site."
NOTFOUND_ZH = "在我们查阅的资料中未找到该议题的具体立场（" + ASOF_ZH + "）；请查看该党官网。"

ISSUES = {
 "housing": {
  "slug": "housing",
  "en": dict(
    title="BC Housing and Rent 2026: Party Positions",
    desc="BC housing and rent in the 2026 election: what voters say, what the government reports on rents and BC Builds, and what each party has published.",
    eyebrow="Election issue", h1="Housing and rent in British Columbia",
    lede="Housing is the top concern in two recent BC polls. Here is what voters say, what the government reports, and what each party has published, with a source for every claim.",
    voters=f"<ul><li><strong>Research Co. (Aug 12–14, 2026):</strong> 29% name housing, poverty and homelessness as the most important issue facing BC, the top issue overall; among ages 35–54 it is 36% ({a('research','Research Co.')}).</li>"
           f"<li><strong>Leger (Apr 3–6, 2026):</strong> 30% name housing affordability as a top concern, alongside healthcare at 29%; government approval on housing, healthcare and the economy is below 50% ({a('leger','Leger')}).</li></ul>",
    facts=f"<p>The BC government reports the following in a June 2, 2026 news release ({a('rent_rel','news.gov.bc.ca')}). These are government claims, not independent findings:</p><ul>"
          "<li>Average asking rent in BC fell 12.5%, from $2,671 in August 2023 to $2,338 in April 2026, a reduction of $333 a month.</li>"
          "<li>Average asking rent in Vancouver and Burnaby is more than $650 lower than the 2023 peak, and BC has the largest year-over-year asking-rent declines of any province.</li>"
          "<li>BC Builds broke ground on its 4,000th unit, with nearly 820 new homes in Burnaby.</li></ul>"
          "<p><strong>How to read this:</strong> asking rent is what landlords advertise for available units. It does not describe what existing tenants pay, and it says nothing about home prices or ownership.</p>",
    positions=[
      ("ndp", f"Says its Homes for People plan, action on short-term rentals, zoning changes and BC Builds are delivering lower rents and more rental construction ({a('rent_rel','government release, June 2, 2026')}).", None),
      ("cons", f"Its platform page pledges to “end the housing shortage and make life more affordable” through a “Get BC Building” plan. The page gives no detailed measures and carries no date ({a('cons_plat','platform page')}).", None),
      ("grn", f"The 2024 platform costs additional housing spending at $1.6 billion in Year 1, $2.1 billion in Year 2 and $1.6 billion in Year 3, and estimates that eliminating deep poverty and ending homelessness would cost over $3 billion a year ({a('grn_plat','2024 platform')}).", None),
      ("ctr", f"No concrete housing position. Its policy committee is developing its first policy pillars, including affordability, and promises a full platform before the next election ({a('cbc_policy','policy page')}).", None),
      ("one", f"Lists as a priority to “make homeownership attainable again” by opening new land for development and eliminating taxes that inflate housing prices ({a('onebc','OneBC priorities')}).", None),
    ],
    faq=[("Have BC rents gone down?", f"The BC government says average asking rent fell 12.5% between August 2023 ($2,671) and April 2026 ($2,338) ({a('rent_rel','news release')}). Asking rents are advertised prices for available units, not what existing tenants pay."),
         ("What do voters say is BC's biggest issue?", f"In Research Co.'s August 2026 poll, 29% said housing, poverty and homelessness, ahead of the economy and jobs (24%) and health care (21%) ({a('research','Research Co.')})."),
         ("What is BC Builds?", f"The government describes BC Builds as its program to build homes; it says the program broke ground on its 4,000th unit in June 2026 ({a('rent_rel','release')}).")],
    watch="Watch for any party publishing costed housing measures, and independent rent and starts data that can be compared with the government's asking-rent figures."),
  "zh": dict(
    title="BC省住房与租金 2026：事实与各党立场",
    desc="2026年BC省选中的住房与租金：选民怎么说、政府公布的租金和BC Builds数据，以及各党已发布的立场。",
    eyebrow="选举议题", h1="BC省的住房与租金",
    lede="住房是近期两项BC民调中选民最关心的问题之一。这里列出选民怎么说、政府公布了什么、各党发布了什么立场，每一项都附来源。",
    voters=f"<ul><li><strong>Research Co.（2026年8月12至14日）：</strong>29%认为住房、贫困和无家可归是BC省最重要的问题，居首位；35至54岁人群中为36%（{a('research','Research Co.')}）。</li>"
           f"<li><strong>Leger（2026年4月3至6日）：</strong>30%把住房负担能力列为首要关切，医疗为29%；政府在住房、医疗和经济方面的认可度均低于50%（{a('leger','Leger')}）。</li></ul>",
    facts=f"<p>BC政府在2026年6月2日的新闻稿中公布了以下数字（{a('rent_rel','news.gov.bc.ca')}）。这些是政府的说法，不是独立调查结果：</p><ul>"
          "<li>BC省平均挂牌租金由2023年8月的2,671元降至2026年4月的2,338元，下降12.5%，每月减少333元。</li>"
          "<li>温哥华和本拿比的平均挂牌租金比2023年高峰低650元以上，且BC省的挂牌租金同比降幅为全国各省最大。</li>"
          "<li>BC Builds开工的房屋已达4,000个单位，其中包括本拿比近820套新房。</li></ul>"
          "<p><strong>如何解读：</strong>挂牌租金是房东为待租单位公布的价格，并不代表现有租客实际缴纳的租金，也不涉及房价或购房。</p>",
    positions=[
      ("ndp", None, f"称其Homes for People计划、短租限制、分区改革和BC Builds正在带来更低的租金和更多租赁房屋建设（{a('rent_rel','政府新闻稿，2026年6月2日')}）。"),
      ("cons", None, f"平台页面承诺通过“Get BC Building”计划“结束住房短缺、让生活更负担得起”。页面没有具体措施，也未标注日期（{a('cons_plat','平台页面')}）。"),
      ("grn", None, f"2024年平台估算住房方面额外开支第1年16亿元、第2年21亿元、第3年16亿元，并估计消除深度贫困和终结无家可归每年需超过30亿元（{a('grn_plat','2024年平台')}）。"),
      ("ctr", None, f"没有具体的住房立场。其政策委员会正在制定首批政策支柱（包括可负担性），并承诺在下次选举前发布完整平台（{a('cbc_policy','政策页面')}）。"),
      ("one", None, f"把“让普通收入者重新买得起房”列为优先事项，做法是开放新的开发土地并取消推高房价的税项（{a('onebc','OneBC优先事项')}）。"),
    ],
    faq=[("BC省的租金下降了吗？", f"BC政府称，平均挂牌租金由2023年8月的2,671元降至2026年4月的2,338元，下降12.5%（{a('rent_rel','新闻稿')}）。挂牌租金是待租单位的公布价格，并非现有租客实际缴纳的租金。"),
         ("选民认为BC省最大的问题是什么？", f"在Research Co.的2026年8月民调中，29%选择住房、贫困和无家可归，高于经济与就业（24%）和医疗（21%）（{a('research','Research Co.')}）。"),
         ("BC Builds是什么？", f"政府把BC Builds描述为其建房计划；称该计划已于2026年6月开工第4,000个单位（{a('rent_rel','新闻稿')}）。")],
    watch="留意各党是否公布带成本估算的住房措施，以及可与政府挂牌租金数字对照的独立租金和开工数据。"),
 },
 "health-care": {
  "slug": "health-care",
  "en": dict(
    title="BC Health Care 2026: Party Positions",
    desc="BC health care and family doctors in the 2026 election: voter concern, government and Health Minister figures on primary care, and each party's published position.",
    eyebrow="Election issue", h1="Health care and family doctors in British Columbia",
    lede="Health care ranks with housing as a top voter concern. The government and its critics cite different numbers about family doctors; here are both, with sources, and what each party has published.",
    voters=f"<ul><li><strong>Research Co. (Aug 12–14, 2026):</strong> 21% name health care as the most important issue; among ages 55 and over it is 34% ({a('research','Research Co.')}).</li>"
           f"<li><strong>Leger (Apr 3–6, 2026):</strong> 29% name healthcare as a top concern, second to housing affordability (30%) ({a('leger','Leger')}).</li></ul>",
    facts=f"<p><strong>What the government says.</strong> An April 1, 2026 release says more than 600,000 people have been connected to a family doctor or nurse practitioner since 2023, that upwards of 77% of British Columbians now have a primary care provider, and that about 4,000 more are matched each week ({a('health_rel','news.gov.bc.ca')}). Budget 2026 includes $2.8 billion in new health funding over three years, $2.3 billion of it to increase system capacity, including hiring more doctors, nurses and health-care workers ({a('bud_rel','budget release, Feb 17, 2026')}).</p>"
          f"<p><strong>What the numbers also show.</strong> {a('tyee_docs','The Tyee reported on May 31, 2026')} that the Health Minister told the Legislature the most up-to-date figure at the end of April was 1,259,425 people not attached to a primary care provider, about 23% of BC's 5.7 million people. The Tyee says a Canadian Community Health Survey found 897,000 (18.2%) unattached when the NDP formed government. The then Conservative health critic, Brennan Day, said government announcements distract from the growing list of unattached patients.</p>"
          "<p><strong>How to read this:</strong> the 77% and the 23% describe the same thing from two sides. “Connected” counts people newly matched; the unattached figure is the share of the population still without a provider. Both can be true at once.</p>",
    positions=[
      ("ndp", f"Budget 2026 adds $2.8 billion in health funding over three years, and the government reports more than 600,000 people connected to primary care since 2023 ({a('bud_rel','budget release')}; {a('health_rel','health release')}).", None),
      ("cons", f"Its platform page lists “Expanding Access to Care and Ending Long Wait Times” under “Putting Patients First,” and names mental wellness and reproductive health care as priorities. The page gives no detailed measures and carries no date ({a('cons_plat','platform page')}).", None),
      ("grn", f"The 2024 platform costs additional health spending at $190.5 million a year, mental health at $142.9 million rising to $154.3 million, and drug policy at about $290–297 million a year; it cites a review and amalgamation of the health authorities as a possible source of offsets ({a('grn_plat','2024 platform')}).", None),
      ("ctr", f"No concrete health position yet. Health care is among the areas its policy committee is developing ({a('cbc_policy','policy page')}).", None),
      ("one", f"Lists as a priority to overhaul BC's healthcare system to “align it with best practices worldwide” ({a('onebc','OneBC priorities')}). The page gives no further detail.", None),
    ],
    faq=[("How many people in BC do not have a family doctor?", f"According to The Tyee's report of the Health Minister's statement to the Legislature, 1,259,425 people (about 23% of the population) were not attached to a primary care provider at the end of April 2026 ({a('tyee_docs','The Tyee')})."),
         ("What does the BC government say it has done on family doctors?", f"It says more than 600,000 people were connected to a family doctor or nurse practitioner between 2023 and April 2026, and that upwards of 77% of British Columbians have a primary care provider ({a('health_rel','news release')})."),
         ("How much new health funding is in Budget 2026?", f"$2.8 billion over three years, including $2.3 billion to increase health system capacity ({a('bud_rel','budget release')}).")],
    watch="Watch for updated unattached-patient figures from the Ministry of Health and any party publishing costed health commitments."),
  "zh": dict(
    title="BC省医疗 2026：事实与各党立场",
    desc="2026年BC省选中的医疗与家庭医生：选民关切、政府和卫生部长公布的基层医疗数字，以及各党已发布的立场。",
    eyebrow="选举议题", h1="BC省的医疗与家庭医生",
    lede="医疗与住房同为选民最关心的问题。政府和批评者就家庭医生引用了不同的数字；这里两者并列，附上来源，以及各党已发布的立场。",
    voters=f"<ul><li><strong>Research Co.（2026年8月12至14日）：</strong>21%认为医疗是最重要的问题；55岁及以上人群中为34%（{a('research','Research Co.')}）。</li>"
           f"<li><strong>Leger（2026年4月3至6日）：</strong>29%把医疗列为首要关切，仅次于住房负担能力（30%）（{a('leger','Leger')}）。</li></ul>",
    facts=f"<p><strong>政府的说法。</strong>2026年4月1日的新闻稿称，自2023年以来已有超过60万人被匹配到家庭医生或执业护士，超过77%的BC居民现有基层医疗提供者，每周约再匹配4,000人（{a('health_rel','news.gov.bc.ca')}）。2026年预算在三年内新增28亿元医疗经费，其中23亿元用于提升系统能力，包括聘请更多医生、护士和医疗人员（{a('bud_rel','预算新闻稿，2026年2月17日')}）。</p>"
          f"<p><strong>数字的另一面。</strong>{a('tyee_docs','The Tyee在2026年5月31日报道')}，卫生部长向立法会表示，4月底最新数字为1,259,425人没有匹配到基层医疗提供者，约占BC省570万人口的23%。The Tyee称，NDP上台时的加拿大社区健康调查显示为897,000人（18.2%）。时任保守党卫生事务发言人Brennan Day说，政府的公告转移了人们对不断增加的未匹配病人名单的注意力。</p>"
          "<p><strong>如何解读：</strong>77%和23%是同一件事的两面。“已连接”统计的是新匹配的人数；未匹配数字是仍没有医疗提供者的人口比例。两者可以同时成立。</p>",
    positions=[
      ("ndp", None, f"2026年预算在三年内增加28亿元医疗经费；政府称自2023年以来已有超过60万人连接到基层医疗（{a('bud_rel','预算新闻稿')}；{a('health_rel','卫生新闻稿')}）。"),
      ("cons", None, f"平台页面在“Putting Patients First”下列出“扩大医疗可及性、终结长时间轮候”，并把心理健康和生殖健康列为优先事项。页面没有具体措施，也未标注日期（{a('cons_plat','平台页面')}）。"),
      ("grn", None, f"2024年平台估算医疗额外开支每年1.905亿元，心理健康每年1.429亿元增至1.543亿元，药物政策每年约2.9亿至2.97亿元；并提到检讨、合并卫生局可作为抵销来源（{a('grn_plat','2024年平台')}）。"),
      ("ctr", None, f"暂无具体的医疗立场。医疗是其政策委员会正在制定的领域之一（{a('cbc_policy','政策页面')}）。"),
      ("one", None, f"把大幅改革BC省医疗体系、使其“与全球最佳做法接轨”列为优先事项（{a('onebc','OneBC优先事项')}）。页面没有更多细节。"),
    ],
    faq=[("BC省有多少人没有家庭医生？", f"据The Tyee报道的卫生部长向立法会所作的陈述，2026年4月底有1,259,425人（约占人口的23%）没有匹配到基层医疗提供者（{a('tyee_docs','The Tyee')}）。"),
         ("BC政府称在家庭医生方面做了什么？", f"政府称，2023年至2026年4月期间超过60万人被匹配到家庭医生或执业护士，超过77%的BC居民有基层医疗提供者（{a('health_rel','新闻稿')}）。"),
         ("2026年预算新增了多少医疗经费？", f"三年内28亿元，其中23亿元用于提升医疗系统能力（{a('bud_rel','预算新闻稿')}）。")],
    watch="留意卫生部更新的未匹配病人数字，以及各党是否公布带成本估算的医疗承诺。"),
 },
 "budget-deficit": {
  "slug": "budget-deficit",
  "en": dict(
    title="BC Budget Deficit 2026: Party Positions",
    desc="BC's 2026 budget: deficits of $9.6B, $13.3B, $12.2B and $11.4B, debt and debt-to-GDP, what voters say, and the tax and spending positions parties have published.",
    eyebrow="Election issue", h1="BC's budget, deficit and debt",
    lede="BC's Budget 2026 forecasts deficits of $13.3 billion this fiscal year, declining to $11.4 billion by 2028-29. Here are the government's figures, how voters see the budget, and what each party has published on taxes and spending.",
    voters=f"<ul><li><strong>Leger (Apr 3–6, 2026):</strong> 46% say the government is spending too much; just 10% believe it is managing the budget responsibly; 53% favour a balanced approach to taxes, deficits and services; 35% prioritize deficit reduction even if it means spending cuts ({a('leger','Leger')}).</li>"
           f"<li><strong>Research Co. (Aug 12–14, 2026):</strong> 24% name the economy and jobs as the most important issue ({a('research','Research Co.')}).</li></ul>",
    facts=f"<p>Figures from the government's Budget 2026 fiscal plan, released February 17, 2026 ({a('bud_fiscal','BC Budget 2026 — Fiscal Plan')}; {a('bud_rel','release')}):</p>"
          '<div class="tablewrap"><table><thead><tr><th>Fiscal year</th><th>Deficit</th><th>Revenue</th><th>Expenses</th><th>Debt-to-GDP</th></tr></thead><tbody>'
          "<tr><td>2025-26 (updated)</td><td>$9.6 billion</td><td>—</td><td>—</td><td>26.1%</td></tr>"
          "<tr><td>2026-27</td><td>$13.3 billion</td><td>$85.5 billion</td><td>$98.8 billion</td><td>30.6%</td></tr>"
          "<tr><td>2027-28</td><td>$12.2 billion</td><td>$88.6 billion</td><td>$100.7 billion</td><td>34.4%</td></tr>"
          "<tr><td>2028-29</td><td>$11.4 billion</td><td>$91.8 billion</td><td>$103.2 billion</td><td>37.4%</td></tr></tbody></table></div>"
          "<ul><li>Taxpayer-supported debt is forecast to rise from $116.5 billion at the end of 2025-26 to $189 billion over the fiscal plan.</li>"
          "<li>The government says deficits decline through its efficiency review, hiring restrictions and streamlined services, and that BC's debt-to-GDP ratio is “among the best in Canada.” It also says its revenue outlook incorporates trade-related uncertainty due to U.S. tariffs.</li></ul>"
          "<p><strong>How to read this:</strong> a deficit is a single year's shortfall; debt is the total accumulated. The debt-to-GDP ratio compares debt with the size of the economy, which is why it is rising here even as deficits shrink.</p>",
    positions=[
      ("ndp", f"Says Budget 2026 makes “careful choices,” with deficits declining from 2026-27 through an efficiency review, hiring restrictions and streamlined services ({a('bud_rel','budget release')}).", None),
      ("cons", f"Its platform page describes “A Free and Prosperous BC” that would “encourage investment, get government working for taxpayers, and grow our living standards again.” It gives no specific tax or deficit figures and carries no date ({a('cons_plat','platform page')}).", None),
      ("grn", f"The 2024 platform proposes a new 22.5% marginal income tax rate above $350,000 ($394.5 million a year), property tax changes to capture the full holdings of owners ($938 million a year) and an 18% rate on corporate profits over $1 billion ($410 million a year), plus carbon tax revenue ({a('grn_plat','2024 platform')}).", None),
      ("ctr", f"Says it will combine a “socially progressive, fiscally responsible” approach; fiscal responsibility and sustainability are among five criteria for its proposals. No tax or deficit figures are published yet ({a('centrebc','CentreBC')}; {a('cbc_policy','policy page')}).", None),
      ("one", f"Priority to “trigger an economic boom with an immediate 50% tax cut on income under $100,000” and a 25% cut on all other personal and corporate income. We found no cost estimate on the page reviewed ({a('onebc','OneBC priorities')}).", None),
    ],
    faq=[("How big is BC's deficit?", f"Budget 2026 forecasts a deficit of $13.3 billion in 2026-27, $12.2 billion in 2027-28 and $11.4 billion in 2028-29, after $9.6 billion in 2025-26 ({a('bud_fiscal','Budget 2026 fiscal plan')})."),
         ("How much debt does BC have?", f"Taxpayer-supported debt was $116.5 billion at the end of 2025-26 and is forecast to reach $189 billion by the end of the fiscal plan; debt-to-GDP rises from 26.1% to 37.4% ({a('bud_fiscal','Budget 2026 fiscal plan')})."),
         ("What do voters think of the government's budget management?", f"In Leger's April 2026 poll, 46% said the government is spending too much and 10% said it is managing the budget responsibly ({a('leger','Leger')}).")],
    watch="Watch for the government's next fiscal update and for parties publishing costed tax and spending plans that can be compared line by line."),
  "zh": dict(
    title="BC省预算赤字与债务 2026：各党立场",
    desc="BC省2026年预算：赤字96亿、133亿、122亿和114亿元，债务与债务占GDP比，选民看法，以及各党已发布的税收与开支立场。",
    eyebrow="选举议题", h1="BC省的预算、赤字与债务",
    lede="BC省2026年预算预测本财年赤字133亿元，到2028-29财年降至114亿元。这里列出政府的数字、选民怎么看预算，以及各党在税收和开支上已发布的立场。",
    voters=f"<ul><li><strong>Leger（2026年4月3至6日）：</strong>46%认为政府开支过多；只有10%认为政府在负责任地管理预算；53%赞成在税收、赤字和服务之间采取平衡做法；35%认为应优先削减赤字，即使要削减开支（{a('leger','Leger')}）。</li>"
           f"<li><strong>Research Co.（2026年8月12至14日）：</strong>24%认为经济与就业是最重要的问题（{a('research','Research Co.')}）。</li></ul>",
    facts=f"<p>以下数字来自政府2026年2月17日发布的预算财政计划（{a('bud_fiscal','BC省2026年预算——财政计划')}；{a('bud_rel','新闻稿')}）：</p>"
          '<div class="tablewrap"><table><thead><tr><th>财政年度</th><th>赤字</th><th>收入</th><th>开支</th><th>债务占GDP</th></tr></thead><tbody>'
          "<tr><td>2025-26（更新）</td><td>96亿元</td><td>—</td><td>—</td><td>26.1%</td></tr>"
          "<tr><td>2026-27</td><td>133亿元</td><td>855亿元</td><td>988亿元</td><td>30.6%</td></tr>"
          "<tr><td>2027-28</td><td>122亿元</td><td>886亿元</td><td>1,007亿元</td><td>34.4%</td></tr>"
          "<tr><td>2028-29</td><td>114亿元</td><td>918亿元</td><td>1,032亿元</td><td>37.4%</td></tr></tbody></table></div>"
          "<ul><li>纳税人支持的债务预计由2025-26财年末的1,165亿元升至财政计划期末的1,890亿元。</li>"
          "<li>政府称，赤字将通过效率检讨、限制聘用和精简服务而下降，并称BC省的债务占GDP比率“在全国属于最好之列”。政府还表示，其收入预测已纳入美国关税带来的贸易不确定性。</li></ul>"
          "<p><strong>如何解读：</strong>赤字是单一年度的缺口，债务是累积总额。债务占GDP比率是把债务与经济规模相比，所以即使赤字缩小，这个比率仍在上升。</p>",
    positions=[
      ("ndp", None, f"称2026年预算作出了“审慎的选择”，赤字从2026-27年度起通过效率检讨、限制聘用和精简服务而下降（{a('bud_rel','预算新闻稿')}）。"),
      ("cons", None, f"平台页面描述“自由繁荣的BC”，将“鼓励投资、让政府为纳税人工作、再次提高我们的生活水平”。页面没有具体的税收或赤字数字，也未标注日期（{a('cons_plat','平台页面')}）。"),
      ("grn", None, f"2024年平台提出：年收入超过35万元的部分新增22.5%边际税率（每年3.945亿元）、修改物业税以涵盖业主全部持有（每年9.38亿元）、对超过10亿元的公司利润征收18%税率（每年4.1亿元），另有碳税收入（{a('grn_plat','2024年平台')}）。"),
      ("ctr", None, f"称将采取“社会上进步、财政上负责”的做法；财政责任与可持续性是评估其提案的五项标准之一。目前未公布税收或赤字数字（{a('centrebc','CentreBC')}；{a('cbc_policy','政策页面')}）。"),
      ("one", None, f"优先事项为“立即对10万元以下的收入减税50%来启动经济繁荣”，其他个人和公司收入减税25%。在我们查阅的页面上未找到成本估算（{a('onebc','OneBC优先事项')}）。"),
    ],
    faq=[("BC省的赤字有多大？", f"2026年预算预测2026-27年度赤字133亿元、2027-28年度122亿元、2028-29年度114亿元，2025-26年度为96亿元（{a('bud_fiscal','2026年预算财政计划')}）。"),
         ("BC省有多少债务？", f"纳税人支持的债务在2025-26财年末为1,165亿元，预计到财政计划期末达1,890亿元；债务占GDP比率由26.1%升至37.4%（{a('bud_fiscal','2026年预算财政计划')}）。"),
         ("选民怎么看政府的预算管理？", f"在Leger的2026年4月民调中，46%认为政府开支过多，10%认为政府在负责任地管理预算（{a('leger','Leger')}）。")],
    watch="留意政府下一次财政更新，以及各党是否公布可以逐项对比的税收和开支计划。"),
 },
 "us-tariffs": {
  "slug": "us-tariffs",
  "en": dict(
    title="BC and U.S. Tariffs 2026: Party Positions",
    desc="U.S. tariffs and BC softwood lumber in 2026: the government's budget assumptions, the softwood duty review and its October 2026 final determination, and party positions.",
    eyebrow="Election issue", h1="U.S. tariffs, softwood lumber and BC's economy",
    lede="Premier Eby called the October 24, 2026 election citing the trade war with the United States as an “existential” issue for BC. This page sets out what the government's budget says about tariffs, where the softwood lumber duty review stands, and what each party has published.",
    voters=f"<ul><li><strong>Research Co. (Aug 12–14, 2026):</strong> 24% name the economy and jobs as the most important issue facing BC, second to housing, poverty and homelessness (29%) ({a('research','Research Co.')}). The poll does not report a separate tariff question.</li></ul>",
    facts=f"<ul><li><strong>Budget assumptions.</strong> The government says its revenue outlook “incorporates trade-related uncertainty due to U.S. tariffs” ({a('bud_fiscal','Budget 2026 fiscal plan')}). To help the forestry sector through sustained international tariffs, it announced $50 million in new provincial and reallocated federal funding ({a('bud_rel','budget release')}).</li>"
          f"<li><strong>Softwood lumber duty review.</strong> On June 30, 2026 the U.S. Department of Commerce published post-preliminary results in its seventh administrative review of the countervailing duty order on Canadian softwood lumber. The BC government says these do not change current duties or cash deposit rates, which will not change until Commerce issues its final determination, expected October 2026. The post-preliminary combined rates it lists are 31.37% for Canfor, 20.92% for West Fraser, 25.49% for Resolute and 25.18% for all others; it notes these are not in effect and may change ({a('softwood','BC government softwood page')}).</li>"
          f"<li><strong>Premier Eby's position.</strong> On April 14, 2026 he urged Ottawa to make a “mutual benefit” case to the U.S., saying the U.S. cannot meet its own lumber demand and has sharply increased imports from Europe and Russia ({a('cp_soft','report of April 14, 2026')}).</li></ul>"
          "<p><strong>How to read this:</strong> the duty rates above are preliminary and for information only. The final determination is the date to watch.</p>",
    positions=[
      ("ndp", f"The government has put money into forestry-sector support in Budget 2026 and, through the premier, is urging Ottawa to press the softwood case with the U.S. ({a('bud_rel','budget release')}; {a('cp_soft','report of April 14, 2026')}).", None),
      ("cons", "The platform page we reviewed contains no position on trade or tariffs. See the party's site for newer policy (" + ASOF_EN + ").", None),
      ("grn", NOTFOUND_EN, None),
      ("ctr", NOTFOUND_EN, None),
      ("one", NOTFOUND_EN, None),
    ],
    faq=[("How do U.S. tariffs affect BC's budget?", f"The government says its revenue outlook incorporates trade-related uncertainty due to U.S. tariffs, and that it is putting $50 million into forestry-sector support ({a('bud_fiscal','fiscal plan')}; {a('bud_rel','release')})."),
         ("When will the U.S. softwood lumber duty rates be final?", f"The BC government says Commerce's final determination in the current administrative review is expected in October 2026; until then current duties and cash deposit rates do not change ({a('softwood','BC government')})."),
         ("Did the premier tie the election call to the trade war?", f"Yes. Premier Eby called the October 24, 2026 election citing the U.S. trade war as an “existential” issue for BC that voters should have a say on ({a('infonews_call','iNFOnews, Sept 22, 2026')}).")],
    watch="The expected October 2026 final softwood determination, any federal tariff relief for lumber, and whether other parties publish trade positions."),
  "zh": dict(
    title="BC省与美国关税 2026：事实与各党立场",
    desc="2026年美国关税与BC省软木材：政府预算的假设、软木材反补贴税复审及预计2026年10月的最终裁定，以及各党立场。",
    eyebrow="选举议题", h1="美国关税、软木材与BC省经济",
    lede="省长Eby宣布2026年10月24日举行省选时，称与美国的贸易战对BC是“生死攸关”的问题。本页列出政府预算对关税的说法、软木材税复审目前进展，以及各党已发布的立场。",
    voters=f"<ul><li><strong>Research Co.（2026年8月12至14日）：</strong>24%认为经济与就业是BC省最重要的问题，仅次于住房、贫困和无家可归（29%）（{a('research','Research Co.')}）。该民调没有单独的关税问题。</li></ul>",
    facts=f"<ul><li><strong>预算假设。</strong>政府称其收入预测“纳入了美国关税带来的贸易不确定性”（{a('bud_fiscal','2026年预算财政计划')}）。为帮助林业行业应对持续的国际关税，政府宣布投入5,000万元新增省府资金和重新分配的联邦资金（{a('bud_rel','预算新闻稿')}）。</li>"
          f"<li><strong>软木材税复审。</strong>2026年6月30日，美国商务部公布了对加拿大软木材反补贴税令第七次行政复审的补充初步结果。BC政府称，这不会改变现行关税和现金保证金税率，税率要到商务部作出最终裁定（预计2026年10月）后才会变动。政府列出的补充初步合计税率为：Canfor 31.37%、West Fraser 20.92%、Resolute 25.49%、其他公司25.18%；并注明这些税率尚未生效，可能改变（{a('softwood','BC政府软木材页面')}）。</li>"
          f"<li><strong>Eby省长的立场。</strong>2026年4月14日，他促请联邦政府向美国阐明“互惠互利”的理由，称美国无法满足自身的木材需求，并大幅增加了从欧洲和俄罗斯的进口（{a('cp_soft','2026年4月14日的报道')}）。</li></ul>"
          "<p><strong>如何解读：</strong>上述税率是初步结果，仅供参考。最终裁定才是要留意的时间点。</p>",
    positions=[
      ("ndp", None, f"政府在2026年预算中投入林业支持资金，并通过省长促请联邦政府向美国力争软木材问题（{a('bud_rel','预算新闻稿')}；{a('cp_soft','2026年4月14日的报道')}）。"),
      ("cons", None, "我们查阅的平台页面没有涉及贸易或关税的立场。较新的政策请查看该党官网（" + ASOF_ZH + "）。"),
      ("grn", None, NOTFOUND_ZH),
      ("ctr", None, NOTFOUND_ZH),
      ("one", None, NOTFOUND_ZH),
    ],
    faq=[("美国关税如何影响BC省预算？", f"政府称其收入预测纳入了美国关税带来的贸易不确定性，并投入5,000万元支持林业行业（{a('bud_fiscal','财政计划')}；{a('bud_rel','新闻稿')}）。"),
         ("美国软木材税率什么时候最终确定？", f"BC政府称，商务部在本轮行政复审中的最终裁定预计在2026年10月；在此之前，现行关税和现金保证金税率不变（{a('softwood','BC政府')}）。"),
         ("省长有没有把选举与贸易战联系起来？", f"有。省长Eby宣布2026年10月24日举行省选时，称与美国的贸易战对BC是“生死攸关”的问题，选民应该有发言权（{a('infonews_call','iNFOnews，2026年9月22日')}）。")],
    watch="预计2026年10月的软木材最终裁定、联邦对木材行业的关税援助，以及其他政党是否发布贸易立场。"),
 },
}


def issue_positions_table(lang, rows):
    en = lang == "en"
    out = ('<div class="tablewrap"><table><thead><tr><th>' + ("Party" if en else "政党") + "</th><th>"
           + ("What it has published" if en else "已发布的内容") + "</th></tr></thead><tbody>")
    for key, en_txt, zh_txt in rows:
        lbl = POS_LABEL[key][0 if en else 1]
        out += f"<tr><td><strong>{lbl}</strong></td><td>{en_txt if en else zh_txt}</td></tr>"
    return out + "</tbody></table></div>"


def issue_method_note(lang):
    if lang == "en":
        return ("<p class=\"source-note\">How we describe positions: only what a party or the government has published, with a link. Government statements are labelled as the government's claims. "
                f"Where we found nothing, we say so. Positions come from platform and policy pages reviewed {ASOF_EN}; several parties have not yet published a 2026 platform, and the Conservative and Green pages cited may pre-date the current leaders. "
                "BC Vote Watch does not rank or endorse parties. Corrections: see <a href=\"/sources\">our sourcing rules</a>.</p>")
    return (f"<p class=\"source-note\">我们如何描述立场：只写政党或政府已发布的内容并附链接；政府的说法会标明是政府的主张；没找到的就如实说明。立场来自{ASOF_ZH}查阅的平台和政策页面；部分政党尚未发布2026年平台，所引用的保守党和绿党页面可能早于现任党魁。"
            "BC Vote Watch不对政党排名，也不作背书。如有更正，见<a href=\"/sources\">来源与方法</a>。</p>")


def page_issue(lang, key):
    L = lambda s: conv(lang, s)
    en = lang == "en"
    d = ISSUES[key]["en" if en else "zh"]
    hub = url_for(lang, "bc-election-issues")
    path = url_for(lang, "issues/" + key)
    sections = (
        hero(d["eyebrow"], d["h1"], d["lede"])
        + f'<section class="section"><div class="wrap"><h2>{"What voters say" if en else "选民怎么说"}</h2>{d["voters"]}</div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{"The facts" if en else "官方数据与事实"}</h2>{d["facts"]}</div></section>'
        + f'<section class="section"><div class="wrap"><h2>{"Where the parties stand" if en else "各党立场"}</h2>{issue_positions_table(lang, d["positions"])}{issue_method_note(lang)}</div></section>'
        + f'<section class="section soft"><div class="wrap"><h2>{"What to watch" if en else "接下来关注"}</h2><p>{d["watch"]}</p></div></section>'
        + faq_html(d["faq"], "FAQ" if en else "常见问题")
        + '<section class="section"><div class="wrap"><h2>' + ("More election issues" if en else "更多议题") + '</h2><div class="linkgrid">'
        + "".join(
            f'<a class="linkcard" href="{url_for(lang, "issues/" + k)}"><strong>{ISSUES[k]["en" if en else "zh"]["h1"]}</strong></a>'
            for k in ISSUE_ORDER if k != key)
        + f'<a class="linkcard" href="{hub}"><strong>{"All election issues" if en else "全部选举议题"}</strong></a></div>'
        + f'<p class="source-note">{"Related" if en else "相关"}: <a href="{url_for(lang, "bc-election-polls")}">{"BC election polls" if en else "BC省选民调"}</a> · <a href="{url_for(lang, "bc-party-leaders")}">{"party leaders" if en else "党魁"}</a> · <a href="{url_for(lang, "bc-election-2026")}">{"is there a BC election?" if en else "省选2026指南"}</a></p></div></section>'
    )
    title = d["title"] if en else L(d["title"])
    desc = d["desc"] if en else L(d["desc"])
    body = sections if en else L(sections)
    schemas = [article_schema(title, desc, lang, path),
               breadcrumb(lang, [("Home" if en else L("首页"), "/"), ("Election Issues" if en else L("选举议题"), hub), (d["h1"] if en else L(d["h1"]), path)]),
               faq_schema([(q, re.sub(r"<[^>]+>", "", a_)) if en else (L(q), L(re.sub(r"<[^>]+>", "", a_))) for q, a_ in d["faq"]])]
    return render(lang, "issues/" + key, title, desc, body, ISSUE_GROUPS[key], schemas)


def page_issues_hub(lang):
    L = lambda s: conv(lang, s)
    en = lang == "en"
    rows_en = [("Housing, poverty and homelessness", "29%", "Ages 35–54: 36%"), ("Economy and jobs", "24%", "Ages 18–34: 32%"),
               ("Health care", "21%", "Ages 55+: 34%"), ("Crime and public safety", "8%", ""), ("Environment", "5%", ""), ("Accountability", "3%", "")]
    rows_zh = [("住房、贫困和无家可归", "29%", "35至54岁：36%"), ("经济与就业", "24%", "18至34岁：32%"),
               ("医疗", "21%", "55岁及以上：34%"), ("犯罪与公共安全", "8%", ""), ("环境", "5%", ""), ("问责", "3%", "")]
    rows = "".join(f"<tr><td>{a_}</td><td>{b}</td><td>{c}</td></tr>" for a_, b, c in (rows_en if en else rows_zh))
    cards = "".join(
        f'<a class="linkcard" href="{url_for(lang, "issues/" + k)}"><strong>{ISSUES[k]["en" if en else "zh"]["h1"]}</strong><span>{ISSUES[k]["en" if en else "zh"]["desc"]}</span></a>'
        for k in ISSUE_ORDER)
    if en:
        body = (
            hero("Election issues", "BC election issues 2026: what voters care about",
                 "The issues most likely to shape a BC election, with what voters say in polls, the official numbers, and what each party has published, sourced line by line.")
            + f'<section class="section"><div class="wrap"><h2>Most important issue facing BC</h2><div class="tablewrap"><table><thead><tr><th>Issue</th><th>Share</th><th>Age note</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f"<p class=\"source-note\">Source: {a('research','Research Co.')}, August 12–14, 2026, 801 adults, ±3.5. In Leger's April 3–6 poll, housing affordability (30%) and healthcare (29%) were the two top concerns ({a('leger','Leger')}).</p></div></section>"
            f'<section class="section soft"><div class="wrap"><h2>Issue guides</h2><div class="linkgrid">{cards}</div>{issue_method_note(lang)}</div></section>'
            '<section class="section"><div class="wrap"><p class="source-note">Next: <a href="/bc-election-polls">BC election polls</a> · <a href="/bc-party-leaders">party leaders</a> · <a href="/bc-election-2026">is there a BC election in 2026?</a> · <a href="/bc-election-ridings">all 93 ridings</a></p></div></section>'
        )
        title = "BC Election Issues 2026: Voter Concerns"
        desc = "BC election issues 2026: housing, health care, the budget and U.S. tariffs, with what voters say, the official numbers and each party's published position."
    else:
        body = (
            hero("选举议题", L("BC省选举议题 2026：选民最关心什么"),
                 L("最可能左右BC省选举的议题：选民在民调中怎么说、官方数字，以及各党已发布的立场，逐条附来源。"))
            + f'<section class="section"><div class="wrap"><h2>{L("BC省面临的最重要问题")}</h2><div class="tablewrap"><table><thead><tr><th>{L("议题")}</th><th>{L("比例")}</th><th>{L("年龄说明")}</th></tr></thead><tbody>{L(rows)}</tbody></table></div>'
            + L(f"<p class=\"source-note\">来源：{a('research','Research Co.')}，2026年8月12至14日，801名成年人，误差±3.5。在Leger的4月3至6日民调中，住房负担能力（30%）和医疗（29%）是两大首要关切（{a('leger','Leger')}）。</p></div></section>")
            + f'<section class="section soft"><div class="wrap"><h2>{L("议题指南")}</h2><div class="linkgrid">{L(cards)}</div>{issue_method_note(lang)}</div></section>'
            + L(f'<section class="section"><div class="wrap"><p class="source-note">继续：<a href="{url_for(lang,"bc-election-polls")}">BC省选民调</a> · <a href="{url_for(lang,"bc-party-leaders")}">党魁</a> · <a href="{url_for(lang,"bc-election-2026")}">BC省选2026指南</a> · <a href="{url_for(lang,"bc-election-ridings")}">全部93个选区</a></p></div></section>')
        )
        title = L("BC省选举议题 2026：选民最关心什么")
        desc = L("BC省2026年选举议题：住房、医疗、预算和美国关税，附选民看法、官方数字和各党已发布的立场。")
    path = url_for(lang, "bc-election-issues")
    schemas = [article_schema(title, desc, lang, path), breadcrumb(lang, [("Home" if en else L("首页"), "/"), ("Election Issues" if en else L("选举议题"), path)])]
    return render(lang, "bc-election-issues", title, desc, body, GROUPS["issues"], schemas)


ISSUE_GROUPS = {k: {"en": "issues/" + k, "zh-cn": "issues/" + k, "zh-tw": "issues/" + k} for k in ISSUE_ORDER}


# ---------------------------------------------------------------- groups + sitemap
GROUPS = {
    "hub": {"en": "bc-election-2026", "zh-cn": "bc-election-2026", "zh-tw": "bc-election-2026"},
    "polls": {"en": "bc-election-polls", "zh-cn": "bc-election-polls", "zh-tw": "bc-election-polls"},
    "how": {"en": "how-to-vote-bc", "zh-cn": "how-to-vote-bc", "zh-tw": "how-to-vote-bc"},
    "leaders": {"en": "bc-party-leaders", "zh-cn": "bc-party-leaders", "zh-tw": "bc-party-leaders"},
    "byel": {"en": "abbotsford-mission-by-election-2026", "zh-cn": "abbotsford-mission-by-election-2026", "zh-tw": "abbotsford-mission-by-election-2026"},
    "ridings": {"en": "bc-election-ridings", "zh-cn": "bc-election-ridings", "zh-tw": "bc-election-ridings"},
    "issues": {"en": "bc-election-issues", "zh-cn": "bc-election-issues", "zh-tw": "bc-election-issues"},
    "results": {"en": "bc-election-results-2024", "zh-cn": "bc-election-results-2024", "zh-tw": "bc-election-results-2024"},
}
EN_ONLY = ["", "bc-election-candidates-2026", "sources"]


def sitemap():
    def loc(l, s):
        return SITE + (url_for(l, s) if s else "/")

    entries = []
    for s in EN_ONLY:
        entries.append(f"<url><loc>{loc('en', s)}</loc><lastmod>{TODAY}</lastmod></url>")
    for g in list(GROUPS.values()) + list(ISSUE_GROUPS.values()) + [riding_group(r["slug"]) for r in RIDINGS]:
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
    """sources.html and 404.html keep their body; only the nav is refreshed."""
    nav = "<nav>" + "".join(f'<a href="{h}">{t}</a>' for h, t in NAV_EN) + "</nav>"
    for name in ("sources.html", "404.html"):
        p = os.path.join(ROOT, name)
        s = open(p, encoding="utf8").read()
        s = re.sub(r"<nav>.*?</nav>", nav, s, count=1, flags=re.S)
        if 'rel="icon"' not in s:
            s = s.replace('<link rel="stylesheet"', ICONS + '<link rel="stylesheet"', 1)
        open(p, "w", encoding="utf8").write(s)


if __name__ == "__main__":
    page_home_en()
    page_hub_en()
    page_polls_en()
    page_how_en()
    page_leaders_en()
    page_candidates_en()
    page_byel_en()
    page_results_en()
    page_ridings_hub("en")
    page_issues_hub("en")
    for k in ISSUE_ORDER:
        page_issue("en", k)
    for r in RIDINGS:
        page_riding("en", r)
    for lang in ("zh-cn", "zh-tw"):
        page_ridings_hub(lang)
        page_issues_hub(lang)
        for k in ISSUE_ORDER:
            page_issue(lang, k)
        for r in RIDINGS:
            page_riding(lang, r)
        page_hub_zh(lang)
        page_polls_zh(lang)
        page_how_zh(lang)
        page_leaders_zh(lang)
        page_byel_zh(lang)
        page_results_zh(lang)
    patch_static()
    print("sitemap urls:", sitemap())
