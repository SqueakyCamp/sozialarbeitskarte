"use strict";
/* Sozialarbeitskarte Wien – Vanilla JS + Leaflet */
const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
const UCOL = { U1: "#e3000f", U2: "#a762a3", U3: "#ee7d00", U4: "#00963f", U5: "#008f95", U6: "#9d6830" };

const state = { b: new Set(), t: new Set(), q: "", bez: "", noloc: true, sel: null, open: null };
let META, ITEMS, BMAP = {}, STATIONS = [], map, cluster, markers = new Map();

/* ---------- Karte ---------- */
function initMap() {
  map = L.map("map", { zoomControl: false, preferCanvas: false, maxZoom: 20, minZoom: 10 }).setView([48.2085, 16.3725], 12);
  L.control.zoom({ position: "bottomright" }).addTo(map);
  const bm = (layer, ext = "png") => `https://mapsneu.wien.gv.at/basemap/${layer}/normal/google3857/{z}/{y}/{x}.${ext}`;
  const attrBm = '© <a href="https://basemap.at">basemap.at</a>';
  const labels = () => L.tileLayer(bm("bmapoverlay"), { maxZoom: 20, maxNativeZoom: 19, attribution: attrBm });
  const base = {
    "Karte": L.tileLayer(bm("geolandbasemap"), { maxZoom: 20, maxNativeZoom: 19, attribution: attrBm }),
    "Karte grau": L.tileLayer(bm("bmapgrau"), { maxZoom: 20, maxNativeZoom: 19, attribution: attrBm }),
    "Hell (OpenStreetMap)": L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", { maxZoom: 20, subdomains: "abcd", attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, © <a href="https://carto.com/attributions">CARTO</a>' }),
    "Satellit (Orthofoto)": L.layerGroup([L.tileLayer(bm("bmaporthofoto30cm", "jpeg"), { maxZoom: 20, maxNativeZoom: 19, attribution: attrBm }), labels()]),
    "Luftbild Stadt Wien": L.layerGroup([L.tileLayer("https://mapsneu.wien.gv.at/wmts/lb/farbe/google3857/{z}/{y}/{x}.jpeg", { maxZoom: 20, maxNativeZoom: 19, attribution: '© <a href="https://data.wien.gv.at">Stadt Wien</a>' }), labels()]),
    "Dunkel": L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 20, subdomains: "abcd", attribution: '© OpenStreetMap, © CARTO' }),
  };
  base["Karte grau"].addTo(map);

  const lazy = (file, build) => {
    const g = L.layerGroup(); let loaded = false;
    g.on("add", async () => { if (loaded) return; loaded = true; const j = await (await fetch("data/" + file)).json(); build(j, g); });
    return g;
  };
  map.createPane("transit"); map.getPane("transit").style.zIndex = 390;
  map.createPane("stations"); map.getPane("stations").style.zIndex = 395;
  const ubahn = lazy("ubahn.geojson", (j, g) => {
    L.geoJSON(j, { pane: "transit", style: f => ({ color: UCOL[f.properties.l] || "#333", weight: 5, opacity: .9, lineCap: "round" }) }).addTo(g);
    L.geoJSON(STATIONS_GJ, {
      pane: "stations",
      pointToLayer: (f, ll) => L.marker(ll, { pane: "stations", icon: L.divIcon({ className: "", html: '<div class="ust-dot"></div>', iconSize: [9, 9], iconAnchor: [7, 7] }), keyboard: false })
        .bindTooltip(`${esc(f.properties.n)} ${f.properties.l.map(l => `<b style="color:${UCOL[l]}">${l}</b>`).join(" ")}`, { className: "st-tip", direction: "top", offset: [0, -6] }),
    }).addTo(g);
  });
  const sbahn = lazy("sbahn.geojson", (j, g) => L.geoJSON(j, { pane: "transit", style: { color: "#0072bc", weight: 3, opacity: .75, dashArray: "8 5" }, onEachFeature: (f, l) => l.bindTooltip(f.properties.l, { sticky: true }) }).addTo(g));
  const tram = lazy("tram.geojson", (j, g) => L.geoJSON(j, { pane: "transit", style: { color: "#c8102e", weight: 2, opacity: .55 }, onEachFeature: (f, l) => l.bindTooltip("Straßenbahn " + f.properties.l, { sticky: true }) }).addTo(g));
  const bez = lazy("bezirke.geojson", (j, g) => L.geoJSON(j, { pane: "transit", style: { color: "#1f1b16", weight: 1.5, opacity: .7, fill: true, fillOpacity: 0, dashArray: "4 4" }, onEachFeature: (f, l) => l.bindTooltip(`${f.properties.b}. ${f.properties.n}`, { sticky: true }) }).addTo(g));
  const over = { "U-Bahn &amp; Stationen": ubahn, "S-Bahn &amp; Badner Bahn": sbahn, "Straßenbahn": tram, "Bezirksgrenzen": bez };
  L.control.layers(base, over, { position: "topright", collapsed: matchMedia("(max-width: 860px)").matches }).addTo(map);
  const ctl = $(".leaflet-control-layers-base"); ctl?.insertAdjacentHTML("afterbegin", '<div class="layer-title">Hintergrund</div>');
  $(".leaflet-control-layers-overlays")?.insertAdjacentHTML("afterbegin", '<div class="layer-title">Orientierung</div>');

  cluster = L.markerClusterGroup({ disableClusteringAtZoom: 16, maxClusterRadius: 38, showCoverageOnHover: false, chunkedLoading: true, spiderfyOnMaxZoom: true,
    iconCreateFunction: c => { const n = c.getChildCount(), s = n < 10 ? 26 : n < 50 ? 32 : 38; return L.divIcon({ className: "", html: `<div class="clu" style="width:${s}px;height:${s}px">${n}</div>`, iconSize: [s, s] }); } });
  map.addLayer(cluster);
  map.on("moveend", () => { if ($("#sort").value === "near") renderList(); });
}

