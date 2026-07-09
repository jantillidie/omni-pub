---
modified: 2026-07-08T00:00:00+02:00
created: 2026-07-08T00:00:00+02:00
tags:
  - python
---
# Dokumentation

**Projekt:** Omni Pub - KI-gestützter Omnichannel-Marketing-Automations-Service für die Gastronomie

**Entwickler:** Jan Maaß

**Projektzeitraum:** 22.06.2026 bis 09.07.2026

---

## 1. Über das Projekt

**TLDR:** Eine Python-App, die ein Foto einer handschriftlichen Wochenkarte einliest (mit Vision-LLM-basierter Text- und Strukturerkennung), per KI strukturiert, in einer Web-GUI zur Korrektur anbietet und die Daten an WordPress sowie zeitgesteuert an Bluesky und Mastodon verteilt (Meta Anbindung in Planung).

Omni Pub automatisiert den manuellen Workflow bei der Vermarktung gastronomischer Wochenkarten. Eine Streamlit-Web-App nimmt ein Foto der Karte auf, eine Vision-LLM extrahiert Tage, Daten und Gerichte als validiertes JSON, der Nutzer korrigiert in einer Tabelle, und das System verteilt die Daten anschließend:

- Textdaten an WordPress (Custom Fields via ACF)
- Generierte PNG-Flyer + Post-Text zeitgesteuert an Bluesky und Mastodon

### Kunden- und projektspezifisch

Dies ist kein generisches SaaS-Produkt, sondern eine Lösung für einen konkreten Kunden. Das bedeutet:

- **WordPress-Custom-Fields sind hart codiert.** Das Datenmodell in `models.py` ist auf das ACF-Schema des Kunden-WordPress zugeschnitten (Custom Post Type `weekly_menu`, Felder für 5 Tage, Format `YYYYMMDD`).
- **ACF (Advanced Custom Fields) ist kostenpflichtig.** Die WordPress-Seite nutzt ACF Pro. Ohne lizenziertes ACF-Plugin funktioniert der WordPress-Versand nicht.
- **Flyer-Template ist kundenspezifisch.** Das HTML/CSS-Template in `flyer-template/` enthält Logo, Farben, Schriftart (Rokkitt) und Layout des Kunden.
- **Post-Texte sind vorformuliert.** Default-Texte, Hashtags und Links sind auf den Kunden angepasst.

Bei Verwendung für eigene Projekte müssen angepasst werden: `models.py` (ACF-Schema), `flyer-template/` (Branding), `main.py` (Default-Texte, Hashtags, WordPress-URL), `config.py` (API-Endpunkte).

---

## 2. Systemarchitektur

**TLDR:** Streamlit-Frontend ruft nacheinander Vision-LLM, WordPress-Service, Flyer-Generator und Scheduler-Service auf. Der Scheduler läuft im Hintergrund und Jobs werden in SQLite dauerhaft gespeichert.

```
Foto-Upload → VisionLLMService → WeeklyMenu (Pydantic)
                                          ↓
                            Streamlit Data Editor (Korrektur)
                                          ↓
                    ┌─────────────────────┴──────────────────────┐
                    ↓                                            ↓
          WordPressService                          FlyerGeneratorService
          (REST-API, ACF)                            (HTML/CSS → PNG)
                                                          ↓
                                              SchedulerService
                                              (APScheduler + SQLite)
                                                          ↓
                                              BlueskyService / MastodonService
```

### Datenfluss im Detail

1. **Upload:** Nutzer lädt JPG/PNG der Wochenkarte hoch.
2. **Analyse:** `VisionLLMService` sendet Base64-Bild an OpenRouter (Gemini 3.1 Flash Lite), LLM gibt validiertes `WeeklyMenu`-JSON zurück.
3. **Korrektur:** Streamlit `data_editor` zeigt die Daten tabellarisch, Nutzer korrigiert Gerichte, Daten, vegetarisch-Flags.
4. **WordPress:** `WordPressService` sendet validierten Payload an `/wp/v2/weekly_menu` (Custom Post Type mit ACF).
5. **Flyer:** `FlyerGeneratorService` rendert pro Tag ein 1080×1080 PNG aus HTML-Template via headless Chrome.
6. **Planung:** `SchedulerService` legt pro Tag und Plattform (Bluesky, Mastodon) je einen APScheduler-Job in SQLite an.
7. **Veröffentlichung:** Zur geplanten Zeit ruft der Scheduler `BlueskyService` und `MastodonService` auf, die Bild + Text posten.

