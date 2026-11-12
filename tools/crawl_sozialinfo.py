"""Crawlt Sozialinfo Wien (FSW) für alle Stichwörter aus categories.py.
Rohdaten -> cache/sozialinfo/*.html, Ergebnis -> cache/sozialinfo.json"""
import json, re, sys, time, html, urllib.parse, urllib.request, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from categories import BEREICHE, OGD_ONLY
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = ROOT / "cache" / "sozialinfo"; C.mkdir(parents=True, exist_ok=True)
B = "https://www.wien.gv.at/sozialinfo/content/de/10/"
UA = {"User-Agent": "Mozilla/5.0 (Sozialarbeitskarte; Lernprojekt)"}

def get(url, fn):
    p = C / fn
    if p.exists() and p.stat().st_size > 1000: return p.read_text("utf-8")
    for a in range(4):
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "replace")
            p.write_text(t, "utf-8"); time.sleep(0.3); return t
        except Exception as e:
            print("retry", url, e); time.sleep(2 * (a + 1))
    return ""

def txt(s):
    s = re.sub(r"<br\s*/?>", "\n", s); s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*", "\n", html.unescape(s))).strip()

ids = {}
for code, name, col, kws in BEREICHE:
    for k in kws:
        if k in OGD_ONLY: continue
        q = urllib.parse.quote_plus(k)
        t = get(B + f"SearchResults.do?keyword={q}", "s_" + re.sub(r"\W+", "_", k) + ".html")
        found = re.findall(r'href="InstitutionDetail\.do\?it_1=(\d+)"', t)
        print(f"{k}: {len(found)}")
        for i in found: ids.setdefault(i, set()).add(k)

out = []
for n, i in enumerate(sorted(ids)):
    t = get(B + f"InstitutionDetail.do?it_1={i}", f"d_{i}.html")
    m = re.search(r'<div class="org"[^>]*id="inst-%s">(.*?)<div class="inst-footer">' % i, t, re.S)
    if not m: print("parse fail", i); continue
    b = m.group(1)
    g = lambda r: (re.search(r, b, re.S) or [None, None])[1]
    adrs = re.findall(r'data-latitude="([\d.]+)" data-longitude="([\d.]+)"><span itemprop="postalCode">(\d*)</span>.*?<span itemprop="streetAddress">([^<]*)</span>', b, re.S)
    d = {
        "id": "si" + i, "name": txt(g(r'<h2 itemprop="name">(.*?)</h2>') or ""),
        "locs": [{"lat": float(a), "lon": float(o), "plz": p, "street": html.unescape(s)} for a, o, p, s in adrs],
        "phone": [txt(x) for x in re.findall(r'itemprop="telephone">(.*?)</span>', b)],
        "email": re.findall(r'itemprop="email" href="mailto:([^"]+)"', b),
        "web": [html.unescape(x) for x in re.findall(r'itemprop="url" href="([^"]+)"', b)],
        "desc": txt(g(r'itemprop="description">(.*?)</div>') or ""),
        "hours": txt(g(r'businesshours"><h4 >Geschäftszeiten</h4><div >(.*?)</div>') or ""),
        "zentrale": [{"id": "si" + a, "name": html.unescape(x)} for a, x in re.findall(r'<dt >Zentrale</dt><dd><a href="InstitutionDetail\.do\?it_1=(\d+)">([^<]+)', b)],
        "themen": [html.unescape(x) for x in re.findall(r'itemprop="itemListElement"><a [^>]*itemprop="name">([^<]+)', b)],
        "src": B + f"InstitutionDetail.do?it_1={i}",
        "updated": (re.search(r"zuletzt geändert am ([^<]+)", t) or [None, ""])[1].strip(),
    }
    out.append(d)
    if n % 100 == 0: print(n, "/", len(ids))
(ROOT / "cache" / "sozialinfo.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
print("institutions", len(out), "with coords", sum(1 for d in out if d["locs"]))
