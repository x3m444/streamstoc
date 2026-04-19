# reports.py
# Report generation functions for the Streamlit dashboard.
# Each function reads data from the database, formats it, and renders a report.

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine
from utils import add_export_buttons, calculate_summary
from config import REPORT_TABS


@st.cache_data(ttl=30)
def _fetch_daily():
    return pd.read_sql(text("""
        SELECT "Nr Lista", "Locatie", "Lungime", "Nr Cabluri"
        FROM list963 WHERE "Data" = CURRENT_DATE
        ORDER BY "Locatie" ASC, "Nr Lista" ASC
    """), get_engine())

@st.cache_data(ttl=30)
def _fetch_weekly():
    sumar = pd.read_sql(text("""
        SELECT COALESCE(SUM("Lungime"),0) as m_sapt,
               COALESCE(SUM("Nr Cabluri"),0) as c_sapt, COUNT(*) as l_sapt
        FROM list963 WHERE "Data" >= DATE_TRUNC('week', CURRENT_DATE)
    """), get_engine())
    zile = pd.read_sql(text("""
        SELECT "Data", SUM("Lungime") as metri, SUM("Nr Cabluri") as cabluri, COUNT(*) as liste
        FROM list963 GROUP BY "Data" ORDER BY "Data" DESC
    """), get_engine())
    return sumar, zile

@st.cache_data(ttl=30)
def _fetch_monthly():
    sumar = pd.read_sql(text("""
        SELECT COALESCE(SUM("Lungime"),0) as total_m,
               COALESCE(SUM("Nr Cabluri"),0) as total_c, COUNT(*) as total_l
        FROM list963 WHERE "Data" >= CURRENT_DATE - INTERVAL '30 days'
    """), get_engine())
    saptamani = pd.read_sql(text("""
        SELECT EXTRACT(YEAR FROM "Data")::INT as an, EXTRACT(WEEK FROM "Data")::INT as nr_sapt,
               SUM("Lungime") as metri, SUM("Nr Cabluri") as cabluri, COUNT(*) as liste
        FROM list963 GROUP BY an, nr_sapt ORDER BY an DESC, nr_sapt DESC
    """), get_engine())
    return sumar, saptamani

@st.cache_data(ttl=30)
def _fetch_ship():
    return pd.read_sql(text("""
        SELECT "Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri",
               "Data", "Tragator", "Trimis", "Data trimisa", "Nava",
               "Dosar", "Rework", "Data Rework", "Ore Rework"
        FROM list963 WHERE "Nava" = 978
    """), get_engine())

@st.cache_data(ttl=30)
def _fetch_shipped():
    return pd.read_sql(text("""
        SELECT "Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri",
               TO_CHAR("Data trimisa", 'DD.MM.YY') as "Data Trimisă", "Dosar"
        FROM list963 WHERE "Nava" = 978 AND "Trimis" = true
    """), get_engine())

@st.cache_data(ttl=30)
def _fetch_hala():
    return pd.read_sql(text("""
        SELECT "Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri", "Rework"
        FROM list963 WHERE "Nava" = 978 AND "Trimis" = false
    """), get_engine())

@st.cache_data(ttl=30)
def _fetch_rework():
    return pd.read_sql(text("""
        SELECT "Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri",
               TO_CHAR("Data Rework", 'DD.MM.YY') as "Data RWK", "Ore Rework"
        FROM list963 WHERE "Nava" = 978 AND "Rework" = true
    """), get_engine())

@st.cache_data(ttl=30)
def _fetch_all_time():
    return pd.read_sql(text("""
        SELECT "Nava" as nava, SUM("Lungime") as lungime_totala,
               SUM("Nr Cabluri") as cabluri_total, COUNT(*) as numar_liste
        FROM list963 GROUP BY "Nava" ORDER BY "Nava" ASC
    """), get_engine())

