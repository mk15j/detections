import streamlit as st
st.set_page_config(page_title="Test Summary", layout="wide")  # ✅ Must be first Streamlit call

import pandas as pd
import plotly.express as px
from utils.db import listeria_collection

# 🔐 Authentication check
if "user" not in st.session_state:
    st.warning("🔒 Please log in to access this page.")
    st.stop()

# 👤 Show current user and logout option
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("✅ Logged out successfully.")
    st.stop()

# 📊 Page title
st.title("🧪 Test Summary")

@st.cache_data
def load_data():
    df = pd.DataFrame(listeria_collection.find({}, {"_id": 0}))
    return df

df = load_data()

# 🧮 Detection Summary
summary = df.groupby("test")["value"].apply(lambda x: (x != "Not Detected").sum()).reset_index(name="Detections")

fig = px.bar(summary, x="test", y="Detections", color="Detections",
             title="Detection Count by Test Type",
             template="plotly_dark", color_continuous_scale="reds")

st.plotly_chart(fig, use_container_width=True)
