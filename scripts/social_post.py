"""Daily LinkedIn job post per region group: post text + square image, published as an RSS feed for Zapier.

Usage: python scripts/social_post.py americas|europe
Writes site/social/<date>-<group>.png and .json, prunes old files, rebuilds site/social/<group>.xml.
"""
import json, os, sys, glob, datetime, html
from email.utils import format_datetime
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, TEES, SHOP, SITE, EXCLUDE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "social")
FONTS = os.path.join(os.path.dirname(__file__), "fonts")
DB = json.load(open(os.path.join(ROOT, "data", "jobs.json")))
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = NOW.date()
SIGNUP = os.environ.get("SIGNUP_URL", "")
GROUPS = {
    "americas": dict(name="USA & Canada", regions=["usa", "canada"], hub="/region/usa/",
                     tags="#ProjectManagement #ProjectManagerJobs #Hiring #PMO #ScrumMaster #USAJobs #CanadaJobs"),
    "europe": dict(name="UK, Europe & Australia", regions=["uk", "europe", "australia"], hub="/region/uk/",
                   tags="#ProjectManagement #ProjectManagerJobs #Hiring #PMO #ScrumMaster #UKJobs #EuropeJobs"),
}
NUMS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
RANK = {r[0]: i for i, r in enumerate(ROLES)}
NAVY, ORANGE, CREAM, GREY = (20, 33, 74), (232, 102, 44), (251, 248, 243), (107, 111, 128)


def pick_jobs(regions, n=8):
    for days in (1, 2, 3, 7):
        cut = (TODAY - datetime.timedelta(days=days)).isoformat()
        js = [j for j in DB.values() if j["region"] in regions and j.get("first_seen", "") >= cut
              and j.get("last_seen", "") >= cut and not any(x in " " + j["title"].lower() + " " for x in EXCLUDE)]
        if len(js) >= 5:
            break
    js.sort(key=lambda j: (RANK.get(j["role"], 99), j.get("posted", "")), reverse=False)
    out, seen, regs = [], {}, {}
    # spread across companies and regions: max 1 per company first pass, then fill
    for cap in (1, 2):
        for j in js:
            c = j["company"].lower()
            if j in out or seen.get(c, 0) >= cap:
                continue
            out.append(j); seen[c] = seen.get(c, 0) + 1
            if len(out) >= n:
                return out
    return out


def short_loc(j):
    loc = j["location"].split(";")[0].strip()
    return loc[:40]


def post_text(g, jobs, tee):
    d = TODAY.strftime("%d %b")
    lines = [f"🚀 Project jobs today: {g['name']} ({d})", "",
             "Fresh project manager, programme, PMO, scrum and planning roles from company career pages and job boards. Apply on the original listing:", ""]
    for i, j in enumerate(jobs):
        lines += [f"{NUMS[i]} {j['title']} at {j['company']} ({short_loc(j)})", f"👉 {j['url']}", ""]
    lines += [f"More jobs (updated daily) and free weekly alerts for your role: {SITE}{g['hub']}"]
    lines += ["", f"👕 Between interviews: {TEES[tee][0]} tee for project pros at {SHOP}",
              "", "Know someone looking? Share this post 🔁", "", g["tags"]]
    return "\n".join(lines)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, f"Inter-{name}.otf"), size)


def fit(draw, text, f, width):
    if draw.textlength(text, font=f) <= width:
        return text
    while text and draw.textlength(text + "…", font=f) > width:
        text = text[:-1]
    return text.rstrip() + "…"


