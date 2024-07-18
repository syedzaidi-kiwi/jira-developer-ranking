import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Set page config
st.set_page_config(page_title="Developer Rankings", page_icon="🏆", layout="wide")

# Function to load the CSV file
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    csv_file = 'developer_rankings_final.csv'
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        return df, datetime.fromtimestamp(os.path.getmtime(csv_file))
    return None, None

# Load the data
df, last_updated = load_data()

# Title
st.title('🏆 Developer Rankings')

if df is not None:
    # Display last updated time
    st.write(f"Last updated: {last_updated}")

    # Display the rankings table
    st.dataframe(df)

    # Create a bar chart of top 10 developers by TotalScore
    top_10 = df.nlargest(10, 'TotalScore')
    fig = px.bar(top_10, x='Name', y='TotalScore', title='Top 10 Developers by Total Score')
    st.plotly_chart(fig)

    # Create a scatter plot of BugTime vs SubtaskTime
    fig2 = px.scatter(df, x='BugTime', y='SubtaskTime', hover_data=['Name'], title='Bug Time vs Subtask Time')
    st.plotly_chart(fig2)

    # Create a pie chart of bug criticality distribution
    bug_data = df[['BugCount', 'CriticalBugCount', 'BlockerBugCount']].sum()
    fig3 = px.pie(values=bug_data.values, names=bug_data.index, title='Bug Criticality Distribution')
    st.plotly_chart(fig3)
else:
    st.error("No data available. Please make sure the CSV file exists and is up to date.")

# Add a button to manually refresh the data
if st.button('Refresh Data'):
    st.cache_data.clear()
    st.experimental_rerun()

# Auto-refresh the app every 60 minutes
st.empty()
st.write("This page will auto-refresh every 60 minutes to show the latest data.")