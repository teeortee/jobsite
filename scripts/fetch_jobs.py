"""Collect project-role jobs from public sources into data/jobs.json.

Sources (all public, each job links back to its original listing):
  - Adzuna API (aggregates thousands of job boards; needs free ADZUNA_APP_ID / ADZUNA_APP_KEY)
  - Company career boards on Greenhouse, Lever and Ashby (public JSON feeds)
  - Remotive and Arbeitnow (public remote/EU job APIs)
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse, hashlib, html
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, EXCLUDE, REGIONS, GREENHOUSE, LEVER, ASHBY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "jobs.json")
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "TeeOrTeeJobsBot/1.0 (+https://jobs.teeortee.com)"}


def get(url, params=None, timeout=25):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        print("  skip", url[:90], type(e).__name__, file=sys.stderr)
        return None


def role_of(title):
    t = " " + title.lower() + " "
    if any(x in t for x in EXCLUDE):
        return None
    for rid, _, kws in ROLES:
        if any(k in t for k in kws):
            return rid
    return None


def region_of(loc, country=None):
    if country:
        for rid, _, codes, _ in REGIONS:
            if country.lower() in codes:
                return rid
    l = " " + (loc or "").lower() + " "
    for rid, _, _, kws in REGIONS:
        if any(k in l for k in kws):
            return rid
    return None


def clean(s, n=140):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()[:n]


def text_of(h, n=6000):
    """Job description HTML -> plain text with line breaks; bullets as '• '."""
    if not h:
        return ""
    h = html.unescape(h) if "&lt;" in h else h
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<li[^>]*>", "\n• ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|div|li|ul|ol|h[1-6])>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", " ", h))
    lines = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in h.split("\n")]
    out = []
    for l in lines:
        if l and l != "•" and (not out or out[-1] != l):
            out.append(l)
    t = "\n".join(out)
    return t[:n].rsplit("\n", 1)[0] if len(t) > n else t


EMP = {"full": "FULL_TIME", "part": "PART_TIME", "contract": "CONTRACTOR", "temp": "TEMPORARY", "intern": "INTERN", "freelance": "CONTRACTOR"}


def emp_type(s):
    s = (s or "").lower()
    return next((v for k, v in EMP.items() if k in s), "")


def add(out, title, company, location, url, source, country=None, posted=None, desc="", remote=None, etype=""):
    rid = role_of(title)
    reg = region_of(location, country)
    if not rid or not reg or not url:
        return
    key = hashlib.sha1((clean(title).lower() + "|" + clean(company).lower() + "|" + reg).encode()).hexdigest()[:16]
    if remote is None:
        remote = "remote" in (location or "").lower() or "anywhere" in (location or "").lower()
    out[key] = dict(id=key, title=clean(title, 120), company=clean(company, 80), location=clean(location, 80),
                    url=url, source=source, role=rid, region=reg, posted=(posted or TODAY)[:10],
                    desc=text_of(desc), remote=bool(remote), etype=emp_type(etype))


def adzuna(out):
    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        print("Adzuna: no API key, skipping", file=sys.stderr)
        return
    queries = ["project manager", "programme manager", "program manager", "PMO", "project controls",
               "planner scheduler", "scrum master", "delivery manager", "project coordinator"]
    for _, _, codes, _ in REGIONS:
        for cc in codes:
            for q in queries:
                d = get(f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1",
                        dict(app_id=app_id, app_key=app_key, what=q, max_days_old=2, results_per_page=50,
                             sort_by="date", content_type="application/json"))
                for j in (d or {}).get("results", []):
                    add(out, j.get("title"), (j.get("company") or {}).get("display_name", ""),
                        (j.get("location") or {}).get("display_name", ""), j.get("redirect_url"),
                        "Adzuna", cc, j.get("created"), desc=j.get("description", ""), etype=j.get("contract_time", ""))
                time.sleep(0.4)


def greenhouse(out):
    for b in GREENHOUSE:
        d = get(f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs", dict(content="true"))
        for j in (d or {}).get("jobs", []):
            add(out, j.get("title"), b.title(), (j.get("location") or {}).get("name", ""),
                j.get("absolute_url"), f"{b.title()} careers", posted=j.get("updated_at"), desc=j.get("content", ""))


def lever(out):
    for b in LEVER:
        d = get(f"https://api.lever.co/v0/postings/{b}", dict(mode="json"))
        for j in d or []:
            ts = j.get("createdAt")
            posted = datetime.date.fromtimestamp(ts / 1000).isoformat() if ts else None
            cat = j.get("categories") or {}
            desc = (j.get("description") or "") + "".join(
                f"<h3>{l.get('text', '')}</h3><ul>{l.get('content', '')}</ul>" for l in j.get("lists") or []) + (j.get("additional") or "")
            add(out, j.get("text"), b.title(), cat.get("location", ""), j.get("hostedUrl"), f"{b.title()} careers",
                posted=posted, desc=desc, remote=(j.get("workplaceType") == "remote") or None, etype=cat.get("commitment", ""))


def ashby(out):
    for b in ASHBY:
        d = get(f"https://api.ashbyhq.com/posting-api/job-board/{b}", dict(includeCompensation="false"))
        for j in (d or {}).get("jobs", []):
            add(out, j.get("title"), b.title(), j.get("location", ""), j.get("jobUrl"),
                f"{b.title()} careers", posted=j.get("publishedAt"), desc=j.get("descriptionHtml") or j.get("descriptionPlain", ""),
                remote=j.get("isRemote") or None, etype=j.get("employmentType", ""))


def remotive(out):
    d = get("https://remotive.com/api/remote-jobs", dict(category="project-management"))
    for j in (d or {}).get("jobs", []):
        add(out, j.get("title"), j.get("company_name"), j.get("candidate_required_location", ""),
            j.get("url"), "Remotive", posted=j.get("publication_date"), desc=j.get("description", ""),
            remote=True, etype=j.get("job_type", ""))


def arbeitnow(out):
    for page in (1, 2, 3):
        d = get("https://www.arbeitnow.com/api/job-board-api", dict(page=page))
        for j in (d or {}).get("data", []):
            ts = j.get("created_at")
            posted = datetime.date.fromtimestamp(ts).isoformat() if ts else None
            add(out, j.get("title"), j.get("company_name"), j.get("location", ""), j.get("url"),
                "Arbeitnow", posted=posted, desc=j.get("description", ""), remote=j.get("remote") or None,
                etype=" ".join(j.get("job_types") or []))


def main():
    db = json.load(open(DB)) if os.path.exists(DB) else {}
    found = {}
    for fn in (adzuna, greenhouse, lever, ashby, remotive, arbeitnow):
        n = len(found)
        fn(found)
        print(f"{fn.__name__}: +{len(found) - n}")
    new = 0
    for k, j in found.items():
        if k in db:
            db[k]["last_seen"] = TODAY
            for f in ("desc", "remote", "etype", "url"):  # fill in details for older records
                if j.get(f) and not db[k].get(f):
                    db[k][f] = j[f]
        else:
            j["first_seen"] = TODAY
            j["last_seen"] = TODAY
            db[k] = j
            new += 1
    # keep 30 days of history
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    db = {k: v for k, v in db.items() if v.get("last_seen", TODAY) >= cutoff}
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    json.dump(db, open(DB, "w"), indent=0, ensure_ascii=False)
    print(f"total {len(db)}, new today {new}")


if __name__ == "__main__":
    main()
