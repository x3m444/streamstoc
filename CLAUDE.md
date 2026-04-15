# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Run tests
python test_app.py
```

## Environment Setup

Two secrets files are required before running:

- `.env` — database credentials (`DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME`)
- `.streamlit/secrets.toml` — app login password (`password = "..."`)

Copy from `.env.example` and `.streamlit/secrets.example.toml` as templates.

## Architecture

This is a **Streamlit** cable inventory management app (`Gestiune Cabluri`) backed by **PostgreSQL**. The entire data model lives in a single table: `list963`.

### Module responsibilities

| Module | Role |
|---|---|
| `app.py` | Entry point: page config, auth gate, DB integrity check, sidebar nav routing |
| `config.py` | All constants — DB config from env, UI strings, menu options, report tab names |
| `database.py` | SQLAlchemy engine (cached via `@lru_cache`), raw psycopg2 fallback, all CRUD helpers |
| `auth.py` | Single-password auth via `st.secrets["password"]` and `st.session_state` |
| `forms.py` | "Introducere Date" (data entry) and "Expediție" (shipment marking) UI + logic |
| `reports.py` | Eight report tabs (daily / weekly / monthly / ship / shipped / warehouse / rework / all-time) |
| `super_viz.py` | Advanced filter+search view with multi-row selection, bulk edit, and bulk delete |
| `utils.py` | Excel export via xlsxwriter (`add_export_buttons`), numeric input validation, dataframe styling |

### Data flow

`app.py` imports top-level functions from each module and calls them based on sidebar selection. `super_viz` is imported lazily inside the `elif` block to avoid a circular import. Every module that needs DB access calls `database.get_engine()` — the engine is a module-level singleton via `lru_cache`.

### Database table: `list963`

Key columns: `ID` (PK), `Nava` (ship number, default 978), `Nr Lista`, `ID Lista`, `Locatie`, `Lungime` (meters), `Nr Cabluri`, `Data` (entry date, UTC+3), `Tragator` (operator), `Trimis` (bool), `Data trimisa`, `Dosar` (shipment folder), `Rework` (bool), `Data Rework`, `Ore Rework`.

### Known SQL injection risk

`database.update_records()` and `database.delete_records()` build raw SQL strings using f-strings with caller-supplied values. The callers in `super_viz.py` (`perform_bulk_update`) and `forms.py` construct these clauses manually. When modifying these paths, be careful not to introduce user-controlled values into the f-string.
