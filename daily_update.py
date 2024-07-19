import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_extraction():
    logging.info("Starting data extraction")
    result = subprocess.run(["python", "jira_extract24hr.py"], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Data extraction failed: {result.stderr}")
        return False
    logging.info("Data extraction completed successfully")
    return True

def run_ranking():
    logging.info("Starting developer ranking")
    result = subprocess.run(["python", "dev_ranking_daily.py"], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Developer ranking failed: {result.stderr}")
        return False
    logging.info("Developer ranking completed successfully")
    return True

def main():
    if run_extraction():
        run_ranking()
    else:
        logging.error("Daily update process failed at data extraction stage")

if __name__ == "__main__":
    main()