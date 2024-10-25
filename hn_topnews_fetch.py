import requests
import sqlite3
import time
from datetime import datetime
import trafilatura
from tqdm import tqdm
import logging

# Define the headers with the specified User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
}

def create_database():
    # db_name='hackernews.db'
    # Get current date in dd_mm_yyyy format
    current_date = datetime.now().strftime("%d_%m_%Y")

    # Create the string with "hackernews" + date + ".db"
    db_name = f"./db/hackernews_{current_date}.db"

    print(db_name)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            title TEXT,
            by TEXT,
            score INTEGER,
            url TEXT,
            content TEXT,
            last_updated TIMESTAMP
        )
    ''')
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
        #response = requests.get(url, headers=HEADERS, timeout=timeout)
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

def story_exists(cursor, story_id):
    cursor.execute('SELECT id FROM stories WHERE id = ?', (story_id,))
    return cursor.fetchone() is not None

def save_story(conn, story):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stories (id, title, by, score, url, content, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        story['id'],
        story.get('title'),
        story.get('by'),
        story.get('score'),
        story.get('url'),
        story.get('content'),
        story.get('last_updated')
    ))
    conn.commit()

def update_story(conn, story):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE stories
        SET title = ?, by = ?, score = ?, url = ?, content = ?, last_updated = ?
        WHERE id = ?
    ''', (
        story.get('title'),
        story.get('by'),
        story.get('score'),
        story.get('url'),
        story.get('content'),
        story.get('last_updated'),
        story['id']
    ))
    conn.commit()

def main():
    # Configure logging
    current_date = datetime.now().strftime("%d_%m_%Y")
    log_filename = f"./db/hackernews_{current_date}.og"
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
                'last_updated': datetime.now()
            }

            if story['url']:
                content = extract_content(story['url'], timeout=10)
                story['content'] = content

            save_story(conn, story)
        #time.sleep(0.5)  # Be polite and don't overwhelm the servers

    conn.close()

if __name__ == '__main__':
    main()
