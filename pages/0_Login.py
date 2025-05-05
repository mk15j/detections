import streamlit as st
from utils.auth import authenticate  # Make sure this path is correct

st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = authenticate(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome, {user['username']}!")
        st.switch_page("Overview Dashboard")  # ✅ Correct title, not filename
    else:
        st.error("Invalid username or password")

