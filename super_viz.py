# super_viz.py
# Super Visualization module with advanced filtering, editing and export.
# This view gives the user a full search/filter interface and the ability to edit or delete rows.

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from sqlalchemy import text
from database import get_engine, update_records, delete_records
from utils import add_export_buttons

def show_super_visualization():
    """Main super visualization interface."""
    # Render the main super visualization panel header.
    st.header("🔭 Centru de Comandă & Filtrare Totală")

    # Filtering panel
    with st.expander("🛠️ Panou de Filtrare și Căutare Rapidă", expanded=True):
        # Row 1: Ship and basic search
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1, 1, 1, 1.2])
        with r1_c1:
            df_nave = pd.read_sql('SELECT DISTINCT "Nava" FROM list963 ORDER BY "Nava" DESC', get_engine())
            lista_nave = df_nave["Nava"].tolist()
            idx_978 = lista_nave.index(978) if 978 in lista_nave else 0
            nava_sel = st.selectbox("🚢 Nava", lista_nave, index=idx_978)
        with r1_c2:
            v_nr_lista = st.text_input("🔢 Nr. Listă", value="", placeholder="Ex: 001")
        with r1_c3:
            v_id_lista = st.text_input("🆔 ID Listă", value="", placeholder="Ex: 963-A")
        with r1_c4:
            df_dosare = pd.read_sql('SELECT DISTINCT "Dosar" FROM list963 WHERE "Dosar" IS NOT NULL ORDER BY "Dosar"', get_engine())
            dosar_sel = st.multiselect("📁 Filtru Dosar", df_dosare["Dosar"].tolist())

        # Row 2: Location and personnel
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
        with r2_c1:
            q_loc = text('SELECT DISTINCT "Locatie" FROM list963 WHERE "Nava" = :nava ORDER BY "Locatie"')
            df_loc = pd.read_sql(q_loc, get_engine(), params={"nava": nava_sel})
            locatii_sel = st.multiselect("📍 Locații", df_loc["Locatie"].tolist())
        with r2_c2:
            df_tragatori = pd.read_sql('SELECT DISTINCT "Tragator" FROM list963 WHERE "Tragator" IS NOT NULL ORDER BY "Tragator"', get_engine())
            tragator_sel = st.multiselect("👷 Tragător", df_tragatori["Tragator"].tolist())
        with r2_c3:
            stare_rework = st.selectbox("🔄 Status Rework", ["Toate", "Doar Rework", "Fără Rework"])
        with r2_c4:
            stare_trimis = st.selectbox("📧 Status Expediție", ["Toate", "Trimise", "Netrimise"])

        # Date filters
        st.markdown("**📅 Intervale de Timp (Bifează pentru activare)**")
        f1, f2, f3 = st.columns(3)
        with f1:
            usa_data = st.checkbox("Data Creării")
            d1 = st.date_input("Creare", [], label_visibility="collapsed") if usa_data else None
        with f2:
            usa_exp = st.checkbox("Data Expedierii")
            d2 = st.date_input("Expediere", [], label_visibility="collapsed") if usa_exp else None
        with f3:
            usa_rew = st.checkbox("Data Rework")
            d3 = st.date_input("Rework", [], label_visibility="collapsed") if usa_rew else None

        # Column selection
        toate_col = ["Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri", "Dosar", "Tragator", "Data", "Data trimisa", "Trimis", "Rework", "Data Rework", "Ore Rework"]
        col_vizibile = st.multiselect("🍱 Coloane vizibile:", options=toate_col, default=["Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri", "Dosar"])

    # Build query
    # Compose SQL from selected filters and visible columns.
    col_sql = ", ".join([f'"{c}"' for c in col_vizibile]) if col_vizibile else "*"
    query = f'SELECT "ID", {col_sql} FROM list963 WHERE "Nava" = :nava'
    params = {"nava": nava_sel}

    if v_nr_lista:
        query += ' AND "Nr Lista" LIKE :nr_l'
        params["nr_l"] = f"%{v_nr_lista}%"
    if v_id_lista:
        query += ' AND "ID Lista" LIKE :id_l'
        params["id_l"] = f"%{v_id_lista}%"
    if locatii_sel:
        query += ' AND "Locatie" = ANY(:locs)'
        params["locs"] = list(locatii_sel)
    if dosar_sel:
        query += ' AND "Dosar" = ANY(:dos)'
        params["dos"] = list(dosar_sel)
    if tragator_sel:
        query += ' AND "Tragator" = ANY(:trag)'
        params["trag"] = list(tragator_sel)

    # Status filters
    if stare_rework == "Doar Rework":
        query += ' AND "Rework" IS TRUE'
    elif stare_rework == "Fără Rework":
        query += ' AND "Rework" IS NOT TRUE'

    if stare_trimis == "Trimise":
        query += ' AND "Trimis" = TRUE'
    elif stare_trimis == "Netrimise":
        query += ' AND "Trimis" = FALSE'

    # Date filters
    if usa_data and d1 and len(d1) == 2:
        query += ' AND "Data" BETWEEN :d1s AND :d1e'
        params["d1s"], params["d1e"] = d1[0], d1[1]
    if usa_exp and d2 and len(d2) == 2:
        query += ' AND "Data trimisa" BETWEEN :d2s AND :d2e'
        params["d2s"], params["d2e"] = d2[0], d2[1]
    if usa_rew and d3 and len(d3) == 2:
        query += ' AND "Data Rework" BETWEEN :d3s AND :d3e'
        params["d3s"], params["d3e"] = d3[0], d3[1]

    query += ' ORDER BY CAST(NULLIF("Nr Lista", \'\') AS INTEGER) ASC'

    # Execute query and load results.
    df_final = pd.read_sql(text(query), get_engine(), params=params)

    # Results display
    if not df_final.empty:
        for date_col in ["Data", "Data trimisa", "Data Rework"]:
            if date_col in df_final.columns:
                df_final[date_col] = pd.to_datetime(df_final[date_col], errors='coerce')

        c_m = st.columns(3)
        c_m[0].metric("Nr. Liste", len(df_final))
        if "Lungime" in df_final.columns:
            m_sum = pd.to_numeric(df_final['Lungime'], errors='coerce').sum()
            c_m[1].metric("Total Metraj", f"{m_sum:,.1f} m")
        if "Nr Cabluri" in df_final.columns:
            c_sum = pd.to_numeric(df_final['Nr Cabluri'], errors='coerce').sum()
            c_m[2].metric("Total Cabluri", int(c_sum))

        st.markdown("---")

        # Display the filtered data and enable row selection.
        event = st.dataframe(
            df_final,
            column_config={
                "ID": None,
                "Lungime": st.column_config.NumberColumn("Lungime", format="%.1f m"),
                "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d"),
                "Ore Rework": st.column_config.NumberColumn("Ore RW", format="%.2f h"),
                "Trimis": st.column_config.CheckboxColumn("Trimis"),
                "Rework": st.column_config.CheckboxColumn("Rework"),
                "Data": st.column_config.DateColumn("Data", format="DD.MM.YYYY"),
                "Data trimisa": st.column_config.DateColumn("Data Trimis", format="DD.MM.YYYY"),
                "Data Rework": st.column_config.DateColumn("Data Rework", format="DD.MM.YYYY")
            },
            hide_index=True,
            width="stretch",
            on_select="rerun",
            selection_mode="multi-row"
        )

        selected_rows = event.selection.rows

        if selected_rows:
            st.info(f"✅ Ai selectat **{len(selected_rows)}** rânduri.")
            tab_edit, tab_del = st.tabs(["📝 Editare în Masă / Individuală", "🗑️ Ștergere"])

            with tab_edit:
                show_bulk_edit_form(df_final, selected_rows)

            with tab_del:
                show_bulk_delete_form(df_final, selected_rows)

        # Export current filtered view to Excel with summary.
        if st.button("🖨️ Export Excel"):
            df_export = df_final.copy()
            if "ID" in df_export.columns:
                df_export = df_export.drop(columns=["ID"])

            total_m = int(pd.to_numeric(df_export["Lungime"], errors='coerce').sum()) if "Lungime" in df_export.columns else 0
            total_c = int(pd.to_numeric(df_export["Nr Cabluri"], errors='coerce').sum()) if "Nr Cabluri" in df_export.columns else 0
            total_l = len(df_export)
            summary = {"METRI": total_m, "CAB": total_c, "LISTE": total_l}

            add_export_buttons(df_export, "SuperVizualizare_978", summary=summary)
    else:
        st.info(f"ℹ️ Nu există date conform filtrelor.")

