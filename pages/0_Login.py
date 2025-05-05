import streamlit as st
from utils.auth import authenticate  # Assuming authenticate is in utils/auth.py

st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = authenticate(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome, {user['username']}!")
        st.switch_page("1_Overview_Dashboard.py")  # You can customize this path
    else:
        st.error("Invalid username or password")
        
