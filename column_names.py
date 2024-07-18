import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import pytz

class DeveloperRanking:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.issues_data = self.load_all_issues()
        self.print_column_info()
        self.developers = self.get_developers()
        self.rankings = pd.DataFrame()

    def load_all_issues(self):
        all_issues = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_issues.csv'):
                df = pd.read_csv(os.path.join(self.data_dir, filename))
                all_issues.append(df)
        return pd.concat(all_issues, ignore_index=True)

    def print_column_info(self):
        print("Available columns in the CSV files:")
        for col in self.issues_data.columns:
            print(f"- {col}")
        print("\nSample data:")
        print(self.issues_data.head())

    def get_developers(self):
        # We'll implement this after we know the correct column names
        return []

    # ... (other methods remain the same)

def main():
    data_dir = 'jira_data'  # Directory containing the CSV files
    ranking = DeveloperRanking(data_dir)
    # We'll comment out the ranking process for now
    # ranking.rank_developers()
    # ranking.save_rankings('developer_rankings.csv')

if __name__ == "__main__":
    main()