def show_bulk_edit_form(df_final, selected_rows):
    """Show bulk edit form"""
    st.write("Completează doar câmpurile pe care vrei să le modifici:")

    # Edit fields
    e1_c1, e1_c2, e1_c3 = st.columns(3)
    with e1_c1:
        edit_nr_l = st.text_input("🔢 Nou Nr. Listă")
    with e1_c2:
        edit_id_l = st.text_input("🆔 Nou ID Listă")
    with e1_c3:
        edit_loc = st.text_input("📍 Nouă Locație")

    e2_c1, e2_c2, e2_c3 = st.columns(3)
    with e2_c1:
        edit_lungime = st.text_input("📏 Nouă Lungime")
    with e2_c2:
        edit_cabluri = st.text_input("🔌 Nou Nr. Cabluri")
    with e2_c3:
        edit_d_creare = st.date_input("📅 Nouă Dată Creare", value=None)

    e3_c1, e3_c2, e3_c3 = st.columns(3)
    with e3_c1:
        edit_dos = st.text_input("📁 Nou Dosar")
    with e3_c2:
        edit_trag = st.text_input("👷 Nou Tragător")

    st.markdown("---")
    e4_c1, e4_c2, e4_c3 = st.columns(3)
    with e4_c1:
        edit_s_trim = st.selectbox("📧 Status Trimis", ["Fără modificare", "True", "False"], key="bu_trim")
    with e4_c2:
        edit_d_trim = st.date_input("🚢 Nouă Dată Trimis", value=None)

    e5_c1, e5_c2, e5_c3 = st.columns(3)
    with e5_c1:
        edit_s_rew = st.selectbox("🔄 Status Rework", ["Fără modificare", "True", "False"], key="bu_rew")
    with e5_c2:
        edit_d_rew = st.date_input("🛠️ Nouă Dată Rework", value=None)
    with e5_c3:
        edit_ore_rew = st.text_input("⏱️ Ore Rework", placeholder="Ex: 1.5")

    if st.button("💾 SALVEAZĂ MODIFICĂRILE"):
        perform_bulk_update(df_final, selected_rows, {
            'nr_lista': edit_nr_l,
            'id_lista': edit_id_l,
            'locatie': edit_loc,
            'lungime': edit_lungime,
            'cabluri': edit_cabluri,
            'data_creare': edit_d_creare,
            'dosar': edit_dos,
            'tragator': edit_trag,
            'status_trimis': edit_s_trim,
            'data_trimis': edit_d_trim,
            'status_rework': edit_s_rew,
            'data_rework': edit_d_rew,
            'ore_rework': edit_ore_rew
        })