/* ---------- Daten ---------- */
let STATIONS_GJ;
async function load() {
  const [m, it, st] = await Promise.all(["meta.json", "einrichtungen.json", "ubahn_stationen.geojson"].map(f => fetch("data/" + f).then(r => r.json())));
  META = m; ITEMS = it; STATIONS_GJ = st;
  META.bereiche.forEach(b => BMAP[b.code] = b);
  STATIONS = st.features.map(f => ({ n: f.properties.n, l: f.properties.l, lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] }));
  ITEMS.forEach(i => {
    i._s = norm([i.name, i.zentrale, i.desc, i.adr, (i.themen || []).join(" "), META.traeger[i.traeger]?.name, i.web_excerpt?.text].join(" "));
  });
  $("#countline").textContent = `${META.counts.total} Einrichtungen · ${META.counts.mapped} auf der Karte`;
  const bz = $("#bez");
  const names = ["Innere Stadt", "Leopoldstadt", "Landstraße", "Wieden", "Margareten", "Mariahilf", "Neubau", "Josefstadt", "Alsergrund", "Favoriten", "Simmering", "Meidling", "Hietzing", "Penzing", "Rudolfsheim-Fünfhaus", "Ottakring", "Hernals", "Währing", "Döbling", "Brigittenau", "Floridsdorf", "Donaustadt", "Liesing"];
  names.forEach((n, i) => bz.insertAdjacentHTML("beforeend", `<option value="${i + 1}">${i + 1}. ${n}</option>`));
}

/* ---------- Filter ---------- */
function matchesBase(i) {
  if (state.bez && String(i.bez) !== state.bez) return false;
  if (!state.noloc && i.lat == null) return false;
  if (state.q) { for (const w of norm(state.q).split(/\s+/)) if (w && !i._s.includes(w)) return false; }
  return true;
}
function matchesCat(i) {
  if (!state.b.size) return true;
  for (const b of state.b) {
    if (!i.bereiche.includes(b)) continue;
    const ts = BMAP[b].themen.filter(t => state.t.has(t));
    if (!ts.length || ts.some(t => i.themen.includes(t))) return true;
  }
  return false;
}
const visible = () => ITEMS.filter(i => matchesBase(i) && matchesCat(i));
function colorOf(i) {
  const b = i.bereiche.find(b => state.b.has(b)) || i.bereiche[0];
  return BMAP[b]?.color || "#555";
}

