"""Build the static jobs.teeortee.com site from data/jobs.json into site/."""
import json, os, re, sys, html, datetime, shutil
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, REGIONS, TEES, ROLE_TEES, SHOP, SITE, EXCLUDE, VERIFY, INDEXNOW_KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
DB = json.load(open(os.path.join(ROOT, "data", "jobs.json")))
TODAY = datetime.date.today()
NICE = TODAY.strftime("%A %d %B %Y")
E = html.escape
ROLE_NAME = {r[0]: r[1] for r in ROLES}
REGION_NAME = {r[0]: r[1] for r in REGIONS}
SIGNUP = os.environ.get("SIGNUP_URL", SHOP)  # Brevo hosted form URL, set later
UTM = "utm_source=jobs.teeortee.com&utm_medium=referral&utm_campaign=jobs"
ACTIVE_CUT = (TODAY - datetime.timedelta(days=2)).isoformat()  # seen in the last 2 daily runs = still open
REGION_CC = {"usa": "US", "uk": "GB", "canada": "CA"}
EU_CC = [("germany", "DE"), ("berlin", "DE"), ("munich", "DE"), ("hamburg", "DE"), ("frankfurt", "DE"), ("netherlands", "NL"),
         ("amsterdam", "NL"), ("france", "FR"), ("paris", "FR"), ("spain", "ES"), ("madrid", "ES"), ("barcelona", "ES"),
         ("ireland", "IE"), ("dublin", "IE"), ("italy", "IT"), ("milan", "IT"), ("belgium", "BE"), ("brussels", "BE"),
         ("austria", "AT"), ("vienna", "AT"), ("switzerland", "CH"), ("zurich", "CH"), ("geneva", "CH"), ("poland", "PL"),
         ("warsaw", "PL"), ("sweden", "SE"), ("stockholm", "SE"), ("denmark", "DK"), ("copenhagen", "DK"),
         ("portugal", "PT"), ("lisbon", "PT"), ("new zealand", "NZ"), ("auckland", "NZ")]
SITEMAP = []  # (path, lastmod) collected by page()


def recent(days):
    cut = (TODAY - datetime.timedelta(days=days)).isoformat()
    return sorted([j for j in DB.values() if j.get("first_seen", "") >= cut
                   and not any(x in " " + j["title"].lower() + " " for x in EXCLUDE)],
                  key=lambda j: (j.get("first_seen", ""), j.get("posted", "")), reverse=True)


def tee_strip(keys, heading="Between interviews: funny tees for project people"):
    cards = "".join(
        f'<a class="card" href="{SHOP}/products/{TEES[k][1]}?{UTM}"><img src="/assets/{k}.png" alt="{E(TEES[k][0])} t-shirt" loading="lazy"><span>{E(TEES[k][0])}</span></a>'
        for k in keys)
    return f'<aside class="strip"><p class="strip-h">{E(heading)}</p><div class="cards">{cards}</div><a class="btn" href="{SHOP}/collections/all?{UTM}">Shop all tees at teeortee.com</a></aside>'


KEYWORD_TEES = [  # title keywords -> most relevant tee
    (("risk", "compliance", "security", "audit", "grc"), "risk"),
    (("schedul", "planner", "planning", "critical path"), "cp"),
    (("controls", "cost", "baseline"), "baseline"),
    (("scrum", "agile", "delivery", "release"), "roadmap"),
    (("program", "portfolio", "transformation"), "deps"),
    (("pmo", "governance", "operations"), "meeting"),
    (("product",), "roadmap"),
    (("construction", "infrastructure", "data center", "engineering"), "scope"),
    (("change",), "cr"),
]


def tees_for(j):
    """3 tees most relevant to this job: keyword match first, then the role's defaults."""
    t = j["title"].lower()
    picks = [k for kws, k in KEYWORD_TEES if any(w in t for w in kws)]
    out = []
    for k in picks + ROLE_TEES[j["role"]] + ["pm", "scope", "cr"]:
        if k not in out:
            out.append(k)
    return out[:3]