---

## 3. Installation

**TLDR:** Repo klonen, venv anlegen, `requirements.txt` installieren, `.envrc` oder `.env` mit API-Keys anlegen, Chrome oder chromium basierter Browser für html2image muss installiert sein.

### Voraussetzungen

- Python 3.12+
- Google Chrome oder Chromium based Browser (für `html2image`)
- WordPress-Instanz mit ACF Pro und Custom Post Type `weekly_menu`
- Accounts bei OpenRouter, Bluesky, Mastodon

### Setup

```sh
git clone <repo-url>
cd omni-pub
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Umgebungsvariablen

In `.envrc` (oder `.env`) anlegen:

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `WP_API_URL` | ja | WordPress REST-API Basis-URL |
| `WP_USERNAME` | ja | WordPress-Benutzer (nicht App-Name) |
| `WP_PASSWORD` | ja | WordPress Application Password |
| `OPENAI_API_KEY` | ja | OpenRouter API-Key |
| `BLUESKY_HANDLE` | nein | Bluesky-Handle ohne `@` |
| `BLUESKY_APP_PASSWORD` | nein | Bluesky App Password |
| `MASTODON_BASE_URL` | nein | Mastodon-Instanz-URL (ohne `/@account`) |
| `MASTODON_ACCESS_TOKEN` | nein | Mastodon Access Token |

Bluesky/Mastodon sind optional, die App startet auch ohne, die Services werfen erst beim Aufruf eine  Fehlermeldung.

### Start

```sh
streamlit run main.py
```

---

## 4. Datenmodell

**TLDR:** Pydantic-Modelle in `models.py` validieren die KI-Ausgabe und definieren das WordPress-ACF-Schema. `WeeklyMenu` besteht aus exakt 5 `DailyMenu`-Objekten.

### `MenuItem`

| Feld | Typ | Beschreibung |
|---|---|---|
| `dish_name` | str | Name des Gerichts |
| `is_vegetarian` | bool | True bei vegetarisch/vegan |

### `DailyMenu`

| Feld | Typ | Beschreibung |
|---|---|---|
| `weekday` | str | Wochentag (z. B. "Dienstag") |
| `menu_date` | str | Datum im ACF-Format `YYYYMMDD` |
| `menu_items` | list[MenuItem] | Mindestens 1 Gericht |

Der `menu_date`-Validator akzeptiert `DD.MM.YYYY`, `DD/MM/YYYY`, `YYYYMMDD` und `date`-Objekte und normalisiert auf `YYYYMMDD`.

### `WeeklyMenu`

| Feld | Typ | Beschreibung |
|---|---|---|
| `menu_start_datetime` | str | Auto-berechnet: erster Tag − 1 Tag, 14:53 Uhr |
| `menu_end_datetime` | str | Auto-berechnet: letzter Tag, 14:53 Uhr |
| `daily_menus` | list[DailyMenu] | Exakt 5 (min_length=5, max_length=5) |

`menu_start_datetime` und `menu_end_datetime` werden automatisch aus den Tagesdaten berechnet. (Das Datum und die spezielle Uhrzeit bedingt durch WordPress-interne Cronjob Logik) 

### `WordPressPayload`

| Feld | Typ | Beschreibung |
|---|---|---|
| `title` | str | Beitragstitel |
| `status` | str | Default: `publish` |
| `acf` | WeeklyMenu | Die ACF-Felddaten |

---

## 5. Services

**TLDR:** Jeder Service ist eine eigenständige Datei in `services/`, die einen Task übernimmt (KI-Analyse, WordPress-Versand, Flyer-Generierung, Social-Media-Publishing, Scheduling).

### `vision_llm_service.py`

Sendet Base64-Bild an OpenRouter (Gemini 3.1 Flash Lite) mit strukturiertem JSON-Schema. Der Prompt enthält kundenspezifische Regeln: 5-Tage-Woche (Di–Fr + Mo), Aufteilung von Wahlgerichten, Feiertags-Behandlung, etc.

### `wordpress_service.py`

Sendet validiertes JSON an die WordPress REST-API (`/wp/v2/weekly_menu`). Authentifizierung via Application Password. Gibt HTTP-Statuscode zurück (201 = Erfolg).

### `flyer_generator_service.py`

Rendert pro Tagesmenü ein 1080×1080 PNG aus dem Jinja2-HTML-Template (`flyer-template/flyer-template.html`) via `html2image` (headless Chrome). Erkennt automatisch Feiertage/Schließungen anhand von Keywords in `dish_name` und rendert ein alternatives Layout. Ausgabe in `tmp/flyers/tagesmenue_YYYYMMDD.png`.

### `bluesky_service.py`

Postet Text und Bild auf Bluesky via ATProto. Lädt Bild als Blob hoch, erzeugt `app.bsky.embed.images`, postet mit `send_post`. Gibt AT-URI zurück.

### `mastodon_service.py`

Postet Text und Bild auf Mastodon via `Mastodon.py`. Lädt Bild via `media_post` hoch, postet Status mit `media_ids`. Gibt Status-URL zurück.

### `scheduler_service.py`

APScheduler mit SQLite-Jobstore (`queue/scheduler.sqlite`). Plant pro Tag und Plattform je einen `date`-Trigger-Job. Konfiguration: `coalesce=True`, `max_instances=1`, `misfire_grace_time=3600`, `timezone="Europe/Berlin"`. Jobs überleben App-Neustarts.

---

## 6. Benutzeroberfläche

**TLDR:** Streamlit-App in `main.py`. Linearer Workflow: Upload → Analyse → Korrektur → WordPress → Flyer → Planung. Mit Test-Modus für Präsentationen.

### Workflow

1. **Upload & Analyse:** Foto hochladen, "Bild analysieren" klicken. KI gibt `WeeklyMenu` zurück.
2. **Korrektur:** Tabellen-Editor mit `weekday`, `menu_date`, `dish_name`, `is_vegetarian`. Validierung prüft auf exakt 5 eindeutige Tage.
3. **WordPress:** Beitragstitel eingeben, senden. Status 201 = Erfolg.
4. **Flyer:** "Flyer für die Woche generieren": erzeugt 5 PNGs und zeigt sie in Tabs an.
5. **Post-Texte:** Pro Tag-Tab ein `text_area` mit Default-Text. Live-Anzeige der Graphem-Länge (Bluesky-Limit: 300).
6. **Planung:** Posting-Uhrzeit wählen, pro Tag Button "Auf Mastodon und Bluesky posten". Legt 2 Jobs pro Tag an.
7. **Verwaltung:** Liste aller geplanten Posts mit Einzel- und "Alle löschen"-Button.

### Test-Modus

Checkbox "Test-Modus: alle Posts heute planen" überschreibt das Post-Datum aller Tage auf `now + X Minuten`. Nur für Präsentation, Flyer und Texte bleiben unverändert. Default: 3 Minuten Puffer vor dem ersten Post.

### Validierung

Vor WordPress-Versand, Flyer-Generierung und Scheduler-Planung wird geprüft, ob die Tabelle exakt 5 eindeutige `(weekday, menu_date)`-Kombinationen enthält. Wenn nicht: Fehlermeldung.

---

## 7. Scheduler & Posting

**TLDR:** APScheduler speichert Jobs dauerhaft in SQLite. Die App muss zur geplanten Zeit laufen, sonst werden Jobs verworfen (`misfire_grace_time=3600`). Bluesky und Mastodon bieten kein serverseitiges Scheduling über ihre APIs.

### Wie das Scheduling funktioniert

- Jobs werden in `queue/scheduler.sqlite` gespeichert.
- Beim App-Start lädt APScheduler alle Jobs und führt fällige aus (innerhalb von 1 Stunde Grace Period).
- `_publish_to_social` Funktion muss auf Modulebene stehen, damit APScheduler sie nache einem Neustart über ihren Namen wiederfinden kann.
- `replace_existing=True` verhindert doppelte Jobs bei wiederholtem Klick.

### Einschränkungen

- **App muss laufen:** Wenn die App zur geplanten Zeit nicht läuft, wird der Post nicht veröffentlicht. APScheduler kann keine API-Calls ausführen, wenn der Prozess nicht existiert.
- **Kein serverseitiges Scheduling:** Weder Bluesky noch Mastodon bieten über ihre API einen "poste zu Zeitpunkt X"-Parameter. (Mastodon hat `scheduled_at`, aber das Media-Cache-Problem macht es für mehrere Tage im voraus unzuverlässig.)
- **Bluesky-Limit:** 300 Grapheme pro Post. Das UI zeigt die Länge live an und blockt das Planen bei Überschreitung.

### Für 24/7-Betrieb

Für Dauerbetrieb: App auf einem kleinen VPS als Docker Container, o.ä.

---

## 8. Flyer-Template

**TLDR:** HTML/CSS-Template mit Jinja2-Platzhaltern in `flyer-template/`. Rendert 1080×1080 PNGs mit kundenspezifischem Branding. Drei Layout-Varianten: Standard, Feiertag/Schließung, Pause.

### Template-Variablen

| Variable | Beschreibung |
|---|---|
| `template_dir` | Pfad zum Template-Verzeichnis (für Font/SVG-Referenzen) |
| `day_name` | Wochentag |
| `date_str` | Formatiertes Datum (DD.MM.) |
| `menu_items` | Liste der Gerichte |
| `is_closed` | Bool: Tag ist geschlossen |
| `closed_reason` | Grund für Schließung |
| `is_pause` | Bool: Winter-/Sommerpause |

### Assets

- `flyer-template/font/Rokkitt-VariableFont_wght.ttf`
- `flyer-template/svg/` `/fork-left, /fork-right, /vegi-logo, /clash-logo`

---

## 9. Tests

**TLDR:** manuelle Test-Skripte lokal, bisher kein automatisiertes Test-Framework.

---

## 10. Nicht implementiert / zurückgestellt

**TLDR:** Facebook und Instagram (Meta Graph API) sind noch nicht implementiert.

### Meta (Facebook/Instagram)

- Bei späterer Implementierung: neuen `meta_service.py` anlegen, analog zu `bluesky_service.py` / `mastodon_service.py`, und in `scheduler_service.py` in die `platform`-Schleife aufnehmen.

---

## 11. Projektstruktur

```
omni-pub/
├── main.py                      # Streamlit-App
├── config.py                    # Env-Variablen, Pflicht-Prüfung
├── models.py                    # Pydantic-Modelle (WeeklyMenu, DailyMenu, ...)
├── requirements.txt
├── .envrc                       # API-Keys (gitignored)
├── services/
│   ├── vision_llm_service.py    # Bild → KI → WeeklyMenu
│   ├── wordpress_service.py     # WeeklyMenu → WordPress REST-API
│   ├── flyer_generator_service.py # WeeklyMenu → PNG-Flyer
│   ├── bluesky_service.py       # Text+Bild → Bluesky
│   ├── mastodon_service.py      # Text+Bild → Mastodon
│   ├── scheduler_service.py     # APScheduler, SQLite-Jobstore
├── flyer-template/
│   ├── flyer-template.html      # Jinja2-HTML/CSS-Template
│   ├── font/                    # Rokkitt
│   └── svg/                     # Logos, Icons
├── queue/                       # scheduler.sqlite (gitignored)
├── tmp/                         # generierte Flyer (gitignored)
├── tests/                       # Test-Skripte, Testbilder (gitignored)
└── docs/
    ├── projektplan.md
    ├── dokumentation.md
    └── omni-pub-projektskizze.png
```

---

## 12. Bekannte Einschränkungen

- **App muss laufen:** Scheduler ist an den Streamlit-Prozess gebunden. Kein 24/7-Betrieb ohne VPS.
- **Bluesky 300-Grapheme-Limit:** Post-Texte müssen gekürzt werden, das UI warnt, wird aber nicht blockiert.
- **Keine automatisierten Tests:** Nur manuelle Skripte, kein pytest.
- **Kundenspezifisch:** ACF-Schema, Flyer-Branding und Post-Texte sind auf den Kunden zugeschnitten.
- **Kein Meta-Support:** Facebook/Instagram noch nicht implementiert.
- **`sys.path`-Hack:** Mehrere Services fügen das Projekt-Root manuell in `sys.path` ein, damit `from config import ...` funktioniert.
