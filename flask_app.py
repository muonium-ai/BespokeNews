from flask import Flask, render_template, request, abort
from markdown import markdown
from markupsafe import Markup  # Updated import
import bleach
import sqlite3
from datetime import datetime
import re
import os

app = Flask(__name__)

# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'p', 'pre',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'rel', 'title'],
    'img': ['src', 'alt', 'title'],
}

@app.template_filter('markdown')
def markdown_filter(text):
    """
    Convert Markdown text to HTML, then sanitize it.
    """
    if not text:
        return ''
    # Convert Markdown to HTML
    html = markdown(text, extensions=['extra', 'codehilite', 'nl2br'])

    # Sanitize the HTML to prevent XSS attacks
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    # Mark the string as safe HTML for Jinja2
    return Markup(clean_html)


# Global variable to store the blacklist
blacklist = None

def get_db_connection():
    current_date = datetime.now().strftime("%d_%m_%Y")
    db_name = f"./db/hackernews_{current_date}.db"
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def load_blacklist():
    """Load blacklist patterns from config/blacklist.txt."""
    blacklist_data = {"regex": [], "string": []}
    
    if os.path.exists("config/blacklist.txt"):
        with open("config/blacklist.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore comments and empty lines
                    if line.startswith("regex:"):
                        pattern = line.split("regex:", 1)[1].strip()
                        blacklist_data["regex"].append(pattern)
                    elif line.startswith("string:"):
                        string_match = line.split("string:", 1)[1].strip()
                        blacklist_data["string"].append(string_match)
    return blacklist_data

def is_blacklisted(url, title):
    """Check if the URL or title matches any blacklist patterns."""
    url = str(url) if url else ""
    title = str(title) if title else ""

    # Access the global blacklist variable
    global blacklist

    for pattern in blacklist["regex"]:
        if re.search(pattern, url) or re.search(pattern, title):
            return True

    for string in blacklist["string"]:
        if string in url or string in title:
            return True

    return False

def fetch_news_items(query=None):
    """Fetch news items from the database, optionally filtering by a search query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if query:
        cursor.execute('''
            SELECT id, title, by, url, score
            FROM stories
            WHERE title LIKE ?
            ORDER BY score DESC
        ''', ('%' + query + '%',))
    else:
        cursor.execute('''
            SELECT id, title, by, url, score
            FROM stories
            ORDER BY score DESC
        ''')
    news_items = cursor.fetchall()
    conn.close()
    return news_items

def filter_news_items(news_items):
    """Filter news items based on the blacklist."""
    filtered_news = [
        item for item in news_items
        if not is_blacklisted(item['url'], item['title'])
    ]
    return filtered_news

@app.before_request
def init():
    """Load the blacklist once when the application starts."""
    global blacklist
    blacklist = load_blacklist()

@app.route('/')
def index():
    news_items = fetch_news_items()
    filtered_news = filter_news_items(news_items)
    return render_template('index.html', news_items=filtered_news)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    news_items = fetch_news_items(query=query)
    filtered_news = filter_news_items(news_items)
    return render_template('index.html', news_items=filtered_news, query=query)


@app.route('/show/<int:id>')
def show(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, by, url, content, summary, score, last_updated
        FROM stories
        WHERE id = ?
    ''', (id,))
    news_item = cursor.fetchone()
    conn.close()

    if news_item is None:
        # Story with the given ID does not exist
        abort(404)

    # Check if the story is blacklisted
    if is_blacklisted(news_item['url'], news_item['title']):
        abort(404)

    return render_template('show.html', news_item=news_item)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=False)
