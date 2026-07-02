from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date, timedelta
from typing import Any
import re

class MenuItem(BaseModel):
    model_config = {"extra": "forbid"}
    dish_name: str = Field(..., description="Name des Gerichts")
    is_vegetarian: bool = Field(..., description="True bei vegetarisch/vegan, sonst False")

class DailyMenu(BaseModel):
    model_config = {"extra": "forbid"}
    weekday: str = Field(..., description="Wochentag")
    menu_date: str = Field(..., description="Datum des Tagesmenüs")
    menu_items: list[MenuItem] = Field(..., min_length=1, description="Liste der Gerichte an diesem Tag")

    @field_validator("menu_date", mode="before")
    @classmethod
    def normalize_and_format_date(cls, value: Any) -> str:
        """
        Normalisiert das Datum aus der KI / dem UI in das native ACF-Format (YYYYMMDD).
        Akzeptiert DD.MM.YYYY, DD/MM/YYYY, YYYYMMDD und datetime.date Objekte.
        """
        # Fall 1: KI/UI liefert ein echtes date/datetime Objekt
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y%m%d")
        
        if isinstance(value, str):
            value = value.strip()
            
            # Fall 2: Bereits im reinen ACF-Format "20260630"
            if re.match(r"^\d{8}$", value):
                return value
                
            # Fall 3: Menschenlesbare Formate mit Punkten, Schrägstrichen oder Bindestrichen
            for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    return parsed_date.strftime("%Y%m%d")
                except ValueError:
                    continue
                    
        raise ValueError(
            f"Ungültiges Datumsformat: '{value}'. "
            f"Erwartet wird DD.MM.YYYY, DD/MM/YYYY oder YYYYMMDD."
        )

class WeeklyMenu(BaseModel):
    model_config = {"extra": "forbid"}
    menu_start_datetime: str = Field(default="", description="Gültigkeitsbeginn (automatisch berechnet aus Tagesdaten).")
    menu_end_datetime: str = Field(default="", description="Gültigkeitsende (automatisch berechnet aus Tagesdaten).")
    daily_menus: list[DailyMenu] = Field(..., min_length=5, max_length=5)

    @model_validator(mode="after")
    def compute_menu_datetimes(self) -> "WeeklyMenu":
        """
        Berechnet menu_start_datetime und menu_end_datetime automatisch aus den Tagesdaten.
        - Start: erster Menütag - 1 Tag, um 14:53 Uhr
        - Ende: letzter Menütag, um 14:53 Uhr
        """
        parsed_dates = [
            datetime.strptime(dm.menu_date, "%Y%m%d") for dm in self.daily_menus
        ]
        first_date = min(parsed_dates)
        last_date = max(parsed_dates)

        self.menu_start_datetime = (first_date - timedelta(days=1)).strftime("%Y-%m-%d 14:53:00")
        self.menu_end_datetime = last_date.strftime("%Y-%m-%d 14:53:00")
        return self

class WordPressPayload(BaseModel):
    title: str = Field(..., description="Titel des WordPress-Beitrags.")
    status: str = Field("publish", description="Beitragsstatus.")
    acf: WeeklyMenu = Field(..., description="Die eigentlichen ACF-Felder für die Wochenkarte.") # ACF = AdvancedCustomFields: WordPress Custom Post Types Plugin
