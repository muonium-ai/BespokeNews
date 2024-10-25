from flask import Flask, render_template
import sqlite3
from datetime import datetime
import re
import os

app = Flask(__name__)

def get_db_connection():
    current_date = datetime.now().strftime("%d_%m_%Y")
    db_name = f"./db/hackernews_{current_date}.db"
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable column access by name: row['column_name']
    return conn

def load_blacklist():
    """Load blacklist patterns from config/blacklist.txt."""
    blacklist = {"regex": [], "string": []}
    
    if os.path.exists("config/blacklist.txt"):
        with open("config/blacklist.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore comments
                    if line.startswith("regex:"):
                        pattern = line.split("regex:", 1)[1].strip()
                        blacklist["regex"].append(pattern)
                    elif line.startswith("string:"):
                        string_match = line.split("string:", 1)[1].strip()
                        blacklist["string"].append(string_match)
    return blacklist

def is_blacklisted(url, title, blacklist):
    """Check if the URL or title matches any blacklist patterns."""
    url = str(url) if url else ""
    title = str(title) if title else ""

    for pattern in blacklist["regex"]:
        if re.search(pattern, url) or re.search(pattern, title):
            return True

    for string in blacklist["string"]:
        if string in url or string in title:
            return True

    return False


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, by, url
        FROM stories
        ORDER BY last_updated DESC
    ''')
    news_items = cursor.fetchall()
    conn.close()

    # Load blacklist and filter the news items
    blacklist = load_blacklist()
    filtered_news = [
        item for item in news_items 
        if not is_blacklisted(item['url'], item['title'], blacklist)
    ]

    return render_template('index.html', news_items=filtered_news)

if __name__ == '__main__':
    app.run(debug=False)
