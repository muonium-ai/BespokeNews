import sqlite3
from datetime import datetime
# Import the Blacklist class from the lib.blacklist module
from lib.blacklist import Blacklist

# Initialize the Blacklist in the app's global context
blacklist = Blacklist(blacklist_files=["config/blacklist.txt", "config/blacklist_urls.txt"])



def get_db_connection():
    current_date = datetime.now().strftime("%d_%m_%Y")
    db_name = f"./db/hackernews_{current_date}.db"
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def fetch_news_items(query=None, order_by=None):
    """Fetch news items from the database, optionally filtering by a search query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if query:
        cursor.execute(
            """
            SELECT id, title, by, url, score, content, summary, priority 
            FROM stories
            WHERE title LIKE ?
            ORDER BY priority DESC, score DESC
        """,
            ("%" + query + "%",),
        )
    else:
        if order_by:
            cursor.execute(f"""
                SELECT id, title, by, url, score, content, summary, priority
                FROM stories
                ORDER BY {order_by} DESC, priority DESC, score DESC
            """)
        else:
            cursor.execute("""
                SELECT id, title, by, url, score, content, summary, priority
                FROM stories
                 ORDER BY priority DESC, score DESC
            """)
    news_items = cursor.fetchall()
    conn.close()
    return news_items


def filter_news_items(news_items):
    """Filter news items based on the blacklist."""
    filtered_news = [
        item
        for item in news_items
        if not blacklist.is_blacklisted(item["url"], item["title"])
    ]
    return filtered_news

