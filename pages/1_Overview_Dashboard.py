import streamlit as st
# ✅ Set page config FIRST
st.set_page_config(page_title="Overview Dashboard", layout="wide")
import pandas as pd
import plotly.express as px
from utils.db import listeria_collection

# 🔐 Authentication check
if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
    st.stop()

# 🌐 Optional: Show who is logged in
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
logout = st.sidebar.button("Logout")
if logout:
    st.session_state.clear()
    st.success("🔓 Logged out successfully.")
    st.stop()
    




# 📊 Load data
@st.cache_data
def load_data():
    data = list(listeria_collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
    return df

def test_summary_by_code(df):
    st.subheader("🔬 Test Summary by Code")

    if "test_code" not in df.columns or "test_result" not in df.columns:
        st.warning("Missing 'test_code' or 'test_result' columns in data.")
        return

    # Clean 'test_result' column
    df["test_result"] = df["test_result"].astype(str).str.strip().str.lower()

    summary_df = (
        df.groupby(["test_code", "test_result"])
        .size()
        .reset_index(name="count")
        .pivot(index="test_code", columns="test_result", values="count")
        .fillna(0)
        .astype(int)
    )

    summary_df["Total"] = summary_df.sum(axis=1)
    if "not detected" in summary_df.columns:
        summary_df["Detection Rate (%)"] = (
            100 * (summary_df["Total"] - summary_df["not detected"]) / summary_df["Total"]
        ).round(2)
    else:
        summary_df["Detection Rate (%)"] = 100.0

    st.dataframe(summary_df.style.background_gradient(cmap="Oranges", axis=1))

# 🔎 Main page content
st.title("📊 Overview Dashboard")
df = load_data()

st.sidebar.header("Filters")
date_range = st.sidebar.date_input("Date Range", [df["sample_date"].min(), df["sample_date"].max()])
df = df[(df["sample_date"] >= pd.to_datetime(date_range[0])) & (df["sample_date"] <= pd.to_datetime(date_range[1]))]

col1, col2, col3 = st.columns(3)
col1.metric("Total Samples", len(df))
col2.metric("Detected", df[df["value"] != "Not Detected"].shape[0])
col3.metric("Detection Rate", f"{(df[df['test_result'] != 'Not Detected'].shape[0] / len(df)) * 100:.2f}%")

# fig = px.bar(
#     df.groupby("sample_date")["test_result"].apply(lambda x: (x != "Not Detected").sum()).reset_index(),
#     x="sample_date", y="test_result", title="Listeria Detection Over Time",
#     template="plotly_dark", color_discrete_sequence=["#00C49F"]
# )
# st.plotly_chart(fig, use_container_width=True)

# 📈 Detection Breakdown by Sample Date
detection_df = df.copy()
detection_df["Detection"] = detection_df["test_result"].map(
    lambda v: "Detected" if v != "Not Detected" else "Not Detected"
)

# Group by date and detection type
datewise_df = (
    detection_df.groupby([detection_df["sample_date"].dt.date, "Detection"])
    .size()
    .reset_index(name="count")
)

# Plot grouped bar chart
fig = px.bar(
    datewise_df,
    x="sample_date",
    y="count",
    color="Detection",
    title="Listeria Detection (Detected vs Not Detected) Over Time",
    barmode="group",
    color_discrete_map={
       "Detected": "#BF00FF",       # Neon Purple
       "Not Detected": "#39FF14"    # Neon Green
    },
    template="plotly_dark"
)
fig.update_layout(
    xaxis_title="Sample Date",
    yaxis_title="Number of Samples",
    legend_title="Detection Result",
)
st.plotly_chart(fig, use_container_width=True)
