# import streamlit as st
# from utils.auth import authenticate  # Assuming authenticate is in utils/auth.py

# st.title("🔐 Login")

# username = st.text_input("Username")
# password = st.text_input("Password", type="password")

# if st.button("Login"):
#     user = authenticate(username, password)
#     if user:
#         st.session_state["user"] = user
#         st.success(f"Welcome, {user['username']}!")
#         st.switch_page("Overview Dashboard")  # You can customize this path
#     else:
#         st.error("Invalid username or password")

import streamlit as st
from streamlit import runtime
from utils.auth import authenticate

st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = authenticate(username, password)
    if user:
        st.session_state["user"] = user
        st.success(f"Welcome, {user['username']}!")

        # Show available page paths for debugging
        available_pages = runtime.scriptrunner.get_pages("")
        st.write("Available Pages:", available_pages)

        # Try correct display name
        st.switch_page("Overview Dashboard")
    else:
        st.error("Invalid username or password")
