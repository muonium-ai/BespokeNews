from flask import Flask, render_template, request, abort
from markdown import markdown
from markupsafe import Markup  # Updated import
import bleach
import sqlite3
from datetime import datetime
import tldextract
import logging

# Import the Blacklist class from the lib.blacklist module
from lib.blacklist import Blacklist

# Initialize the Blacklist in the app's global context
blacklist = Blacklist(blacklist_file="config/blacklist.txt")

# Create a filter class to exclude static file requests
class NoStaticFilter(logging.Filter):
    def filter(self, record):
        # Check if args exists and is a tuple with content
        if hasattr(record, 'args') and isinstance(record.args, tuple) and len(record.args) > 0:
            # Check if the first argument contains 'static'
            return not (isinstance(record.args[0], str) and '/static/' in record.args[0].lower())
        return True

# Apply the filter to Werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(NoStaticFilter())

# Define custom patterns to exclude static files, accounting for leading quotes
custom_patterns = [
    r'^"GET /static/',      # Matches "GET /static/...
    r'^"HEAD /static/'      # Matches "HEAD /static/...
]


  # Uses default patterns

app = Flask(__name__)


# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "p",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "img",
]
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id"],
    "a": ["href", "rel", "title"],
    "img": ["src", "alt", "title"],
}


def extract_main_domain(url):
    """
    Extracts the main domain from a given URL, handling complex TLDs.

    Parameters:
        url (str): The URL string.

    Returns:
        str: The main domain (e.g., example.co.uk) or None if the URL is invalid.
    """
    try:
        ext = tldextract.extract(url)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
        else:
            return None
    except Exception:
        # Log the error if necessary
        return None


@app.template_filter("extract_main_domain")
def extract_main_domain_filter(url):
    return extract_main_domain(url)


@app.template_filter("markdown")
def markdown_filter(text):
    """
    Convert Markdown text to HTML, then sanitize it.
    """
    if not text:
        return ""
    # Convert Markdown to HTML
    html = markdown(text, extensions=["extra", "codehilite", "nl2br"])

    # Sanitize the HTML to prevent XSS attacks
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    # Mark the string as safe HTML for Jinja2
    return Markup(clean_html)


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


@app.before_request
def init():
    """initialize"""


@app.route("/")
def index():
    news_items = fetch_news_items()
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news)


@app.route("/latest")
def latest():
    news_items = fetch_news_items(order_by="last_updated")
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news)


@app.route("/search")
def search():
    query = request.args.get("q", "")
    news_items = fetch_news_items(query=query)
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news, query=query)


@app.route("/show/<int:id>")
def show(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, title, by, url, content, summary, score, last_updated, priority
        FROM stories
        WHERE id = ?
    """,
        (id,),
    )
    news_item = cursor.fetchone()
    conn.close()

    if news_item is None:
        # Story with the given ID does not exist
        abort(404)

    # Check if the story is blacklisted
    if blacklist.is_blacklisted(news_item["url"], news_item["title"]):
        abort(404)

    return render_template("show.html", news_item=news_item)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=False)
