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

if not all(col in data.columns for col in ['sub_area', 'before_during', 'test_result']):
    st.error("Required columns missing in MongoDB data.")
    st.stop()

data['before_during'] = data['before_during'].str.upper()
data['test_result'] = data['test_result'].str.strip()

# Summarize
grouped = data.groupby(['sub_area', 'before_during'])
summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# Title
st.title("📊 Listeria Detection Analysis")

# Chart
for phase in summary['before_during'].unique():
    st.subheader(f"{phase} Phase")

    df = summary[summary['before_during'] == phase]

    fig = go.Figure()

    # Bar chart: Total Tests
    fig.add_trace(go.Bar(
        x=df['sub_area'],
        y=df['total_tests'],
        name='Total Tests',
        marker_color='rgba(0, 123, 255, 0.7)',
        width=0.5,
        yaxis='y1'
    ))

    # Line chart: Detection Rate
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        line=dict(color='crimson', shape='spline', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))

    # Layout
    fig.update_layout(
        template='plotly_white',
        height=500,
        xaxis=dict(title='Sub Area'),
        yaxis=dict(
            title='Total Tests',
            titlefont=dict(color='rgba(0,123,255,1)'),
            tickfont=dict(color='rgba(0,123,255,1)')
        ),
        yaxis2=dict(
            title='Detection Rate (%)',
            titlefont=dict(color='crimson'),
            tickfont=dict(color='crimson'),
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=60, r=60, t=60, b=60)
    )

    st.plotly_chart(fig, use_container_width=True)
