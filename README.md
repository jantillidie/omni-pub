# 📋 Omni Pub

Ein KI-gestützter Omnichannel-Marketing-Automations-Service für die Gastronomie. Das System digitalisiert handschriftliche Wochenkarten per Foto, stellt sie zur manuellen Korrektur in einer Weboberfläche bereit und verteilt die Daten anschließend automatisiert an WordPress sowie verschiedene Social-Media-Kanäle.

---

## 🎯 Projektziel

Dieses Projekt entsteht im Rahmen eines 3-wöchigen Zwischenprojekts. Ziel ist es, den manuellen Workflow bei der Vermarktung von gastronomischen Speisekarten zu automatisieren. 

### Geplanter Datenfluss:
1. **Input:** Der Nutzer lädt ein Foto der handschriftlichen Karte in einer Benutzeroberfläche hoch.
2. **Analyse:** Eine Vision-LLM (KI) extrahiert die Gerichte und Preise als strukturiertes JSON.
3. **Review:** Der Nutzer prüft und korrigiert die Daten in der Web-GUI (Human-in-the-Loop).
4. **Distribution:** - Reine Textdaten fließen zeitgesteuert in die Custom Fields (ACF) von **WordPress**.
   - Das System generiert automatisch visuelle Bilddateien (PNG) aus einem HTML/CSS-Template.
   - Eine zeitgesteuerte Warteschlange postet das PNG und Text zu festen Zeiten an **Mastodon**, **Bluesky** und **Meta (Facebook/Instagram)**.

---

## 🗺️ Systemarchitektur

Die visuelle Projektskizze und der detaillierte Umsetzungsplan liegen im Dokumentations-Ordner:
👉 `[Zum Projektplan & Systemarchitektur](docs/projektplan.md)`

---

## 🛠️ Geplante Technologien

- **Sprache:** Python 🐍
- **Frameworks & APIs:** Streamlit (Web-GUI), OpenAI/Anthropic API (Vision LLM), WordPress REST-API, ATProto (Bluesky), Mastodon.py, Meta Graph API.
- **Design & Rendering:** HTML/CSS & html2image.

---

## 🚀 Installation & Setup (In Vorbereitung)

> ⚠️ **Hinweis:** Das Projekt befindet sich aktuell in der Konzeptionsphase. Die Installationsanweisungen und Abhängigkeiten werden nach dem Setup der Entwicklungsumgebung hier ergänzt.

### Geplante Schritte:
1. Repository klonen: `git clone <repo-url>`
2. Virtuelle Umgebung erstellen: `python -m venv .venv`
3. Abhängigkeiten installieren: `pip install -r requirements.txt`
4. `.env`-Datei mit API-Schlüsseln anlegen.