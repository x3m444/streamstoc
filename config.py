# config.py
# Configuration constants and settings for the application.
# This module centralizes environment loading and configuration values used by the app.

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from the local .env file before resolving settings.
load_dotenv()

# Database connection settings read from environment variables.
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME')
}

# Default values used across the app for session initialization.
DEFAULT_SHIP = 978
DEFAULT_TRAGATOR = "COSTEL"
TIMEZONE_OFFSET = timedelta(hours=3)

# Streamlit UI configuration.
PAGE_TITLE = "Gestiune Cabluri"
PAGE_LAYOUT = "centered"

# Sidebar menu options.
MENU_OPTIONS = [
    "📥 Introducere Date",
    "📦 Expediție",
    "📊 Super Vizualizare",
    "📊 Rapoarte & Export"
]

# Report tabs
REPORT_TABS = [
    "📅 Azi",
    "🗓️ Săpt.",
    "🌙 Lună",
    "🚢 Navă",
    "📤 Trimise",
    "🏭 Hală",
    "⚠️ Rework",
    "♾️ All Time"
]

# Column configurations for dataframes
COLUMN_CONFIGS = {
    'basic': {
        "Nr Lista": "Nr Lista",
        "Locatie": "Locație",
        "Lungime": "Lungime",
        "Nr Cabluri": "Nr Cabluri"
    }
}