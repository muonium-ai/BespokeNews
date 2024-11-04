# hf.py
import os
import sys
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, render_template

hf = Blueprint('huggingface', __name__)

@hf.route("/")
def index():
    response = requests.get("https://huggingface.co/api/trending")
    if response.status_code == 200:
        trending_items = response.json().get("recentlyTrending", [])
        news_items = [
            {
                "title": item["repoData"].get("title", "No Title"),
                "url": f"https://huggingface.co/{item['repoData']['id']}",
                "author": item["repoData"].get("author", "Unknown Author"),
                "downloads": item["repoData"].get("downloads", 0),
                "likes": item["repoData"].get("likes", 0)
            }
            for item in trending_items
        ]
    else:
        news_items = []

    return render_template("huggingface.html", news_items=news_items)