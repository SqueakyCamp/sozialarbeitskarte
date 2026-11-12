"""OGD-Layer der Stadt Wien (data.wien.gv.at, CC BY 4.0) -> site/data/*.geojson (verkleinert)."""
import json, pathlib, collections
R = pathlib.Path(__file__).resolve().parent.parent
O = R / "cache" / "ogd"; D = R / "site" / "data"; D.mkdir(parents=True, exist_ok=True)

def simplify(pts, tol):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1; L = (dx * dx + dy * dy) or 1e-18
    best, bi = 0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]; t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
        dd = (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2
        if dd > best: best, bi = dd, i
    if best ** .5 <= tol: return [pts[0], pts[-1]]
    return simplify(pts[:bi + 1], tol)[:-1] + simplify(pts[bi:], tol)

def rnd(c): return [round(c[0], 5), round(c[1], 5)]
def geom(g, tol):
    if g["type"] == "LineString": return {"type": "LineString", "coordinates": [rnd(c) for c in simplify(g["coordinates"], tol)]}
    if g["type"] == "MultiLineString": return {"type": "MultiLineString", "coordinates": [[rnd(c) for c in simplify(l, tol)] for l in g["coordinates"]]}
    if g["type"] == "Polygon": return {"type": "Polygon", "coordinates": [[rnd(c) for c in simplify(l, tol)] for l in g["coordinates"]]}
    if g["type"] == "MultiPolygon": return {"type": "MultiPolygon", "coordinates": [[[rnd(c) for c in simplify(l, tol)] for l in p] for p in g["coordinates"]]}
    return g
def save(name, feats): (D / name).write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":")), "utf-8")
load = lambda n: json.load(open(O / f"{n}.json", encoding="utf-8"))["features"]

save("ubahn.geojson", [{"type": "Feature", "properties": {"l": f"U{f['properties']['LINFO']}"}, "geometry": geom(f["geometry"], 2e-5)} for f in load("UBAHNOGD")])
st = collections.defaultdict(lambda: {"lines": set()})
for f in load("UBAHNHALTOGD"):
    n = f["properties"]["HTXT"].strip(); s = st[n]; s["lines"].add(f"U{f['properties']['LINFO']}"); s.setdefault("c", f["geometry"]["coordinates"])
save("ubahn_stationen.geojson", [{"type": "Feature", "properties": {"n": n, "l": sorted(s["lines"])}, "geometry": {"type": "Point", "coordinates": rnd(s["c"])}} for n, s in st.items()])
lin = load("OEFFLINIENOGD")
inside = lambda f: any(16.17 < c[0] < 16.58 and 48.11 < c[1] < 48.33 for c in (f["geometry"]["coordinates"] if f["geometry"]["type"] == "LineString" else [p for l in f["geometry"]["coordinates"] for p in l]))
save("sbahn.geojson", [{"type": "Feature", "properties": {"l": f["properties"]["LBEZEICHNUNG"]}, "geometry": geom(f["geometry"], 3e-5)} for f in lin if f["properties"]["LTYPTXT"] in ("S-Bahn", "Badner Bahn") and inside(f)])
save("tram.geojson", [{"type": "Feature", "properties": {"l": f["properties"]["LBEZEICHNUNG"]}, "geometry": geom(f["geometry"], 2e-5)} for f in lin if f["properties"]["LTYP"] == "1"])
save("bezirke.geojson", [{"type": "Feature", "properties": {"n": f["properties"].get("NAMEK"), "b": f["properties"].get("BEZNR")}, "geometry": geom(f["geometry"], 4e-5)} for f in load("BEZIRKSGRENZEOGD")])
for p in sorted(D.glob("*.geojson")): print(p.name, p.stat().st_size // 1024, "KB")