def image(g, jobs, tee, path):
    W = 1200
    im = Image.new("RGB", (W, W), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 18], fill=ORANGE)
    d.text((70, 70), "TeeOrTee", font=font("Bold", 40), fill=ORANGE)
    d.text((70 + d.textlength("TeeOrTee ", font=font("Bold", 40)), 70), "Jobs", font=font("Bold", 40), fill=NAVY)
    d.text((70, 150), "PROJECT JOBS TODAY", font=font("Bold", 30), fill=ORANGE)
    d.text((70, 190), g["name"], font=font("Bold", 68), fill=NAVY)
    d.text((70, 280), TODAY.strftime("%A %d %B %Y"), font=font("Regular", 32), fill=GREY)
    y = 360
    for i, j in enumerate(jobs[:6]):
        d.ellipse([70, y + 6, 110, y + 46], fill=NAVY)
        n = str(i + 1)
        d.text((90 - d.textlength(n, font=font("Bold", 24)) / 2, y + 11), n, font=font("Bold", 24), fill="white")
        d.text((130, y), fit(d, j["title"], font("Bold", 34), 550), font=font("Bold", 34), fill=NAVY)
        d.text((130, y + 44), fit(d, f"{j['company']} · {short_loc(j)}", font("Regular", 26), 550), font=font("Regular", 26), fill=GREY)
        y += 100
    # tee on the right
    tp = os.path.join(ROOT, "site", "assets", f"{tee}.png")
    if os.path.exists(tp):
        t = Image.open(tp).convert("RGBA")
        t.thumbnail((420, 420))
        x0 = W - 490
        d.rounded_rectangle([x0, 360, W - 50, 880], radius=24, fill="white", outline=(230, 225, 216), width=3)
        im.paste(t, (x0 + (440 - t.width) // 2, 380), t)
        nm = fit(d, TEES[tee][0], font("Bold", 26), 400)
        d.text((x0 + (440 - d.textlength(nm, font=font("Bold", 26))) / 2, 810), nm, font=font("Bold", 26), fill=NAVY)
        d.text((W - 490, 900), "Between interviews:", font=font("Bold", 26), fill=NAVY)
        d.text((W - 490, 936), "funny tees for project pros", font=font("Regular", 26), fill=NAVY)
    d.rectangle([0, W - 140, W, W], fill=NAVY)
    d.text((70, W - 105), "Apply links in the post  ·  jobs.teeortee.com", font=font("Bold", 34), fill="white")
    d.text((70, W - 58), "Shop the tees at teeortee.com", font=font("Regular", 26), fill=(255, 200, 170))
    im.save(path, optimize=True)


def feed(key, g):
    items = []
    for f in sorted(glob.glob(os.path.join(OUT, f"*-{key}.json")), reverse=True)[:10]:
        p = json.load(open(f))
        items.append(
            f"<item><title>{html.escape(p['title'])}</title><link>{p['link']}</link><guid isPermaLink=\"false\">{p['id']}</guid>"
            f"<pubDate>{p['pubDate']}</pubDate><description>{html.escape(p['text'])}</description>"
            f"<enclosure url=\"{p['image']}\" type=\"image/png\" length=\"{p['bytes']}\"/></item>")
    open(os.path.join(OUT, f"{key}.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>TeeOrTee Jobs LinkedIn – {html.escape(g['name'])}</title><link>{SITE}</link>"
        f"<description>Daily project jobs post for {html.escape(g['name'])}</description>{''.join(items)}</channel></rss>")


def pinterest_feed():
    """One feed with both regions for Pinterest auto-publish (title <= 100, description <= 500 chars)."""
    items = []
    for f in sorted(glob.glob(os.path.join(OUT, "20*.json")), reverse=True)[:20]:
        p = json.load(open(f))
        g = GROUPS[p["id"].split("-", 3)[3]]
        jobs = p.get("jobs") or []
        sample = "; ".join(jobs[:3])
        desc = (f"{p.get('count', len(jobs))} new project manager, programme, PMO and scrum master jobs in {g['name']} today"
                + (f", including {sample}" if sample else "") + ". See all jobs and apply on the original listings at jobs.teeortee.com. "
                "Funny t-shirts for project professionals at teeortee.com. #projectmanagement #jobs #projectmanager")[:500]
        link = f"{p['link']}?utm_source=pinterest&utm_medium=social&utm_campaign=daily-jobs"
        items.append(
            f"<item><title>{html.escape(p['title'][:100])}</title><link>{html.escape(link)}</link><guid isPermaLink=\"false\">pin-{p['id']}</guid>"
            f"<pubDate>{p['pubDate']}</pubDate><description>{html.escape(desc)}</description>"
            f"<enclosure url=\"{p['image']}\" type=\"image/png\" length=\"{p['bytes']}\"/></item>")
    open(os.path.join(OUT, "pinterest.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>TeeOrTee Jobs – daily project jobs</title><link>{SITE}</link>"
        f"<description>Daily project manager jobs for USA, UK, Europe, Canada and Australia</description>{''.join(items)}</channel></rss>")


def prune(days=14):
    cut = (TODAY - datetime.timedelta(days=days)).isoformat()
    for f in glob.glob(os.path.join(OUT, "20*")):
        if os.path.basename(f)[:10] < cut:
            os.remove(f)


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else ("europe" if NOW.hour < 11 else "americas")
    g = GROUPS[key]
    os.makedirs(OUT, exist_ok=True)
    jobs = pick_jobs(g["regions"])
    if len(jobs) < 3:
        print("not enough jobs, skipping", key); return
    tees = list(TEES)
    tee = tees[(TODAY.toordinal() * 2 + (key == "europe")) % len(tees)]
    text = post_text(g, jobs, tee)
    while len(text) > 2900 and len(jobs) > 3:
        jobs = jobs[:-1]; text = post_text(g, jobs, tee)
    stem = f"{TODAY.isoformat()}-{key}"
    png = os.path.join(OUT, stem + ".png")
    image(g, jobs, tee, png)
    json.dump(dict(id=stem, title=f"Project jobs today: {g['name']} ({TODAY.strftime('%d %b')})", text=text,
                   link=SITE + g["hub"], image=f"{SITE}/social/{stem}.png", bytes=os.path.getsize(png),
                   pubDate=format_datetime(NOW), tee=tee, count=len(jobs),
                   jobs=[f"{j['title']} at {j['company']}" for j in jobs[:3]], tee_url=f"{SHOP}/products/{TEES[tee][1]}?utm_source=linkedin&utm_medium=social&utm_campaign=daily-jobs"),
              open(os.path.join(OUT, stem + ".json"), "w"), ensure_ascii=False, indent=1)
    prune()
    feed(key, g)
    pinterest_feed()
    print("post", stem, len(jobs), "jobs,", len(text), "chars")


if __name__ == "__main__":
    main()
