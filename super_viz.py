# super_viz.py
# Query builder interface - mobile friendly.
# Allows building custom queries with dynamic conditions, column selection and sorting.

import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine, update_records, delete_records
from utils import add_export_buttons

ALL_FIELDS = [
    "Nava", "Nr Lista", "ID Lista", "Locatie", "Lungime",
    "Nr Cabluri", "Dosar", "Tragator", "Data", "Data trimisa",
    "Trimis", "Rework", "Data Rework", "Ore Rework"
]

FIELD_TYPES = {
    "Nava": "numeric", "Nr Lista": "numeric", "ID Lista": "text",
    "Locatie": "text", "Lungime": "numeric", "Nr Cabluri": "numeric",
    "Dosar": "text", "Tragator": "text", "Data": "date",
    "Data trimisa": "date", "Trimis": "boolean", "Rework": "boolean",
    "Data Rework": "date", "Ore Rework": "numeric"
}

OPERATORS = {
    "text":    ["conține", "=", "≠"],
    "numeric": ["=", "≠", ">", "<", "≥", "≤"],
    "date":    ["=", ">", "<", "≥", "≤"],
    "boolean": ["= True", "= False"]
}

DEFAULT_COLS = ["Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri", "Dosar"]


# --------------------------------------------------------------------------- #
# Session state init                                                            #
# --------------------------------------------------------------------------- #

def _init():
    if "sv_cond_ids" not in st.session_state:
        st.session_state.sv_cond_ids = [0]
        st.session_state.sv_cond_next = 1
        st.session_state["cf_0"] = "Nava"
        st.session_state["co_0"] = "="
        st.session_state["cv_0"] = "978"
    if "sv_sort_ids" not in st.session_state:
        st.session_state.sv_sort_ids = []
        st.session_state.sv_sort_next = 0
    if "sv_results" not in st.session_state:
        st.session_state.sv_results = None
    if "sv_cols" not in st.session_state:
        st.session_state.sv_cols = DEFAULT_COLS.copy()


# --------------------------------------------------------------------------- #
# SQL builder                                                                   #
# --------------------------------------------------------------------------- #

def _cond_to_sql(field, op, val, cid):
    col = f'"{field}"'
    p = f"p{cid}"
    ft = FIELD_TYPES.get(field, "text")

    if op == "conține":
        return f'{col} ILIKE :{p}', {p: f"%{val}%"}
    if op in ("= True", "= False"):
        return f'{col} IS {"TRUE" if op == "= True" else "FALSE"}', {}

    op_map = {"=": "=", "≠": "!=", ">": ">", "<": "<", "≥": ">=", "≤": "<="}
    sql_op = op_map.get(op, "=")

    if ft == "numeric":
        try:
            return f'{col} {sql_op} :{p}', {p: float(val.replace(",", "."))}
        except (ValueError, AttributeError):
            return None, {}

    if not val:
        return None, {}
    return f'{col} {sql_op} :{p}', {p: val}


def _run_query():
    col_ids   = st.session_state.sv_cond_ids
    sort_ids  = st.session_state.sv_sort_ids
    vis_cols  = st.session_state.sv_cols or ALL_FIELDS

    col_sql = ", ".join([f'"{c}"' for c in vis_cols])
    where_parts, params = [], {}

    for cid in col_ids:
        field = st.session_state.get(f"cf_{cid}", "Nava")
        op    = st.session_state.get(f"co_{cid}", "=")
        val   = st.session_state.get(f"cv_{cid}", "")
        ft    = FIELD_TYPES.get(field, "text")

        if ft == "boolean" or val:
            sql_part, p = _cond_to_sql(field, op, val, cid)
            if sql_part:
                where_parts.append(sql_part)
                params.update(p)

    where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    order_parts = []
    for sid in sort_ids:
        sf  = st.session_state.get(f"sf_{sid}", "Nr Lista")
        sd  = st.session_state.get(f"sd_{sid}", "ASC ↑")
        dir = "ASC" if "ASC" in sd else "DESC"
        order_parts.append(f'"{sf}" {dir}')
    order_sql = f"ORDER BY {', '.join(order_parts)}" if order_parts else ""

    query = f'SELECT "ID", {col_sql} FROM list963 {where_sql} {order_sql}'

    try:
        df = pd.read_sql(text(query), get_engine(), params=params)
        for dc in ["Data", "Data trimisa", "Data Rework"]:
            if dc in df.columns:
                df[dc] = pd.to_datetime(df[dc], errors="coerce")
        return df
    except Exception as e:
        st.error(f"❌ Eroare interogare: {e}")
        return None