def job_li(j):
    return (f'<li><a href="/job/{E(j["id"])}/"><strong>{E(j["title"])}</strong></a>'
            f'<span>{E(j["company"])} · {E(j["location"])}</span>'
            f'<em>{E(ROLE_NAME[j["role"]])} · Source: {E(j["source"])} · Added {E(j["first_seen"])}</em></li>')


def country_of(j):
    if j["region"] in REGION_CC:
        return REGION_CC[j["region"]]
    l = j["location"].lower()
    if j["region"] == "australia":
        return "NZ" if ("zealand" in l or "auckland" in l) else "AU"
    return next((c for k, c in EU_CC if k in l), "")


def desc_html(t):
    """Plain text with '• ' bullets -> simple safe HTML."""
    out, ul = [], []
    for line in t.split("\n"):
        if line.startswith("• "):
            ul.append(f"<li>{E(line[2:])}</li>")
            continue
        if ul:
            out.append("<ul>" + "".join(ul) + "</ul>"); ul = []
        out.append(f"<p>{E(line)}</p>")
    if ul:
        out.append("<ul>" + "".join(ul) + "</ul>")
    return "".join(out)


def job_schema(j, dhtml):
    valid = (datetime.date.fromisoformat(j.get("last_seen", TODAY.isoformat())) + datetime.timedelta(days=30)).isoformat()
    cc = country_of(j)
    o = {"@context": "https://schema.org", "@type": "JobPosting", "title": j["title"], "description": dhtml,
         "datePosted": j.get("posted") or j["first_seen"], "validThrough": valid + "T23:59:59Z",
         "hiringOrganization": {"@type": "Organization", "name": j["company"]},
         "directApply": False, "url": SITE + f"/job/{j['id']}/"}
    if j.get("etype"):
        o["employmentType"] = j["etype"]
    loc = j["location"]
    if j.get("remote"):
        o["jobLocationType"] = "TELECOMMUTE"
        o["applicantLocationRequirements"] = {"@type": "Country", "name": cc or REGION_NAME[j["region"]]}
    if loc and not (j.get("remote") and loc.lower().strip() in ("remote", "anywhere", "worldwide")):
        addr = {"@type": "PostalAddress", "addressLocality": loc.split(";")[0].split(",")[0].strip()}
        if cc:
            addr["addressCountry"] = cc
        o["jobLocation"] = {"@type": "Place", "address": addr}
    return o


