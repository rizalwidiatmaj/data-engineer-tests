"""
scraper.py

A script to scrape Wikipedia articles, extract structured metadata, main content, and categories, and save the results as JSON Lines.

Classes:
    WikipediaArticleParser(HTMLParser):
        Custom HTMLParser for extracting metadata, article content, and categories from Wikipedia article HTML.

Usage:
    python scraper.py <article_title> [proxy_url]

Arguments:
    article_title (str): The title of the Wikipedia article to scrape.
    proxy_url (str, optional): Optional HTTPS proxy URL to use for the request.

Functionality:
    - Constructs the Wikipedia article URL from the provided title.
    - Optionally connects via a specified HTTPS proxy.
    - Fetches the article HTML and parses it to extract:
        - Metadata from <script type="application/ld+json">.
        - Main textual content from <p>, <ul>, and heading <div> tags within the article body.
        - Article categories from the category links section.
    - Formats the extracted data into a JSON object with fields: title, link, content, createdAt, and category.
    - Appends the JSON object as a line to 'articles.jsonl'.

Exits:
    - If insufficient arguments are provided.
    - If the article metadata cannot be found.
    - If the host or proxy host is not defined.

Dependencies:
    - Built-in: ssl, sys, json, datetime, http.client, urllib.parse, html.parser
"""

import os
import ssl
import sys
import json
import datetime
import http.client
import urllib.parse

from html.parser import HTMLParser


class WikipediaArticleParser(HTMLParser):
    """
    WikipediaArticleParser is a custom HTMLParser for extracting structured data from Wikipedia article HTML.
    Attributes:
        is_parsing_metadata (bool): Indicates if the parser is currently inside a metadata <script> tag.
        article_metadata (list): Stores metadata content extracted from <script type="application/ld+json"> tags.
        is_parsing_content (bool): Indicates if the parser is currently inside the main article content.
        article_content (list): Stores the main textual content of the article, extracted from <p>, <ul>, and heading <div> tags within the body.
        is_inside_body (bool): Tracks whether the parser is inside the main body content <div class="mw-body-content">.
        article_categories (list): Stores the categories associated with the article, extracted from the category links section.
        is_parsing_category (bool): Indicates if the parser is currently inside the category links section.
    Methods:
        handle_starttag(tag, attrs): Handles the start of HTML tags, updating parsing state based on tag type and attributes.
        handle_endtag(tag): Handles the end of HTML tags, updating parsing state accordingly.
        handle_data(data): Handles the textual data within tags, appending relevant content to the appropriate attribute lists.
    """
    def __init__(self):
        super().__init__()
        self.is_parsing_metadata = False
        self.article_metadata = []
        self.is_parsing_content = False
        self.article_content = []
        self.is_inside_body = False
        self.article_categories = []
        self.is_parsing_category = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == 'script':
            if attrs.get('type') == "application/ld+json":
                self.is_parsing_metadata = True
        if tag.lower() == 'div' and 'class' in attrs:
            if attrs.get('class') == 'mw-body-content':
                self.is_inside_body = True
            if attrs.get('class') == "catlinks":
                self.is_inside_body = False
            if attrs.get('class') == "mw-normal-catlinks":
                self.is_parsing_category = True
        if tag.lower() == 'p' and self.is_inside_body:
            self.is_parsing_content = True
        if tag.lower() == 'div' and 'class' in attrs and self.is_inside_body:
            if attrs.get("class") in ("mw-heading2", "mw-heading3", "mw-heading4"):
                self.is_parsing_content = True
        if tag.lower() == 'ul' and self.is_inside_body:
            self.is_parsing_content = True

    def handle_endtag(self, tag):
        if tag.lower() == 'script' and self.is_parsing_metadata:
            self.is_parsing_metadata = False
        if tag.lower() == 'p' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'div' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'ul' and self.is_parsing_content and self.is_inside_body:
            self.is_parsing_content = False
        if tag.lower() == 'div' and self.is_parsing_category:
            self.is_parsing_category = False

    def handle_data(self, data):
        if self.is_parsing_metadata:
            self.article_metadata.append(data.strip())
        if self.is_parsing_content:
            self.article_content.append(data.strip())
        if self.is_parsing_category:
            self.article_categories.append(data.strip())


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)

    phrase = sys.argv[1]
    phrase = phrase.lower().replace(' ', '_').capitalize()
    proxy = sys.argv[2].strip() if len(sys.argv) == 3 else None

    print("===============================")
    print(f"[*] Wikipedia Scraper for Phrase: {phrase}")
    if proxy:
        print(f"[*] Using Forwarded Proxy: {proxy}")

    url = f"https://en.wikipedia.org/wiki/{phrase}"
    print(f"[*] Go to link: {url}")

    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.hostname
    path = parsed_url.path or '/'
    if parsed_url.query:
        path += f"?{parsed_url.query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    if not host:
        print("[!] Host Unknown")
        sys.exit(0)

    if proxy:
        context = ssl.create_default_context()
        proxy_url = urllib.parse.urlparse(proxy)
        proxy_host = proxy_url.hostname
        if not proxy_host:
            print("[!] Proxy Host not defined")
            sys.exit(0)
        proxy_port = proxy_url.port
        conn = http.client.HTTPSConnection(proxy_host, port=proxy_port, context=context)
        conn.set_tunnel(host, port=443)
        conn.connect()
    else:
        conn = http.client.HTTPSConnection(host, port=443)

    try:
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        parser = WikipediaArticleParser()
        parser.feed(data.decode())

        if len(parser.article_metadata) == 0:
            print(f"[!] Article {phrase} Metadata NOT FOUND")
            sys.exit(0)

        metadata = json.loads(parser.article_metadata[0])
        content = " ".join([chunk_text for chunk_text in parser.article_content if chunk_text != ''])
        categories = parser.article_categories[2:]
        date_published = metadata['datePublished']
        dt = datetime.datetime.strptime(date_published, "%Y-%m-%dT%H:%M:%SZ")
        created_at = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        article = {
            "title": metadata['name'],
            "link": metadata['url'],
            "content": content,
            "createdAt": created_at,
            "category": categories
        }
        print(f"[*] Found the {phrase} Article")
        print(f"Title: {metadata['name']}")
        print(f"Link: {metadata['url']}")
        print(f"Content: {content[:100]}...")
        print(f"Created At: {created_at}")
        print(f"Categories: {', '.join(categories)[:50]}...")
        if not os.path.exists('output'):
            print("[*] Create output/ directory.")
            os.makedirs('output', exist_ok=True)
        with open('./output/articles.jsonl', 'a') as f:
            print("[*] Writing the output into ./output/articles.jsonl")
            json_line = json.dumps(article)
            f.write(json_line + '\n')
    except Exception as e:
        print(f"Error when connecting: {e}")
    finally:
        conn.close()
        print("===============================")
