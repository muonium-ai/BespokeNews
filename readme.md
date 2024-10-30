
# Hacker News Stories Fetcher

A tool to **fetch and store Hacker News stories locally**, with a built-in Flask app for viewing and managing the data.

---

## Setup

1. **Create a Conda environment:**
   ```bash
   conda create -n hnlocal -y
   conda activate hnlocal
   ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    uv run ruff check
    ```

3. ** Pre-Commit **
    ```bash
    uv run ruff check
    ruff format
    ```

---

## Usage

1. **Open two terminals:**

   - **Terminal 1**: Fetch Hacker News stories  
     ```bash
     python hn_topnews_fetch.py
     ```

   - **Terminal 2**: Run the Flask app
    ```bash
    python .\flask_app.py
     ```

    ### run in production mode
    ```bash
    gunicorn -w 4 -b 0.0.0.0:8000 flask_app:app
     ```
---
## Features Completed

- **Whitelist and Prioritylist**  
  Apply a whitelist or blacklist to filter stories.

- **Parallel Downloads**  
  Explore parallelization for faster downloads.

- **Separate Databases by Day**  
  Organize data with separate databases for each day.

- **Content Extraction and AI Summary**  
  Extract main text, and generate AI summaries 

- **Flask UI Improvements**  
  Make the Flask interface more user-friendly.

- **WebUI Updates**  
  Enable updating stories directly from the WebUI.
  cron and recurring update implemented at 1 minute update
  page refresh enabled for all pages for now at 1 minute interval

- **Save Story Details Locally**  
  Fetch and store story URLs, main text, and metadata locally.

- **Cache Content**  
  Cache stories for 24 hours to avoid redundant downloads.

## Features in Progress (TODO)

- **Dynamic User-Agent**  
  Read the User-Agent from a text file instead of hardcoding.

- **get a audio version of content**
  possibly NotebookLM integration

- **Podcast of Interesting Stories**  
  List top stories as a short podcast.

- **Pinokio (Possible Feature)**  
  Investigate new feature integration with "Pinokio".


---

## Additional Ideas

- **Search Stories via Algolia API**  
  Example: [Hacker News Algolia Search](https://hn.algolia.com/?q=llama)

- **screenshot of URLs**
  image, pdf and html using shot-scraper

- ** Extend HNLocal and LocalNews and fetch from other sites**
  - google news
  - specific sites
  - rss feeds
  - podcast





---

## License

MIT License. Feel free to contribute or suggest improvements!

---

## Contact

If you encounter any issues or have suggestions, please open an issue on GitHub.

## Author

**Senthil Nayagam**  
Email: senthil @ muonium.ai
X: [senthilnayagam ](https://x.com/senthilnayagam)