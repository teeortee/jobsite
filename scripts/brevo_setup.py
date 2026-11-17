"""One-off Brevo setup: folder, one list per role, and a REGION contact attribute. Safe to re-run."""
import json, os, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
from config import ROLES, REGIONS

KEY = os.environ["BREVO_API_KEY"]
FOLDER = "TeeOrTee Jobs"


def api(method, path, body=None):
    req = urllib.request.Request("https://api.brevo.com/v3" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"api-key": KEY, "content-type": "application/json", "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            t = r.read().decode()
            return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        print(method, path, e.code, e.read().decode()[:300])
        return None


def main():
    folders = (api("GET", "/contacts/folders?limit=50") or {}).get("folders", [])
    fid = next((f["id"] for f in folders if f["name"] == FOLDER), None)
    if not fid:
        fid = api("POST", "/contacts/folders", {"name": FOLDER})["id"]
    print("folder", fid)
    lists = (api("GET", "/contacts/lists?limit=50") or {}).get("lists", [])
    have = {l["name"]: l["id"] for l in lists}
    for rid, rname, _ in ROLES:
        name = f"Jobs - {rname}"
        if name not in have:
            have[name] = api("POST", "/contacts/lists", {"name": name, "folderId": fid})["id"]
        print("list", name, have[name])
    enum = [{"value": i + 1, "label": r[1]} for i, r in enumerate(REGIONS)]
    api("POST", "/contacts/attributes/category/REGION", {"type": "category", "enumeration": enum})
    print("attribute REGION ok")


if __name__ == "__main__":
    main()
