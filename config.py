import os
from dotenv import load_dotenv

load_dotenv()

WP_API_URL = os.environ["WP_API_URL"]
WP_USERNAME = os.environ["WP_USERNAME"] # Username, not App name!
WP_PASSWORD = os.environ["WP_PASSWORD"]  # App PW
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

if not all([WP_API_URL, WP_USERNAME, WP_PASSWORD, OPENAI_API_KEY]):
    raise ValueError("Fehlende Variablen in der .env!")
