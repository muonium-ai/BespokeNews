import bleach

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



def html_cleaner(html):
    """
    Clean the provided HTML content by removing unwanted tags and attributes.

    Parameters:
        html (str): The HTML content to clean.

    Returns:
        str: The cleaned HTML content.
    """
    # Sanitize the HTML to prevent XSS attacks
    clean_html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    return clean_html