import requests
import sqlite3
import time
from datetime import datetime
import trafilatura
from tqdm import tqdm
import logging
import os
import urllib3

# Import the Ollama Python client
import ollama

# Suppress InsecureRequestWarning due to verify=False in requests.get
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define the headers with the specified User-Agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
    )
}

def create_database():
    # Create folder 'db' if it does not exist
    if not os.path.exists('db'):
        os.makedirs('db')

    # Get current date in dd_mm_yyyy format
    current_date = datetime.now().strftime("%d_%m_%Y")

    # Create the database name with the current date
    db_name = f"./db/hackernews_{current_date}.db"

    print(f"Database: {db_name}")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Modify the table creation to include the 'summary' field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            title TEXT,
            by TEXT,
            score INTEGER,
            url TEXT,
            content TEXT,
            summary TEXT,
            last_updated TIMESTAMP
        )
    ''')

    # Add 'summary' column if it doesn't exist (for existing databases)
    cursor.execute("PRAGMA table_info(stories)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'summary' not in columns:
        cursor.execute("ALTER TABLE stories ADD COLUMN summary TEXT")

    conn.commit()
    return conn

def fetch_top_story_ids():
    top_stories_url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    response = requests.get(top_stories_url)
    if response.status_code == 200:
        story_ids = response.json()
        return story_ids
    else:
        print('Error fetching top stories.')
        return []

def fetch_story_details(story_id):
    story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
    response = requests.get(story_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching story ID {story_id}.')
        return None

def extract_content(url, timeout=10):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)
        if response.status_code == 200:
            downloaded = response.text
            content = trafilatura.extract(downloaded, url=url)
            return content
        else:
            print(f'Error fetching content from URL: {url}, Status Code: {response.status_code}')
            logging.error(f'Error fetching content from URL: {url}, Status Code: {response.status_code}')
            return None
    except Exception as e:
        print(f'Exception while fetching content from URL: {url}')
        print(f'Error: {e}')
        return None

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

def story_exists(cursor, story_id):
    cursor.execute('SELECT id FROM stories WHERE id = ?', (story_id,))
    return cursor.fetchone() is not None

def save_story(conn, story):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stories (id, title, by, score, url, content, summary, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        story['id'],
        story.get('title'),
        story.get('by'),
        story.get('score'),
        story.get('url'),
        story.get('content'),
        story.get('summary'),
        story.get('last_updated')
    ))
    conn.commit()

def update_story(conn, story):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE stories
        SET title = ?, by = ?, score = ?, url = ?, content = ?, summary = ?, last_updated = ?
        WHERE id = ?
    ''', (
        story.get('title'),
        story.get('by'),
        story.get('score'),
        story.get('url'),
        story.get('content'),
        story.get('summary'),
        story.get('last_updated'),
        story['id']
    ))
    conn.commit()

def main():
    # Configure logging
    current_date = datetime.now().strftime("%d_%m_%Y")
    log_filename = f"./db/hackernews_{current_date}.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO)
    conn = create_database()
    cursor = conn.cursor()
    top_story_ids = fetch_top_story_ids()
    total_stories = len(top_story_ids)
    print(f"Total stories to process: {total_stories}")

    for story_id in tqdm(top_story_ids, desc='Processing stories'):
        if story_exists(cursor, story_id):
            continue

        story_details = fetch_story_details(story_id)
        if story_details:
            story = {
                'id': story_details.get('id'),
                'title': story_details.get('title'),
                'by': story_details.get('by'),
                'score': story_details.get('score'),
                'url': story_details.get('url'),
                'content': None,
                'summary': None,
                'last_updated': datetime.now()
            }

            if story['url']:
                content = extract_content(story['url'], timeout=10)
                story['content'] = content

                # Generate summary using Ollama Llama 3.2 model
                summary = generate_summary(content)
                story['summary'] = summary

            save_story(conn, story)

        # Be polite and don't overwhelm the servers
        time.sleep(0.5)

    conn.close()

if __name__ == '__main__':
    main()
