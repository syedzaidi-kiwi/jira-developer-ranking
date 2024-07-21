import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests
from io import StringIO

# Set page config
st.set_page_config(page_title="KiwiTech Developer Rankings", page_icon="🏆", layout="wide")

# Function to load the CSV file from GitHub
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    try:
        github_csv_url = "https://raw.githubusercontent.com/syedzaidi-kiwi/jira-developer-ranking/main/developer_rankings_final.csv"
        response = requests.get(github_csv_url)
        response.raise_for_status()  # Raise an exception for bad responses
        
        csv_content = StringIO(response.text)
        df = pd.read_csv(csv_content)
        
        # Convert 'TotalScore' to numeric, replacing any non-numeric values with NaN
        df['TotalScore'] = pd.to_numeric(df['TotalScore'], errors='coerce')
        # Drop rows where 'TotalScore' is NaN
        df = df.dropna(subset=['TotalScore'])
        
        last_updated = datetime.now()
        return df, last_updated
    except requests.RequestException as e:
        st.error(f"Error fetching data from GitHub: {str(e)}")
    except pd.errors.EmptyDataError:
        st.error("The CSV file is empty.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
    
    return None, None

# Load the data
df, last_updated = load_data()

# Title
st.title('🏆 KiwiTech Developer Rankings')

if df is not None and not df.empty:
    # Display last updated time
    st.write(f"Last updated: {last_updated}")

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
    filtered_df = df
    if selected_developers:
        filtered_df = filtered_df[filtered_df['Name'].isin(selected_developers)]
    filtered_df = filtered_df[(filtered_df['TotalScore'] >= score_range[0]) & (filtered_df['TotalScore'] <= score_range[1])]

    # Display the rankings table
    st.subheader("Developer Rankings")
    st.dataframe(filtered_df.reset_index(drop=True))

    # Create a bar chart of top 10 developers by TotalScore
    top_10 = filtered_df.nlargest(10, 'TotalScore')
    fig = px.bar(top_10, x='Name', y='TotalScore', title='Top 10 Developers by Total Score')
    st.plotly_chart(fig)

    # Create a scatter plot of BugTime vs SubtaskTime
    fig2 = px.scatter(filtered_df, x='BugTime', y='SubtaskTime', hover_data=['Name'], title='Bug Time vs Subtask Time')
    st.plotly_chart(fig2)

    # Create a pie chart of project time vs bench time
    time_data = filtered_df[['ProjectTime', 'BenchTime']].sum()
    fig3 = px.pie(values=time_data.values, names=time_data.index, title='Project Time vs Bench Time Distribution')
    st.plotly_chart(fig3)

    # Add a new chart: Average Completion Time by Developer
    avg_completion_time = filtered_df.groupby('Name')['AvgCompletionTime'].mean().sort_values(ascending=False)
    fig4 = px.bar(avg_completion_time, title='Average Completion Time by Developer')
    st.plotly_chart(fig4)

else:
    st.error("No data available. Please check the GitHub repository or your internet connection.")

# Add a button to manually refresh the data
if st.sidebar.button('Refresh Data'):
    st.cache_data.clear()
    st.experimental_rerun()

# Information about auto-refresh
st.sidebar.info("This page will auto-refresh every 60 minutes to show the latest data.")

# Footer
st.markdown("---")
st.markdown("Developer Rankings Dashboard - Created with :hearts:by KiwiTech AI Team")