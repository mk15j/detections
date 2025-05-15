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
# slope, intercept = np.polyfit(x_vals, y_vals, 1)
# trend_y = slope * x_vals + intercept

# Fit a 2nd-degree polynomial trend line
coeffs = np.polyfit(x_vals, y_vals, deg=2)
poly = np.poly1d(coeffs)
trend_y = poly(x_vals)


# Create the combo chart
st.subheader("Detection Summary")

fig = go.Figure()


# Bar for total tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['total_tests'],
    name='Total Tests',
    marker_color='#f2bb05',
    yaxis='y1'
))

# Bar for detected tests
fig.add_trace(go.Bar(
    x=summary['week'],
    y=summary['detected_tests'],
    name='Detected Tests',
    marker_color='#d74e09',
    yaxis='y1'
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

# Dotted trend line
fig.add_trace(go.Scatter(
    x=summary['week'],
    y=trend_y,
    name='Trend Line',
    mode='lines',
    line=dict(color='#8b1e3f', dash='dot'),  
    yaxis='y2'
))


fig.update_layout(
    title="Detection Summary by Week",
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
    bargap=0.3,        # Gap between weeks (x categories)
    bargroupgap=0      # No gap between bars in the same group (Total vs Detected)
)

st.plotly_chart(fig, use_container_width=True)


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
    title='📍 Detection Rate by Area',
    xaxis=dict(title='Area', categoryorder='array', categoryarray=area_summary['sub_area']),
    yaxis=dict(title='Detection Rate (%)', range=[0, 60]),
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
    marker_color='#f2bb05',
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

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate before Production',
    xaxis=dict(
        title='Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
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
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.1,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='before_production_trend')


# Filter for 'During Production'
filtered = data[data['before_during'] == 'DP']

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

# Layout with top legend and all date ticks
fig.update_layout(
    title='# Samples vs Detection Rate During Production',
    xaxis=dict(
        title='Date',
        type='date',
        tickangle=-90,
        tickformat='%d-%b',  # e.g., 12-May
        dtick='D1',          # Force daily tick labels
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
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.1,  # Above chart
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='during_production_trend')


# Ensure datetime format
data['sample_date'] = pd.to_datetime(data['sample_date'])

# Group and pivot to get counts for BP and DP
summary = data.groupby(['sample_date', 'before_during'])['test_result'].count().reset_index()
summary = summary.pivot(index='sample_date', columns='before_during', values='test_result').fillna(0)
summary = summary.sort_index()

# Rename columns if necessary
summary = summary.rename(columns={'BP': 'Before Production', 'DP': 'During Production'})

# Create chart
fig = go.Figure()

# Add BP bars
fig.add_trace(go.Bar(
    x=summary.index,
    y=summary['Before Production'],
    name='Before Production',
    marker_color='#64b5f6'
))

# Add DP bars
fig.add_trace(go.Bar(
    x=summary.index,
    y=summary['During Production'],
    name='During Production',
    marker_color='#ffb74d'
))

# Layout
fig.update_layout(
    title='Total Samples: Before vs During Production',
    barmode='group',
    xaxis=dict(
        title='Date',
        tickangle=-90,
        tickformat='%d-%b',
        dtick='D1',
        type='date'
    ),
    yaxis=dict(title='Total Samples'),
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.1,
        xanchor='center',
        x=0.5
    ),
    height=500
)

# Streamlit chart
st.plotly_chart(fig, use_container_width=True, key='bp_dp_comparison')