# --------------------------------------------------------------------------- #
# Main view                                                                     #
# --------------------------------------------------------------------------- #

def show_super_visualization():
    _init()
    st.header("🔭 Interogare Date")

    # ── Condiții ──────────────────────────────────────────────────────────── #
    st.markdown("#### 🔍 Condiții")

    rm_cid = None
    for cid in list(st.session_state.sv_cond_ids):
        field = st.session_state.get(f"cf_{cid}", ALL_FIELDS[0])
        ft    = FIELD_TYPES.get(field, "text")
        ops   = OPERATORS[ft]
        cur_op = st.session_state.get(f"co_{cid}", ops[0])
        if cur_op not in ops:
            cur_op = ops[0]

        c1, c2, c3, c4 = st.columns([2, 1.5, 2, 0.5])
        with c1:
            st.selectbox("Câmp", ALL_FIELDS,
                         index=ALL_FIELDS.index(field),
                         key=f"cf_{cid}", label_visibility="collapsed")
        with c2:
            st.selectbox("Op", ops,
                         index=ops.index(cur_op),
                         key=f"co_{cid}", label_visibility="collapsed")
        with c3:
            if ft == "boolean":
                st.empty()
            elif ft == "date":
                st.text_input("Val", placeholder="YYYY-MM-DD",
                              key=f"cv_{cid}", label_visibility="collapsed")
            else:
                st.text_input("Val", placeholder="valoare...",
                              key=f"cv_{cid}", label_visibility="collapsed")
        with c4:
            if st.button("✕", key=f"crm_{cid}"):
                rm_cid = cid

    if rm_cid is not None:
        st.session_state.sv_cond_ids.remove(rm_cid)
        st.rerun()

    if st.button("＋ Adaugă condiție", use_container_width=True):
        nid = st.session_state.sv_cond_next
        st.session_state.sv_cond_ids.append(nid)
        st.session_state.sv_cond_next += 1
        st.rerun()

    st.divider()

    # ── Coloane vizibile ──────────────────────────────────────────────────── #
    st.markdown("#### 📋 Coloane vizibile")
    sel = st.multiselect("Coloane", ALL_FIELDS,
                         default=st.session_state.sv_cols,
                         label_visibility="collapsed")
    st.session_state.sv_cols = sel

    st.divider()

    # ── Sortare ───────────────────────────────────────────────────────────── #
    st.markdown("#### ↕ Sortare")

    rm_sid = None
    for sid in list(st.session_state.sv_sort_ids):
        s1, s2, s3 = st.columns([2.5, 1.5, 0.5])
        with s1:
            st.selectbox("Câmp sort", ALL_FIELDS,
                         index=ALL_FIELDS.index(st.session_state.get(f"sf_{sid}", "Nr Lista")),
                         key=f"sf_{sid}", label_visibility="collapsed")
        with s2:
            st.selectbox("Dir", ["ASC ↑", "DESC ↓"],
                         key=f"sd_{sid}", label_visibility="collapsed")
        with s3:
            if st.button("✕", key=f"srm_{sid}"):
                rm_sid = sid

    if rm_sid is not None:
        st.session_state.sv_sort_ids.remove(rm_sid)
        st.rerun()

    if st.button("＋ Adaugă sortare", use_container_width=True):
        sid = st.session_state.sv_sort_next
        st.session_state.sv_sort_ids.append(sid)
        st.session_state.sv_sort_next += 1
        st.rerun()

    st.divider()

    # ── Execută ───────────────────────────────────────────────────────────── #
    if st.button("🔍  EXECUTĂ INTEROGAREA", type="primary", use_container_width=True):
        st.session_state.sv_results = _run_query()

    # ── Rezultate ─────────────────────────────────────────────────────────── #
    if st.session_state.sv_results is not None:
        _show_results(st.session_state.sv_results)