/* ---------- UI: Filter ---------- */
function renderFilters() {
  const base = ITEMS.filter(matchesBase);
  const wrap = $("#bereiche"); wrap.innerHTML = "";
  for (const b of META.bereiche) {
    const n = base.filter(i => i.bereiche.includes(b.code)).length;
    const on = state.b.has(b.code);
    const div = document.createElement("div"); div.className = "bereich"; div.style.setProperty("--c", b.color);
    div.innerHTML = `<div class="brow"><button class="chip ${on ? "on" : ""} ${!n ? "dim" : ""}" data-b="${b.code}"><span class="dot"></span>${esc(b.name)} <span class="n">${n}</span></button>
      ${b.themen.length > 1 ? `<button class="more" data-x="${b.code}" aria-label="Unterkategorien">${state.open === b.code ? "▾" : "▸"} ${b.themen.length}</button>` : ""}</div>`;
    if (state.open === b.code) {
      const th = document.createElement("div"); th.className = "themen";
      for (const t of b.themen) {
        const tn = base.filter(i => i.bereiche.includes(b.code) && i.themen.includes(t)).length;
        th.insertAdjacentHTML("beforeend", `<button class="chip ${state.t.has(t) && on ? "on" : ""} ${!tn ? "dim" : ""}" data-b="${b.code}" data-t="${esc(t)}">${esc(t)} <span class="n">${tn}</span></button>`);
      }
      div.append(th);
    }
    wrap.append(div);
  }
  renderBereichInfo();
}
function renderBereichInfo() {
  const box = $("#bereichInfo");
  if (state.b.size !== 1) { box.hidden = true; return; }
  const b = BMAP[[...state.b][0]], inf = b.info || {};
  if (!inf.text) { box.hidden = true; return; }
  box.style.setProperty("--c", b.color); box.hidden = false;
  const links = [...(inf.wiki || []).map(([t, u]) => ({ t: t + " (Wikipedia)", u })), ...(inf.links || [])];
  const wasOpen = box.querySelector("details")?.open && box.dataset.b === b.code; box.dataset.b = b.code;
  box.innerHTML = `<details ${wasOpen ? "open" : ""}><summary>${esc(b.name)} in Wien – so ist es organisiert</summary><p>${esc(inf.text)}</p>${links.length ? `<div class="links">${links.map(l => `<a href="${esc(l.u)}" target="_blank" rel="noopener">↗ ${esc(l.t)}</a>`).join("")}</div>` : ""}</details>`;
}
$("#bereiche").addEventListener("click", e => {
  const x = e.target.closest("[data-x]");
  if (x) { state.open = state.open === x.dataset.x ? null : x.dataset.x; renderFilters(); return; }
  const c = e.target.closest("[data-b]"); if (!c) return;
  const b = c.dataset.b, t = c.dataset.t;
  if (t) {
    state.t.has(t) ? state.t.delete(t) : state.t.add(t);
    if (state.t.has(t)) state.b.add(b);
  } else {
    if (state.b.has(b)) { state.b.delete(b); BMAP[b].themen.forEach(t => state.t.delete(t)); }
    else { state.b.add(b); state.open = b; }
  }
  update();
});
$("#resetBtn").onclick = () => { state.b.clear(); state.t.clear(); state.q = ""; $("#q").value = ""; state.bez = ""; $("#bez").value = ""; state.open = null; update(); };
let qT; $("#q").addEventListener("input", e => { clearTimeout(qT); qT = setTimeout(() => { state.q = e.target.value.trim(); update(); }, 160); });
$("#bez").onchange = e => { state.bez = e.target.value; update(true); };
$("#noloc").onchange = e => { state.noloc = e.target.checked; update(); };
$("#sort").onchange = renderList;

/* ---------- Marker + Liste ---------- */
function pinIcon(i, big) { return L.divIcon({ className: "", html: `<div class="pin ${big ? "big" : ""}" style="--c:${colorOf(i)}"></div>`, iconSize: [14, 14], iconAnchor: [9, 9] }); }
function renderMarkers(fit) {
  cluster.clearLayers(); markers.clear();
  const vis = visible().filter(i => i.lat != null), ms = [];
  for (const i of vis) {
    const m = L.marker([i.lat, i.lon], { icon: pinIcon(i, state.sel === i.id), title: i.name, riseOnHover: true });
    m.on("click", () => select(i.id, false));
    markers.set(i.id, m); ms.push(m);
  }
  cluster.addLayers(ms);
  if (fit && ms.length) map.fitBounds(L.latLngBounds(ms.map(m => m.getLatLng())).pad(0.1), { maxZoom: 15 });
}
function dist(a, b, c, d) { const R = 6371e3, r = Math.PI / 180, x = (d - b) * r * Math.cos((a + c) / 2 * r), y = (c - a) * r; return Math.sqrt(x * x + y * y) * R; }
function renderList() {
  let vis = visible();
  if ($("#sort").value === "near") { const c = map.getCenter(); vis.sort((a, b) => (a.lat == null) - (b.lat == null) || dist(c.lat, c.lng, a.lat, a.lon) - dist(c.lat, c.lng, b.lat, b.lon)); }
  else {
    const q = norm(state.q).split(/\s+/).filter(Boolean), sc = i => q.length && q.every(w => norm(i.name + " " + (i.zentrale || "")).includes(w)) ? 0 : 1;
    vis.sort((a, b) => sc(a) - sc(b) || a.name.localeCompare(b.name, "de"));
  }
  $("#listcount").textContent = `${vis.length} Treffer`;
  const max = 400, ol = $("#list");
  ol.innerHTML = vis.slice(0, max).map(i => `<li data-id="${i.id}" class="${state.sel === i.id ? "sel" : ""}"><span class="dot" style="background:${colorOf(i)}"></span><div><div class="nm">${esc(i.name)}</div><div class="meta">${i.adr ? esc(i.adr) : '<span class="noloc">kein fester Standort</span>'}${i.themen?.length ? " · " + esc(i.themen.slice(0, 2).join(", ")) : ""}</div></div></li>`).join("")
    + (vis.length > max ? `<li class="more-items">… und ${vis.length - max} weitere – Filter oder Suche verfeinern</li>` : "");
}
$("#list").addEventListener("click", e => { const li = e.target.closest("li[data-id]"); if (li) select(li.dataset.id, true); });