def perform_bulk_update(df_final, selected_rows, edits):
    """Perform bulk update operation using parameterized queries."""
    ids_upd = df_final.iloc[selected_rows]["ID"].tolist()
    updates_dict = {}

    # Text fields
    if edits['nr_lista'].strip():
        updates_dict['Nr Lista'] = edits['nr_lista'].strip()
    if edits['id_lista'].strip():
        updates_dict['ID Lista'] = edits['id_lista'].strip()
    if edits['locatie'].strip():
        updates_dict['Locatie'] = edits['locatie'].strip()
    if edits['dosar'].strip():
        updates_dict['Dosar'] = edits['dosar'].strip()
    if edits['tragator'].strip():
        updates_dict['Tragator'] = edits['tragator'].strip()

    # Numeric fields with validation
    if edits['lungime'].strip():
        try:
            updates_dict['Lungime'] = float(edits['lungime'].replace(",", "."))
        except ValueError:
            st.error("⚠️ Lungime invalidă")
            return

    if edits['cabluri'].strip():
        try:
            updates_dict['Nr Cabluri'] = int(edits['cabluri'])
        except ValueError:
            st.error("⚠️ Cabluri invalide")
            return

    if edits['ore_rework'].strip():
        try:
            updates_dict['Ore Rework'] = float(edits['ore_rework'].replace(",", "."))
        except ValueError:
            st.error("⚠️ Ore invalid!")
            return

    # Date fields
    if edits['data_creare']:
        updates_dict['Data'] = str(edits['data_creare'])
    if edits['data_trimis']:
        updates_dict['Data trimisa'] = str(edits['data_trimis'])
    if edits['data_rework']:
        updates_dict['Data Rework'] = str(edits['data_rework'])

    # Boolean status fields
    if edits['status_trimis'] != "Fără modificare":
        updates_dict['Trimis'] = edits['status_trimis'] == "True"
    if edits['status_rework'] != "Fără modificare":
        updates_dict['Rework'] = edits['status_rework'] == "True"

    if updates_dict:
        update_records(get_engine(), updates_dict, ids_upd)
        st.success("✅ Actualizat!")
        st.rerun()

def show_bulk_delete_form(df_final, selected_rows):
    """Show bulk delete confirmation"""
    st.error("⚠️ Atenție! Ștergerea este definitivă.")
    if st.checkbox("Confirm ștergerea datelor bifate") and st.button("🚨 EXECUTĂ ȘTERGEREA"):
        ids_del = df_final.iloc[selected_rows]["ID"].tolist()
        delete_records(get_engine(), ids_del)
        st.success("🔥 S-a șters!")
        st.rerun()