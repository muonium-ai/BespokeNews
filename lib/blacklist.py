# lib/blacklist.py

import os
import re


class Blacklist:
    def __init__(self, blacklist_files=["config/blacklist.txt"]):
        """
        Initialize the Blacklist with patterns from one or more files.

        Parameters:
            blacklist_files (list of str): List of paths to blacklist files.
                                           Defaults to ["config/blacklist.txt"].
        """
        self.regex_patterns = []
        self.string_patterns = []
        self.load_blacklists(blacklist_files)

    def load_blacklists(self, blacklist_files):
        """
        Load blacklist patterns from the specified list of files.

        Each blacklist file should have entries in the following format:
        - Lines starting with 'regex:' are treated as regular expressions.
        - Lines starting with 'string:' are treated as plain string matches.
        - Lines starting with '#' are comments and are ignored.
        - Empty lines are ignored.

        Parameters:
            blacklist_files (list of str): List of paths to blacklist files.
        """
        for file in blacklist_files:
            if not os.path.exists(file):
                print(f"Blacklist file '{file}' not found. Skipping.")
                continue

            with open(file, "r") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # Ignore comments and empty lines

                    if line.startswith("regex:"):
                        pattern = line.split("regex:", 1)[1].strip()
                        if self.validate_regex(pattern, file, line_number):
                            self.regex_patterns.append(pattern)
                    elif line.startswith("string:"):
                        string_match = line.split("string:", 1)[1].strip().lower()
                        self.string_patterns.append(string_match)
                    else:
                        print(f"Ignoring invalid line {line_number} in '{file}': {line}")

    def validate_regex(self, pattern, file, line_number):
        """
        Validate the provided regex pattern.

        Parameters:
            pattern (str): The regex pattern to validate.
            file (str): The file from which the pattern is loaded.
            line_number (int): The line number of the pattern in the file.

        Returns:
            bool: True if the regex is valid, False otherwise.
        """
        try:
            re.compile(pattern)
            return True
        except re.error as e:
            print(f"Invalid regex pattern at line {line_number} in '{file}': {e}")
            return False

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