function update(fit) { renderFilters(); renderMarkers(fit); renderList(); writeHash(); }

/* ---------- Detail ---------- */
function nearestStation(i) {
  let best = null;
  for (const s of STATIONS) { const d = dist(i.lat, i.lon, s.lat, s.lon); if (!best || d < best.d) best = { ...s, d }; }
  return best;
}
const ytId = u => (u.match(/v=([\w-]{11})/) || [])[1];
function select(id, pan) {
  const prev = state.sel; state.sel = id;
  const i = ITEMS.find(x => x.id === id); if (!i) return;
  if (prev && markers.get(prev)) { const p = ITEMS.find(x => x.id === prev); markers.get(prev).setIcon(pinIcon(p, false)); }
  if (i.lat != null) {
    const m = markers.get(id);
    if (m) m.setIcon(pinIcon(i, true));
    if (pan) { map.setView([i.lat, i.lon], Math.max(map.getZoom(), 16)); }
  }
  document.querySelectorAll("#list li.sel").forEach(li => li.classList.remove("sel"));
  const li = $(`#list li[data-id="${CSS.escape(id)}"]`); li?.classList.add("sel");
  renderDetail(i); writeHash();
  if (matchMedia("(max-width: 860px)").matches) document.body.classList.remove("side-open");
}
function renderDetail(i) {
  const T = i.traeger ? META.traeger[i.traeger] : null;
  const bereiche = i.bereiche.map(b => BMAP[b]);
  const st = i.lat != null ? nearestStation(i) : null;
  const h = [];
  h.push(`<div class="badges">${bereiche.map(b => `<span class="badge" style="--c:${b.color}">${esc(b.name)}</span>`).join("")}</div>`);
  h.push(`<h2>${esc(i.name)}</h2>`);
  h.push(`<div class="badges">${(i.themen || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</div>`);
  // Kontakt
  const kv = [];
  if (i.adr) kv.push(["📍", `${esc(i.adr)} · <a href="https://www.google.com/maps/dir/?api=1&destination=${i.lat},${i.lon}" target="_blank" rel="noopener">Route</a>`]);
  else kv.push(["📍", `<span class="hint">Kein öffentlicher Standort (z. B. Hotline, Online-Angebot, mobil oder aus Schutzgründen geheime Adresse).</span>`]);
  if (st) kv.push(["🚇", `${esc(st.n)} ${st.l.map(l => `<b style="color:${UCOL[l]}">${l}</b>`).join(" ")} · ca. ${Math.round(st.d / 10) * 10} m Luftlinie`]);
  if (i.phone?.length) kv.push(["☎", i.phone.map(p => `<a href="tel:${esc(p.replace(/[^\d+]/g, ""))}">${esc(p)}</a>`).join(", ")]);
  if (i.email?.length) kv.push(["✉", i.email.map(m => `<a href="mailto:${esc(m)}">${esc(m)}</a>`).join(", ")]);
  if (i.web?.length) kv.push(["🌐", i.web.map(u => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "").slice(0, 48))}</a>`).join("<br>")]);
  if (i.hours) kv.push(["🕑", `<span class="pre">${esc(i.hours)}</span>`]);
  h.push(`<div class="sec kv">${kv.map(([a, b]) => `<span>${a}</span><div>${b}</div>`).join("")}</div>`);
  // Was sie tun
  if (i.desc || i.web_excerpt) {
    h.push(`<div class="sec"><h4>Was die Einrichtung macht</h4>`);
    if (i.web_excerpt) h.push(`<div class="quote">${esc(i.web_excerpt.text)}</div><p class="src">Auszug von der Website: <a href="${esc(i.web_excerpt.url)}" target="_blank" rel="noopener">${esc(i.web_excerpt.title || i.web_excerpt.url)}</a></p>`);
    if (i.desc) h.push(`<p class="pre">${esc(i.desc)}</p><p class="src">Laut <a href="${esc(i.src.url)}" target="_blank" rel="noopener">${esc(i.src.name)}</a>${i.src.updated ? `, Stand ${esc(i.src.updated)}` : ""}</p>`);
    h.push(`</div>`);
  }
  // Einordnung
  h.push(`<div class="sec"><h4>Einordnung in die Soziale Arbeit</h4>`);
  for (const b of bereiche) {
    const ts = (i.themen || []).filter(t => b.themen.includes(t));
    h.push(`<p><b style="color:${b.color}">${esc(b.name)}</b>${ts.length ? ` – ${esc(ts.join(", "))}` : ""}. <a href="#" data-showb="${b.code}">Wie das Feld in Wien organisiert ist →</a></p>`);
  }
  h.push(`</div>`);
  // Träger
  if (T || i.zentrale || i.funding || i.funding_hint) {
    h.push(`<div class="sec"><h4>Träger, Struktur &amp; Förderung</h4>`);
    if (i.zentrale && (!T || norm(i.zentrale) !== norm(T.name))) h.push(`<p>Gehört zu: <b>${esc(i.zentrale)}</b></p>`);
    if (T) {
      h.push(`<div class="traeger"><b>${esc(T.name)}</b><div class="src">${esc(T.typ)}</div><p>${esc(T.text)}</p>${T.struktur ? `<p><i>${esc(T.struktur)}</i></p>` : ""}
        <div class="links">${T.web ? `<a href="${esc(T.web)}" target="_blank" rel="noopener">↗ Website des Trägers</a>` : ""}${T.wiki ? `<a href="${esc(T.wiki)}" target="_blank" rel="noopener">↗ Wikipedia</a>` : ""}</div></div>`);
    }
    if (i.funding) h.push(`<p><b>Förderung:</b> ${esc(i.funding)} <span class="src">(laut Sozialinfo Wien)</span></p>`);
    else if (i.funding_hint) h.push(`<p class="hint">Allgemeiner Hinweis: ${esc(i.funding_hint)}</p>`);
    h.push(`</div>`);
  }
  // Medien
  const arts = T?.links || [];
  if (i.videos?.length || arts.length) {
    h.push(`<div class="sec"><h4>Mehr erfahren – Videos &amp; Artikel</h4>`);
    for (const v of i.videos || []) {
      const id = ytId(v.u);
      h.push(`<a class="vid" href="${esc(v.u)}" target="_blank" rel="noopener">${id ? `<img loading="lazy" src="https://i.ytimg.com/vi/${id}/mqdefault.jpg" alt="">` : ""}<span>▶ ${esc(v.t)}<small>${esc(v.a)}${id ? " · YouTube" : " · Vimeo"}</small></span></a>`);
    }
    if (arts.length) h.push(`<div class="links">${arts.map(l => `<a href="${esc(l.u)}" target="_blank" rel="noopener">↗ ${esc(l.t)}</a>`).join("")}</div>${T ? `<p class="src">Artikel zum Träger ${esc(T.name)}, nicht unbedingt zu genau diesem Standort.</p>` : ""}`);
    h.push(`</div>`);
  }
  h.push(`<p class="src" style="margin-top:16px">Datenquelle: <a href="${esc(i.src.url)}" target="_blank" rel="noopener">${esc(i.src.name)}</a>. Angaben ohne Gewähr – vor einem Besuch bitte auf der Website prüfen.</p>`);
  $("#detailBody").innerHTML = h.join("");
  $("#detail").hidden = false; $("#detail").scrollTop = 0; document.body.classList.add("detail-open");
}
$("#detail").addEventListener("click", e => {
  const a = e.target.closest("[data-showb]"); if (!a) return;
  e.preventDefault(); state.b = new Set([a.dataset.showb]); state.t.clear(); state.open = a.dataset.showb;
  update();
  if (matchMedia("(max-width: 860px)").matches) { $("#detail").hidden = true; document.body.classList.add("side-open"); }
  const d = $("#bereichInfo details"); if (d) d.open = true; $("#bereichInfo").scrollIntoView({ behavior: "smooth", block: "nearest" });
});
$("#closeDetail").onclick = () => { $("#detail").hidden = true; document.body.classList.remove("detail-open"); const p = state.sel; state.sel = null; if (p && markers.get(p)) markers.get(p).setIcon(pinIcon(ITEMS.find(x => x.id === p), false)); writeHash(); };
$("#mapBtn").onclick = () => document.body.classList.remove("side-open");
$("#sideToggle").onclick = () => document.body.classList.toggle("side-open");

/* ---------- URL-Zustand ---------- */
function writeHash() {
  const p = new URLSearchParams();
  if (state.b.size) p.set("b", [...state.b].join(","));
  if (state.t.size) p.set("t", [...state.t].join("|"));
  if (state.q) p.set("q", state.q);
  if (state.bez) p.set("bez", state.bez);
  if (state.sel) p.set("id", state.sel);
  history.replaceState(null, "", p.toString() ? "#" + p.toString() : location.pathname);
}
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  if (p.get("b")) p.get("b").split(",").filter(b => BMAP[b]).forEach(b => state.b.add(b));
  if (p.get("t")) p.get("t").split("|").forEach(t => state.t.add(t));
  if (state.b.size === 1) state.open = [...state.b][0];
  state.q = p.get("q") || ""; $("#q").value = state.q;
  state.bez = p.get("bez") || ""; $("#bez").value = state.bez;
  return p.get("id");
}

/* ---------- Über ---------- */
$("#aboutBtn").onclick = () => {
  $("#aboutBody").innerHTML = `<h2>Über die Sozialarbeitskarte</h2>
  <p>Die Karte zeigt Einrichtungen der Sozialen Arbeit in Wien, sortiert nach Arbeitsfeldern. Klick auf einen Punkt zeigt, was die Einrichtung macht (Website-Auszug und Beschreibung aus der Sozialinfo Wien), zu welchem Träger sie gehört, wie das Arbeitsfeld organisiert und finanziert ist, und, wo vorhanden, Videos und Artikel.</p>
  <h4>Quellen</h4>
  <ul>
   <li><a href="https://www.wien.gv.at/sozialinfo/" target="_blank" rel="noopener">Sozialinfo Wien</a> (Fonds Soziales Wien): Einrichtungen, Adressen, Themen, Beschreibungen</li>
   <li><a href="https://data.wien.gv.at" target="_blank" rel="noopener">Offene Daten der Stadt Wien</a> (CC BY 4.0): Jugendangebote, wohnpartner, U-Bahn, Öffi-Linien, Bezirksgrenzen</li>
   <li>Websites der Einrichtungen: Beschreibungstexte (Auszüge) und eingebettete Videos</li>
   <li>Träger-Profile und Bereichstexte: selbst zusammengefasst aus Websites, Wikipedia und den verlinkten Medienberichten</li>
   <li>Hintergrundkarten: <a href="https://basemap.at" target="_blank" rel="noopener">basemap.at</a>, Stadt Wien (Luftbild), OpenStreetMap/CARTO</li>
  </ul>
  <h4>Grenzen</h4>
  <p>Frauenhäuser, Krisenzentren der Kinder- und Jugendhilfe und manche Wohnangebote haben aus Schutzgründen keine öffentliche Adresse und erscheinen nur als Einrichtung „ohne Standort“ oder gar nicht. Die Zuordnung zu Arbeitsfeldern folgt den Themen der Sozialinfo Wien und ist eine Einordnung, keine offizielle Einteilung. Förderangaben stammen aus der Sozialinfo-Beschreibung; wo „Allgemeiner Hinweis“ steht, ist es die übliche Finanzierung des Felds, nicht für die Einrichtung geprüft.</p>
  <p class="src">Datenstand: ${esc(META.built)} · ${META.counts.total} Einrichtungen</p>
  <h4>Weiterlesen</h4><div class="links">${META.general.map(l => `<a href="${esc(l.u)}" target="_blank" rel="noopener">↗ ${esc(l.t)}</a>`).join("")}</div>`;
  $("#about").showModal();
};

/* ---------- Start ---------- */
(async () => {
  initMap();
  await load();
  const id = readHash();
  update();
  map.on("click", () => document.body.classList.remove("side-open"));
  if (id) select(id, true);
})();
