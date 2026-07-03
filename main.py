import sys
from pathlib import Path
import base64
import streamlit as st
import pandas as pd
from typing import cast

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.vision_llm_service import VisionLLMService
from services.wordpress_service import send_menu_to_wordpress
from models import WeeklyMenu, WordPressPayload

# Menü umwandeln damit es bearbeitet werden kann
def menu_to_dataframe(menu: WeeklyMenu) -> pd.DataFrame:
    rows = []
    for day in menu.daily_menus:
        for item in day.menu_items:
            rows.append({
                "weekday": day.weekday,
                "menu_date": day.menu_date,
                "dish_name": item.dish_name,
                "is_vegetarian": item.is_vegetarian,
            })
    return pd.DataFrame(rows)

# bearbeitetes Menü zurück in ein Objekt
def dataframe_to_menu(df: pd.DataFrame) -> WeeklyMenu:
    daily_menus = []
    grouped = df.groupby(["weekday", "menu_date"], sort=False)

    for key, group in grouped:
        weekday, menu_date = cast(tuple, key)
        
        menu_items = []
        for _, row in group.iterrows():
            menu_items.append({
                "dish_name": row["dish_name"],
                "is_vegetarian": row["is_vegetarian"],
            })
        daily_menus.append({
            "weekday": weekday,
            "menu_date": menu_date,
            "menu_items": menu_items,
        })

    return WeeklyMenu(daily_menus=daily_menus)

# Seitentitel und Icon im Browser
st.set_page_config(
    page_title="Omni Pub",
    page_icon="🍽️",
    layout="wide",
)

# Titel und Beschreibung
st.title("🍽️ Omni Pub")
st.markdown(
    "Lade ein Foto der Wochenkarte hoch. Die KI extrahiert automatisch "
    "die Gerichte, Daten und Tage. Das Ergebnis kann dann an WordPress "
    "gesendet werden."
)

# Upload
uploaded_file = st.file_uploader(
    "📷 Wochenkarten-Foto hochladen",
    type=["jpg", "jpeg", "png"],
)

# Bild anzeigen und analysieren
if uploaded_file is not None:
    st.sidebar.image(uploaded_file, caption="Hochgeladenes Bild", width="stretch")

    # Bild in Base64 umwandeln
    image_bytes = uploaded_file.getvalue()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")

    st.success(f"✅ Bild geladen ({len(image_bytes):,} Bytes / {len(base64_str):,} Base64-Zeichen)")

    # Bild an KI schicken und analysieren
    if st.button("🤖 Bild analysieren", type="primary"):
        with st.spinner("Bild wird analysiert, das kann ein paar Sekunden dauern"):
            try:
                service = VisionLLMService()
                menu: WeeklyMenu = service.analyze_image(base64_str)

                # Das Ergebnis wird im Session State gespeichert
                st.session_state["menu"] = menu
                st.success("✅ Analyse erfolgreich!")

            except Exception as e:
                st.error(f"⚠️ Fehler bei der KI-Analyse: {e}")

# Ergebnis zeigen
if "menu" in st.session_state:
    weekly_menu: WeeklyMenu = st.session_state["menu"]

    st.divider()
    st.header("📋 Extrahierte Wochenkarte")

    # Zeitspanne zeigen
    col1, col2 = st.columns(2)
    col1.metric("Gültig ab", weekly_menu.menu_start_datetime)
    col2.metric("Gültig bis", weekly_menu.menu_end_datetime)

    # Tagesmenüs zeigen
    # for day in weekly_menu.daily_menus:
    #     with st.expander(f"📅 {day.weekday} — {day.menu_date}", expanded=True):
    #         for item in day.menu_items:
    #             icon = "🌱" if item.is_vegetarian else "🥩"
    #             st.markdown(f"{icon} **{item.dish_name}**")

    st.subheader("📋 Gerichte in der Tabelle bearbeiten")
    
    df = menu_to_dataframe(weekly_menu)
    
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "weekday": st.column_config.MultiselectColumn(
                options=["Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Montag"],
                required=True,
            ),
            "menu_date": st.column_config.TextColumn(
                "Datum (YYYYMMDD)",
                help="Format: YYYYMMDD, z. B. 20260616",
            ),
            "dish_name": st.column_config.TextColumn(
                "Gericht",
                required=True,
            ),
            "is_vegetarian": st.column_config.CheckboxColumn(
                "🌱 Vegi",
                default=False,
            ),
        },
    )


    # JSON zeigen
    # with st.expander("🔧 Rohdaten (JSON)"):
    #     st.json(dataframe_to_menu(edited_df).model_dump())

    # An WordPress Rest API senden
    st.divider()
    st.header("⬆️ An WordPress senden")

    title = st.text_input(
        "Titel des Beitrags",
        value=f"Wochenkarte {weekly_menu.daily_menus[0].menu_date}",
    )

    if st.button("⬆️ An WordPress senden", type="primary"):
        with st.spinner("Validiere und sende an WordPress…"):
            try:
                validated_menu = dataframe_to_menu(edited_df)
                
                payload = WordPressPayload(
                    title=title,
                    status="publish",
                    acf=weekly_menu,
                )

                status_code = send_menu_to_wordpress(payload.model_dump())

                if status_code == 201:
                    st.success("✅ Beitrag erfolgreich in WordPress angelegt.")
                else:
                    st.warning(f"WordPress Status Code: {status_code}.")

            except Exception as e:
                st.error(f"⚠️ Validierung fehlgeschlagen: {e}")
                st.info("Korrigiere die Tabelle oben und klicke erneut auf Senden.")

else:
    st.info("⬆️ Bild hochladen und auf „Bild analysieren“ klicken, um zu starten.")
