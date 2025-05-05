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

# Load Data
data = pd.DataFrame(list(listeria_collection.find()))

# Ensure necessary fields are present
required_columns = ['sub_area', 'before_during', 'test_result']
if not all(col in data.columns for col in required_columns):
    st.error("Missing required columns in MongoDB data.")
    st.stop()

# Standardize column values
data['before_during'] = data['before_during'].str.upper()
data['test_result'] = data['test_result'].str.strip()

# Compute detection stats
grouped = data.groupby(['sub_area', 'before_during'])

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# Create combo chart for each before_during value
for bpdp in summary['before_during'].unique():
    st.subheader(f"Detection Summary for `{bpdp}`")

    df = summary[summary['before_during'] == bpdp]

    fig = go.Figure()

    # Bar for number of tests with adjusted bar width
    fig.add_trace(go.Bar(
        x=df['sub_area'],
        y=df['total_tests'],
        name='Total Tests',
        marker_color='#64b5f6', #neon orange
        yaxis='y1',
        width=0.1  # Adjust bar thickness (default is 0.8)
    ))

    # Line for detection rate % with custom color
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        marker=dict(color='#2196f3'),
        line=dict(color='#0d47a1'),  # Set line color to #C00000
        yaxis='y2'
    ))

    # Layout with secondary y-axis and adjusted bar thickness
    fig.update_layout(
        title=f"Sub-area Detection Rate and Test Count ({bpdp})",
        # xaxis_title="Sub Area",
        yaxis=dict(
            title="Total Tests",
            side="left",
            range=[0, 100]
        ),
        yaxis2=dict(
            title="Detection Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100]
        ),
        legend=dict(x=0.5, xanchor="center", orientation="h"),
        height=500,
        bargap=0.1,  # Gap between bars
        bargroupgap=0.1  # Gap between groups of bars (if applicable)
    )

    st.plotly_chart(fig, use_container_width=True)



# # Compute detection stats by week (without categorizing by before_during)
# grouped = data.groupby(['week'])

# summary = grouped['test_result'].agg(
#     total_tests='count',
#     detected_tests=lambda x: (x == 'Detected').sum()
# ).reset_index()

# summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# # Extract numeric part of week for proper sorting (e.g., "Week-12" → 12)
# summary['week_num'] = summary['week'].str.extract(r'Week-(\d+)').astype(int)

# # Sort by the extracted week number
# summary = summary.sort_values(by='week_num')

# # Create a single combo chart for total tests, detected tests, and detection rate
# st.subheader("Detection Summary")

# fig = go.Figure()

# # Bar for total tests (Column chart)
# fig.add_trace(go.Bar(
#     x=summary['week'],
#     y=summary['total_tests'],
#     name='Total Tests',
#     marker_color='skyblue',
#     yaxis='y1',
#     width=0.3
# ))

# # Bar for detected tests
# fig.add_trace(go.Bar(
#     x=summary['week'],
#     y=summary['detected_tests'],
#     name='Detected Tests',
#     marker_color='orange',
#     yaxis='y1',
#     width=0.3
# ))

# # Line for detection rate % (Secondary y-axis)
# fig.add_trace(go.Scatter(
#     x=summary['week'],
#     y=summary['detection_rate_percent'],
#     name='Detection Rate (%)',
#     mode='lines+markers',
#     marker=dict(color='#C00000'),
#     line=dict(color='#C00000'),
#     yaxis='y2'
# ))

# # Layout with secondary y-axis and adjusted bar thickness
# fig.update_layout(
#     title="Detection Summary (All Production Phases)",
#     # xaxis_title="Week",
#     yaxis=dict(
#         title="Total/Detected Tests",
#         side="left",
#         range=[0, 100]
#     ),
#     yaxis2=dict(
#         title="Detection Rate (%)",
#         overlaying="y",
#         side="right",
#         range=[0, 100]
#     ),
#     legend=dict(x=0.5, xanchor="center", orientation="h"),
#     height=500,
#     bargap=0.2,
#     bargroupgap=0.1
# )

# st.plotly_chart(fig, use_container_width=True)


import numpy as np

# Compute detection stats by week (without categorizing by before_during)
grouped = data.groupby(['week'])

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (summary['detected_tests'] / summary['total_tests']) * 100

# Extract numeric part of week for proper sorting (e.g., "Week-12" → 12)
summary['week_num'] = summary['week'].str.extract(r'Week-(\d+)').astype(int)

# Sort by the extracted week number
summary = summary.sort_values(by='week_num')

# Fit a linear trend line to detection_rate_percent
x_vals = summary['week_num']
y_vals = summary['detection_rate_percent']
slope, intercept = np.polyfit(x_vals, y_vals, 1)
trend_y = slope * x_vals + intercept

# Create the combo chart
st.subheader("Detection Summary")

fig = go.Figure()

# Bar for total tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['total_tests'],
    name='Total Tests',
    marker_color='skyblue',
    yaxis='y1',
    width=0.3
))

# Bar for detected tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['detected_tests'],
    name='Detected Tests',
    marker_color='orange',
    yaxis='y1',
    width=0.3
))

# Line for detection rate %
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    marker=dict(color='#C00000'),
    line=dict(color='#C00000'),
    yaxis='y2'
))

# Dotted trend line (neon purple)
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=trend_y,
    name='Trend Line',
    mode='lines',
    line=dict(color='#D300FF', dash='dot'),  # Neon purple with dotted style
    yaxis='y2'
))

# Layout
fig.update_layout(
    title="Detection Summary (All Production Phases)",
    # xaxis_title="Week",
    yaxis=dict(
        title="Total/Detected Tests",
        side="left",
        range=[0, 100]
    ),
    yaxis2=dict(
        title="Detection Rate (%)",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    legend=dict(x=0.5, xanchor="center", orientation="h"),
    height=500,
    bargap=0.2,
    bargroupgap=0.1
)

st.plotly_chart(fig, use_container_width=True)

