"""Führt Sozialinfo-Wien-Daten, OGD-Layer, Website-Auszüge und kuratierte Infos zusammen.
-> site/data/einrichtungen.json, site/data/meta.json"""
import json, re, sys, pathlib, math, urllib.request, urllib.parse, time, unicodedata
R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from categories import BEREICHE, OGD_ONLY
from curated import TRAEGER, BEREICH_INFO, GENERAL_LINKS

si = json.load(open(R / "cache/sozialinfo.json", encoding="utf-8"))
web = json.load(open(R / "cache/web.json", encoding="utf-8"))
ogd = lambda n: json.load(open(R / f"cache/ogd/{n}.json", encoding="utf-8"))["features"]

KW2B = {}
for code, name, col, kws in BEREICHE:
    for k in kws: KW2B.setdefault(k, []).append(code)

# ---------- Video-Titel (YouTube/Vimeo oEmbed, gecacht) ----------
VC = R / "cache/video_titles.json"
vt = json.load(open(VC)) if VC.exists() else {}
def video_title(u):
    if u in vt: return vt[u]
    api = ("https://www.youtube.com/oembed?format=json&url=" if "youtube" in u else "https://vimeo.com/api/oembed.json?url=") + urllib.parse.quote(u, safe="")
    try:
        j = json.load(urllib.request.urlopen(urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"}), timeout=15))
        vt[u] = {"t": j.get("title", ""), "a": j.get("author_name", "")}
    except Exception:
        vt[u] = None
    time.sleep(0.1)
    return vt[u]

# ---------- Träger-Zuordnung ----------
def norm(s): return unicodedata.normalize("NFC", s.lower())
def traeger_for(*names):
    for n in names:
        n = norm(n or "")
        for t in TRAEGER:
            for m in t["match"]:
                if (m.startswith("re:") and re.search(m[3:], n)) or (not m.startswith("re:") and m in n):
                    return t["key"]
    return None

JUNK = re.compile(r"haftung|impressum|cookies?|javascript|404|nicht gefunden|seite wurde nicht|access denied|forbidden|bitte aktivieren|wartungsarbeiten|anmelden|login", re.I)
def excerpt(urls):
    for u in urls:
        r = web.get(u) or {}
        parts = []
        if r.get("meta") and not JUNK.search(r["meta"]): parts.append(r["meta"])
        for p in r.get("paras", []):
            if JUNK.search(p) or any(p[:60] in x for x in parts): continue
            parts.append(p)
            if sum(map(len, parts)) > 700: break
        if parts:
            txt = " ".join(parts)
            if len(txt) > 1100: txt = txt[:1100].rsplit(" ", 1)[0] + " …"
            return {"text": txt, "url": u, "title": r.get("title", "")}
    return None

def funding(desc):
    m = re.findall(r"((?:gefördert|finanziert|unterstützt) (?:von|vom|durch|aus)[^.\n]{3,160})", desc, re.I)
    return "; ".join(dict.fromkeys(x.strip(" ,;") for x in m)) or None

FUND_DEFAULT = {  # Bereichstypische Finanzierung, nur als Hinweis gekennzeichnet
    "wlh": "Angebote der Wiener Wohnungslosenhilfe werden in der Regel vom Fonds Soziales Wien (FSW) finanziert.",
    "oja": "Offene Jugendarbeit in Wien wird von der Stadt Wien (MA 13) und den Bezirken gefördert.",
    "sucht": "Suchthilfeangebote in Wien werden meist von der Sucht- und Drogenkoordination Wien gefördert.",
    "beh": "Leistungen für Menschen mit Behinderung werden in Wien meist vom FSW gefördert.",
}

items, seen = [], []
# ---------- Sozialinfo ----------
for d in si:
    themen = [t for t in d["themen"] if t in KW2B]
    if not themen: continue
    bereiche = list(dict.fromkeys(b for t in themen for b in KW2B[t]))
    zname = d["zentrale"][0]["name"] if d["zentrale"] else ""
    name = d["name"]
    tk = traeger_for(zname, name)
    vids = []
    for u in d["web"]:
        for v in (web.get(u) or {}).get("videos", []):
            ti = video_title(v)
            if ti and ti["t"]: vids.append({"t": ti["t"], "a": ti["a"], "u": v})
    ex = excerpt(d["web"])
    fund = funding(d["desc"])
    base = {
        "name": name, "bereiche": bereiche, "themen": themen, "traeger": tk, "zentrale": zname or None,
        "desc": d["desc"] or None, "hours": d["hours"] or None, "phone": d["phone"][:2], "email": d["email"][:1],
        "web": d["web"][:2], "web_excerpt": ex, "videos": vids[:3], "funding": fund,
        "funding_hint": None if fund else next((FUND_DEFAULT[b] for b in bereiche if b in FUND_DEFAULT), None),
        "src": {"name": "Sozialinfo Wien (FSW)", "url": d["src"], "updated": d["updated"]},
    }
    if d["locs"]:
        for i, l in enumerate(d["locs"]):
            it = dict(base, id=d["id"] + (f"-{i}" if i else ""), lat=l["lat"], lon=l["lon"], adr=f"{l['plz']} Wien, {l['street']}".strip(), bez=int(l["plz"][1:3]) if re.fullmatch(r"1\d\d0", l["plz"] or "") else None)
            items.append(it)
    else:
        items.append(dict(base, id=d["id"], lat=None, lon=None, adr=None, bez=None))

def near(lat, lon, name):
    for it in items:
        if it["lat"] and abs(it["lat"] - lat) < 0.0004 and abs(it["lon"] - lon) < 0.0006:
            a, b = set(re.findall(r"\w{4,}", norm(it["name"]))), set(re.findall(r"\w{4,}", norm(name)))
            if a & b: return it
    return None

# ---------- OGD: Jugendangebote ----------
JMAP = {"Indoor": "Jugendzentrum", "Parkbetreuung": "Parkbetreuung", "Fair-Play-Team": "Fair-Play-Team", "Mobil": "Mobile Jugendarbeit", "Wienweit": "Jugendzentrum"}
for f in ogd("JGDANGEBOTOGD"):
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
    th = JMAP.get(p["ANGEBOT_LABEL_TXT"], "Jugendzentrum")
    ex = near(lat, lon, p["BEZEICHNUNG"])
    if ex:
        if "oja" not in ex["bereiche"]: ex["bereiche"].append("oja")
        if th not in ex["themen"]: ex["themen"].append(th)
        continue
    urls = [u for u in [p.get("WEBLINK1")] if u]
    items.append({
        "id": f"jg{p['ANGEBOT_ID']}", "name": p["BEZEICHNUNG"] + (f" – {p['VEREIN']}" if p.get("VEREIN") else ""),
        "bereiche": ["oja"], "themen": [th], "traeger": traeger_for(p.get("VEREIN"), p["BEZEICHNUNG"]) or "oja", "zentrale": p.get("VEREIN"),
        "desc": {"Indoor": "Jugendzentrum / Jugendtreff (Indoor-Angebot der Offenen Kinder- und Jugendarbeit).", "Parkbetreuung": "Parkbetreuung: Spiel-, Sport- und Gesprächsangebote für Kinder und Jugendliche in Parks, vor allem in der warmen Jahreszeit.",
                 "Fair-Play-Team": "Fair-Play-Team: aufsuchende Arbeit im öffentlichen Raum für alle Altersgruppen, vermittelt bei Nutzungskonflikten und fördert ein faires Miteinander.",
                 "Mobil": "Mobile Jugendarbeit / Streetwork: Sozialarbeiter:innen suchen Jugendliche an ihren Treffpunkten im öffentlichen Raum auf.", "Wienweit": "Wienweites Angebot der Offenen Kinder- und Jugendarbeit."}.get(p["ANGEBOT_LABEL_TXT"]) + (f" {p['ZUSATZANGEBOT']}" if p.get("ZUSATZANGEBOT") else ""),
        "hours": re.sub(r"<br\s*/?>", "\n", p.get("OEFFNUNGSZEIT") or "") or None, "phone": [p["TELEFON"]] if p.get("TELEFON") else [], "email": [p["EMAIL"]] if p.get("EMAIL") else [],
        "web": urls, "web_excerpt": None, "videos": [], "funding": None, "funding_hint": FUND_DEFAULT["oja"],
        "src": {"name": "Stadt Wien – data.wien.gv.at, Jugendangebote (CC BY 4.0)", "url": "https://www.data.gv.at/katalog/dataset/stadt-wien_angebotefrjugendlicheinwien", "updated": ""},
        "lat": lat, "lon": lon, "adr": p["ADRESSE"], "bez": p.get("BEZIRK"),
    })

for f in ogd("WOHNPARTNEROGD"):
    p = f["properties"]; lon, lat = f["geometry"]["coordinates"]
    ex = near(lat, lon, "wohnpartner " + p["BEZEICHNUNG"])
    if ex:
        if "gwa" not in ex["bereiche"]: ex["bereiche"].append("gwa")
        if "wohnpartner" not in ex["themen"]: ex["themen"].append("wohnpartner")
        continue
    bez = re.match(r"\s*(\d+)", p["ADRESSE"]); bez = int(bez.group(1)) if bez else None
    items.append({"id": f"wp{p['OBJECTID']}", "name": f"{p['BEZEICHNUNG']} – wohnpartner" + (f" ({bez}. Bezirk)" if bez else ""), "bereiche": ["gwa"], "themen": ["wohnpartner"], "traeger": "wohnpartner", "zentrale": "wohnpartner, Wohnservice Wien GmbH",
                  "desc": "Lokal von wohnpartner: Anlaufstelle für Bewohner:innen der Wiener Gemeindebauten bei Nachbarschaftsthemen und Konflikten; Gemeinwesenarbeit und Projekte im Grätzl.",
                  "hours": re.sub(r"<br\s*/?>", "\n", p.get("OEFFNUNGSZEIT") or "") or None, "phone": [p["TELEFON"]] if p.get("TELEFON") else [], "email": [p["EMAIL"]] if p.get("EMAIL") else [],
                  "web": [p.get("WEBLINK") or "https://wohnpartner-wien.at"], "web_excerpt": None, "videos": [], "funding": None, "funding_hint": "Von der Stadt Wien finanziert (Wohnservice Wien).",
                  "src": {"name": "Stadt Wien – data.wien.gv.at, wohnpartner-Standorte (CC BY 4.0)", "url": "https://www.data.gv.at/katalog/dataset/stadt-wien_wohnpartnerstandortewien", "updated": ""},
                  "lat": lat, "lon": lon, "adr": p["ADRESSE"], "bez": bez})

# Website-Auszug auch für OGD-Einträge holen, falls im Cache
for it in items:
    if not it["web_excerpt"] and it["web"]: it["web_excerpt"] = excerpt(it["web"])

# ---------- Ausgabe ----------
ORDER = {c: n for n, (c, *_r) in enumerate(BEREICHE)}
for it in items:
    it["bereiche"].sort(key=ORDER.get)
    it["lat"] = round(it["lat"], 6) if it["lat"] else None
    it["lon"] = round(it["lon"], 6) if it["lon"] else None
    for k in list(it):
        if it[k] in (None, [], ""): del it[k]

used = {it.get("traeger") for it in items}
meta = {
    "bereiche": [{"code": c, "name": n, "color": col, "themen": [k for k in kws if any(k in it.get("themen", []) for it in items)], "info": BEREICH_INFO.get(c, {})} for c, n, col, kws in BEREICHE],
    "traeger": {t["key"]: {k: v for k, v in t.items() if k != "match"} for t in TRAEGER if t["key"] in used},
    "general": GENERAL_LINKS, "built": time.strftime("%Y-%m-%d"),
    "counts": {"total": len(items), "mapped": sum(1 for i in items if "lat" in i)},
}
json.dump(vt, open(VC, "w"), ensure_ascii=False)
(R / "site/data/einrichtungen.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), "utf-8")
(R / "site/data/meta.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), "utf-8")
from collections import Counter
print(meta["counts"], Counter(b for i in items for b in i["bereiche"]))
print("mit Träger-Profil", sum(1 for i in items if i.get("traeger")), "mit Website-Auszug", sum(1 for i in items if i.get("web_excerpt")), "mit Videos", sum(1 for i in items if i.get("videos")))
print("size KB", (R / "site/data/einrichtungen.json").stat().st_size // 1024)