def job_page(j, similar):
    rid, gid = j["role"], j["region"]
    rname, gname = ROLE_NAME[rid], REGION_NAME[gid]
    active = j.get("last_seen", "") >= ACTIVE_CUT
    d = j.get("desc", "")
    dhtml = desc_html(d) if d else ""
    indexable = active and len(d) >= 200
    work = "Remote" if j.get("remote") else "See listing"
    etype = (j.get("etype") or "").replace("_", " ").title() or "Not stated"
    sim = "".join(job_li(x) for x in similar)
    trail = [("Jobs today", "/"), (f"{rname} jobs", f"/role/{rid}/"), (f"{rname} jobs in {gname}", f"/role/{rid}/{gid}/")]
    closed = "" if active else '<p class="note closed">This listing was not found in our latest check and may have closed. Check the source before applying.</p>'
    body = (f'<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(f'<a href="{u}">{E(n)}</a>' for n, u in trail) + '</nav>'
            f'<article class="job"><p class="eyebrow">{E(rname)} · {E(gname)}</p>'
            f'<h1>{E(j["title"])}</h1><p class="sub">{E(j["company"])} · {E(j["location"])}</p>{closed}'
            f'<dl class="meta"><dt>Company</dt><dd>{E(j["company"])}</dd><dt>Location</dt><dd>{E(j["location"])}</dd>'
            f'<dt>Work type</dt><dd>{work}</dd><dt>Employment</dt><dd>{E(etype)}</dd>'
            f'<dt>Role type</dt><dd><a href="/role/{rid}/">{E(rname)}</a></dd><dt>Region</dt><dd><a href="/region/{gid}/">{E(gname)}</a></dd>'
            f'<dt>Posted</dt><dd><time datetime="{E(j.get("posted") or j["first_seen"])}">{E(j.get("posted") or j["first_seen"])}</time></dd><dt>Source</dt><dd>{E(j["source"])}</dd></dl>'
            f'<a class="btn apply" href="{E(j["url"])}" target="_blank" rel="nofollow noopener">Apply on {E(j["source"])} ↗</a>'
            + (f'<section class="desc"><h2>About this {E(j["title"])} role</h2>{dhtml}</section>'
               f'<a class="btn apply" href="{E(j["url"])}" target="_blank" rel="nofollow noopener">Apply on {E(j["source"])} ↗</a>' if dhtml else "")
            + f'<p class="note">You will apply on the original listing. TeeOrTee does not handle applications and is not affiliated with {E(j["company"])}.</p></article>'
            + tee_strip(tees_for(j), f"Funny tees for {rname} roles")
            + signup()
            + (f'<section><h2>Similar {E(rname)} jobs in {E(gname)}</h2><ol>{sim}</ol>'
               f'<p><a href="/role/{rid}/{gid}/">All {E(rname)} jobs in {E(gname)} →</a></p></section>' if sim else ""))
    snippet = re.sub(r"\s+", " ", d.replace("• ", ""))[:150].rsplit(" ", 1)[0] + "…" if d else ""
    title = f"{j['title']} – {j['company']} – {j['location']}"
    meta = (f"{j['company']} is hiring a {j['title']} in {j['location']}. {snippet}" if snippet else
            f"{j['title']} job at {j['company']} in {j['location']}. {rname} role in {gname}, posted {j.get('posted') or j['first_seen']}. Apply on the original listing.")
    schema = [crumbs_ld(trail + [(j["title"], f"/job/{j['id']}/")])]
    if indexable:
        schema.append(job_schema(j, dhtml))
    if len(title) > 70:
        title = f"{j['title']} – {j['company']}"
    if len(title) > 70:
        title = title[:68].rsplit(" ", 1)[0] + "…"
    page(f"/job/{j['id']}/", f"{title} | TeeOrTee Jobs", meta[:160], body, noindex=not indexable,
         schema=schema, lastmod=j.get("last_seen"), ogtype="article")


def nav():
    roles = "".join(f'<a href="/role/{r[0]}/">{E(r[1])}</a>' for r in ROLES)
    regs = "".join(f'<a href="/region/{r[0]}/">{E(r[1])}</a>' for r in REGIONS)
    return f'<nav class="chips"><b>Roles</b>{roles}</nav><nav class="chips"><b>Regions</b>{regs}</nav>'


def signup():
    return (f'<div class="signup"><div><strong>Get matching jobs by email, once a week</strong>'
            f'<p>Choose your role and region. Free, unsubscribe any time.</p></div>'
            f'<a class="btn" href="{E(SIGNUP)}">Sign up for job alerts</a></div>')


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


