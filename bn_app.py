from flask import Flask, render_template, request, abort, redirect, url_for
from markdown import markdown
from markupsafe import Markup  # Updated import
import bleach
import sqlite3
from datetime import datetime
import tldextract
import logging
import sys
import signal
import atexit

# app blueprints to load multiple apps
from apps.rss import rss_bp
from apps.hn import hn


# Import the Blacklist class from the lib.blacklist module
from lib.blacklist import Blacklist
from lib.html_cleaner import html_cleaner

# Initialize the Blacklist in the app's global context
blacklist = Blacklist(blacklist_files=["config/blacklist.txt", "config/blacklist_urls.txt"])

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

# Store start time globally
start_time = datetime.now()
print(f"\n HNLocal started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

def cleanup():
    """Function to run when the app exits"""
    end_time = datetime.now()
    runtime = end_time - start_time
    print(f"\nApplication stopped at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total runtime: {runtime}")

# Register the cleanup function to run at exit
atexit.register(cleanup)


# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print('\nCtrl+C pressed...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


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
    clean_html = html_cleaner(html)

    # Mark the string as safe HTML for Jinja2
    return Markup(clean_html)




@app.before_request
def init():
    """initialize"""

@app.route("/")
def index():
    return redirect('/hackernews')

@app.route("/favicon.ico")
def favicon():
    # send static/favicon.ico file
    return app.send_static_file("favicon.ico")

app.register_blueprint(rss_bp,name="rss2",url_prefix='/rss')
app.register_blueprint(hn,url_prefix='/hackernews')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
