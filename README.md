# JIRA Developer Ranking Project

This project is designed to rank developers based on their performance metrics extracted from JIRA data. It analyzes various aspects of a developer's work, including time spent on bugs and tasks, bug counts by criticality, average completion time, and estimation accuracy.
Created by Syed Asad (Senior AI/ML Lead)

## Features

- Extracts data from JIRA CSV files
- Identifies developers based on their work on subtasks and bugs
- Calculates various performance metrics for each developer
- Generates a ranking of developers based on a composite score

## Prerequisites

- Python 3.7+
- pandas
- numpy
- pytz

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/syedzaidi-kiwi/jira-developer-ranking.git
   cd jira-developer-ranking
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install pandas numpy pytz
   ```

4. Place your JIRA CSV files in a directory named `jira_data` in the project root.

## Usage

1. Ensure your JIRA data CSV files are in the `jira_data` directory.

2. Run the ranking script:
   ```
   python dev_ranking.py
   ```

3. The script will generate a `developer_rankings.csv` file with the rankings.

## Configuration

You can adjust the scoring weights and criteria in the `calculate_score` method of the `DeveloperRanking` class in `dev_ranking.py`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is proprietary software belonging to KiwiTech LLC. 
All rights reserved. See the LICENSE file for full license details