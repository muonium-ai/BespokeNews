from flask import Flask, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    current_date = datetime.now().strftime("%d_%m_%Y")
    # Create the string with "hackernews" + date + ".db"
    db_name = f"./db/hackernews_{current_date}.db"
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Enable column access by name: row['column_name']
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, by, url
        FROM stories
        ORDER BY last_updated DESC
    ''') # LIMIT 30
    news_items = cursor.fetchall()
    conn.close()
    return render_template('index.html', news_items=news_items)

if __name__ == '__main__':
    app.run(debug=False)
