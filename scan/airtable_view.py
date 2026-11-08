# Usage: python3 -I airtable_view.py SHARE_ID OUTJSON
# Reads a publicly shared Airtable view the same way the browser does (no login).
import sys, re, json, urllib.request, http.cookiejar
share, out = sys.argv[1], sys.argv[2]
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
req = urllib.request.Request("https://airtable.com/embed/" + share, headers={"User-Agent": UA})
html = op.open(req, timeout=30).read().decode("utf-8", "replace")
m = re.search(r'urlWithParams: "([^"]+)"', html)
url = "https://airtable.com" + m.group(1).encode().decode("unicode_escape")
hm = re.search(r'var headers = (\{.*?\});', html)
h = json.loads(hm.group(1))
h.pop("x-airtable-accept-msgpack", None)
h.pop("x-early-prefetch", None)
h["x-time-zone"] = "Asia/Jerusalem"
h["User-Agent"] = UA
title = re.search(r"<title>(.*?)</title>", html).group(1)
r = op.open(urllib.request.Request(url, headers=h), timeout=30).read()
data = json.loads(r)
open(out, "w").write(json.dumps(data))
print(title)
tbl = data["data"]["table"]
cols = {c["id"]: c["name"] for c in tbl["columns"]}
print("columns:", list(cols.values()))
rows = tbl.get("rows", [])
print("rows:", len(rows))
