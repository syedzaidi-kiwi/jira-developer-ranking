import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
import pytz
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DeveloperRanking:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.issues_data = self.load_all_issues()
        self.developers = self.get_developers()
        self.rankings = pd.DataFrame()

    def load_all_issues(self):
        all_issues = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_issues.csv'):
                df = pd.read_csv(os.path.join(self.data_dir, filename))
                all_issues.append(df)
        return pd.concat(all_issues, ignore_index=True)

    def get_developers(self):
        dev_issues = self.issues_data[self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug'])]
        grouped = dev_issues.groupby('fields.creator.displayName')
        
        developers = []
        for name, group in grouped:
            has_subtasks = (group['fields.issuetype.name'] == 'Sub-task').any()
            has_bugs = (group['fields.issuetype.name'] == 'Bug').any()
            has_logged_time = (group['fields.timespent'] > 0).any()
            significant_issues = len(group) >= 5
            
            if (has_subtasks or has_bugs) and has_logged_time and significant_issues:
                developers.append(name)
        
        return developers

    def calculate_time_spent(self, developer):
        dev_issues = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) &
            (self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug']))
        ]
        bug_time = dev_issues[dev_issues['fields.issuetype.name'] == 'Bug']['fields.timespent'].sum() / 3600
        subtask_time = dev_issues[dev_issues['fields.issuetype.name'] == 'Sub-task']['fields.timespent'].sum() / 3600
        return round(bug_time, 2), round(subtask_time, 2)

    def count_bugs_by_criticality(self, developer):
        dev_bugs = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) & 
            (self.issues_data['fields.issuetype.name'] == 'Bug')
        ]
        normal = dev_bugs[dev_bugs['fields.priority.name'].isin(['Lowest', 'Low', 'Medium'])].shape[0]
        critical = dev_bugs[dev_bugs['fields.priority.name'] == 'High'].shape[0]
        blocker = dev_bugs[dev_bugs['fields.priority.name'].isin(['Highest', 'Must Have'])].shape[0]
        return normal, critical, blocker

    def calculate_avg_completion_time(self, developer):
        dev_issues = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) &
            (self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug']))
        ].copy()
        
        def parse_date(date_str):
            try:
                dt = pd.to_datetime(date_str, format='mixed')
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.UTC)
                else:
                    dt = dt.astimezone(pytz.UTC)
                return dt.replace(tzinfo=None)
            except:
                return pd.NaT

        dev_issues['created_date'] = dev_issues['fields.created'].apply(parse_date)
        dev_issues['resolution_date'] = dev_issues['fields.resolutiondate'].apply(parse_date)
        
        dev_issues = dev_issues.dropna(subset=['created_date', 'resolution_date'])
        dev_issues['completion_time'] = (dev_issues['resolution_date'] - dev_issues['created_date']).dt.total_seconds() / 3600
        
        dev_issues = dev_issues[dev_issues['completion_time'] >= 0]
        
        return round(dev_issues['completion_time'].mean(), 2) if not dev_issues.empty else 0

    def calculate_days_logged_8_hours(self, developer):
        dev_issues = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) &
            (self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug']))
        ]
        total_time_spent = dev_issues['fields.timespent'].sum() / 3600
        days_logged_8_hours = total_time_spent / 8
        return round(days_logged_8_hours, 2)

    def calculate_estimation_accuracy(self, developer):
        dev_issues = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) &
            (self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug']))
        ].copy()
        dev_issues['estimation_accuracy'] = (dev_issues['fields.timespent'] / dev_issues['fields.timeoriginalestimate']) * 100
        dev_issues = dev_issues[dev_issues['estimation_accuracy'].notna() & (dev_issues['estimation_accuracy'] != np.inf)]
        return round(dev_issues['estimation_accuracy'].mean(), 2) if not dev_issues.empty else 0

    def calculate_project_vs_bench_time(self, developer):
        project_time = self.issues_data[
            (self.issues_data['fields.creator.displayName'] == developer) &
            (self.issues_data['fields.issuetype.name'].isin(['Sub-task', 'Bug']))
        ]['fields.timespent'].sum() / 3600
        total_work_hours = 6 * 22 * 8
        bench_time = max(0, total_work_hours - project_time)
        return round(project_time, 2), round(bench_time, 2)

    def calculate_score(self, row):
        try:
            score = (
                (row['SubtaskTime'] / (row['BugTime'] + 1)) * 10 +
                (row['BugCount'] * 1 + row['CriticalBugCount'] * 2 + row['BlockerBugCount'] * 3) * -1 +
                (480 - min(row['AvgCompletionTime'], 480)) / 48 * 10 +
                row['DaysLogged8Hours'] / 132 * 100 +
                (2 - min(abs(1 - (row['EstimationAccuracy'] / 100)), 1)) * 50 +
                row['ProjectTime'] / (row['BenchTime'] + 1) * 10
            )
            return round(max(0, score), 2)
        except Exception as e:
            logging.error(f"Error calculating score for row: {row}")
            logging.error(f"Error message: {str(e)}")
            return 0  # Return a default score if calculation fails

    def rank_developers(self):
        rankings_list = []
        for developer in self.developers:
            bug_time, subtask_time = self.calculate_time_spent(developer)
            normal_bugs, critical_bugs, blocker_bugs = self.count_bugs_by_criticality(developer)
            avg_completion_time = self.calculate_avg_completion_time(developer)
            days_logged_8_hours = self.calculate_days_logged_8_hours(developer)
            estimation_accuracy = self.calculate_estimation_accuracy(developer)
            project_time, bench_time = self.calculate_project_vs_bench_time(developer)

            rankings_list.append({
                'Name': developer,
                'Email': f"{developer.lower().replace(' ', '.')}@kiwitech.com",
                'BugTime': bug_time,
                'SubtaskTime': subtask_time,
                'BugCount': normal_bugs,
                'CriticalBugCount': critical_bugs,
                'BlockerBugCount': blocker_bugs,
                'AvgCompletionTime': avg_completion_time,
                'DaysLogged8Hours': days_logged_8_hours,
                'EstimationAccuracy': estimation_accuracy,
                'ProjectTime': project_time,
                'BenchTime': bench_time
            })

        self.rankings = pd.DataFrame(rankings_list)
        
        if self.rankings.empty:
            logging.warning("No developers met the criteria for ranking.")
            self.rankings = pd.DataFrame(columns=['Name', 'Email', 'TotalScore', 'Rank'])
        else:
            self.rankings['TotalScore'] = self.rankings.apply(self.calculate_score, axis=1)
            self.rankings = self.rankings.sort_values('TotalScore', ascending=False)
            self.rankings['Rank'] = range(1, len(self.rankings) + 1)

        logging.info("Rankings DataFrame:")
        logging.info(self.rankings.head())
        logging.info(f"Shape of rankings DataFrame: {self.rankings.shape}")
        logging.info("Columns in the rankings DataFrame:")
        logging.info(self.rankings.columns.tolist())

    def save_rankings(self, output_file):
        desired_columns = ['Name', 'Email', 'BugTime', 'SubtaskTime', 'AvgCompletionTime', 'DaysLogged8Hours', 'ProjectTime', 'BenchTime', 'TotalScore', 'Rank']
        available_columns = self.rankings.columns.tolist()
        
        logging.info("Desired columns:")
        logging.info(desired_columns)
        logging.info("Available columns:")
        logging.info(available_columns)
        
        columns_to_keep = [col for col in desired_columns if col in available_columns]
        
        if not columns_to_keep:
            logging.error("No desired columns found in the DataFrame")
            raise ValueError("No desired columns found in the DataFrame")
        
        missing_columns = set(desired_columns) - set(columns_to_keep)
        if missing_columns:
            logging.warning(f"Missing columns in the DataFrame: {missing_columns}")
        
        rankings_to_save = self.rankings[columns_to_keep]
        
        logging.info("Columns in the rankings_to_save DataFrame:")
        logging.info(rankings_to_save.columns.tolist())
        logging.info(f"Shape of rankings_to_save DataFrame: {rankings_to_save.shape}")

        rankings_to_save.to_csv(output_file, index=False)
        logging.info(f"Rankings saved to {output_file}")

def main():
    try:
        data_dir = 'jira_data_daily'
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Directory not found: {data_dir}")
        
        files = [f for f in os.listdir(data_dir) if f.endswith('_issues.csv')]
        if not files:
            raise FileNotFoundError(f"No CSV files found in {data_dir}")
        
        logging.info(f"Found {len(files)} CSV files in {data_dir}")
        
        ranking = DeveloperRanking(data_dir)
        ranking.rank_developers()
        ranking.save_rankings('`develop`er_rankings_final.csv')
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()