def show_reports_section():
    """Main reports section with tabs."""
    # This is the root view for all reporting tabs.
    st.subheader("📊 Panou Central Monitorizare")

    with st.expander("🔍 ACCESEAZĂ TOATE RAPOARTELE PROIECTULUI", expanded=True):
        tabs = st.tabs(REPORT_TABS)

        with tabs[0]:  # Azi
            show_daily_report()
        with tabs[1]:  # Săptămână
            show_weekly_report()
        with tabs[2]:  # Lună
            show_monthly_report()
        with tabs[3]:  # Navă
            show_ship_report()
        with tabs[4]:  # Trimise
            show_shipped_report()
        with tabs[5]:  # Hală
            show_hala_report()
        with tabs[6]:  # Rework
            show_rework_report()
        with tabs[7]:  # All Time
            show_all_time_report()

@st.fragment
def show_daily_report():
    """Show today's activity report"""
    st.markdown("<h5 style='margin:0px;'>📍 Activitate Curentă</h5>", unsafe_allow_html=True)

    try:
        df = _fetch_daily()

        if not df.empty:
            # Summarize daily results for UI and export.
            total_m = int(df['Lungime'].sum())
            total_c = int(df['Nr Cabluri'].sum())
            total_l = len(df)

            summary = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}

            # Status bar
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:8px; border-radius:4px; border-left:4px solid #fff9c4; display:flex; justify-content:space-around; align-items:center; border:0.1px solid #333; margin-bottom:10px;">
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">METRI</span><br><b style="color:#fff9c4; font-size:16px;">{total_m}</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">CABLURI</span><br><b style="color:#fff9c4; font-size:16px;">{total_c}</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">LISTE</span><br><b style="color:#fff9c4; font-size:16px;">{total_l}</b></div>
                </div>
            """, unsafe_allow_html=True)

            # Dataframe display
            df_display = df.copy()
            df_display.columns = ["NR", "LOCAȚIE", "METRI", "CAB"]

            st.dataframe(
                df_display,
                hide_index=True,
                width="stretch",
                column_config={
                    "NR": st.column_config.NumberColumn("NR", format="%d"),
                    "LOCAȚIE": st.column_config.TextColumn("LOCAȚIE"),
                    "METRI": st.column_config.NumberColumn("METRI", format="%d m"),
                    "CAB": st.column_config.NumberColumn("CAB", format="%d")
                }
            )

            # Export
            add_export_buttons(df_display, "Raport_Azi", summary=summary)
        else:
            st.info("ℹ️ Nicio listă introdusă astăzi.")

    except Exception as e:
        st.error(f"Eroare la încărcarea datelor: {e}")

@st.fragment
def show_weekly_report():
    """Show weekly activity report"""
    st.markdown("<h4 style='margin:0px;'>📅 Jurnal Activitate Zilnică</h4>", unsafe_allow_html=True)

    try:
        df_sumar, df_zile = _fetch_weekly()

        # Status bar
        if not df_sumar.empty:
            ms = int(df_sumar['m_sapt'].iloc[0])
            cs = int(df_sumar['c_sapt'].iloc[0])
            ls = int(df_sumar['l_sapt'].iloc[0])

            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:8px; border-radius:4px; border-left:4px solid #4db6ac; display:flex; justify-content:space-around; align-items:center; border:0.1px solid #333; margin-bottom:10px;">
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">SĂPTĂMÂNA ASTA</span><br><b style="color:#4db6ac; font-size:15px;">{ms} m</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">CABLURI</span><br><b style="color:#4db6ac; font-size:15px;">{cs}</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">LISTE</span><br><b style="color:#4db6ac; font-size:15px;">{ls}</b></div>
                </div>
            """, unsafe_allow_html=True)

        # Data display
        if not df_zile.empty:
            df_final = df_zile.copy()
            df_final.columns = ["DATA", "METRI", "CAB", "LISTE"]
            df_final["DATA"] = pd.to_datetime(df_final["DATA"]).dt.date

            st.dataframe(
                df_final,
                hide_index=True,
                width="stretch",
                column_config={
                    "DATA": st.column_config.DateColumn("DATA", format="DD.MM.YY"),
                    "METRI": st.column_config.NumberColumn("METRI", format="%d m"),
                    "CAB": st.column_config.NumberColumn("CAB", format="%d"),
                    "LISTE": st.column_config.NumberColumn("LISTE", format="%d")
                }
            )

            # Export
            date_sumar = {
                "METRI": int(df_final["METRI"].sum()),
                "CAB": int(df_final["CAB"].sum()),
                "LISTE": int(df_final["LISTE"].sum())
            }
            add_export_buttons(df_final, "Istoric_Zilnic", summary=date_sumar)

    except Exception as e:
        st.error(f"Eroare la procesare: {e}")

