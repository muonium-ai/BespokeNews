import os
import sys
from .common import get_db_connection, fetch_news_items, filter_news_items, blacklist
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, render_template, request, abort

hn = Blueprint('rss', __name__)

@hn.route("/")
def index():
    news_items = fetch_news_items()
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news)


@hn.route("/latest")
def latest():
    news_items = fetch_news_items(order_by="last_updated")
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news)


@hn.route("/search")
def search():
    query = request.args.get("q", "")
    news_items = fetch_news_items(query=query)
    filtered_news = filter_news_items(news_items)
    return render_template("index.html", news_items=filtered_news, query=query)


@hn.route("/show/<int:id>")
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

