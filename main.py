from calendar import day_name
from datetime import datetime, time, timedelta
import base64
import streamlit as st
import pandas as pd
from typing import cast

from services.flyer_generator_service import FlyerGeneratorService
from services.vision_llm_service import VisionLLMService
from services.wordpress_service import send_menu_to_wordpress
from services.scheduler_service import schedule_post, list_scheduled_posts, cancel_post
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

def validate_day_count(df: pd.DataFrame) -> tuple[bool, int]:
    """
    Prüft, ob die Tabelle genau 5 eindeutige (weekday, menu_date)-Kombinationen enthält.
    Gibt (is_valid, count) zurück.
    """
    unique_days = df[["weekday", "menu_date"]].drop_duplicates()
    return len(unique_days) == 5, len(unique_days)


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

    # An WordPress Rest API senden
    st.divider()
    st.header("⬆️ An WordPress senden")

    title = st.text_input(
        "Titel des Beitrags",
        value=f"Wochenkarte {weekly_menu.daily_menus[0].menu_date}",
    )

    if st.button("⬆️ An WordPress senden", type="primary"):
        # Prüfen, ob genau 5 Tage vorhanden sind
        is_valid, day_count = validate_day_count(edited_df)
        if not is_valid:
            st.error(
                f"⚠️ Die Tabelle enthält {day_count} eindeutige Tage, "
                f"erwartet werden genau 5. Bitte prüfe auf doppelte oder "
                f"fehlende Einträge."
            )
        else:
            with st.spinner("Validiere und sende an WordPress…"):                
                try:
                    validated_menu = dataframe_to_menu(edited_df)
                    
                    payload = WordPressPayload(
                        title=title,
                        status="publish",
                        acf=validated_menu,
                    )
    
                    status_code = send_menu_to_wordpress(payload.model_dump())
    
                    if status_code == 201:
                        st.success("✅ Beitrag erfolgreich in WordPress angelegt.")
                    else:
                        st.warning(f"WordPress Status Code: {status_code}.")
    
                except Exception as e:
                    st.error(f"⚠️ Validierung fehlgeschlagen: {e}")
                    st.info("Korrigiere die Tabelle oben und klicke erneut auf Senden.")

    st.divider()
    st.header("Social Media Flyer generieren")
    st.markdown(
        "Generiere Tagesmenü Flyer (1080x1080px) für die Social Media Kanäle"
    )

    if st.button("Flyer für die Woche generieren", type="secondary"):
        is_valid, day_count = validate_day_count(edited_df)
        if not is_valid:
            st.error(
                f"⚠️ Die Tabelle enthält {day_count} eindeutige Tage, "
                f"erwartet werden genau 5. Bitte prüfe auf doppelte oder "
                f"fehlende Einträge."
            )
        else:
            with st.spinner("Generiere Flyer..."):
                try:
                    current_menu = dataframe_to_menu(edited_df)
    
                    generator = FlyerGeneratorService()
                    flyer_paths = generator.generate_all_flyers(current_menu)
    
                    st.session_state["flyer_paths"] = flyer_paths
                    st.success("Flyer erfolgreich generiert und zwischengespeichert")
                except Exception as e:
                    st.error(f"⚠️ Fehler bei der Flyer-Generierung: {e}")

    if "flyer_paths" in st.session_state:
        flyer_paths = st.session_state["flyer_paths"]

        st.subheader("Flyer und Texte prüfen")

        post_time = st.time_input(
            "Tägliche Uhrzeit für den Post",
            value=time(hour=9, minute=0),
            step=timedelta(minutes=30),
            help="Datum und Uhrzeit für den Post",
        )

        # Test-Modus für Präsentation
        test_mode = st.checkbox(
            "🧪 Test-Modus: alle Posts heute planen",
            value=False,
            help="Überschreibt das Post-Datum für alle Tage mit dem heutigen Tag. "
                 "Nur für Tests/Präsentation: die Flyer und Texte bleiben unverändert.",
        )
        test_start_in_minutes = 3
        if test_mode:
            test_start_in_minutes = st.number_input(
                "Erster Post in Minuten:",
                min_value=1,
                max_value=120,
                value=3,
                step=1,
            )
            st.warning(
                f"⚠️ Test-Modus: alle Posts heute, "
                f"erster in {test_start_in_minutes} min."
            )


        is_valid, day_count = validate_day_count(edited_df)
        if not is_valid:
            st.warning(
                f"⚠️ Die Tabelle enthält {day_count} eindeutige Tage, "
                f"erwartet werden genau 5. Flyer-Anzeige und Planung sind "
                f"deaktiviert, bis die Tabelle korrigiert ist."
            )
        else:
            current_menu = dataframe_to_menu(edited_df)
            
            tabs = st.tabs(list(flyer_paths.keys()))
    
    
            for tab, (day_name, img_path) in zip(tabs, flyer_paths.items()):
                with tab:
                    col1, col2 = st.columns([1, 1])
    
                    with col1:
                        st.image(img_path, width="content")
    
                    with col2:
                        st.markdown(f"Social Media Post für {day_name}")
    
                        day_menu = next(d for d in current_menu.daily_menus if d.weekday == day_name)
    
                        dishes_text = ""
                        for item in day_menu.menu_items:
                            icon = "🌱" if item.is_vegetarian else "🥩"
                            dishes_text += f"\n{icon} {item.dish_name}"
    
                        default_text = (
                            f"TEST-BOT / DEVELOPMENT ONLY\n"
                            f"Tagesmenü für {day_name}, den {day_menu.menu_date[6:8]}.{day_menu.menu_date[4:6]}. von 12.00 bis 15.00 Uhr:\n"
                            f"{dishes_text}\n\n"
                            f"Wochenkarte hier -> https://omni-pub-wp-site.indomea.de/\n"
                            f"#tagesmenü #kreuzberg #food"
                        )
    
                        post_text = st.text_area(
                            "Post-Text anpassen",
                            value=default_text,
                            height=250,
                            key=f"text_{day_name}"
                        )
    
                        st.caption(f"{len(post_text)} / 300 Graphemen (Bluesky-Limit)")
    
                        # Post-Datum berechnen
                        if test_mode:
                            post_datetime = datetime.now() + timedelta(
                                minutes=int(test_start_in_minutes)
                            )
                        else:
                            post_date = datetime.strptime(day_menu.menu_date, "%Y%m%d").date()
                            post_datetime = datetime.combine(post_date, post_time)

                        st.caption(
                            f"Geplant für: {post_datetime.strftime('%d.%m.%Y um %H:%M')} Uhr"
                        )

    
                        if st.button(
                            f"⬆️ Auf Mastodon und Bluesky posten ({day_name})",
                            key=f"btn_{day_name}",
                            type="primary",
                        ):
                            # Bluesky-Limit: 300 'Grapheme'
                            if len(post_text) > 300:
                                st.error(
                                    f"⚠️ Post-Text ist {len(post_text)} 'Grapheme' lang. "
                                    f"Bluesky erlaubt maximal 300. Bitte kürzen."
                                )
                            else:
                                try:
                                    job_ids = schedule_post(
                                        day_name=day_name,
                                        text=post_text,
                                        image_path=img_path,
                                        post_datetime=post_datetime,
                                    )
                                    st.success(
                                        f"✅ {day_name} geplant für "
                                        f"{post_datetime.strftime('%d.%m.%Y um %H:%M')} Uhr "
                                        f"auf Bluesky und Mastodon."
                                    )
                                    st.info(
                                        "⚠️ Die App muss zur geplanten Zeit laufen, "
                                        "damit die Posts veröffentlicht werden können."
                                    )
                                except Exception as e:
                                    st.error(f"⚠️ Fehler beim Planen: {e}")
                                    
        # Geplante Posts anzeigen
        st.divider()
        st.subheader("📅 Geplante Posts")
        
        try:
            scheduled = list_scheduled_posts()
            if scheduled:
                # Nach Datum sortieren
                scheduled.sort(key=lambda j: j["next_run"])

                # "Alle löschen" Button
                col_del_all, _ = st.columns([1, 3])
                with col_del_all:
                    if st.button("🗑️ Alle geplanten Posts löschen", type="secondary"):
                        for job in scheduled:
                            cancel_post(job["id"])
                        st.success("✅ Alle geplanten Posts gelöscht.")
                        st.rerun()

                # Tabelle mit einzelnen Lösch-Buttons
                for job in scheduled:
                    with st.container():
                        col_info, col_cancel, _ = st.columns([3, 1, 1])
                        with col_info:
                            # Job-ID lesbar machen
                            label = job["id"].replace("_", " ", 1).split("_T")[0]
                            st.write(
                                f"• {label} → "
                                f"{job['next_run'].strftime('%d.%m.%Y %H:%M')}"
                            )
                        with col_cancel:
                            if st.button("🗑️", key=f"del_{job['id']}"):
                                if cancel_post(job["id"]):
                                    st.success(f"✅ Post gelöscht: {label}")
                                else:
                                    st.info(f"Post war nicht mehr vorhanden: {label}")
                                st.rerun()
            else:
                st.info("Keine Posts geplant.")
        except Exception as e:
            st.warning(f"Scheduler-Status konnte nicht geladen werden: {e}")

else:
    st.info("⬆️ Bild hochladen und auf „Bild analysieren“ klicken, um zu starten.")

# HELL ON EARTH....