@st.fragment
def show_monthly_report():
    """Show monthly activity report"""
    st.markdown("<h4 style='margin:0px;'>🌙 Istoric pe Săptămâni</h4>", unsafe_allow_html=True)

    try:
        df_sumar, df_ist = _fetch_monthly()

        # Summary display
        if not df_sumar.empty:
            m_30 = int(df_sumar['total_m'].iloc[0])
            c_30 = int(df_sumar['total_c'].iloc[0])
            l_30 = int(df_sumar['total_l'].iloc[0])

            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:8px; border-radius:4px; border-left:4px solid #ce93d8; display:flex; justify-content:space-around; align-items:center; border:0.1px solid #333; margin-bottom:10px;">
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">ULTIMELE 30 ZILE</span><br><b style="color:#ce93d8; font-size:15px;">{m_30} m</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">CABLURI</span><br><b style="color:#ce93d8; font-size:15px;">{c_30}</b></div>
                    <div style="width:1px; height:15px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:9px;">LISTE</span><br><b style="color:#ce93d8; font-size:15px;">{l_30}</b></div>
                </div>
            """, unsafe_allow_html=True)

        # Weekly data display
        if not df_ist.empty:
            df_display = df_ist.copy()
            df_display["SĂPTĂMÂNĂ"] = "S " + df_display["nr_sapt"].astype(str) + " - " + df_display["an"].astype(str)
            df_display = df_display[["SĂPTĂMÂNĂ", "metri", "cabluri", "liste"]]
            df_display.columns = ["SĂPTĂMÂNĂ", "METRI", "CABLURI", "LISTE"]

            st.dataframe(
                df_display,
                hide_index=True,
                width="stretch",
                column_config={
                    "SĂPTĂMÂNĂ": st.column_config.TextColumn("SĂPTĂMÂNĂ"),
                    "METRI": st.column_config.NumberColumn("METRI", format="%d m"),
                    "CABLURI": st.column_config.NumberColumn("CABLURI", format="%d"),
                    "LISTE": st.column_config.NumberColumn("LISTE", format="%d")
                }
            )

            # Export
            date_rezumat = {
                "METRI": int(df_display["METRI"].sum()),
                "CAB": int(df_display["CABLURI"].sum()),
                "LISTE": int(df_display["LISTE"].sum())
            }
            add_export_buttons(df_display, "Raport_Saptamani_Luna", summary=date_rezumat)

    except Exception as e:
        st.error(f"Eroare: {e}")

@st.fragment
def show_ship_report():
    """Show ship-specific report"""
    st.markdown("<h4 style='margin:0px;'>🚢 Registru Tehnic - Nava 978</h4>", unsafe_allow_html=True)

    try:
        df = _fetch_ship()

        if not df.empty:
            # Sort and clean
            df["Nr Lista"] = pd.to_numeric(df["Nr Lista"], errors='coerce').fillna(0).astype(int)
            for col in ["Lungime", "Nr Cabluri", "Ore Rework", "Nava"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            for date_col in ["Data", "Data trimisa", "Data Rework"]:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

            df = df.sort_values(by="Nr Lista", ascending=True)

            # Summary
            total_m = int(df["Lungime"].sum())
            total_c = int(df["Nr Cabluri"].sum())
            total_l = len(df)

            # Summary display
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:12px; border-radius:6px; border:1px solid #333; display:flex; justify-content:space-around; align-items:center; margin-bottom:15px; border-left: 5px solid #f1c40f;">
                    <div style="text-align:center;"><span style="color:#888; font-size:10px;">METRI TOTALI</span><br><b style="color:#fff9c4; font-size:18px;">{total_m} m</b></div>
                    <div style="width:1px; height:25px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px;">CABLURI</span><br><b style="color:#fff9c4; font-size:18px;">{total_c}</b></div>
                    <div style="width:1px; height:25px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px;">LISTE OK</span><br><b style="color:#fff9c4; font-size:18px;">{total_l}</b></div>
                </div>
            """, unsafe_allow_html=True)

            # Data preparation for export
            df_export = df.copy()
            if "Data" in df_export.columns:
                df_export["Data"] = pd.to_datetime(df_export["Data"], errors='coerce')

            df_display = df.copy()
            if "Data" in df_display.columns:
                df_display["Data"] = df_display["Data"].dt.strftime('%d.%m.%y')

            # Dataframe display
            st.dataframe(
                df_display,
                hide_index=True,
                width="stretch",
                column_config={
                    "Nr Lista": st.column_config.NumberColumn("Nr Lista", format="%d", width=80),
                    "ID Lista": st.column_config.TextColumn("ID Lista", width=160),
                    "Locatie": st.column_config.TextColumn("Locație", width=140),
                    "Lungime": st.column_config.NumberColumn("Metri", format="%d", width=80),
                    "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d", width=80),
                    "Data": st.column_config.TextColumn("Data", width=85),
                    "Tragator": st.column_config.TextColumn("Trăgător", width=100),
                    "Trimis": st.column_config.CheckboxColumn("Trimis", width=70),
                    "Data trimisa": st.column_config.DateColumn("Data Trimisă", format="DD.MM.YY"),
                    "Nava": st.column_config.NumberColumn("Navă", format="%d"),
                    "Dosar": st.column_config.TextColumn("Dosar"),
                    "Rework": st.column_config.CheckboxColumn("RWK"),
                    "Data Rework": st.column_config.DateColumn("Data RWK"),
                    "Ore Rework": st.column_config.NumberColumn("Ore RWK", format="%.1f")
                }
            )

            # Export
            sumar = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}
            add_export_buttons(df_export, "Registru_Tehnic_978", summary=sumar)
        else:
            st.warning("⚠️ Nu s-au găsit liste înregistrate pentru Nava 978.")

    except Exception as e:
        st.error(f"Eroare la procesarea datelor navei: {e}")

