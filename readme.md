
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

## Features in Progress (TODO)

- **Whitelist and Blacklist**  
  Apply a whitelist or blacklist to filter stories.
  
- **Dynamic User-Agent**  
  Read the User-Agent from a text file instead of hardcoding.

- **Parallel Downloads**  
  Explore parallelization for faster downloads.

- **Flask UI Improvements**  
  Make the Flask interface more user-friendly.

- **Pinokio (Possible Feature)**  
  Investigate new feature integration with "Pinokio".

- **Separate Databases by Day**  
  Organize data with separate databases for each day.

- **WebUI Updates**  
  Enable updating stories directly from the WebUI.

- **Content Extraction and AI Summary**  
  Extract main text, and generate AI summaries (NotebookLM integration).

---

## Additional Ideas

- **Search Stories via Algolia API**  
  Example: [Hacker News Algolia Search](https://hn.algolia.com/?q=llama)

- **Cache Content**  
  Cache stories for 24 hours to avoid redundant downloads.

- **Podcast of Interesting Stories**  
  List top stories as a short podcast.

- **Save Story Details Locally**  
  Fetch and store story URLs, main text, and metadata locally.

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