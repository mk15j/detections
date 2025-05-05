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
col2.metric("Detected", df[df["test_result"] != "Not Detected"].shape[0])
col3.metric("Detection Rate", f"{(df[df['test_result'] != 'Not Detected'].shape[0] / len(df)) * 100:.2f}%")


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
       "Detected": "#42a5f5",       
       "Not Detected": "#bbdefb"   
    },
    template="plotly_dark"
)
fig.update_layout(
    xaxis_title="Sample Date",
    yaxis_title="Number of Samples",
    legend_title="Detection Result",
)
st.plotly_chart(fig, use_container_width=True)

# @st.cache_data
# def load_data():
#     data = list(listeria_collection.find({}, {"_id": 0}))
#     df = pd.DataFrame(data)
#     if "sample_date" in df.columns:
#         df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
#     return df

# df = load_data()
# if df.empty:
#     st.warning("No data available.")
#     st.stop()

st.sidebar.header("Filters")
date_range = st.sidebar.date_input("Date Range", [df["sample_date"].min(), df["sample_date"].max()])
df_filtered = df[(df["sample_date"] >= pd.to_datetime(date_range[0])) & (df["sample_date"] <= pd.to_datetime(date_range[1]))]


# 🧬 Detection Outcome by Code with Trendline
st.subheader("🧬 Detection Outcome by Code - Trendline")

if "test_result" in df_filtered.columns and "location_code" in df_filtered.columns:
    import plotly.graph_objects as go

    # Clean and normalize detection values
    df_filtered["Detection"] = df_filtered["test_result"].map({
        "Detected": "Detected",
        "Not Detected": "Not Detected"
    }).fillna("Unknown")

    # Group by code and detection outcome
    heat_df = df_filtered.groupby(["location_code", "Detection"]).size().reset_index(name="count")
    pivot_df = heat_df.pivot(index="location_code", columns="Detection", values="count").fillna(0)

    # Prepare data
    codes = pivot_df.index.tolist()
    detected_counts = pivot_df["Detected"] if "Detected" in pivot_df.columns else pd.Series([0]*len(codes), index=codes)
    not_detected_counts = pivot_df["Not Detected"] if "Not Detected" in pivot_df.columns else pd.Series([0]*len(codes), index=codes)

    # Plotting
    fig = go.Figure()

    # Not Detected Bar
    fig.add_trace(go.Bar(
        x=codes,
        y=not_detected_counts,
        name="Not Detected",
        marker_color="#bbdefb"  
    ))

    # Detected Bar
    fig.add_trace(go.Bar(
        x=codes,
        y=detected_counts,
        name="Detected",
        marker_color="#42a5f5"  
    ))

    # Trendline (Detected)
    fig.add_trace(go.Scatter(
        x=codes,
        y=detected_counts,
        name="Detection Trendline",
        mode="lines+markers",
        line=dict(color="#0d21a1", width=1, dash="dash") 
    ))

    # Layout
    fig.update_layout(
        barmode="stack",
        # title="🧬 Detection Outcome by Code (with Detection Trendline)",
        xaxis_title="Location Code",
        yaxis_title="Number of Samples",
        legend_title="Detection Outcome",
        plot_bgcolor="#FFFFFF",  # Dark background
        paper_bgcolor="#FFFFFF",
        font=dict(color="#000000")  # White font for dark mode
    )

    st.plotly_chart(fig, use_container_width=True)


# 🧬 Detection ratio for Samples
st.subheader("🧬 Detection Ratio for Samples")

if 'value' in df_filtered.columns:
    value_counts = df_filtered['test_result'].value_counts().reset_index()
    value_counts.columns = ['test_result', 'count']

    # Define custom neon colors for categories
    color_map = {
        "Detected": "#42a5f5",        # Neon Purple 
        "Not Detected": "#bbdefb"     # Neon Green
    }

    # Ensure the colors align with the data order
    custom_colors = [color_map.get(v, "#FFFFFF") for v in value_counts['test_result']]

    fig_value_donut = px.pie(
        value_counts,
        names='test_result',
        values='count',
        hole=0.4,
        # title="Listeria Test Result Breakdown",
        color_discrete_sequence=custom_colors
    )

    # Optional: dark theme style
    fig_value_donut.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#FFFFFF")
    )

    st.plotly_chart(fig_value_donut, use_container_width=True)


