# auth.py
# Authentication functions for the Streamlit app.
# Cookie-based persistent login using HMAC-signed tokens.

import streamlit as st
import extra_streamlit_components as stx
import hmac
import hashlib
import time
from datetime import datetime, timedelta

COOKIE_NAME = "gestiune_auth"
COOKIE_EXPIRY_DAYS = 30


def _get_cookie_manager():
    return stx.CookieManager()


def _generate_token(password: str) -> str:
    timestamp = str(int(time.time()))
    sig = hmac.new(password.encode(), timestamp.encode(), hashlib.sha256).hexdigest()
    return f"{sig}:{timestamp}"


def _validate_token(cookie_val: str, password: str) -> bool:
    try:
        sig, timestamp = cookie_val.rsplit(":", 1)
        if int(time.time()) - int(timestamp) > COOKIE_EXPIRY_DAYS * 86400:
            return False
        expected = hmac.new(password.encode(), timestamp.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


def check_password():
    """Check cookie first, then session state, then show login form."""
    cookie_manager = _get_cookie_manager()

    # Already authenticated this session
    if st.session_state.get("password_correct", False):
        return True

    # Check persistent cookie
    try:
        cookie_val = cookie_manager.get(COOKIE_NAME)
        if cookie_val and _validate_token(cookie_val, st.secrets["password"]):
            st.session_state["password_correct"] = True
            return True
    except Exception:
        pass

    # Show login form
    st.markdown("<h2 style='text-align: center; color: #f1c40f;'>🔐 Acces Restricționat</h2>", unsafe_allow_html=True)

    with st.form("login_form"):
        password_input = st.text_input("Introduceți parola:", type="password")
        submit_button = st.form_submit_button("AUTENTIFICARE", width="stretch")

        if submit_button:
            try:
                if password_input == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    token = _generate_token(st.secrets["password"])
                    cookie_manager.set(
                        COOKIE_NAME, token,
                        expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)
                    )
                    st.rerun()
                    return True
                else:
                    st.error("❌ Parolă incorectă!")
            except KeyError:
                st.error("❌ Configurare autentificare lipsă!")

    return False
