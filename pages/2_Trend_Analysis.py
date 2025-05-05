import streamlit as st
st.set_page_config(page_title="Trend Analysis", layout="wide")  # MUST be first Streamlit command

import pandas as pd
import plotly.express as px
from utils.db import listeria_collection

# 🔐 Authentication check
if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
    st.stop()

# 👤 Show user info and logout button
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("🔓 Logged out successfully.")
    st.stop()


# 📅 Page content
st.title("📅 Trend Analysis")

@st.cache_data
def load_data():
    df = pd.DataFrame(listeria_collection.find({}, {"_id": 0}))
    df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
    return df

df = load_data()

# ✅ Ensure necessary columns exist
if "sample_date" not in df.columns or "value" not in df.columns:
    st.warning("The dataset is missing 'sample_date' or 'value' columns.")
    st.stop()

# 🧪 Label Detection
df["Detection"] = df["value"].apply(lambda x: "Detected" if x != "Not Detected" else "Not Detected")

# 🗓️ Restrict date range for X-axis
start_date = pd.to_datetime("2025-02-03")
end_date = pd.to_datetime("2025-03-28")

df = df[(df["sample_date"] >= start_date) & (df["sample_date"] <= end_date)]

# 📊 Group by date and detection
if df.empty:
    st.warning("No data available in the selected date range.")
else:
    trend_df = df.groupby(["sample_date", "Detection"]).size().reset_index(name="count")

    # 💎 Plot line chart with value labels and diamond markers
    fig = px.line(
        trend_df,
        x="sample_date",
        y="count",
        color="Detection",
        title="Detection Trend Over Time",
        template="plotly_dark",
        color_discrete_map={
            "Detected": "#8A00C4",       # Neon Purple
            "Not Detected": "#39FF14"    # Neon Green
        },
        markers=True
    )

    # 🔧 Customize markers and annotations
    fig.update_traces(marker=dict(symbol="diamond", size=10), text=trend_df["count"], textposition="top center")

    # 🛠️ Customize x-axis to show all dates vertically
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=all_dates,
            tickformat='%d-%b',
            tickangle=90
        ),
        xaxis_title="Sample Date",
        yaxis_title="Number of Samples",
        legend_title="Detection Result"
    )

    st.plotly_chart(fig, use_container_width=True)






# df = load_data()

# trend = df.groupby(["test", "sample_date"])["value"].apply(lambda x: (x != "Not Detected").sum()).reset_index()

# fig = px.line(trend, x="sample_date", y="value", color="test",
#               title="Detection Trends by Test",
#               template="plotly_dark", color_discrete_sequence=px.colors.qualitative.T10)

# st.plotly_chart(fig, use_container_width=True)
