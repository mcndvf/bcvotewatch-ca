#!/usr/bin/env python3
"""Parse Elections BC's 2024 Statement of Votes into data/ridings-2024.json.

Source (download it first, 3.7 MB, not stored in this repo):
  https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf

    python3 scripts/parse_statement_of_votes.py path/to/statement-of-votes.pdf

Needs pypdf and fonttools. The script refuses to write output unless every
district passes integrity checks against the official district summary table:
candidate votes must add up to the district's total valid votes, and the NDP,
Conservative and Green columns must match the candidates' party totals.
"""
import json
import os
import re
import sys

from pypdf import PdfReader

PARTIES = [
    "Christian Heritage Party of B.C.",
    "Communist Party of BC",
    "Freedom Party of BC",
    "Conservative Party",
    "BC Green Party",
    "Unaffiliated",
    "Libertarian",
    "Independent",
    "BC NDP",
]
HEADER_RE = re.compile(
    r"^(Elections BC( \d+)?|\d+ Elections BC|Elections BC \| Statement of Votes.*|Summary of results by candidate|"
    r"Electoral district Candidate ballot name.*|Elected candidates are shown.*)$"
)


def clean_nums(s):
    # the PDF text layer sometimes inserts spaces: "17 ,208", "47 .35%", "7 ,560"
    s = re.sub(r"(\d)\s+([,.])", r"\1\2", s)
    s = re.sub(r"([,.])\s+(\d)", r"\1\2", s)
    return s


def num(s):
    return int(s.replace(",", ""))


def main(pdf_path, out_path):
    reader = PdfReader(pdf_path)
    pages = [(p.extract_text() or "") for p in reader.pages]

    # --- district summary table -------------------------------------------------
    summary = {}
    order = []
    row_re = re.compile(
        r"^(?P<name>.+?) (?P<ndp>[\d,]+|---) (?P<cp>[\d,]+|---) (?P<gp>[\d,]+|---) (?P<oth>[\d,]+|---) "
        r"(?P<valid>[\d,]+) (?P<rej>[\d,]+) (?P<voted>[\d,]+)\s+(?P<reg>[\d,]+) (?P<pct>\d+\.\d+)%$"
    )
    for t in pages:
        if "Summary of results by electoral district" not in t:
            continue
        for line in t.splitlines():
            line = clean_nums(line.strip())
            m = row_re.match(line)
            if not m:
                continue
            v = lambda k: 0 if m.group(k) == "---" else num(m.group(k))
            name = m.group("name")
            if name == "Total":
                continue
            summary[name] = {
                "ndp": v("ndp"), "cp": v("cp"), "gp": v("gp"), "other": v("oth"),
                "valid": v("valid"), "rejected": v("rej"), "voted": v("voted"),
                "registered": v("reg"), "turnout": float(m.group("pct")),
            }
            order.append(name)
    if len(order) != 93:
        sys.exit(f"expected 93 districts in the summary table, found {len(order)}")
    by_len = sorted(order, key=len, reverse=True)

    # --- candidate table --------------------------------------------------------
    lines = []
    for t in pages:
        if "Summary of results by candidate" not in t or "Summary of results by electoral district" in t:
            continue
        for line in t.splitlines():
            line = line.strip()
            if not line or HEADER_RE.match(line):
                continue
            lines.append(clean_nums(line))
    rec_end = re.compile(r"^(?P<txt>.*?)\s*(?P<votes>\d[\d,]*) (?P<pct>\d+\.\d+)%$")
    cands = {d: [] for d in order}
    buf = ""
    current = None
    for line in lines:
        buf = (buf + " " + line).strip()
        m = rec_end.match(buf)
        if not m:
            continue
        txt = m.group("txt").strip()
        for d in by_len:
            if txt == d or txt.startswith(d + " "):
                current = d
                txt = txt[len(d):].strip()
                break
        if current is None:
            sys.exit(f"record before any district: {buf}")
        party = next((p for p in PARTIES if txt.endswith(" " + p)), None)
        if party is None:
            sys.exit(f"unknown party in: {buf!r}")
        name = txt[: -len(party)].strip()
        incumbent = name.endswith("*")
        name = name.rstrip("*").strip()
        cands[current].append({
            "name": name, "party": party, "votes": num(m.group("votes")),
            "pct": float(m.group("pct")), "incumbent": incumbent,
        })
        buf = ""
    if buf:
        sys.exit(f"unparsed trailing text: {buf!r}")

    # --- integrity checks -------------------------------------------------------
    key = {"BC NDP": "ndp", "Conservative Party": "cp", "BC Green Party": "gp"}
    ridings = []
    for d in order:
        cs = cands[d]
        s = summary[d]
        if sum(c["votes"] for c in cs) != s["valid"]:
            sys.exit(f"{d}: candidate votes {sum(c['votes'] for c in cs)} != valid {s['valid']}")
        for p, k in key.items():
            got = sum(c["votes"] for c in cs if c["party"] == p)
            if got != s[k]:
                sys.exit(f"{d}: {p} {got} != summary {s[k]}")
        for c in cs:
            if abs(c["pct"] - round(100 * c["votes"] / s["valid"], 2)) > 0.011:
                sys.exit(f"{d}: pct mismatch for {c['name']}: {c['pct']}")
        cs = sorted(cs, key=lambda c: -c["votes"])
        ridings.append({"name": d, **s, "candidates": cs})

    tot = {k: sum(r[k] for r in ridings) for k in ("ndp", "cp", "gp", "other", "valid", "rejected", "registered")}
    if (tot["ndp"], tot["cp"], tot["gp"], tot["valid"], tot["registered"]) != (944579, 911153, 173377, 2105341, 3609288):
        sys.exit(f"province totals do not match the official summary: {tot}")
    prov = {}
    for r in ridings:
        w = r["candidates"][0]["party"]
        prov[w] = prov.get(w, 0) + 1
    print("seats by party:", prov)
    out = {
        "source": "https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf",
        "title": "Statement of Votes, 43rd Provincial General Election, October 19, 2024",
        "note": "Incumbent = member of the 42nd Parliament, as marked by Elections BC. Winner = most votes.",
        "ridings": ridings,
    }
    with open(out_path, "w", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", out_path, len(ridings), "ridings")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1], os.path.join(root, "data", "ridings-2024.json"))
