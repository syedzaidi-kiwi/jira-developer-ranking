import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
from requests.auth import HTTPBasicAuth
import json
import sys
from dotenv import load_dotenv

class JiraDataExtractor:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json"}

    def get_all_issues(self, jql, fields, start_at=0, max_results=100):
        url = f"{self.base_url}/rest/api/2/search"
        issues = []

        while True:
            params = {
                "jql": jql,
                "fields": ",".join(fields),
                "startAt": start_at,
                "maxResults": max_results
            }
            response = requests.get(url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            data = response.json()
            
            issues.extend(data['issues'])
            
            if len(issues) >= data['total']:
                break
            
            start_at += max_results

        return issues

    def get_issue_changelog(self, issue_key):
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/changelog"
        response = requests.get(url, headers=self.headers, auth=self.auth)
        response.raise_for_status()
        data = response.json()
        return data.get('values', [])  # Use 'values' instead of 'histories', provide empty list if not found

    def get_code_reviews(self, issue_key):
        # This is a placeholder. In reality, you'd need to integrate with your code review system
        # For example, if using Crucible, you might use its API to fetch reviews linked to this issue
        return []

def extract_data():
    # Load environment variables from .env file
    load_dotenv()

    # Load JIRA credentials from environment variables
    jira_url = os.getenv('JIRA_BASE_URL')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_api_token = os.getenv('JIRA_API_TOKEN')

    # Check if all required environment variables are set
    if not all([jira_url, jira_email, jira_api_token]):
        print("Error: Missing environment variables. Please ensure JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN are set in your .env file.")
        sys.exit(1)

    try:
        extractor = JiraDataExtractor(jira_url, jira_email, jira_api_token)

        # Define JQL query to fetch issues from the last 6 months
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        jql = f'created >= "{six_months_ago}" ORDER BY created DESC'

        fields = [
            "key", "project", "issuetype", "creator", "assignee", "status",
            "resolution", "resolutiondate", "created", "updated",
            "timespent", "timeoriginalestimate", "timeestimate",
            "priority", "labels", "components"
        ]

        issues = extractor.get_all_issues(jql, fields)

        data = []
        for issue in issues:
            try:
                issue_data = {
                    'Key': issue['key'],
                    'Type': issue['fields']['issuetype']['name'],
                    'Project': issue['fields']['project']['key'],
                    'Creator': issue['fields']['creator']['displayName'],
                    'Assignee': issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else None,
                    'Status': issue['fields']['status']['name'],
                    'Resolution': issue['fields']['resolution']['name'] if issue['fields']['resolution'] else None,
                    'Created': issue['fields']['created'],
                    'Updated': issue['fields']['updated'],
                    'Resolved': issue['fields']['resolutiondate'],
                    'TimeSpent': issue['fields']['timespent'],
                    'OriginalEstimate': issue['fields']['timeoriginalestimate'],
                    'CurrentEstimate': issue['fields']['timeestimate'],
                    'Priority': issue['fields']['priority']['name'],
                    'Labels': ','.join(issue['fields']['labels']),
                    'Components': ','.join([c['name'] for c in issue['fields']['components']])
                }

                # Get changelog
                changelog = extractor.get_issue_changelog(issue['key'])
                status_changes = [h for h in changelog if any(i['field'] == 'status' for i in h['items'])]
                issue_data['StatusChanges'] = len(status_changes)

                # Get code reviews
                code_reviews = extractor.get_code_reviews(issue['key'])
                issue_data['CodeReviews'] = len(code_reviews)

                data.append(issue_data)
            except Exception as e:
                print(f"Error processing issue {issue['key']}: {str(e)}")

        df = pd.DataFrame(data)

        # Create data_advanced directory if it doesn't exist
        os.makedirs('data_advanced', exist_ok=True)

        # Save data to CSV
        df.to_csv('data_advanced/jira_issues_advanced.csv', index=False)

        print("Data extraction completed. Data saved in 'data_advanced/jira_issues_advanced.csv'")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to JIRA: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    extract_data()