from pathlib import Path
from jinja2 import Template
from html2image import Html2Image
from models import DailyMenu, WeeklyMenu

class FlyerGeneratorService:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.template_path = self.project_root / "flyer-template" / "flyer-template.html"
        self.output_dir = self.project_root / "tmp" / "flyers"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.h2i = Html2Image(
            browser='chrome',
            custom_flags=[
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--allow-file-access-from-files',
                '--hide-scrollbars',
                '--default-background-color=000000',
                '--password-store=basic', # KeePassXC specific
                '--disable-features=GlobalShortcutsPortal' # D-Bus specific
            ],
            output_path=str(self.output_dir)
        )

    # Prüft ob an dem Tag geschlossen ist
    def _detect_closed_state(self, day_menu: DailyMenu) -> tuple[bool, str]:
        for item in day_menu.menu_items:
            name = item.dish_name.lower()
            if any(word in name for word in ["kein mittagstisch", "geschlossen", "feiertag"]):
                return True, item.dish_name
        return False, ""

    # Generiert Flyer für einzelnen Tag, speichert als PNG, gibt Pfad zum PNG zurück
    def generate_flyer_for_day(self, day_menu: DailyMenu, date_str: str) -> str:
        with open(self.template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)

        is_closed, closed_reason = self._detect_closed_state(day_menu)

        formatted_date = date_str
        if len(date_str) == 8:
            formatted_date = f"{date_str[6:8]}.{date_str[4:6]}."

        template_dir_path = self.project_root / "flyer-template"

        render_data = {
            "template_dir": template_dir_path.as_posix(),
            "day_name": day_menu.weekday,
            "date_str": formatted_date,
            "menu_items": day_menu.menu_items,
            "is_closed": is_closed,
            "closed_reason": closed_reason,
            "is_pause": False,
        }

        rendered_html = template.render(**render_data)

        temp_html_path = template_dir_path / f"temp_{day_menu.weekday}.html"
        with open(temp_html_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(rendered_html)

        filename = f"tagesmenue_{day_menu.menu_date}.png"

        self.h2i.screenshot(
            html_str=rendered_html,
            save_as=filename,
            size=(1080, 1080),
        )

        if temp_html_path.exists():
            temp_html_path.unlink()

        return str(self.output_dir / filename)

    # Generiert Flyer für die Woche, gibt Dict zurück { "Tag": "pfad/zum/flyer", ...}
    def generate_all_flyers(self, weekly_menu: WeeklyMenu) -> dict[str, str]:
        generated_paths = {}
        for day in weekly_menu.daily_menus:
            path = self.generate_flyer_for_day(day, day.menu_date)
            generated_paths[day.weekday] = path
        return generated_paths
        