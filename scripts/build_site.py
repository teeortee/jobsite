"""Build the static jobs.teeortee.com site from data/jobs.json into site/."""
import json, os, sys, html, datetime, shutil
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, REGIONS, TEES, ROLE_TEES, SHOP, SITE

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


def recent(days):
    cut = (TODAY - datetime.timedelta(days=days)).isoformat()
    return sorted([j for j in DB.values() if j.get("first_seen", "") >= cut],
                  key=lambda j: (j.get("first_seen", ""), j.get("posted", "")), reverse=True)


def tee_strip(keys, heading="Between interviews: funny tees for project people"):
    cards = "".join(
        f'<a class="card" href="{SHOP}/products/{TEES[k][1]}?{UTM}"><img src="/assets/{k}.png" alt="{E(TEES[k][0])} t-shirt" loading="lazy"><span>{E(TEES[k][0])}</span></a>'
        for k in keys)
    return f'<aside class="strip"><p class="strip-h">{E(heading)}</p><div class="cards">{cards}</div><a class="btn" href="{SHOP}/collections/all?{UTM}">Shop all tees at teeortee.com</a></aside>'


def job_li(j):
    return (f'<li><a href="{E(j["url"])}" target="_blank" rel="nofollow noopener"><strong>{E(j["title"])}</strong></a>'
            f'<span>{E(j["company"])} · {E(j["location"])}</span>'
            f'<em>{E(ROLE_NAME[j["role"]])} · Source: {E(j["source"])} · Added {E(j["first_seen"])}</em></li>')


def nav():
    roles = "".join(f'<a href="/role/{r[0]}/">{E(r[1])}</a>' for r in ROLES)
    regs = "".join(f'<a href="/region/{r[0]}/">{E(r[1])}</a>' for r in REGIONS)
    return f'<nav class="chips"><b>Roles</b>{roles}</nav><nav class="chips"><b>Regions</b>{regs}</nav>'


def signup():
    return (f'<div class="signup"><div><strong>Get matching jobs by email, once a week</strong>'
            f'<p>Choose your role and region. Free, unsubscribe any time.</p></div>'
            f'<a class="btn" href="{E(SIGNUP)}">Sign up for job alerts</a></div>')


def page(path, title, desc, body):
    canon = SITE + path
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{SITE}/assets/og.png"><link rel="icon" href="/assets/pm.png">
<link rel="stylesheet" href="/assets/style.css"></head><body>
<header class="top"><a class="logo" href="/">TeeOrTee <span>Jobs</span></a><a class="shop" href="{SHOP}?{UTM}">Shop tees</a></header>
<main>{body}</main>
<footer><p>Listings are collected daily from public job boards and company career pages, and every job links to its original source. TeeOrTee is not affiliated with any employer or job board; always apply on the source site.</p>
<p><a href="{SHOP}?{UTM}">teeortee.com</a> · Funny t-shirts for project professionals</p></footer></body></html>'''
    full = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(doc)


def grouped(jobs, by, names, order, per, tee_for):
    parts, i = [], 0
    for key in order:
        js = [j for j in jobs if j[by] == key][:per]
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
    regs = [r[0] for r in REGIONS]
    rls = [r[0] for r in ROLES]
    rot = list(TEES)
    body = (f'<p class="eyebrow">Updated {E(NICE)}</p><h1>Project jobs today</h1>'
            f'<p class="lede">{len(today)} new project roles across the USA, UK, Europe, Canada and Australia, for project managers, programme managers, PMO, planners, project controls, scrum masters and delivery leads.</p>'
            + nav() + signup()
            + grouped(today, "region", REGION_NAME, regs, 20, lambda k: rot[regs.index(k) * 2 % 9:][:3] or rot[:3])
            + tee_strip(["pm", "scope", "cr"]))
    page("/", f"Project Manager Jobs Today ({TODAY.strftime('%d %b %Y')}) – USA, UK, Europe, Canada | TeeOrTee Jobs",
         f"{len(today)} new project manager, programme manager, PMO, planner and scrum master jobs today across the USA, UK, Europe, Canada and Australia. Updated daily, links to original listings.", body)
    for rid, rname, _ in ROLES:
        js = [j for j in week if j["role"] == rid]
        body = (f'<p class="eyebrow">Last 7 days · updated {E(NICE)}</p><h1>{E(rname)} jobs</h1>'
                f'<p class="lede">{len(js)} new {E(rname)} roles this week across the USA, UK, Europe, Canada and Australia.</p>'
                + nav() + signup() + grouped(js, "region", REGION_NAME, regs, 40, lambda k, rid=rid: ROLE_TEES[rid])
                + tee_strip(ROLE_TEES[rid], f"Made for {rname}s"))
        page(f"/role/{rid}/", f"{rname} Jobs – USA, UK, Europe, Canada | TeeOrTee Jobs",
             f"Latest {rname} jobs posted this week, updated daily, with links to the original listings.", body)
    for gid, gname, _, _ in REGIONS:
        js = [j for j in week if j["region"] == gid]
        body = (f'<p class="eyebrow">Last 7 days · updated {E(NICE)}</p><h1>Project jobs in {E(gname)}</h1>'
                f'<p class="lede">{len(js)} new project roles in {E(gname)} this week.</p>'
                + nav() + signup() + grouped(js, "role", ROLE_NAME, rls, 30, lambda k: ROLE_TEES[k]))
        page(f"/region/{gid}/", f"Project Manager Jobs in {gname} | TeeOrTee Jobs",
             f"New project manager, programme manager, PMO and scrum jobs in {gname} this week, updated daily.", body)
    # weekly feed for the email digest
    json.dump(week, open(os.path.join(OUT, "week.json"), "w"), ensure_ascii=False)
    urls = ["/"] + [f"/role/{r[0]}/" for r in ROLES] + [f"/region/{r[0]}/" for r in REGIONS]
    open(os.path.join(OUT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>daily</changefreq></url>" for u in urls)
        + "</urlset>")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print("built", len(today), "today,", len(week), "this week")


if __name__ == "__main__":
    main()
