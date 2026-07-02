import os
from pathlib import Path

# .env-Datei laden, falls vorhanden (für Nutzer ohne direnv/.envrc).
# Wenn keine .env existiert, passiert nichts — dann müssen die Variablen
# über die Shell / direnv / .envrc gesetzt sein.
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

WP_API_URL = os.environ.get("WP_API_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")  # Username, not App name!
WP_PASSWORD = os.environ.get("WP_PASSWORD")  # App PW
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not all([WP_API_URL, WP_USERNAME, WP_PASSWORD, OPENAI_API_KEY]):
    raise ValueError(
        "Fehlende Umgebungsvariablen! "
        "Benötigt: WP_API_URL, WP_USERNAME, WP_PASSWORD, OPENAI_API_KEY. "
        "Lege eine .env-Datei an oder nutze .envrc / direnv."
    )