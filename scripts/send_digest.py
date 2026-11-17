"""Weekly job-alert emails via Brevo: one campaign per role list, with matching jobs and matching tees.

Env:
  BREVO_API_KEY  Brevo API key (GitHub secret)
  BREVO_LISTS    JSON map of role id -> Brevo list id, e.g. {"project-manager": 3, "pmo": 5}
  TEST_EMAIL     if set, only send a test of every campaign to this address
"""
import json, os, sys, html, datetime, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, REGIONS, TEES, ROLE_TEES, SHOP, SITE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = json.load(open(os.path.join(ROOT, "data", "jobs.json")))
KEY = os.environ["BREVO_API_KEY"]
LISTS = json.loads(os.environ.get("BREVO_LISTS") or "{}")
TEST = (os.environ.get("TEST_EMAIL") or "").strip()
SENDER = {"name": "TeeOrTee Jobs", "email": "social@teeortee.com"}
E = html.escape
TODAY = datetime.date.today()
CUT = (TODAY - datetime.timedelta(days=7)).isoformat()
UTM = "utm_source=brevo&utm_medium=email&utm_campaign=weekly-jobs"


def api(method, path, body=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"api-key": KEY, "content-type": "application/json", "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        t = r.read().decode()
        return json.loads(t) if t else {}


def email_html(rid, rname, jobs):
    blocks = []
    for gid, gname, _, _ in REGIONS:
        js = [j for j in jobs if j["region"] == gid][:6]
        if not js:
            continue
        rows = "".join(
            f'<tr><td style="padding:10px 0;border-bottom:1px solid #e6e1d8"><a href="{E(j["url"])}" style="color:#14214a;font-weight:700;font-size:16px;text-decoration:none">{E(j["title"])}</a><br>'
            f'<span style="font-size:14px;color:#14214a">{E(j["company"])} · {E(j["location"])}</span><br>'
            f'<span style="font-size:12px;color:#6b6f80">Source: {E(j["source"])}</span></td></tr>' for j in js)
        blocks.append(f'<h2 style="font-size:20px;color:#14214a;border-bottom:3px solid #e8662c;padding-bottom:4px;margin:24px 0 4px">{E(gname)}</h2><table width="100%" cellpadding="0" cellspacing="0">{rows}</table>')
    tees = "".join(
        f'<td width="33%" style="padding:4px;text-align:center"><a href="{SHOP}/products/{TEES[k][1]}?{UTM}" style="text-decoration:none;color:#14214a">'
        f'<img src="{SITE}/assets/{k}.png" width="160" style="width:100%;max-width:160px;border-radius:8px" alt="{E(TEES[k][0])}"><br>'
        f'<span style="font-size:13px;font-weight:700">{E(TEES[k][0])}</span></a></td>' for k in ROLE_TEES[rid])
    return f'''<div style="background:#fbf8f3;padding:20px 0"><table width="100%" style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;font-family:Arial,sans-serif;color:#14214a" cellpadding="20"><tr><td>
<p style="color:#e8662c;font-weight:700;font-size:20px;margin:0">TeeOrTee <span style="color:#14214a">Jobs</span></p>
<h1 style="font-size:26px;margin:12px 0 6px">{len(jobs)} new {E(rname)} jobs this week</h1>
<p style="font-size:15px;margin:0">Collected from public job boards and company career pages. Each link takes you to the original listing.</p>
{"".join(blocks)}
<p style="margin:20px 0"><a href="{SITE}/role/{rid}/?{UTM}" style="background:#14214a;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:700">See all {E(rname)} jobs</a></p>
<div style="background:#14214a;border-radius:12px;padding:16px;text-align:center;color:#fff"><p style="font-weight:700;font-size:17px;margin:0 0 10px">Made for {E(rname)}s</p>
<table width="100%"><tr>{tees}</tr></table>
<p style="margin:12px 0 0"><a href="{SHOP}/collections/all?{UTM}" style="background:#e8662c;color:#fff;padding:11px 22px;border-radius:999px;text-decoration:none;font-weight:700">Shop teeortee.com</a></p></div>
<p style="font-size:12px;color:#6b6f80;margin-top:20px">You get this because you signed up for {E(rname)} job alerts at jobs.teeortee.com. TeeOrTee is not affiliated with the employers or job boards listed; always apply on the source site.<br><a href="{{{{ unsubscribe }}}}" style="color:#6b6f80">Unsubscribe</a></p>
</td></tr></table></div>'''


def main():
    week = [j for j in DB.values() if j.get("first_seen", "") >= CUT]
    week.sort(key=lambda j: j.get("first_seen", ""), reverse=True)
    for rid, rname, _ in ROLES:
        lid = LISTS.get(rid)
        jobs = [j for j in week if j["role"] == rid]
        if not lid or len(jobs) < 3:
            print("skip", rid, "list", lid, "jobs", len(jobs))
            continue
        c = api("POST", "/emailCampaigns", {
            "name": f"Weekly {rname} jobs {TODAY}", "subject": f"{len(jobs)} new {rname} jobs this week",
            "previewText": "Fresh roles across the USA, UK, Europe, Canada and Australia",
            "sender": SENDER, "htmlContent": email_html(rid, rname, jobs),
            "recipients": {"listIds": [int(lid)]}, "inlineImageActivation": False})
        if TEST:
            api("POST", f"/emailCampaigns/{c['id']}/sendTest", {"emailTo": [TEST]})
            print("test sent", rid, c["id"])
        else:
            api("POST", f"/emailCampaigns/{c['id']}/sendNow")
            print("sent", rid, c["id"], len(jobs), "jobs")


if __name__ == "__main__":
    main()