# --------------------------------------------------------------------------- #
# Results + edit/delete                                                         #
# --------------------------------------------------------------------------- #

def _show_results(df):
    if df is None or df.empty:
        st.info("ℹ️ Nicio înregistrare găsită.")
        return

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Nr. Liste", len(df))
    if "Lungime" in df.columns:
        c2.metric("Total Metraj", f"{pd.to_numeric(df['Lungime'], errors='coerce').sum():,.0f} m")
    if "Nr Cabluri" in df.columns:
        c3.metric("Total Cabluri", int(pd.to_numeric(df["Nr Cabluri"], errors="coerce").sum()))

    st.markdown("---")

    col_cfg = {
        "ID": None,
        "Lungime": st.column_config.NumberColumn("Lungime", format="%.0f m"),
        "Nr Cabluri": st.column_config.NumberColumn("Cabluri", format="%d"),
        "Ore Rework": st.column_config.NumberColumn("Ore RW", format="%.2f h"),
        "Trimis": st.column_config.CheckboxColumn("Trimis"),
        "Rework": st.column_config.CheckboxColumn("Rework"),
        "Data": st.column_config.DateColumn("Data", format="DD.MM.YYYY"),
        "Data trimisa": st.column_config.DateColumn("Data Trimis", format="DD.MM.YYYY"),
        "Data Rework": st.column_config.DateColumn("Data Rework", format="DD.MM.YYYY"),
    }

    event = st.dataframe(
        df, column_config=col_cfg,
        hide_index=True, width="stretch",
        on_select="rerun", selection_mode="multi-row"
    )

    selected = event.selection.rows

    # Export
    if st.button("📥 Export Excel", use_container_width=True):
        df_exp = df.drop(columns=["ID"], errors="ignore")
        total_m = int(pd.to_numeric(df_exp.get("Lungime", pd.Series()), errors="coerce").sum())
        total_c = int(pd.to_numeric(df_exp.get("Nr Cabluri", pd.Series()), errors="coerce").sum())
        add_export_buttons(df_exp, "Interogare_Date", summary={"METRI": total_m, "CAB": total_c, "LISTE": len(df_exp)})

    # Edit / Delete
    if selected:
        st.info(f"✅ {len(selected)} rânduri selectate.")
        tab_edit, tab_del = st.tabs(["✏️ Editare", "🗑️ Ștergere"])
        with tab_edit:
            show_bulk_edit_form(df, selected)
        with tab_del:
            show_bulk_delete_form(df, selected)


# --------------------------------------------------------------------------- #
# Bulk edit / delete (neschimbate functional)                                   #
# --------------------------------------------------------------------------- #