@st.fragment
def show_shipped_report():
    """Show shipped items report"""
    st.markdown("<h4 style='margin:0px;'>📤 Liste Finalizate și Trimise - 978</h4>", unsafe_allow_html=True)

    try:
        df = _fetch_shipped()

        if not df.empty:
            # Sort and clean
            df["Nr Lista"] = pd.to_numeric(df["Nr Lista"], errors='coerce').fillna(0).astype(int)
            df = df.sort_values(by="Nr Lista", ascending=True)

            # Summary
            total_m = pd.to_numeric(df["Lungime"]).sum()
            total_c = pd.to_numeric(df["Nr Cabluri"]).sum()
            total_l = len(df)

            # Summary display
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:10px; border-radius:4px; border-left:4px solid #4caf50; display:flex; justify-content:space-around; align-items:center; border:0.1px solid #333; margin-bottom:15px;">
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">METRI TRIMIȘI</span><br><b style="color:#4caf50; font-size:16px;">{int(total_m)} m</b></div>
                    <div style="width:1px; height:20px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">CABLURI</span><br><b style="color:#4caf50; font-size:16px;">{int(total_c)}</b></div>
                    <div style="width:1px; height:20px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">LISTE OK</span><br><b style="color:#4caf50; font-size:16px;">{total_l}</b></div>
                </div>
            """, unsafe_allow_html=True)

            # Clean data
            for c in ["Lungime", "Nr Cabluri"]:
                df[c] = pd.to_numeric(df[c]).fillna(0).astype(int)

            # Display
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    "Nr Lista": st.column_config.NumberColumn("Nr Lista", format="%d", width=90),
                    "ID Lista": st.column_config.TextColumn("ID Lista", width=160),
                    "Locatie": st.column_config.TextColumn("Locatie", width=140),
                    "Lungime": st.column_config.NumberColumn("Metri", format="%d", width=80),
                    "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d", width=80),
                    "Data Trimisă": st.column_config.TextColumn("Data Trimisă", width=100),
                    "Dosar": st.column_config.TextColumn("Dosar", width=120)
                }
            )

            # Export
            sumar = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}
            add_export_buttons(df, "Raport_Liste_Trimise_978", summary=sumar)
        else:
            st.info("ℹ️ Încă nu există liste marcate ca trimise pentru Nava 978.")

    except Exception as e:
        st.error(f"Eroare la generarea raportului de trimise: {e}")

@st.fragment
def show_hala_report():
    """Show hala (warehouse) report"""
    st.markdown("<h4 style='margin:0px;'>🏭 Unități în Hală / Rămase - 978</h4>", unsafe_allow_html=True)

    try:
        df = _fetch_hala()

        if not df.empty:
            # Sort
            df["Nr Lista"] = pd.to_numeric(df["Nr Lista"], errors='coerce').fillna(0).astype(int)
            df = df.sort_values(by="Nr Lista", ascending=True)

            # Summary
            total_m = pd.to_numeric(df["Lungime"]).sum()
            total_c = pd.to_numeric(df["Nr Cabluri"]).sum()
            total_l = len(df)

            # Summary display
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:10px; border-radius:4px; border-left:4px solid #ff5252; display:flex; justify-content:space-around; align-items:center; border:0.1px solid #333; margin-bottom:15px;">
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">METRI RĂMAȘI</span><br><b style="color:#ff5252; font-size:16px;">{int(total_m)} m</b></div>
                    <div style="width:1px; height:20px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">CABLURI</span><br><b style="color:#ff5252; font-size:16px;">{int(total_c)}</b></div>
                    <div style="width:1px; height:20px; background-color:#444;"></div>
                    <div style="text-align:center;"><span style="color:#888; font-size:10px; font-weight:bold;">LISTE</span><br><b style="color:#ff5252; font-size:16px;">{total_l}</b></div>
                </div>
            """, unsafe_allow_html=True)

            # Clean and display
            for c in ["Lungime", "Nr Cabluri"]:
                df[c] = pd.to_numeric(df[c]).fillna(0).astype(int)

            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    "Nr Lista": st.column_config.NumberColumn("Nr Lista", format="%d", width=90),
                    "ID Lista": st.column_config.TextColumn("ID Lista", width=160),
                    "Locatie": st.column_config.TextColumn("Locație", width=140),
                    "Lungime": st.column_config.NumberColumn("Metri", format="%d", width=80),
                    "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d", width=80),
                    "Rework": st.column_config.CheckboxColumn("RWK", width=60)
                }
            )

            # Export
            sumar = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}
            add_export_buttons(df, "Stoc_Hala_Ramas_978", summary=sumar)
        else:
            st.success("🎉 Toate listele de pe Nava 978 au fost trimise!")

    except Exception as e:
        st.error(f"Eroare la generarea sumarului din hală: {e}")

