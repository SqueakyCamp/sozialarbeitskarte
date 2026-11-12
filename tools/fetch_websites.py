"""Holt die Websites der Einrichtungen und extrahiert Beschreibung (meta/og), erste Absätze,
YouTube/Vimeo-Videos. Rohseiten -> cache/web/, Ergebnis -> cache/web.json"""
import json, re, html, hashlib, pathlib, urllib.request, concurrent.futures as cf
R = pathlib.Path(__file__).resolve().parent.parent
C = R / "cache" / "web"; C.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36", "Accept-Language": "de-AT,de;q=0.9"}


def fetch(u):
    p = C / (hashlib.sha1(u.encode()).hexdigest() + ".html")
    if p.exists(): return p.read_text("utf-8", "replace"), None
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25)
        if "html" not in (r.headers.get("content-type") or "html"): return "", r.geturl()
        t = r.read(3_000_000).decode(r.headers.get_content_charset() or "utf-8", "replace")
        p.write_text(t, "utf-8"); return t, r.geturl()
    except Exception as e:
        return "", "ERR " + str(e)[:80]


def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
BAD = re.compile(r"cookie|javascript|datenschutz|newsletter|©|copyright|captcha|browser|alle rechte|spenden sie jetzt|zum inhalt springen", re.I)


def parse(u, t):
    def meta(n):
        ms = re.findall(r'<meta[^>]+(?:name|property)=["\']%s["\'][^>]*content=["\']([^"\']*)' % n, t, re.I)
        ms += re.findall(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:name|property)=["\']%s["\']' % n, t, re.I)
        return next((clean(m) for m in ms if len(clean(m)) > 30), "")
    body = re.sub(r"(?is)<(script|style|nav|header|footer|form|noscript|svg)\b.*?</\1>", " ", t)
    m = re.search(r"(?is)<main\b.*?</main>", body) or re.search(r'(?is)<article\b.*?</article>', body)
    if m: body = m.group(0)
    paras = []
    for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", body):
        s = clean(p)
        if 80 <= len(s) <= 900 and not BAD.search(s) and s not in paras: paras.append(s)
        if len(paras) >= 3: break
    vids = set()
    for v in re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([\w-]{11})', t): vids.add("https://www.youtube.com/watch?v=" + v)
    for a, b in re.findall(r'player\.vimeo\.com/video/(\d+)|vimeo\.com/(\d{6,})', t): vids.add("https://vimeo.com/" + (a or b))
    title = clean((re.search(r"(?is)<title[^>]*>(.*?)</title>", t) or [None, ""])[1])[:160]
    return {"title": title, "meta": meta("description") or meta("og:description"), "paras": paras, "videos": sorted(vids)[:4]}


def job(u):
    t, final = fetch(u)
    r = {"url": u, "final": final}
    if t: r.update(parse(u, t))
    return r


if __name__ == "__main__":
    d = json.load(open(R / "cache" / "sozialinfo.json", encoding="utf-8"))
    urls = sorted({u for x in d for u in x["web"]})
    with cf.ThreadPoolExecutor(12) as ex: res = list(ex.map(job, urls))
    out = {r["url"]: r for r in res}
    (R / "cache" / "web.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    ok = [r for r in res if r.get("meta") or r.get("paras")]
    print(len(res), "ok", len(ok), "videos", sum(len(r.get("videos", [])) for r in res))
