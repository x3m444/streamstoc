# app.py
# Main Streamlit application

import streamlit as st
from config import PAGE_TITLE, PAGE_LAYOUT, MENU_OPTIONS
from auth import check_password
from database import get_engine, check_db_integrity
from forms import show_data_entry_form, show_expedition_form
from reports import show_reports_section

# Page configuration
st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)

# Authentication check
if not check_password():
    st.stop()

# Database integrity check
engine = get_engine()
db_safe, db_info = check_db_integrity(engine)

if not db_safe:
    st.error("🚨 EROARE CRITICĂ: TABELUL 'list963' LIPSEȘTE!")
    st.markdown(f"**Detaliu Tehnic:** `{db_info}`")
    st.warning("⚠️ Baza de date nu a fost găsită pe disc.")
    st.info("Sistemul a fost oprit pentru a preveni introducerea de date într-o bază goală.")
    st.stop()
else:
    st.sidebar.success(f"✅ Bază activă: {db_info} înregistrări")

# Navigation menu
choice = st.sidebar.radio("Navigare", MENU_OPTIONS)

# Route to appropriate module
if choice == "📥 Introducere Date":
    show_data_entry_form()

elif choice == "📦 Expediție":
    show_expedition_form()

elif choice == "📊 Super Vizualizare":
    # Import here to avoid circular imports
    from super_viz import show_super_visualization
    show_super_visualization()

elif choice == "📊 Rapoarte & Export":
    show_reports_section()