@st.fragment
def show_rework_report():
    """Show rework report"""
    st.markdown("<h4 style='margin:0px;'>🛠️ Registru Intervenții (Rework) - 978</h4>", unsafe_allow_html=True)

    try:
        df = _fetch_rework()

        if not df.empty:
            # Sort
            df["Nr Lista"] = pd.to_numeric(df["Nr Lista"], errors='coerce').fillna(0).astype(int)
            df = df.sort_values(by="Nr Lista", ascending=True)

            # Clean data
            df["Lungime"] = pd.to_numeric(df["Lungime"]).fillna(0)
            df["Nr Cabluri"] = pd.to_numeric(df["Nr Cabluri"]).fillna(0)
            df["Ore Rework"] = pd.to_numeric(df["Ore Rework"]).fillna(0)

            # Summary
            total_m = int(df["Lungime"].sum())
            total_c = int(df["Nr Cabluri"].sum())
            total_ore = df["Ore Rework"].sum()
            nr_liste = len(df)

            # Summary display
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:15px; border-radius:8px; border-left:5px solid #f1c40f; display:flex; justify-content:space-around; align-items:center; margin-top:10px; margin-bottom:20px; border:0.1px solid #333;">
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">METRI REWORK</span><br>
                        <b style="color:#f1c40f; font-size:20px;">{total_m} m</b>
                    </div>
                    <div style="width:1px; height:30px; background-color:#444;"></div>
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">CABLURI REWORK</span><br>
                        <b style="color:#f1c40f; font-size:20px;">{total_c}</b>
                    </div>
                    <div style="width:1px; height:30px; background-color:#444;"></div>
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">LISTE REWORK</span><br>
                        <b style="color:#f1c40f; font-size:20px;">{nr_liste}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Display
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    "Nr Lista": st.column_config.NumberColumn("Nr Lista", format="%d", width=90),
                    "ID Lista": st.column_config.TextColumn("ID Lista", width=160),
                    "Locatie": st.column_config.TextColumn("Locație", width=140),
                    "Lungime": st.column_config.NumberColumn("Metri", format="%d", width=80),
                    "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d", width=80),
                    "Data RWK": st.column_config.TextColumn("Data RWK", width=100),
                    "Ore Rework": st.column_config.NumberColumn("Ore RWK", format="%.1f", width=80)
                }
            )

            # Export
            sumar = {"METRI": total_m, "CAB": total_c, "LISTE": nr_liste}
            add_export_buttons(df, "Registru_Rework_978", summary=sumar)
        else:
            st.info("ℹ️ Nu există liste cu status rework pentru Nava 978.")

    except Exception as e:
        st.error(f"Eroare la generarea raportului rework: {e}")

