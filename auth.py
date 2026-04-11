# auth.py
# Authentication functions for the Streamlit app.
# This module handles simple password-based access control using Streamlit session state.

import streamlit as st

def check_password():
    """Show a login form and validate the user password."""
    # If the user already entered a correct password in this session, allow access.
    if st.session_state.get("password_correct", False):
        return True

    # Render the login UI when the user is not authenticated.
    st.markdown("<h2 style='text-align: center; color: #f1c40f;'>🔐 Acces Restricționat</h2>", unsafe_allow_html=True)

    with st.form("login_form"):
        password_input = st.text_input("Introduceți parola:", type="password")
        submit_button = st.form_submit_button("AUTENTIFICARE", width="stretch")

        if submit_button:
            try:
                if password_input == st.secrets["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                    return True
                else:
                    st.error("❌ Parolă incorectă!")
            except KeyError:
                st.error("❌ Configurare autentificare lipsă!")

    return False