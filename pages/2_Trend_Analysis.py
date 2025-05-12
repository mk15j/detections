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

summary['detection_rate_percent'] = ((summary['detected_tests'] / summary['total_tests']) * 100).round(1)

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
        width=0.3  # Adjust bar thickness (default is 0.8)
    ))

    # Line for detection rate % with custom color
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        marker=dict(color='#0d21a1'),
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
        legend=dict(x=0.2, xanchor="center", orientation="h"),
        height=500,
        bargap=0.05,  # Gap between bars
        bargroupgap=0.1  # Gap between groups of bars (if applicable)
    )

    st.plotly_chart(fig, use_container_width=True)





import numpy as np

# Compute detection stats by week (without categorizing by before_during)
grouped = data.groupby(['week'])

summary = grouped['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

summary['detection_rate_percent'] = (
    (summary['detected_tests'] / summary['total_tests']) * 100
).round(1)

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
    marker_color='#bbdefb',
    yaxis='y1',
    width=0.2
))

# Bar for detected tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['detected_tests'],
    name='Detected Tests',
    marker_color='#42a5f5',
    yaxis='y1',
    width=0.2
))

# Line for detection rate %
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    marker=dict(color='#1976d2'),
    line=dict(color='#1976d2'),
    yaxis='y2'
))

# Dotted trend line
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=trend_y,
    name='Trend Line',
    mode='lines',
    line=dict(color='#90caf9', dash='dot'),  
    yaxis='y2'
))

