import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
from io import StringIO

# Set page config
st.set_page_config(page_title="Developer Rankings", page_icon="🏆", layout="wide")

# Function to load the CSV file from GitHub
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    # GitHub raw content URL for your CSV file
    github_csv_url = "https://raw.githubusercontent.com/syedzaidi-kiwi/jira-developer-ranking/main/developer_rankings_final.csv"
    
    response = requests.get(github_csv_url)
    if response.status_code == 200:
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        last_updated = datetime.now()  # Using current time as GitHub doesn't provide last modified time easily
        return df, last_updated
    else:
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

    # Add filters
    st.sidebar.header("Filters")
    
    # Filter by developer name
    selected_developers = st.sidebar.multiselect(
        "Select Developers",
        options=df['Name'].unique(),
        default=[]
    )

    # Filter by total score range
    score_range = st.sidebar.slider(
        "Total Score Range",
        float(df['TotalScore'].min()),
        float(df['TotalScore'].max()),
        (float(df['TotalScore'].min()), float(df['TotalScore'].max()))
    )

    # Apply filters
    if selected_developers:
        df = df[df['Name'].isin(selected_developers)]
    df = df[(df['TotalScore'] >= score_range[0]) & (df['TotalScore'] <= score_range[1])]

    # Display filtered data
    st.subheader("Filtered Rankings")
    st.dataframe(df)

else:
    st.error("No data available. Please check the GitHub repository or your internet connection.")

# Add a button to manually refresh the data
if st.button('Refresh Data'):
    st.cache_data.clear()
    st.experimental_rerun()

# Information about auto-refresh
st.sidebar.info("This page will auto-refresh every 60 minutes to show the latest data.")

# Footer
st.markdown("---")
st.markdown("Developer Rankings Dashboard - Created with Streamlit")