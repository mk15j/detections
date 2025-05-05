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

# @st.cache_data
# def load_data():
#     df = pd.DataFrame(listeria_collection.find({}, {"_id": 0}))
#     df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
#     return df

# df = load_data()

# # ✅ Ensure necessary columns exist
# if "sample_date" not in df.columns or "value" not in df.columns:
#     st.warning("The dataset is missing 'sample_date' or 'value' columns.")
#     st.stop()

# # 🧪 Label Detection
# df["Detection"] = df["test_result"].apply(lambda x: "Detected" if x != "Not Detected" else "Not Detected")

# # 🗓️ Restrict date range for X-axis
# start_date = pd.to_datetime("2025-02-03")
# end_date = pd.to_datetime("2025-04-15")

# df = df[(df["sample_date"] >= start_date) & (df["sample_date"] <= end_date)]

# # 📊 Group by date and detection
# if df.empty:
#     st.warning("No data available in the selected date range.")
# else:
#     trend_df = df.groupby(["sample_date", "Detection"]).size().reset_index(name="count")

#     # 💎 Plot line chart with value labels and diamond markers
#     fig = px.line(
#         trend_df,
#         x="sample_date",
#         y="count",
#         color="Detection",
#         title="Detection Trend Over Time",
#         template="plotly_dark",
#         color_discrete_map={
#             "Detected": "#8A00C4",       # Neon Purple
#             "Not Detected": "#39FF14"    # Neon Green
#         },
#         markers=True
#     )

#     # 🔧 Customize markers and annotations
#     fig.update_traces(marker=dict(symbol="diamond", size=10), text=trend_df["count"], textposition="top center")

#     # 🛠️ Customize x-axis to show all dates vertically
#     all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
#     fig.update_layout(
#         xaxis=dict(
#             tickmode='array',
#             tickvals=all_dates,
#             tickformat='%d-%b',
#             tickangle=90
#         ),
#         xaxis_title="Sample Date",
#         yaxis_title="Number of Samples",
#         legend_title="Detection Result"
#     )

#     st.plotly_chart(fig, use_container_width=True)






# # df = load_data()

# # trend = df.groupby(["test", "sample_date"])["value"].apply(lambda x: (x != "Not Detected").sum()).reset_index()

# # fig = px.line(trend, x="sample_date", y="value", color="test",
# #               title="Detection Trends by Test",
# #               template="plotly_dark", color_discrete_sequence=px.colors.qualitative.T10)

# # st.plotly_chart(fig, use_container_width=True)




# import streamlit as st
# import pandas as pd
# import pymongo


# # Connect to MongoDB
# client = pymongo.MongoClient("mongodb://localhost:27017")  # Update with your MongoDB URI
# db = client["koral"]
# collection = db["fresh"]

# Load data into a DataFrame
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

    # Bar for number of tests
    fig.add_trace(go.Bar(
        x=df['sub_area'],
        y=df['total_tests'],
        name='Total Tests',
        marker_color='skyblue',
        yaxis='y1'
    ))

    # Line for detection rate %
    fig.add_trace(go.Scatter(
        x=df['sub_area'],
        y=df['detection_rate_percent'],
        name='Detection Rate (%)',
        mode='lines+markers',
        marker=dict(color='red'),
        yaxis='y2'
    ))

    # Layout with secondary y-axis
    fig.update_layout(
        title=f"Sub-area Detection Rate and Test Count ({bpdp})",
        xaxis_title="Sub Area",
        yaxis=dict(
            title="Total Tests",
            side="left"
        ),
        yaxis2=dict(
            title="Detection Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100]
        ),
        legend=dict(x=0.5, xanchor="center", orientation="h"),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

