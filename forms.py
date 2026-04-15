# forms.py
# Form handling functions

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database import get_engine, insert_cable_record, get_locations_for_ship
from utils import validate_numeric_input, add_export_buttons
from config import DEFAULT_SHIP, DEFAULT_TRAGATOR, TIMEZONE_OFFSET

def initialize_session_state():
    """Initialize session state variables"""
    if 'last_nava' not in st.session_state:
        st.session_state['last_nava'] = DEFAULT_SHIP
    if 'last_tragator' not in st.session_state:
        st.session_state['last_tragator'] = DEFAULT_TRAGATOR

    # Refresh date if needed
    current_date = (datetime.utcnow() + TIMEZONE_OFFSET).date()
    if 'last_data' not in st.session_state or st.session_state['last_data'] < current_date:
        st.session_state['last_data'] = current_date

def show_data_entry_form():
    """Display and handle data entry form."""
    # Main title for the data entry section.
    st.subheader("📥 Introducere Rapidă Cabluri")

    # Initialize session state with default values for ship, operator and date.
    initialize_session_state()

    # Settings expander
    with st.expander("⚙️ Setări Implicite (Navă / Trăgător / Dată)"):
        nava_val = st.number_input("Navă", value=int(st.session_state['last_nava']), step=1)
        tragator_val = st.text_input("Trăgător", value=st.session_state['last_tragator'])

        data_val = st.date_input("Data Înregistrării", value=st.session_state['last_data'])

        # Update session state
        st.session_state['last_nava'] = nava_val
        st.session_state['last_tragator'] = tragator_val
        st.session_state['last_data'] = data_val

    # Get location suggestions
    engine = get_engine()
    suggestions = get_locations_for_ship(engine, nava_val)

    # Main form
    with st.form("add_form", clear_on_submit=True):
        nr_lista = st.text_input("📄 Nr Lista")
        id_final = st.text_input("🆔 ID Lista")

        st.write(f"📍 Locații nava {nava_val}:")
        loc_select = st.selectbox("Caută/Alege locație", options=[""] + suggestions)
        loc_manual = st.text_input("Sau scrie locația nouă:")

        loc_final = loc_manual.strip() if loc_manual.strip() else loc_select

        lungime_raw = st.text_input("📏 Lungime (m)")
        nr_cabluri_raw = st.text_input("🔢 Nr Cabluri")

        st.markdown("---")
        submitted = st.form_submit_button("🚀 SALVEAZĂ ÎN BAZA DE DATE", width="stretch")

        if submitted:
            if not all([nr_lista.strip(), id_final.strip(), loc_final, lungime_raw.strip(), nr_cabluri_raw.strip()]):
                st.error("⚠️ Toate câmpurile sunt obligatorii!")
                return

            try:
                val_l = validate_numeric_input(lungime_raw, "Lungime")
                val_c = validate_numeric_input(nr_cabluri_raw, "Nr Cabluri")

                # Insert record
                data = {
                    'nava': nava_val,
                    'nr_lista': nr_lista.strip(),
                    'id_lista': id_final.strip(),
                    'locatie': loc_final,
                    'lungime': val_l,
                    'nr_cabluri': val_c,
                    'data': data_val,
                    'tragator': tragator_val,
                    'trimis': False
                }

                insert_cable_record(engine, data)

                st.success(f"✅ Salvat cu succes: {id_final} pe data {data_val.strftime('%d.%m.%Y')}")
                st.rerun()

            except ValueError as e:
                st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"❌ Eroare: {e}")

    # Show today's entries below the data entry form.
    show_today_entries(engine, data_val)


def show_expedition_form():
    """Display expedition management interface."""
    # Section title for shipment management.
    st.header("🚢 Gestiune Expediție - Nava 978")

    # Expedition form parameters: date and folder name.
    col1, col2 = st.columns(2)
    with col1:
        data_expediere = st.date_input("📅 Data Expediției", datetime.now().date())
    with col2:
        nume_dosar = st.text_input("📁 Nume Dosar / Destinație", placeholder="Ex: FWD-SEC1")

    # Get available records
    engine = get_engine()
    query = text("""
        SELECT "Nr Lista", "Locatie", "Lungime", "Nr Cabluri", "ID"
        FROM list963
        WHERE ("Trimis" IS NOT TRUE) AND ("Rework" IS NOT TRUE) AND "Nava" = 978
        ORDER BY "Nr Lista" ASC
    """)

    df_disp = pd.read_sql(query, engine)

    if not df_disp.empty:
        df_disp["display"] = df_disp["Nr Lista"] + " (" + df_disp["Locatie"] + ")"
        selectate = st.multiselect("🔎 Marcare liste noi:", options=df_disp["display"].tolist())

        if selectate:
            df_f = df_disp[df_disp["display"].isin(selectate)].copy()

            if st.button("🚀 CONFIRMĂ ȘI MARCHEAZĂ", width="stretch"):
                if not nume_dosar:
                    st.error("⚠️ Introdu numele dosarului!")
                    return

                try:
                    ids = df_f["ID"].tolist()
                    with engine.connect() as conn:
                        conn.execute(
                            text('UPDATE list963 SET "Trimis"=TRUE, "Data trimisa"=:data, "Dosar"=:dosar WHERE "ID" = ANY(:ids)'),
                            {"data": str(data_expediere), "dosar": nume_dosar, "ids": ids}
                        )
                        conn.commit()
                    st.success("✅ Liste marcate pentru expediție!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Eroare: {e}")

    # Show today's shipments
    show_today_shipments(engine, data_expediere)

