# lib/blacklist.py

import os
import re


class Blacklist:
    def __init__(self, blacklist_file="config/blacklist.txt"):
        """
        Initialize the Blacklist with patterns from a file.

        Parameters:
            blacklist_file (str): Path to the blacklist file.
        """
        self.regex_patterns = []
        self.string_patterns = []
        self.load_blacklist(blacklist_file)

    def load_blacklist(self, blacklist_file):
        """
        Load blacklist patterns from the specified file.

        The blacklist file should have entries in the following format:
        - Lines starting with 'regex:' are treated as regular expressions.
        - Lines starting with 'string:' are treated as plain string matches.
        - Lines starting with '#' are comments and are ignored.
        - Empty lines are ignored.

        Parameters:
            blacklist_file (str): Path to the blacklist file.
        """
        if not os.path.exists(blacklist_file):
            print(f"Blacklist file '{blacklist_file}' not found.")
            return

        with open(blacklist_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Ignore comments and empty lines

                if line.startswith("regex:"):
                    pattern = line.split("regex:", 1)[1].strip()
                    self.regex_patterns.append(pattern)
                elif line.startswith("string:"):
                    string_match = line.split("string:", 1)[1].strip().lower()
                    self.string_patterns.append(string_match)

    def is_blacklisted(self, url, title):
        """
        Check if the URL or title matches any blacklist patterns.

        Parameters:
            url (str): The URL to check.
            title (str): The title to check.

        Returns:
            bool: True if blacklisted, False otherwise.
        """
        url = str(url).lower() if url else ""
        title = str(title).lower() if title else ""

        # Check regex patterns
        for pattern in self.regex_patterns:
            if re.search(pattern, url) or re.search(pattern, title):
                return True

        # Check string patterns
        for string in self.string_patterns:
            if string in url or string in title:
                return True

        return False