@st.fragment
def show_all_time_report():
    """Show all-time summary report"""
    st.markdown("<h4 style='margin:0px;'>🏗️ Sumar Parametri per Navă</h4>", unsafe_allow_html=True)

    try:
        df = _fetch_all_time()

        if not df.empty:
            # Clean data
            df["lungime_totala"] = pd.to_numeric(df["lungime_totala"]).fillna(0).astype(int)
            df["cabluri_total"] = pd.to_numeric(df["cabluri_total"]).fillna(0).astype(int)
            df["numar_liste"] = pd.to_numeric(df["numar_liste"]).fillna(0).astype(int)

            # Summary
            total_m = int(df["lungime_totala"].sum())
            total_c = int(df["cabluri_total"].sum())
            total_l = int(df["numar_liste"].sum())

            # Summary display
            st.markdown(f"""
                <div style="background-color:#1a1c23; padding:15px; border-radius:8px; border-left:5px solid #00d2ff; display:flex; justify-content:space-around; align-items:center; margin-top:10px; margin-bottom:20px; border:0.1px solid #333;">
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">METRI TOTALI</span><br>
                        <b style="color:#00d2ff; font-size:20px;">{total_m} m</b>
                    </div>
                    <div style="width:1px; height:30px; background-color:#444;"></div>
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">CABLURI TOTAL</span><br>
                        <b style="color:#00d2ff; font-size:20px;">{total_c}</b>
                    </div>
                    <div style="width:1px; height:30px; background-color:#444;"></div>
                    <div style="text-align:center;">
                        <span style="color:#888; font-size:11px; font-weight:bold; letter-spacing:1px;">LISTE TOTAL</span><br>
                        <b style="color:#00d2ff; font-size:20px;">{total_l}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Display
            df_view = df.rename(columns={
                "nava": "NAVA",
                "lungime_totala": "METRI",
                "cabluri_total": "CAB",
                "numar_liste": "LISTE"
            })

            st.dataframe(
                df_view,
                hide_index=True,
                width="stretch",
                column_config={
                    "NAVA": st.column_config.NumberColumn("NAVA", format="%d"),
                    "METRI": st.column_config.NumberColumn("LUNGIME TOTALĂ (m)", format="%d"),
                    "CAB": st.column_config.NumberColumn("NR. CABLURI TOTAL", format="%d"),
                    "LISTE": st.column_config.NumberColumn("TOTAL LISTE", format="%d")
                }
            )

            # Export
            date_sumar = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}
            add_export_buttons(df_view, "Centralizator_General_Nave", summary=date_sumar)
        else:
            st.warning("⚠️ Nu există date înregistrate.")

    except Exception as e:
        st.error(f"Eroare la generarea centralizatorului: {e}")