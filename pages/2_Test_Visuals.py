import streamlit as st
st.set_page_config(page_title="Test Visuals", layout="wide")  # 🔧 Must be the very first Streamlit call

import pandas as pd
import plotly.express as px
from utils.db import listeria_collection

# 🔐 Authentication check
if "user" not in st.session_state:
    st.warning("Please log in to access this page.")
    st.stop()

# 👤 Show user info and logout
st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.user['username']}`")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("🔓 Logged out successfully.")
    st.stop()

# 🥚 Main content
# st.title("🥚 Test Summary Visuals")

@st.cache_data
def load_data():
    data = list(listeria_collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    if "sample_date" in df.columns:
        df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
    return df

df = load_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

st.sidebar.header("Filters")
date_range = st.sidebar.date_input("Date Range", [df["sample_date"].min(), df["sample_date"].max()])
df_filtered = df[(df["sample_date"] >= pd.to_datetime(date_range[0])) & (df["sample_date"] <= pd.to_datetime(date_range[1]))]


# 🧬 Detection Outcome by Code with Trendline
st.subheader("🧬 Detection Outcome by Code - Trendline")

if "value" in df_filtered.columns and "code" in df_filtered.columns:
    import plotly.graph_objects as go

    # Clean and normalize detection values
    df_filtered["Detection"] = df_filtered["value"].map({
        "Detected": "Detected",
        "Not Detected": "Not Detected"
    }).fillna("Unknown")

    # Group by code and detection outcome
    heat_df = df_filtered.groupby(["code", "Detection"]).size().reset_index(name="count")
    pivot_df = heat_df.pivot(index="code", columns="Detection", values="count").fillna(0)

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
        marker_color="#39FF14"  # Neon Green
    ))

    # Detected Bar
    fig.add_trace(go.Bar(
        x=codes,
        y=detected_counts,
        name="Detected",
        marker_color="#8A00C4"  # Neon Purple
    ))

    # Trendline (Detected)
    fig.add_trace(go.Scatter(
        x=codes,
        y=detected_counts,
        name="Detection Trendline",
        mode="lines+markers",
        line=dict(color="#FF3131", width=1, dash="dash")  # Neon Red
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


# 🔢 Test Frequency by Code
st.subheader("🔢 Test Frequency by Code")
code_count = df_filtered["code"].value_counts().reset_index()
code_count.columns = ["Code", "Test Count"]
fig_code = px.bar(code_count, x="Code", y="Test Count", color="Test Count", color_continuous_scale="Sunsetdark")
# title="Number of Tests by Code", 
st.plotly_chart(fig_code, use_container_width=True)

# 🏭 Test Frequency by Description
# st.subheader("🏭 Test Frequency by Description")
# desc_count = df_filtered["eng_description"].value_counts().reset_index()
# desc_count.columns = ["Description", "Test Count"]
# fig_desc = px.bar(desc_count, x="Test Count", y="Description", orientation="h", title="Test Frequency by Sample Description", color="Test Count", color_continuous_scale="Agsunset")
# st.plotly_chart(fig_desc, use_container_width=True)

# 🧬 Detection Outcome by Code
# st.subheader("🧬 Detection Outcome by Code - Stacked Chart")
# if "value" in df_filtered.columns:
#     heat_df = df_filtered.groupby(["code", "value"]).size().reset_index(name="count")
#     fig_heat = px.bar(heat_df, x="code", y="count", color="value", barmode="stack")
#     #, title="Detection Outcome by Test Code"
#     st.plotly_chart(fig_heat, use_container_width=True)


# 📊 Detection Outcome by Code (Area Chart)
st.subheader("📊 Detection Outcome by Code - Area Chart")

if "code" in df_filtered.columns and "value" in df_filtered.columns:
    df_code_area = df_filtered.copy()

    # Normalize detection values
    df_code_area["Detection"] = df_code_area["value"].map({
        "Detected": "Detected",
        "Not Detected": "Not Detected"
    }).fillna("Unknown")

    # Group by code and detection status
    detection_by_code = df_code_area.groupby(["code", "Detection"]).size().reset_index(name="Count")

    # Plot as area chart
    fig_area_code = px.area(
        detection_by_code,
        x="code",
        y="Count",
        color="Detection",
        line_group="Detection",
        # title="Detection Outcome by Code (Detected vs Not Detected)",
        color_discrete_map={"Detected": "#8A00C4", "Not Detected": "#39FF14", "Unknown": "#FF5C00"}
    )

    fig_area_code.update_layout(
        xaxis_title="Test Code (Location)",
        yaxis_title="Number of Samples",
        legend_title="Detection Outcome"
    )

    st.plotly_chart(fig_area_code, use_container_width=True)



# 🧬 Detection ratio for Samples
st.subheader("🧬 Detection Ratio for Samples")

if 'value' in df_filtered.columns:
    value_counts = df_filtered['value'].value_counts().reset_index()
    value_counts.columns = ['value', 'count']

    # Define custom neon colors for categories
    color_map = {
        "Detected": "#8A00C4",        # Neon Purple 
        "Not Detected": "#39FF14"     # Neon Green
    }

    # Ensure the colors align with the data order
    custom_colors = [color_map.get(v, "#FFFFFF") for v in value_counts['value']]

    fig_value_donut = px.pie(
        value_counts,
        names='value',
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





