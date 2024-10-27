import requests
import sqlite3
import time
from datetime import datetime
import trafilatura
from tqdm import tqdm
import logging
import os
import urllib3
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def load_blacklist(blacklist_file="config/blacklist_urls.txt"):
    """
    Load blacklist patterns from a file.

    The blacklist file should have entries in the following format:
    - Lines starting with 'regex:' are treated as regular expressions.
    - Lines starting with 'string:' are treated as plain string matches.
    - Lines starting with '#' are comments and are ignored.
    - Empty lines are ignored.

    Parameters:
        blacklist_file (str): Path to the blacklist file.

    Returns:
        dict: A dictionary with two keys 'regex' and 'string', containing lists of patterns.
    """
    blacklist_data = {"regex": [], "string": []}
    
    if os.path.exists(blacklist_file):
        with open(blacklist_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore comments and empty lines
                    if line.startswith("regex:"):
                        pattern = line.split("regex:", 1)[1].strip()
                        blacklist_data["regex"].append(pattern)
                    elif line.startswith("string:"):
                        string_match = line.split("string:", 1)[1].strip()
                        blacklist_data["string"].append(string_match)
    else:
        print(f"Blacklist file '{blacklist_file}' not found.")
    return blacklist_data

def is_blacklisted(url, blacklist):
    """
    Check if the URL matches any blacklist patterns.

    Parameters:
        url (str): The URL to check.
        blacklist (dict): The blacklist data loaded from 'load_blacklist'.

    Returns:
        bool: True if the URL is blacklisted, False otherwise.
    """
    url = str(url) if url else ""

    # Check against regex patterns
    for pattern in blacklist.get("regex", []):
        if re.search(pattern, url):
            return True

    # Check against plain string matches
    for string in blacklist.get("string", []):
        if string in url:
            return True

    return False

def create_database():
    """
    Create the SQLite database and the 'stories' table if they don't exist.

    Returns:
        sqlite3.Connection: The database connection object.
    """
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
    """
    Fetch the top story IDs from Hacker News.

    Returns:
        list: A list of top story IDs.
    """
    top_stories_url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    try:
        response = requests.get(top_stories_url, timeout=10)
        if response.status_code == 200:
            story_ids = response.json()
            return story_ids
        else:
            print('Error fetching top stories.')
            return []
    except Exception as e:
        print(f"Exception while fetching top stories: {e}")
        return []

def fetch_story_details(story_id):
    """
    Fetch the details of a specific story by ID.

    Parameters:
        story_id (int): The ID of the story.

    Returns:
        dict or None: The story details if successful, None otherwise.
    """
    story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
    try:
        response = requests.get(story_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error fetching story ID {story_id}. Status Code: {response.status_code}')
            logging.error(f'Error fetching story ID {story_id}. Status Code: {response.status_code}')
            return None
    except Exception as e:
        print(f'Exception while fetching story ID {story_id}: {e}')
        logging.error(f'Exception while fetching story ID {story_id}: {e}')
        return None

def extract_content(url, timeout=10, blacklist=None):
    """
    Extract the main content from a URL using trafilatura.

    Parameters:
        url (str): The URL to extract content from.
        timeout (int): Timeout for the HTTP request.
        blacklist (dict): The blacklist data.

    Returns:
        str or None: The extracted content if successful, None otherwise.
    """
    if not is_blacklisted(url, blacklist):
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
            logging.error(f'Exception while fetching content from URL: {url}, Error: {e}')
            return None
    else:
        print(f'URL is blacklisted, skipping it: {url}')
        return None

def save_story(conn, story):
    """
    Save a story to the SQLite database.

    Parameters:
        conn (sqlite3.Connection): The database connection.
        story (dict): The story data to save.
    """
    try:
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
    except sqlite3.IntegrityError:
        print(f"Story ID {story['id']} already exists in the database.")
        logging.warning(f"Story ID {story['id']} already exists in the database.")
    except Exception as e:
        print(f"Error saving story ID {story['id']}: {e}")
        logging.error(f"Error saving story ID {story['id']}: {e}")

def process_story(story_id, blacklist):
    """
    Process a single story: fetch details and extract content.

    Parameters:
        story_id (int): The ID of the story to process.
        blacklist (dict): The blacklist data.

    Returns:
        dict or None: The processed story data, or None if failed.
    """
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
            content = extract_content(story['url'], timeout=10, blacklist=blacklist)
            story['content'] = content

            # Generate summary using Ollama Llama 3.2 model
            # Uncomment and implement the summary generation if needed
            # summary = generate_summary(content)
            # story['summary'] = summary

        return story
    else:
        return None

def main():
    """
    The main function to orchestrate fetching and processing stories.
    """
    # Configure logging
    current_date = datetime.now().strftime("%d_%m_%Y")
    log_filename = f"./db/hackernews_{current_date}.log"
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s'
    )
    
    # Create database
    conn = create_database()
    cursor = conn.cursor()
    
    # Fetch existing story IDs to avoid reprocessing
    try:
        cursor.execute("SELECT id FROM stories")
        existing_ids = set(row[0] for row in cursor.fetchall())
    except Exception as e:
        print(f"Error fetching existing story IDs: {e}")
        logging.error(f"Error fetching existing story IDs: {e}")
        existing_ids = set()
    
    # Fetch top story IDs
    top_story_ids = fetch_top_story_ids()
    if not top_story_ids:
        print("No top stories fetched. Exiting.")
        return
    total_stories = len(top_story_ids)
    print(f"Total stories fetched from Hacker News: {total_stories}")
    
    # Filter out already processed stories
    stories_to_process = [sid for sid in top_story_ids if sid not in existing_ids]
    total_to_process = len(stories_to_process)
    print(f"Total new stories to process: {total_to_process}")
    
    if total_to_process == 0:
        print("No new stories to process. Exiting.")
        return
    
    # Load blacklist
    blacklist = load_blacklist()
    
    # Define the number of worker threads
    max_workers = 10  # Adjust based on your system's capabilities
    
    # Initialize ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks to the executor
        future_to_story_id = {
            executor.submit(process_story, sid, blacklist): sid for sid in stories_to_process
        }
        
        # Initialize progress bar
        with tqdm(total=total_to_process, desc='Processing stories') as pbar:
            for future in as_completed(future_to_story_id):
                story_id = future_to_story_id[future]
                try:
                    story = future.result()
                    if story:
                        save_story(conn, story)
                except Exception as e:
                    print(f"Exception occurred while processing story ID {story_id}: {e}")
                    logging.error(f"Exception occurred while processing story ID {story_id}: {e}")
                finally:
                    pbar.update(1)
    
    # Close the database connection
    conn.close()
    print("Processing completed.")

if __name__ == '__main__':
    main()
