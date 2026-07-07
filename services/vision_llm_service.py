import os
import sys
from pathlib import Path
from openai import OpenAI

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models import WeeklyMenu


class VisionLLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENAI_API_KEY"),
            default_headers={
                "HTTP-Referer": "https://github.com/jantillidie/omni-pub",
                "X-Title": "Omni Pub"
            }
        )

    def analyze_image(self, base64_str: str) -> WeeklyMenu:
        response = self.client.chat.completions.create(
            model="google/gemini-3.1-flash-lite",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            "Extrahiere aus dem Bild der Wochenkarte die Tage, Daten und Gerichte. "
                            "Die Woche besteht immer aus Dienstag, Mittwoch, Donnerstag, Freitag und dem darauffolgenden Montag. "
                            "Jeder Tag MUSS mindestens einen Eintrag in menu_items enthalten. "
                            "Gibt es an einem Tag kein Mittagstisch (z.B. wegen Feiertag oder Veranstaltung), "
                            "trage als dish_name den Grund ein, z.B. 'kein Mittagstisch, wegen Feiertag' oder 'kein Mittagstisch, wegen Veranstaltung'. "
                            "Setze is_vegetarian in diesem Fall auf false. "
                            "Lass menu_items niemals leer."
                            "Bei Angaben wie z.B. 'wahlweise' oder 'Fleisch/vegetarisch' oder 'auch vegetarisch', die Menüs aufteilen: z.B.: 'Braten mit Rotkohl und Kartoffeln (wahlweise Gemüsebratling)' zu 'Braten mit Rotkohl und Kartoffeln' und 'Gemüsebratling mit Rotkohl und Kartoffeln'. "
                            "Bei Angaben wie (vegan o. vegetarisch), Menü aufteilen: z.B.: 'Mac n Cheese mit Salat (vegan)' und 'Mac n Cheese mit Salat (vegetarisch)' "
                            "Ersetze das 'Kaufmanns-Und' '&' durch ein normales 'und'."
                        )},

                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}}
                    ]
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "weekly_menu",
                    "strict": True,
                    "schema": WeeklyMenu.model_json_schema(),
                }
            }
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenRouter response content is None")
        return WeeklyMenu.model_validate_json(content)
        