def show_today_shipments(engine, data_expediere):
    """Show shipments for selected date."""
    # Query all records shipped on the selected expedition date.
    query_zi = text("""
        SELECT "Nr Lista", "Locatie", "Lungime", "Nr Cabluri", "Dosar"
        FROM list963
        WHERE "Data trimisa" = :data_expediere AND "Nava" = 978
        ORDER BY "Dosar" ASC, "Locatie" ASC
    """)

    df_zi = pd.read_sql(query_zi, engine, params={"data_expediere": data_expediere})

    if not df_zi.empty:
        df_zi["Lungime"] = pd.to_numeric(df_zi["Lungime"], errors='coerce').fillna(0)
        df_zi["Nr Cabluri"] = pd.to_numeric(df_zi["Nr Cabluri"], errors='coerce').fillna(0)

        dosare_unice = ", ".join(df_zi['Dosar'].unique())

        st.markdown(f"""
        <div style="
            border: 1px solid #464b5d;
            border-radius: 8px;
            padding: 15px;
            background-color: #0e1117;
            margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #808495; font-size: 0.9rem; font-weight: bold;">📊 SITUAȚIE ZI: {data_expediere.strftime('%d.%m.%Y')}</span>
                <span style="color: #00d4ff; font-size: 1.1rem; font-weight: bold;">{len(df_zi)} Liste | {df_zi['Lungime'].sum():,.1f} m | {df_zi['Nr Cabluri'].sum()} Cab</span>
            </div>
            <div style="margin-top: 8px; border-top: 1px solid #1d2129; padding-top: 8px;">
                <span style="color: #525866; font-size: 0.85rem;">📁 Dosare active: </span>
                <span style="color: #d1d5db; font-size: 0.85rem; font-style: italic;">{dosare_unice}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Export functionality would go here
        if st.button("🖨️ GENEREAZĂ BORDEROU EXCEL", width="stretch"):
            generate_borderou_excel(df_zi, data_expediere)

def generate_borderou_excel(df_zi, data_expediere):
    """Generate Excel borderou for shipments using the shared export utility."""
    summary = {
        "METRI": int(df_zi["Lungime"].sum()),
        "CAB": int(df_zi["Nr Cabluri"].sum()),
        "LISTE": len(df_zi)
    }
    filename = f"Borderou_Expeditie_{data_expediere.strftime('%d-%m-%Y')}"
    add_export_buttons(df_zi, filename, summary=summary)


def show_today_entries(engine, selected_date):
    """Display today's entries under the data entry form."""
    query = text("""
        SELECT "Nr Lista", "Locatie", "Nr Cabluri", "Lungime", "ID Lista"
        FROM list963
        WHERE "Data" = :selected_date
        ORDER BY "Locatie" ASC, "Nr Lista" ASC
    """)

    df_today = pd.read_sql(query, engine, params={"selected_date": selected_date})

    if df_today.empty:
        st.info(f"ℹ️ Nicio intrare pentru data {selected_date.strftime('%d.%m.%Y')}.")
        return

    df_today["Lungime"] = pd.to_numeric(df_today["Lungime"], errors='coerce').fillna(0)
    df_today["Nr Cabluri"] = pd.to_numeric(df_today["Nr Cabluri"], errors='coerce').fillna(0)

    total_m = df_today["Lungime"].sum()
    total_c = int(df_today["Nr Cabluri"].sum())
    total_l = len(df_today)

    st.markdown(f"### 📋 Intrări pentru {selected_date.strftime('%d.%m.%Y')}")
    st.markdown(f"**{total_l} liste** | **{total_m:,.1f} m** | **{total_c} cabluri**")

    df_display = df_today.copy()
    df_display["Nr Lista"] = df_display["Nr Lista"].astype(int)
    df_display["Nr Cabluri"] = df_display["Nr Cabluri"].astype(int)
    df_display["Lungime"] = df_display["Lungime"].astype(int).astype(str) + " m"
    df_display = df_display.rename(columns={"Locatie": "Locație"})

    headers_html = "".join([
        f'<th style="text-align:center;padding:8px 12px;background-color:#1a1c23;'
        f'color:#af7c4c;font-size:12px;font-weight:400;text-transform:uppercase;'
        f'border-bottom:2px solid #262730;">{col}</th>'
        for col in df_display.columns
    ])
    rows_html = "".join([
        "<tr>" + "".join([
            f'<td style="text-align:center;padding:7px 12px;color:#dad4bd;'
            f'font-size:13px;border-bottom:1px solid #262730;">{val}</td>'
            for val in row
        ]) + "</tr>"
        for _, row in df_display.iterrows()
    ])
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;background-color:#111111;">'
        f'<thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table>',
        unsafe_allow_html=True
    )