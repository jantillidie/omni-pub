from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class WeekdayEnum(str, Enum):
    MONTAG = "Montag"
    DIENSTAG = "Dienstag"
    MITTWOCH = "Mittwoch"
    DONNERSTAG = "Donnerstag"
    FREITAG = "Freitag"

class MenuItem(BaseModel):
    dish_name: str = Field(..., description="Name des Gerichts.")
    is_vegetarian: bool = Field(..., description="True bei vegetarisch/vegan, sonst False.")

class DailyMenu(BaseModel):
    weekday: WeekdayEnum = Field(..., description="Wochentag.")
    menu_date: str = Field(..., description="Datum im Format dd/mm/yyyy.")
    menu_items: List[MenuItem] = Field(..., description="Gerichte des Tages.")

class WeeklyMenu(BaseModel):
    menu_start_datetime: str = Field(..., description="Gültigkeitsbeginn im Format YYYY-MM-DD HH:MM:SS.")
    menu_end_datetime: str = Field(..., description="Gültigkeitsende im Format YYYY-MM-DD HH:MM:SS.")
    daily_menus: List[DailyMenu] = Field(..., min_length=5, max_length=5)