"""Tell Bing/Yandex/Seznam (IndexNow) about new and updated pages after each deploy."""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from config import SITE, INDEXNOW_KEY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
urls = json.load(open(os.path.join(ROOT, "site", "urls.json")))[:10000]
body = {"host": SITE.split("//")[1], "key": INDEXNOW_KEY, "keyLocation": f"{SITE}/{INDEXNOW_KEY}.txt", "urlList": urls}
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow", r.status, len(urls), "urls")
except Exception as e:
    print("IndexNow failed (non-fatal):", e)