def page(path, title, desc, body, noindex=False, schema=(), lastmod=None, ogtype="website"):
    canon = SITE + path
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">'
    if not noindex:
        SITEMAP.append((path, lastmod or TODAY.isoformat()))
    verify = "".join(f'<meta name="{k}" content="{E(v)}">' for k, v in VERIFY.items() if v) if path == "/" else ""
    robots += verify + "".join(ld(o) for o in schema)
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{robots}
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/assets/og.png"><meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="TeeOrTee Jobs"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/pm.png">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header class="top"><a class="logo" href="/">TeeOrTee <span>Jobs</span></a><a class="shop" href="{SHOP}?{UTM}">Shop tees</a></header>
<main>{body}</main>
<footer><p>Listings are collected daily from public job boards and company career pages, and every job links to its original source. TeeOrTee is not affiliated with any employer or job board; always apply on the source site.</p>
<p><a href="{SHOP}?{UTM}">teeortee.com</a> · Funny t-shirts for project professionals</p></footer></body></html>'''
    full = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(doc)


ROLE_RANK = {r[0]: i for i, r in enumerate(ROLES)}


def pick(js, per, per_company=3):
    """Project roles first (product roles last), at most 3 jobs per company, then fill."""
    js = sorted(js, key=lambda j: ROLE_RANK.get(j["role"], 99))
    out, seen, rest = [], {}, []
    for j in js:
        c = j["company"].lower()
        if seen.get(c, 0) < per_company:
            out.append(j); seen[c] = seen.get(c, 0) + 1
        else:
            rest.append(j)
    return (out + rest)[:per]


def grouped(jobs, by, names, order, per, tee_for):
    parts, i = [], 0
    for key in order:
        js = pick([j for j in jobs if j[by] == key], per)
        if not js:
            continue
        parts.append(f'<section id="{key}"><h2>{E(names[key])} <small>{len(js)}</small></h2><ol>{"".join(job_li(j) for j in js)}</ol></section>')
        i += 1
        if i % 2 == 0:
            parts.append(tee_strip(tee_for(key)))
    return "".join(parts)


def main():
    if os.path.exists(OUT):
        for f in os.listdir(OUT):
            if f not in ("assets", "CNAME"):
                p = os.path.join(OUT, f)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    today = recent(1) or recent(3)
    week = recent(7)
    active = [j for j in recent(30) if j.get("last_seen", "") >= ACTIVE_CUT]
    regs = [r[0] for r in REGIONS]
    rls = [r[0] for r in ROLES]
    rot = list(TEES)
    body = (f'<p class="eyebrow">Updated {E(NICE)}</p><h1>Project jobs today</h1>'
            f'<p class="lede">{len(today)} new project roles across the USA, UK, Europe, Canada and Australia, for project managers, programme managers, PMO, planners, project controls, scrum masters and delivery leads.</p>'
            + nav() + signup()
            + grouped(today, "region", REGION_NAME, regs, 20, lambda k: rot[regs.index(k) * 2 % 9:][:3] or rot[:3])
            + tee_strip(["pm", "scope", "cr"]))
    home_ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "TeeOrTee Jobs", "url": SITE + "/",
                "publisher": {"@type": "Organization", "name": "TeeOrTee", "url": SHOP, "logo": SITE + "/assets/pm.png",
                              "sameAs": ["https://www.linkedin.com/company/146972843", "https://www.pinterest.com/teeorteeshop/"]}},
               {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/job/{j['id']}/"} for i, j in enumerate(today[:50])]}]
    page("/", f"Project Manager Jobs Today ({TODAY.strftime('%d %b %Y')}) – USA, UK, Europe, Canada | TeeOrTee Jobs",
         f"{len(today)} new project manager, programme manager, PMO, planner and scrum master jobs today across the USA, UK, Europe, Canada and Australia. Updated daily, links to original listings.", body, schema=home_ld)
    for rid, rname, _ in ROLES:
        js = [j for j in week if j["role"] == rid]
        body = (f'<p class="eyebrow">Last 7 days · updated {E(NICE)}</p><h1>{E(rname)} jobs</h1>'
                f'<p class="lede">{len(js)} new {E(rname)} roles this week across the USA, UK, Europe, Canada and Australia.</p>'
                + nav() + '<nav class="chips"><b>' + E(rname) + ' jobs in</b>' + "".join(f'<a href="/role/{rid}/{g}/">{E(n)}</a>' for g, n, _, _ in REGIONS) + '</nav>'
                + signup() + grouped(js, "region", REGION_NAME, regs, 40, lambda k, rid=rid: ROLE_TEES[rid])
                + tee_strip(ROLE_TEES[rid], f"Funny tees for {rname} roles"))
        page(f"/role/{rid}/", f"{rname} Jobs – USA, UK, Europe, Canada | TeeOrTee Jobs",
             f"Latest {rname} jobs posted this week, updated daily, with links to the original listings.", body,
             schema=[crumbs_ld([("Jobs today", "/"), (f"{rname} jobs", f"/role/{rid}/")])])
        # role x region landing pages, e.g. /role/project-manager/uk/
        for gid, gname, _, _ in REGIONS:
            rj = pick([j for j in active if j["role"] == rid and j["region"] == gid]
                      or [j for j in week if j["role"] == rid and j["region"] == gid], 60)
            if not rj:
                continue
            trail = [("Jobs today", "/"), (f"{rname} jobs", f"/role/{rid}/"), (f"{rname} jobs in {gname}", f"/role/{rid}/{gid}/")]
            others = "".join(f'<a href="/role/{rid}/{g}/">{E(n)}</a>' for g, n, _, _ in REGIONS if g != gid)
            b = (f'<nav class="crumbs" aria-label="Breadcrumb">' + " › ".join(f'<a href="{u}">{E(n)}</a>' for n, u in trail) + '</nav>'
                 f'<p class="eyebrow">Open roles · updated {E(NICE)}</p><h1>{E(rname)} jobs in {E(gname)}</h1>'
                 f'<p class="lede">{len(rj)} open {E(rname)} jobs in {E(gname)}, collected daily from company career pages and public job boards. Each job links to the original listing.</p>'
                 f'<nav class="chips"><b>Other regions</b>{others}</nav>' + signup()
                 + f'<section><ol>{"".join(job_li(j) for j in rj)}</ol></section>'
                 + tee_strip(ROLE_TEES[rid], f"Funny tees for {rname} roles"))
            page(f"/role/{rid}/{gid}/", f"{rname} Jobs in {gname} ({TODAY.strftime('%b %Y')}) | TeeOrTee Jobs",
                 f"{len(rj)} open {rname} jobs in {gname}, updated daily from company career pages and job boards. Apply on the original listing.",
                 b, schema=[crumbs_ld(trail)])
    for gid, gname, _, _ in REGIONS:
        js = [j for j in week if j["region"] == gid]
        body = (f'<p class="eyebrow">Last 7 days · updated {E(NICE)}</p><h1>Project jobs in {E(gname)}</h1>'
                f'<p class="lede">{len(js)} new project roles in {E(gname)} this week.</p>'
                + nav() + '<nav class="chips"><b>In ' + E(gname) + '</b>' + "".join(f'<a href="/role/{r}/{gid}/">{E(n)}</a>' for r, n, _ in ROLES) + '</nav>'
                + signup() + grouped(js, "role", ROLE_NAME, rls, 30, lambda k: ROLE_TEES[k]))
        page(f"/region/{gid}/", f"Project Manager Jobs in {gname} | TeeOrTee Jobs",
             f"New project manager, programme manager, PMO and scrum jobs in {gname} this week, updated daily.", body,
             schema=[crumbs_ld([("Jobs today", "/"), (f"Jobs in {gname}", f"/region/{gid}/")])])
    # one details page per open job (and per job listed this week), with Apply button, description and matching tees
    pool = {j["id"]: j for j in active + week}
    for j in pool.values():
        similar = [x for x in active if x["role"] == j["role"] and x["region"] == j["region"] and x["id"] != j["id"]][:6]
        job_page(j, similar)
    # weekly feed for the email digest
    json.dump(week, open(os.path.join(OUT, "week.json"), "w"), ensure_ascii=False)
    page("/404.html", "Job not found | TeeOrTee Jobs", "This job listing has closed or moved.",
         '<h1>This job has closed or moved</h1><p class="lede">Listings are removed once they close at the source. Browse open roles below.</p>'
         + nav() + signup() + tee_strip(["pm", "scope", "cr"]), noindex=True)
    os.replace(os.path.join(OUT, "404.html", "index.html"), os.path.join(OUT, "404.tmp"))
    os.rmdir(os.path.join(OUT, "404.html")); os.replace(os.path.join(OUT, "404.tmp"), os.path.join(OUT, "404.html"))
    open(os.path.join(OUT, f"{INDEXNOW_KEY}.txt"), "w").write(INDEXNOW_KEY)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{m}</lastmod></url>" for u, m in SITEMAP)
        + "</urlset>")
    json.dump([SITE + u for u, _ in SITEMAP], open(os.path.join(OUT, "urls.json"), "w"))
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print("built", len(today), "today,", len(week), "this week,", len(active), "open,", len(SITEMAP), "indexable pages")


if __name__ == "__main__":
    main()
