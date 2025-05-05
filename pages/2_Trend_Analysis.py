import streamlit as st
st.set_page_config(page_title="Trend Analysis", layout="wide")  # MUST be first Streamlit command

import pandas as pd
import plotly.express as px
from utils.db import listeria_collection
import plotly.graph_objects as go

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


# # 📅 Page content
# st.title("📅 Trend Analysis")

# Load Data
data = pd.DataFrame(list(listeria_collection.find()))

# Validate essential columns
required_columns = ['sub_area', 'before_during', 'test_result']
if not all(col in data.columns for col in required_columns):
    st.error("Required columns missing in MongoDB data.")
    st.stop()

# Normalize columns
data['before_during'] = data['before_during'].str.upper()
data['test_result'] = data['test_result'].str.strip()

# Group and summarize data
grouped = data.groupby(['sub_area', 'before_during'])

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# Title
st.title("🧪 Listeria Detection Overview by Sub Area")

# Combo Chart Loop
for bpdp in summary['before_during'].unique():
    st.markdown(f"### `{bpdp}` Phase Summary")

    df = summary[summary['before_during'] == bpdp]

    fig = go.Figure()

    # Bar chart: Total tests with custom style
    fig.add_trace(go.Bar(
        x=df['sub_area'],
        y=df['total_tests'],
        name='Total Tests',
        marker=dict(
            color='rgba(0,123,255,0.8)',
            line=dict(color='rgba(0,123,255,1.0)', width=1.5)
        ),
        hovertemplate='%{x}<br>Total Tests: %{y}<extra></extra>',
        width=0.5,
        yaxis='y1'
    ))

    # Line chart: Detection rate
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        line=dict(shape='spline', color='crimson', width=3),
        marker=dict(size=8),
        hovertemplate='%{x}<br>Detection Rate: %{y:.2f}%<extra></extra>',
        yaxis='y2'
    ))

    # Layout styling
    fig.update_layout(
        template='plotly_white',
        height=500,
        xaxis=dict(title='Sub Area'),
        yaxis=dict(
            title='Total Tests',
            showgrid=False,
            titlefont=dict(color='rgba(0,123,255,1)'),
            tickfont=dict(color='rgba(0,123,255,1)')
        ),
        yaxis2=dict(
            title='Detection Rate (%)',
            overlaying='y',
            side='right',
            range=[0, 100],
            titlefont=dict(color='crimson'),
            tickfont=dict(color='crimson'),
            showgrid=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        plot_bgcolor='rgba(245, 245, 245, 1)',
        margin=dict(t=60, b=40, l=40, r=40),
    )

    st.plotly_chart(fig, use_container_width=True)