def show_bulk_edit_form(df_final, selected_rows):
    st.write("Completează doar câmpurile pe care vrei să le modifici:")

    e1, e2, e3 = st.columns(3)
    with e1:
        edit_nr_l = st.text_input("🔢 Nou Nr. Listă")
    with e2:
        edit_id_l = st.text_input("🆔 Nou ID Listă")
    with e3:
        edit_loc = st.text_input("📍 Nouă Locație")

    e4, e5, e6 = st.columns(3)
    with e4:
        edit_lungime = st.text_input("📏 Nouă Lungime")
    with e5:
        edit_cabluri = st.text_input("🔌 Nou Nr. Cabluri")
    with e6:
        edit_d_creare = st.date_input("📅 Nouă Dată Creare", value=None)

    e7, e8 = st.columns(2)
    with e7:
        edit_dos = st.text_input("📁 Nou Dosar")
    with e8:
        edit_trag = st.text_input("👷 Nou Tragător")

    st.markdown("---")
    f1, f2 = st.columns(2)
    with f1:
        edit_s_trim = st.selectbox("📧 Status Trimis", ["Fără modificare", "True", "False"], key="bu_trim")
    with f2:
        edit_d_trim = st.date_input("🚢 Nouă Dată Trimis", value=None)

    g1, g2, g3 = st.columns(3)
    with g1:
        edit_s_rew = st.selectbox("🔄 Status Rework", ["Fără modificare", "True", "False"], key="bu_rew")
    with g2:
        edit_d_rew = st.date_input("🛠️ Nouă Dată Rework", value=None)
    with g3:
        edit_ore_rew = st.text_input("⏱️ Ore Rework", placeholder="Ex: 1.5")

    if st.button("💾 SALVEAZĂ MODIFICĂRILE", use_container_width=True):
        perform_bulk_update(df_final, selected_rows, {
            'nr_lista': edit_nr_l, 'id_lista': edit_id_l, 'locatie': edit_loc,
            'lungime': edit_lungime, 'cabluri': edit_cabluri, 'data_creare': edit_d_creare,
            'dosar': edit_dos, 'tragator': edit_trag,
            'status_trimis': edit_s_trim, 'data_trimis': edit_d_trim,
            'status_rework': edit_s_rew, 'data_rework': edit_d_rew,
            'ore_rework': edit_ore_rew
        })


def perform_bulk_update(df_final, selected_rows, edits):
    ids_upd = df_final.iloc[selected_rows]["ID"].tolist()
    updates_dict = {}

    for key, col in [('nr_lista','Nr Lista'),('id_lista','ID Lista'),('locatie','Locatie'),
                     ('dosar','Dosar'),('tragator','Tragator')]:
        if edits[key] and edits[key].strip():
            updates_dict[col] = edits[key].strip()

    for key, col in [('lungime','Lungime'),('ore_rework','Ore Rework')]:
        if edits[key] and edits[key].strip():
            try:
                updates_dict[col] = float(edits[key].replace(",", "."))
            except ValueError:
                st.error(f"⚠️ Valoare invalidă pentru {col}")
                return

    if edits['cabluri'] and edits['cabluri'].strip():
        try:
            updates_dict['Nr Cabluri'] = int(edits['cabluri'])
        except ValueError:
            st.error("⚠️ Cabluri invalide")
            return

    if edits['data_creare']:
        updates_dict['Data'] = str(edits['data_creare'])
    if edits['data_trimis']:
        updates_dict['Data trimisa'] = str(edits['data_trimis'])
    if edits['data_rework']:
        updates_dict['Data Rework'] = str(edits['data_rework'])
    if edits['status_trimis'] != "Fără modificare":
        updates_dict['Trimis'] = edits['status_trimis'] == "True"
    if edits['status_rework'] != "Fără modificare":
        updates_dict['Rework'] = edits['status_rework'] == "True"

    if updates_dict:
        update_records(get_engine(), updates_dict, ids_upd)
        st.session_state.sv_results = None
        st.success("✅ Actualizat!")
        st.rerun()


def show_bulk_delete_form(df_final, selected_rows):
    st.error("⚠️ Ștergerea este definitivă.")
    if st.checkbox("Confirm ștergerea") and st.button("🚨 EXECUTĂ ȘTERGEREA", use_container_width=True):
        delete_records(get_engine(), df_final.iloc[selected_rows]["ID"].tolist())
        st.session_state.sv_results = None
        st.success("🔥 Șters!")
        st.rerun()