# Layout
fig.update_layout(
    title="Detection Summary (All Production Phases)",
    # xaxis_title="Week",
    yaxis=dict(
        title="Total/Detected Tests",
        side="left",
        range=[0, 200]
    ),
    yaxis2=dict(
        title="Detection Rate (%)",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    legend=dict(x=0.2, xanchor="center", orientation="h"),
    height=500,
    bargap=0.05,
    bargroupgap=0.1
)

st.plotly_chart(fig, use_container_width=True)


# # Group by week and compute test stats
# grouped = data.groupby(['week'])
# summary = grouped['test_result'].agg(
#     total_tests='count',
#     detected_tests=lambda x: (x == 'Detected').sum()
# ).reset_index()

# summary['detection_rate_percent'] = (
#     (summary['detected_tests'] / summary['total_tests']) * 100
# ).round(1)

# # Extract numeric week for sorting
# summary['week_num'] = summary['week'].str.extract(r'Week-(\d+)').astype(int)
# summary = summary.sort_values('week_num')

# # Trend line (optional)
# x_vals = summary['week_num']
# y_vals = summary['detection_rate_percent']
# slope, intercept = np.polyfit(x_vals, y_vals, 1)
# trend_y = slope * x_vals + intercept

# # 📊 Combined chart
# st.subheader("📈 Weekly Detection Analysis")

# fig = go.Figure()

# # Bar: Sample Count (Total Tests)
# fig.add_trace(go.Bar(
#     x=summary['week'],
#     y=summary['total_tests'],
#     name='Sample Count',
#     marker_color='#64b5f6',
#     yaxis='y1',
#     width=0.25
# ))

# # Bar: Detected Count
# fig.add_trace(go.Bar(
#     x=summary['week'],
#     y=summary['detected_tests'],
#     name='Detected Count',
#     marker_color='#1976d2',
#     yaxis='y1',
#     width=0.25
# ))

# # Line: Detection Rate (%)
# fig.add_trace(go.Scatter(
#     x=summary['week'],
#     y=summary['detection_rate_percent'],
#     name='Detection Rate (%)',
#     mode='lines+markers',
#     line=dict(color='#C00000', width=2),
#     marker=dict(size=6),
#     yaxis='y2'
# ))

# # Optional trend line (dotted)
# fig.add_trace(go.Scatter(
#     x=summary['week'],
#     y=trend_y,
#     name='Trend Line',
#     mode='lines',
#     line=dict(color='gray', dash='dot'),
#     yaxis='y2'
# ))

# # Layout
# fig.update_layout(
#     title="📊 Weekly Detection Rate vs Sample Volume",
#     xaxis=dict(title="Week"),
#     yaxis=dict(
#         title="Sample / Detected Count",
#         side="left"
#     ),
#     yaxis2=dict(
#         title="Detection Rate (%)",
#         overlaying="y",
#         side="right",
#         range=[0, 100]
#     ),
#     barmode='group',
#     legend=dict(x=0.01, y=1.15, orientation="h"),
#     height=550,
#     bargap=0.1
# )

# st.plotly_chart(fig, use_container_width=True)

# # Group by area and calculate detection rate
# area_summary = data.groupby('sub_area')['test_result'].agg(
#     total_tests='count',
#     detected_tests=lambda x: (x == 'Detected').sum()
# ).reset_index()

# area_summary['detection_rate_percent'] = (
#     (area_summary['detected_tests'] / area_summary['total_tests']) * 100
# ).round(1)

# # Sort by detection rate for better readability
# area_summary = area_summary.sort_values(by='detection_rate_percent', ascending=False)

# # Plot bar chart using go.Figure for full control
# fig = go.Figure()

# fig.add_trace(go.Bar(
#     x=area_summary['sub_area'],
#     y=area_summary['detection_rate_percent'],
#     name='Detection Rate (%)',
#     marker_color='#bbdefb',
#     text=area_summary['detection_rate_percent'],
#     textposition='outside'
# ))

# # Layout updates
# fig.update_layout(
#     title='📍 Detection Rate by Area',
#     xaxis=dict(title='Area'),
#     yaxis=dict(title='Detection Rate (%)', range=[0, 100]),
#     height=500,
#     legend=dict(title='Legend', orientation='h', y=-0.2),
#     uniformtext_minsize=8,
#     uniformtext_mode='hide'
# )

# st.plotly_chart(fig, use_container_width=True)

# # Group by area and calculate detection rate
# area_summary = data.groupby('sub_area')['test_result'].agg(
#     total_tests='count',
#     detected_tests=lambda x: (x == 'Detected').sum()
# ).reset_index()

# area_summary['detection_rate_percent'] = (
#     (area_summary['detected_tests'] / area_summary['total_tests']) * 100
# ).round(1)

# # ✅ Sort by area name (alphabetical order)
# area_summary = area_summary.sort_values(by='sub_area')

# # Plot bar chart
# fig = go.Figure()

# fig.add_trace(go.Bar(
#     x=area_summary['sub_area'],
#     y=area_summary['detection_rate_percent'],
#     name='Detection Rate (%)',
#     marker_color='#bbdefb',
#     text=area_summary['detection_rate_percent'],
#     textposition='outside'
# ))

# # Layout settings
# fig.update_layout(
#     title='📍 Detection Rate by Area (Alphabetical)',
#     xaxis=dict(title='Area', categoryorder='array', categoryarray=area_summary['sub_area']),
#     yaxis=dict(title='Detection Rate (%)', range=[0, 100]),
#     height=500,
#     legend=dict(title='Legend', orientation='h', y=-0.2),
#     uniformtext_minsize=8,
#     uniformtext_mode='hide'
# )

# st.plotly_chart(fig, use_container_width=True)
# Group by area and calculate detection rate
area_summary = data.groupby('sub_area')['test_result'].agg(
    total_tests='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

area_summary['detection_rate_percent'] = (
    (area_summary['detected_tests'] / area_summary['total_tests']) * 100
).round(1)

# ✅ Sort by area name (alphabetical order)
area_summary = area_summary.sort_values(by='sub_area')

# Plot bar chart
fig = go.Figure()

fig.add_trace(go.Bar(
    x=area_summary['sub_area'],
    y=area_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    marker_color='#bbdefb',
    text=area_summary['detection_rate_percent'],
    textposition='outside'
))

# Layout settings
fig.update_layout(
    title='📍 Detection Rate by Area (Alphabetical)',
    xaxis=dict(title='Area', categoryorder='array', categoryarray=area_summary['sub_area']),
    yaxis=dict(title='Detection Rate (%)', range=[0, 100]),
    height=500,
    legend=dict(title='Legend', orientation='h', y=-0.2),
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

# ✅ Add a unique key to avoid duplicate element errors
st.plotly_chart(fig, use_container_width=True, key="detection_rate_by_area")


# Group data
area_summary = data.groupby('sub_area')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
area_summary['detection_rate_percent'] = (
    (area_summary['detected_tests'] / area_summary['total_samples']) * 100
).round(1)

# Sort areas alphabetically
area_summary = area_summary.sort_values(by='sub_area')

# Create figure
fig = go.Figure()

# Bar for # Samples
fig.add_trace(go.Bar(
    x=area_summary['sub_area'],
    y=area_summary['total_samples'],
    name='Total Samples',
    marker_color='#bbdefb',
    yaxis='y1'
))

# Line for % Detection Rate
fig.add_trace(go.Scatter(
    x=area_summary['sub_area'],
    y=area_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers+text',
    text=area_summary['detection_rate_percent'],
    textposition='top center',
    yaxis='y2',
    line=dict(color='crimson', width=3)
))

# Layout
fig.update_layout(
    title='# Samples vs % Detection Rate by Area',
    xaxis=dict(title='Area', categoryorder='array', categoryarray=area_summary['sub_area']),
    yaxis=dict(title='Total Samples', side='left', showgrid=False),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    height=500
)

# Display in Streamlit with unique key
st.plotly_chart(fig, use_container_width=True, key="samples_vs_detection_rate")

# # Filter for 'Before Production'
# filtered = data[data['before_during'] == 'BP']

# # Ensure date column is datetime
# filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# # Group by Date
# date_summary = filtered.groupby('sample_date')['test_result'].agg(
#     total_samples='count',
#     detected_tests=lambda x: (x == 'Detected').sum()
# ).reset_index()

# # Calculate detection rate
# date_summary['detection_rate_percent'] = (
#     (date_summary['detected_tests'] / date_summary['total_samples']) * 100
# ).round(1)

# # Sort by date
# date_summary = date_summary.sort_values(by='sample_date')

# # Create chart
# fig = go.Figure()

# # Bar for total samples
# fig.add_trace(go.Bar(
#     x=date_summary['sample_date'],
#     y=date_summary['total_samples'],
#     name='Total Samples',
#     marker_color='#bbdefb',
#     yaxis='y1'
# ))

# # Line for detection rate
# fig.add_trace(go.Scatter(
#     x=date_summary['sample_date'],
#     y=date_summary['detection_rate_percent'],
#     name='Detection Rate (%)',
#     mode='lines+markers',
#     line=dict(color='crimson', width=2),
#     yaxis='y2'
# ))

# # Layout
# fig.update_layout(
#     title='# Samples vs Detection Rate before Production',
#     xaxis=dict(
#         title='Date',
#         rangeslider=dict(visible=True),  # Scrollable X-axis
#         type='date'
#     ),
#     yaxis=dict(title='Total Samples', side='left'),
#     yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
#     legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
#     height=500
# )

# # Streamlit chart
# st.plotly_chart(fig, use_container_width=True, key='before_production_trend')

# Filter for 'Before Production'
filtered = data[data['before_during'] == 'BP']

# Ensure date column is datetime
filtered['sample_date'] = pd.to_datetime(filtered['sample_date'])

# Group by Date
date_summary = filtered.groupby('sample_date')['test_result'].agg(
    total_samples='count',
    detected_tests=lambda x: (x == 'Detected').sum()
).reset_index()

# Calculate detection rate
date_summary['detection_rate_percent'] = (
    (date_summary['detected_tests'] / date_summary['total_samples']) * 100
).round(1)

# Sort by date
date_summary = date_summary.sort_values(by='sample_date')

# Create chart
fig = go.Figure()

# Bar for total samples
fig.add_trace(go.Bar(
    x=date_summary['sample_date'],
    y=date_summary['total_samples'],
    name='Total Samples',
    marker_color='#bbdefb',
    yaxis='y1'
))

# Line for detection rate
fig.add_trace(go.Scatter(
    x=date_summary['sample_date'],
    y=date_summary['detection_rate_percent'],
    name='Detection Rate (%)',
    mode='lines+markers',
    line=dict(color='crimson', width=2),
    yaxis='y2'
))

# Layout with minimal slider bar (no mini chart)
fig.update_layout(
    title='# Samples vs Detection Rate before Production',
    xaxis=dict(
        title='Date',
        type='date',
        rangeslider=dict(
            visible=True,
            thickness=0.05,
            bgcolor='lightgrey',
            bordercolor='grey',
            borderwidth=1
        ),
        showgrid=True
    ),
    yaxis=dict(title='Total Samples', side='left'),
    yaxis2=dict(title='Detection Rate (%)', overlaying='y', side='right', range=[0, 100]),
    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='before_production_trend')
