# Sozialarbeitskarte Wien

Interaktive Karte aller sozialarbeiterischen Einrichtungen in Wien, gebaut 2026-11-12 für Daniel (Soziale-Arbeit-Kontext, vgl. Sprengel). Statisch auf GitHub Pages (SqueakyCamp/sozialarbeitskarte, Action deployt `site/`), Vanilla JS + Leaflet (vendored), kein Build-Schritt fürs Frontend.

## Daten-Pipeline (Python, nur stdlib)
1. `tools/crawl_sozialinfo.py` – crawlt Sozialinfo Wien (FSW) für alle Stichwörter aus `tools/categories.py` → `cache/sozialinfo.json` (Rohseiten in `cache/sozialinfo/`, langsam: ~1 Anfrage/2 s).
2. `tools/fetch_websites.py` – holt die Websites der Einrichtungen, extrahiert meta-Description, erste Absätze, eingebettete YouTube/Vimeo-Videos → `cache/web.json`.
3. OGD-Layer der Stadt Wien liegen in `cache/ogd/*.json` (WFS data.wien.gv.at, Layer UBAHNOGD, UBAHNHALTOGD, OEFFLINIENOGD, BEZIRKSGRENZEOGD, JGDANGEBOTOGD, WOHNPARTNEROGD). `tools/build_layers.py` → `site/data/*.geojson`.
4. `tools/build_data.py` – führt alles zusammen (+ `tools/curated.py`: Träger-Profile, Bereichstexte, Artikel-Links; Video-Titel per oEmbed, gecacht) → `site/data/einrichtungen.json`, `site/data/meta.json`.

`cache/` ist nicht in Git (fremde Rohseiten). Zum Aktualisieren: Cache löschen, Schritte 1–4 laufen lassen.

## Konventionen
- Arbeitsfelder (15) und ihre Unterfilter = Sozialinfo-Stichwörter in `categories.py`; `OGD_ONLY` sind Unterfilter aus OGD-Daten.
- Träger-Zuordnung über `match`-Teilstrings in `curated.py` (erstes Profil gewinnt, `re:` = Regex).
- Förderung: nur aus Sozialinfo-Text („gefördert von …“); sonst als „Allgemeiner Hinweis“ pro Feld gekennzeichnet.
- Artikel-Links nur aus tatsächlich gefundenen Quellen eintragen, mit Medium in Klammern.
- Frauenhäuser/Krisenzentren haben keine öffentliche Adresse → erscheinen ohne Standort.
- Bei Änderungen an app.js/app.css `?v=` in index.html hochzählen.
- Lokal testen: `python3 -m http.server 8797 --bind 127.0.0.1` in `site/` (8765 ist belegt).
