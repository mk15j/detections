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

# Validate required fields
required_cols = ['sub_area', 'before_during', 'test_result']
if not all(col in data.columns for col in required_cols):
    st.error(f"Missing required fields in data: {', '.join(required_cols)}")
    st.stop()

data['before_during'] = data['before_during'].str.upper()
data['test_result'] = data['test_result'].str.strip()

# Aggregate results
grouped = data.groupby(['sub_area', 'before_during'])
summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()
summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# Streamlit UI
st.title("📈 Listeria Detection Trend Analysis")

# Chart loop
for phase in summary['before_during'].unique():
    st.subheader(f"{phase} Phase")

    df = summary[summary['before_during'] == phase]

    fig = go.Figure()

    # Bar Chart
    fig.add_trace(go.Bar(
        x=df['sub_area'],
        y=df['total_tests'],
        name='Total Tests',
        marker_color='steelblue',
        yaxis='y1'
    ))

    # Line Chart
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        line=dict(color='crimson', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))

    # Layout - clean, safe, beautiful
    fig.update_layout(
        title=f"{phase} Phase - Test Summary",
        xaxis=dict(title='Sub Area'),
        yaxis=dict(
            title='Total Tests',
            showgrid=False,
            titlefont=dict(color='steelblue'),
            tickfont=dict(color='steelblue')
        ),
        yaxis2=dict(
            title='Detection Rate (%)',
            overlaying='y',
            side='right',
            showgrid=False,
            titlefont=dict(color='crimson'),
            tickfont=dict(color='crimson'),
            range=[0, 100]
        ),
        legend=dict(x=0.5, y=1.1, orientation='h', xanchor='center'),
        height=500,
        margin=dict(l=60, r=60, t=60, b=60),
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)
