# database.py
# Database operations and connections
# This module centralizes database access logic, SQL execution helpers, and
# any row-level inserts/updates/deletes for the application.

import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from functools import lru_cache
from config import DB_CONFIG

# Load environment variables from .env into the process environment before
# any database configuration values are resolved.
load_dotenv()

def get_db_url():
    """Generate database URL from config."""
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

@lru_cache(maxsize=1)
def get_engine():
    """Create and return a cached SQLAlchemy engine with connection pooling."""
    db_url = get_db_url()
    return create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        future=True
    )

def get_conn():
    """Return a raw psycopg2 connection for legacy use cases."""
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port']
    )

def check_db_integrity(engine):
    """Verify the application's main table exists and is accessible."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text('SELECT count(*) FROM "list963"'))
            count = result.fetchone()[0]
        return True, count
    except Exception as e:
        # Return the exception details so the UI can display a helpful message.
        return False, str(e)

def get_locations_for_ship(engine, ship_number):
    """Return distinct location names for the selected ship."""
    query = text('SELECT DISTINCT "Locatie" FROM "list963" WHERE "Nava"::text = :nava AND "Locatie" IS NOT NULL ORDER BY "Locatie"')
    df = pd.read_sql(query, engine, params={"nava": str(ship_number)})
    return [str(loc) for loc in df["Locatie"].tolist()]

def insert_cable_record(engine, data):
    """Insert a new cable inventory record into the database."""
    query = text('''
        INSERT INTO "list963"
        ("Nava", "Nr Lista", "ID Lista", "Locatie", "Lungime", "Nr Cabluri", "Data", "Tragator", "Trimis")
        VALUES (:nava, :nr_lista, :id_lista, :locatie, :lungime, :nr_cabluri, :data, :tragator, :trimis)
    ''')
    with engine.connect() as conn:
        conn.execute(query, data)
        conn.commit()

def update_records(engine, updates_dict, ids):
    """Update records by ID using a fully parameterized query.
    updates_dict: {column_name: value} — no SQL interpolation of user values."""
    if not updates_dict or not ids:
        return

    set_parts = []
    params = {}
    for col, val in updates_dict.items():
        param_key = 'col_' + col.replace(' ', '_')
        set_parts.append(f'"{col}" = :{param_key}')
        params[param_key] = val

    params['ids'] = ids
    query = f'UPDATE list963 SET {", ".join(set_parts)} WHERE "ID" = ANY(:ids)'

    with engine.connect() as conn:
        conn.execute(text(query), params)
        conn.commit()

def delete_records(engine, ids):
    """Delete records matching the provided IDs."""
    if not ids:
        return

    with engine.connect() as conn:
        conn.execute(text('DELETE FROM list963 WHERE "ID" = ANY(:ids)'), {"ids": ids})
        conn.commit()