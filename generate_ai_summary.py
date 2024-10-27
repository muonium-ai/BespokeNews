import sqlite3
import os
import logging
from datetime import datetime
from tqdm import tqdm
import ollama

def get_database_name():
    current_date = datetime.now().strftime("%d_%m_%Y")
    db_name = f"./db/hackernews_{current_date}.db"
    return db_name

def connect_to_database(db_name):
    conn = sqlite3.connect(db_name)
    return conn

def get_stories_without_summary(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, content FROM stories WHERE content IS NOT NULL AND summary IS NULL')
    stories = cursor.fetchall()
    return stories

def generate_summary(content):
    """
    Generate a summary of the content using the Ollama Llama 3.2 model.
    """
    if not content:
        return None

    try:

        # Initialize the Ollama client
        client = ollama.Client()  # Adjust initialization if required by the client

        # Define the prompt for summarization
        prompt = f"Summarize the following article:\n\n{content}\n\nSummary:"



        response = ollama.chat(model='llama3.2', messages=[
        {
        'role': 'user',
        'content': prompt,
        }])
        summary = response['message']['content'].strip()

        return summary
    except Exception as e:
        print(f'Error generating summary: {e}')
        logging.error(f'Error generating summary: {e}')
        return None

def update_story_summary(conn, story_id, summary):
    cursor = conn.cursor()
    cursor.execute('UPDATE stories SET summary = ?, last_updated = ? WHERE id = ?', (summary, datetime.now(), story_id))
    conn.commit()

def main():
    # Configure logging
    current_date = datetime.now().strftime("%d_%m_%Y")
    log_filename = f"./db/hackernews_summary_{current_date}.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO)

    # Get database name based on the current date
    db_name = get_database_name()

    # Check if the database exists
    if not os.path.exists(db_name):
        print(f"Database {db_name} does not exist. Please fetch new news first.")
        return

    print(f"Using database: {db_name}")
    conn = connect_to_database(db_name)

    stories = get_stories_without_summary(conn)
    total_stories = len(stories)
    print(f"Total stories without summary: {total_stories}")

    for story in tqdm(stories, desc='Generating summaries'):
        story_id, content = story
        if not content:
            continue
        summary = generate_summary(content)
        if summary:
            update_story_summary(conn, story_id, summary)
        else:
            logging.error(f"Failed to generate summary for story ID {story_id}")

    conn.close()

if __name__ == '__main__':
    main()
