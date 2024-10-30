import schedule
import time
import subprocess
import logging
from datetime import datetime


def fetch_news():
    """
    Function to run the news fetching script.
    """
    print(f"{datetime.now()}: Fetching news...")
    try:
        # Run the news fetching script
        subprocess.run(["python", "concurrent_hn_topnews_fetch.py"], check=True)
        logging.info(f"{datetime.now()}: Successfully fetched news.")
    except subprocess.CalledProcessError as e:
        logging.error(f"{datetime.now()}: Error fetching news - {e}")


def generate_summaries():
    """
    Function to run the summary generation script.
    """
    print(f"{datetime.now()}: Generating summaries...")
    try:
        # Run the summary generation script
        subprocess.run(["python", "concurrent_generate_ai_summary.py"], check=True)
        logging.info(f"{datetime.now()}: Successfully generated summaries.")
    except subprocess.CalledProcessError as e:
        logging.error(f"{datetime.now()}: Error generating summaries - {e}")


def main():
    # Configure logging
    logging.basicConfig(filename="./db/scheduler.log", level=logging.INFO)

    # Schedule the tasks every 5 minutes
    duration = 1
    schedule.every(duration).minutes.do(fetch_news)
    schedule.every(duration).minutes.do(generate_summaries)

    print("Scheduler started. Press Ctrl+C to exit.")
    # Run the tasks immediately before starting the schedule loop
    fetch_news()
    generate_summaries()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
        logging.info(f"{datetime.now()}: Scheduler stopped by user.")


if __name__ == "__main__":
    main()
