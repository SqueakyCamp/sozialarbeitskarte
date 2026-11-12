"""Sozialinfo-Wien-Stichwörter -> Arbeitsfelder der Sozialen Arbeit.

Reihenfolge innerhalb eines Bereichs = Reihenfolge der Unterfilter in der App.
"""
BEREICHE = [
  ("wlh", "Wohnungslosenhilfe", "#c2410c", [
    "Notunterkunft für obdachlose Menschen", "Chancenhäuser für obdachlose Menschen",
    "Stationär betreutes Wohnen für obdachlose Menschen", "Mobil betreutes Wohnen für obdachlose Menschen",
    "Wohnen für obdachlose Menschen", "Straßensozialarbeit mit wohnungslosen Menschen",
    "Medizinische Betreuung für wohnungslose Menschen", "Wohnungslosigkeit", "Wohnungssicherung",
    "Zwangsräumung", "Wohnen für Mutter und Kind"]),
  ("kjf", "Kinder-, Jugend- & Familienhilfe", "#2563eb", [
    "Jugendamt", "Krisenzentren für junge Menschen", "Wohngemeinschaften für junge Menschen",
    "Wohnen für junge Menschen", "Pflegefamilien", "Adoption", "Gewalt gegen Kinder", "Kinderrechte",
    "Familienberatung", "Familienberatung bei Gericht", "Erziehungsberatung", "Elternberatung", "Elternhilfe",
    "Eltern Kind Zentren", "Familienhilfe zu Hause", "Besuchsbegleitung", "Trennungsbegleitung für Kinder",
    "Alleinerziehende Eltern", "Schwangerschaft und Geburt"]),
  ("oja", "Offene Jugendarbeit", "#0891b2", [
    "Jugendzentrum", "Parkbetreuung", "Fair-Play-Team", "Mobile Jugendarbeit",
    "Straßensozialarbeit mit jungen Menschen", "Jugendberatung", "Mädchenberatung",
    "Freizeitangebote für junge Menschen", "Berufsintegration junger Menschen", "Psychotherapie für junge Menschen"]),
  ("sucht", "Sucht & Drogen", "#7c3aed", [
    "Drogenabhängigkeit", "Straßensozialarbeit mit drogenabhängigen Menschen", "Alkoholabhängigkeit",
    "Medikamentenabhängigkeit", "Spielsucht", "Kaufsucht", "Mediensucht", "Sucht"]),
  ("psy", "Psychosoziale Versorgung", "#db2777", [
    "Sozialpsychiatrische Dienste", "Krisenintervention", "Psychosoziale Akutbetreuung", "Suizid",
    "Tageszentren für psychisch kranke Menschen", "Tagesstruktur für psychisch kranke Menschen",
    "Wohnen für psychisch kranke Menschen", "Arbeit für psychisch kranke Menschen",
    "Berufsintegration psychisch kranker Menschen", "Psychische Erkrankungen", "Psychologische Beratung", "Trauma"]),
  ("gew", "Gewaltschutz & Opferhilfe", "#dc2626", [
    "Frauenhaus", "Gewalt gegen Frauen", "Sexualisierte Gewalt", "Gewalt", "Opferhilfe", "Verbrechensopfer",
    "Gerichtsbegleitung", "Menschenhandel", "Zwangsheirat", "Genitalverstümmelung", "Stalking",
    "Gewalt gegen alte Menschen"]),
  ("gender", "Frauen, Männer & LGBTIQA+", "#be185d", [
    "Frauenberatung", "Männerberatung", "LGBTIQA+", "Prostitution"]),
  ("mig", "Migration & Flucht", "#059669", [
    "Flucht", "Wohnen für Flüchtlinge", "Migration", "Wohnen für MigrantInnen",
    "Familienberatung für Migranten/Migrantinnen", "Finanzielle Nothilfen für Migranten/Migrantinnen",
    "Rückkehrhilfe", "Roma", "Rassismus"]),
  ("exist", "Existenzsicherung & Armut", "#ca8a04", [
    "Sozialzentren", "Sozialberatung", "Sozialarbeit", "Schulden", "Finanzielle Nothilfen",
    "Finanzielle Nothilfen für Familien", "Finanzielle Nothilfen für alte Menschen", "Sozialmärkte",
    "Lebensmittelhilfe", "Kleidung", "Möbel", "Kost-nix-Laden"]),
  ("arbeit", "Arbeit & Beschäftigung", "#4d7c0f", [
    "Arbeitsprojekte", "Berufsintegration", "Gelegenheitsarbeiten", "Arbeitslosigkeit"]),
  ("straf", "Straffälligenhilfe", "#475569", [
    "Bewährungshilfe", "Haftentlassung", "Häftlingsbetreuung", "Tatausgleich"]),
  ("beh", "Behinderung", "#0d9488", [
    "Behindertenberatung", "Wohnen für Menschen mit Behinderung", "Tagesstruktur für Menschen mit Behinderung",
    "Arbeit für Menschen mit Behinderung", "Berufsintegration für Menschen mit Behinderung",
    "Persönliche Assistenz", "Freizeitangebote für Menschen mit Behinderung"]),
  ("alter", "Alter & Pflege", "#9333ea", [
    "Seniorenberatung/Seniorinnenberatung", "Tageszentren für SeniorInnen", "Pflegeberatung",
    "Wohnhäuser für alte Menschen", "Wohn- und Pflegehäuser öffentlich",
    "Wohn- und Pflegehäuser privat mit Förderung", "Wohngemeinschaften für alte Menschen",
    "Wohnen für demenzkranke Menschen", "Betreuende Angehörige", "Hospiz und Palliativpflege"]),
  ("gwa", "Gemeinwesenarbeit & Nachbarschaft", "#16a34a", [
    "Gebietsbetreuung", "wohnpartner", "Nachbarschaftshilfe", "Straßensozialarbeit", "Mediation"]),
  ("ges", "Gesundheit & Sozialmedizin", "#0284c7", [
    "Krankenhaussozialdienst", "Aids", "Frauengesundheit", "Männergesundheit", "Familienplanung"]),
]
# Unterfilter, die nicht aus Sozialinfo, sondern aus OGD-Layern der Stadt kommen
OGD_ONLY = {"Jugendzentrum", "Parkbetreuung", "Fair-Play-Team", "Mobile Jugendarbeit", "wohnpartner"}
