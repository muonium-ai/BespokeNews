# rss.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, render_template
#from bn_app import fetch_news_items, filter_news_items

rss_bp = Blueprint('rss2', __name__)

@rss_bp.route("/")
def index():
    return 'Hello, World! from RSS'