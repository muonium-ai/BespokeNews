import sqlite3
import os
import logging
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import ollama
import sys

# Add the parent directory to the sys.path to ensure lib can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def get_database_name():
    """
    Generate the database name based on the current date.
    """
    # Create folder 'db' if it does not exist
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))
    current_date = datetime.now().strftime("%d_%m_%Y")
    db_name = os.path.join(db_dir, f"hackernews_{current_date}.db")
    return db_name


def connect_to_database(db_name):
    """
    Connect to the SQLite database.

    Parameters:
        db_name (str): The name of the database file.

    Returns:
        sqlite3.Connection: The database connection object.
    """
    conn = sqlite3.connect(db_name, check_same_thread=False)
    return conn


def get_stories_without_summary(conn):
    """
    Retrieve stories that have content but no summary from the database.

    Parameters:
        conn (sqlite3.Connection): The database connection.

    Returns:
        list of tuples: Each tuple contains (story_id, content).
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, content FROM stories WHERE content IS NOT NULL AND length(trim(content)) > 0  AND summary IS NULL"
    )
    stories = cursor.fetchall()
    return stories


def generate_summary(content):
    # set python environment variable to use ollama host
    os.environ["OLAMA_HOST"] = "0.0.0.0:11434"

    """
    Generate a summary of the content using the Ollama Llama 3.2 model.

    Parameters:
        content (str): The content to summarize.

    Returns:
        str or None: The generated summary, or None if an error occurs.
    """
    if not content:
        return None

    try:
        # Initialize the Ollama client
        client = ollama.Client(host='http://localhost:11434')  # Adjust initialization if required by the client

        # Define the prompt for summarization
        prompt = f"Summarize the following article:\n\n{content}\n\nSummary:"

        response = client.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        summary = response["message"]["content"].strip()
        return summary
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return None


def update_story_summary(conn, story_id, summary):
    """
    Update the summary of a story in the database.

    Parameters:
        conn (sqlite3.Connection): The database connection.
        story_id (int): The ID of the story.
        summary (str): The generated summary.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE stories
            SET summary = ?, last_updated = ?
            WHERE id = ?
        """,
            (summary, datetime.now(), story_id),
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Error updating summary for story ID {story_id}: {e}")


def process_story(story):
    """
    Process a single story: generate its summary.

    Parameters:
        story (tuple): A tuple containing (story_id, content).

    Returns:
        tuple: (story_id, summary) or (story_id, None) if failed.
    """
    story_id, content = story
    if not content:
        return (story_id, None)
    summary = generate_summary(content)
    return (story_id, summary)


def main():
    """
    The main function to orchestrate summary generation.
    """
    # Configure logging
    current_date = datetime.now().strftime("%d_%m_%Y")
    log_filename = f"./db/hackernews_summary_{current_date}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
    )

    # Get database name based on the current date
    db_name = get_database_name()

    # Check if the database exists
    if not os.path.exists(db_name):
        print(f"Database {db_name} does not exist. Please fetch new news first.")
        return

    print(f"Using database: {db_name}")
    conn = connect_to_database(db_name)

    # Retrieve stories without summaries
    stories = get_stories_without_summary(conn)
    total_stories = len(stories)
    print(f"Total stories without summary: {total_stories}")

    if total_stories == 0:
        print("No stories to process. All stories have summaries.")
        conn.close()
        return

    # Define the number of worker threads
    max_workers = 10  # Adjust based on your system's capabilities

    # Initialize ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks to the executor
        future_to_story_id = {
            executor.submit(process_story, story): story[0] for story in stories
        }

        # Initialize progress bar
        with tqdm(total=total_stories, desc="Generating summaries") as pbar:
            for future in as_completed(future_to_story_id):
                story_id = future_to_story_id[future]
                try:
                    result = future.result()
                    if result:
                        _, summary = result
                        if summary:
                            update_story_summary(conn, story_id, summary)
                        else:
                            logging.error(
                                f"Failed to generate summary for story ID {story_id}"
                            )
                except Exception as e:
                    logging.error(
                        f"Exception occurred while processing story ID {story_id}: {e}"
                    )
                finally:
                    pbar.update(1)

    # Close the database connection
    conn.close()
    print("Summary generation completed.")


if __name__ == "__main__":
    main()
