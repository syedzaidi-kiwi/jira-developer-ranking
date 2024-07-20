import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import time
import os
import shutil
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class JiraDataExtractor:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update(self.headers)

    def get_all_projects(self):
        url = f"{self.base_url}/rest/api/2/project"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_project_details(self, project_key):
        url = f"{self.base_url}/rest/api/2/project/{project_key}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_issues(self, jql, fields, start_at=0, max_results=100):
        url = f"{self.base_url}/rest/api/2/search"
        issues = []

        while True:
            params = {
                "jql": jql,
                "fields": ",".join(fields),
                "startAt": start_at,
                "maxResults": max_results
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            issues.extend(data['issues'])
            
            if len(issues) >= data['total']:
                break
            
            start_at += max_results
            time.sleep(1)  # Respect rate limits

        return issues

def clean_and_transform_data(df):
    date_columns = ['fields.created', 'fields.updated', 'fields.resolutiondate']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df

def save_to_csv(df, filename, output_dir='jira_data_daily'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_path = os.path.join(output_dir, filename)
    df.to_csv(file_path, index=False)
    logging.info(f"Data saved to {file_path}")

def process_project(jira, project, start_date):
    project_key = project['key']
    logging.info(f"Processing project: {project_key}")

    try:
        jql = f'project = "{project_key}" AND updated >= "{start_date}"'
        fields = ["key", "project", "creator", "issuetype", "priority", "created", "updated", "resolutiondate", "timeoriginalestimate", "timespent"]
        issues = jira.get_issues(jql, fields)

        return {
            'project_key': project_key,
            'issues': issues
        }
    except Exception as e:
        logging.error(f"Error processing project {project_key}: {str(e)}")
        return None

def main():
    logging.info("Starting JIRA data extraction")
    load_dotenv()

    jira = JiraDataExtractor(
        base_url=os.getenv('JIRA_BASE_URL'),
        email=os.getenv('JIRA_EMAIL'),
        api_token=os.getenv('JIRA_API_TOKEN')
    )

    logging.info(f"JIRA Base URL: {os.getenv('JIRA_BASE_URL')}")
    logging.info(f"JIRA Email: {os.getenv('JIRA_EMAIL')}")

    # Calculate start date (24 hours ago)
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    logging.info(f"Fetching data from: {start_date}")

    # Create a temporary directory for new data
    temp_dir = 'jira_data_temp'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    logging.info(f"Created temporary directory: {temp_dir}")

    projects = jira.get_all_projects()
    logging.info(f"Found {len(projects)} projects")
    projects_df = pd.DataFrame(projects)
    save_to_csv(projects_df, 'all_projects.csv', output_dir=temp_dir)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_project = {executor.submit(process_project, jira, project, start_date): project for project in projects}
        for future in as_completed(future_to_project):
            project_data = future.result()
            if project_data:
                project_key = project_data['project_key']
                
                issues_df = pd.json_normalize(project_data['issues'])
                if not issues_df.empty:
                    issues_df = clean_and_transform_data(issues_df)
                    save_to_csv(issues_df, f'{project_key}_issues.csv', output_dir=temp_dir)
                else:
                    logging.info(f"No issues found for project: {project_key}")

    # Replace old data with new data
    old_dir = 'jira_data_daily'
    if os.path.exists(old_dir):
        shutil.rmtree(old_dir)
    os.rename(temp_dir, old_dir)
    logging.info(f"Replaced old data directory with new data")

    logging.info("Daily data extraction completed. Old data replaced with new data.")
    logging.info(f"Contents of jira_data_daily: {os.listdir('jira_data_daily')}")

if __name__ == "__main__":
    main()