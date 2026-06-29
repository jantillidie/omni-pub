from dotenv import load_dotenv # TODO: resolve module not found error
import os

load_dotenv()

WP_API_URL = os.getenv("WP_API_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")  # App PW
AI_API_KEY = os.getenv("AI_API_KEY")

if not all([WP_API_URL, WP_USERNAME, WP_PASSWORD, AI_API_KEY]):
    raise ValueError("Fehlende Variablen in der .env!")
