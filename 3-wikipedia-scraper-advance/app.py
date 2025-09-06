"""
Wikipedia Article Scraper

This script scrapes Wikipedia articles from provided links, extracts metadata, content, and categories,
and saves the results in JSON Lines format. It keeps track of processed and currently scraping links
to avoid duplicate processing.

Functions:
    scraper(link: str):
        Fetches a Wikipedia article from the given URL, parses its metadata, content, and categories,
        and appends the extracted information as a JSON object to './output/articles.jsonl'.

Main Execution:
    - Reads 'processed_links' and 'scraping_links' files to determine which links need processing.
    - Iterates over unique processed links, skipping those already in 'scraping_links'.
    - For each unprocessed link, calls the scraper function and updates 'scraping_links' accordingly.
    - Handles KeyboardInterrupt to allow graceful termination.
"""

import os
import sys
import json
import datetime
import http.client
import urllib.parse

from utils.wikipedia_parser import WikipediaArticleParser


if not os.path.exists('output'):
    print("[*] Create output/ directory.")
    os.makedirs('output', exist_ok=True)


def scraper(link: str):
    """
    Fetches and parses a Wikipedia article from the given URL, extracts metadata, content, and categories,
    and appends the structured article data as a JSON line to './output/articles.jsonl'.
    Args:
        link (str): The URL of the Wikipedia article to scrape.
    Raises:
        SystemExit: If the host is unknown or article metadata is not found.
    Side Effects:
        Writes a JSON line representing the article to './output/articles.jsonl'.
    """

    parsed_url = urllib.parse.urlparse(link)
    host = parsed_url.hostname
    path = parsed_url.path or '/'
    if parsed_url.query:
        path += f"?{parsed_url.query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    if not host:
        print("Host unknown")
        sys.exit(0)

    conn = http.client.HTTPSConnection(host, port=443)

    try:
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        parser = WikipediaArticleParser()
        parser.feed(data.decode())

        if len(parser.article_metadata) == 0:
            print("Article Metadata not found")
            sys.exit(0)

        metadata = json.loads(parser.article_metadata[0])
        content = " ".join([chunk_text for chunk_text in parser.article_content if chunk_text != ''])
        categories = parser.article_categories[2:]
        date_published = metadata['datePublished']
        dt = datetime.datetime.strptime(date_published, "%Y-%m-%dT%H:%M:%SZ")
        article = {
            "title": metadata['name'],
            "link": metadata['url'],
            "content": content,
            "createdAt": dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "category": categories
        }
        with open('./output/articles.jsonl', 'a') as f:
            json_line = json.dumps(article)
            f.write(json_line + '\n')
    finally:
        conn.close()


if __name__ == '__main__':
    print("===============================")
    with open('processed_links', 'r') as plf, open('scraping_links', 'r') as slf:
        processed_links = plf.read().split('\n')
        scraping_links = slf.read().split('\n')
    print(f"[*] Got the processing Links: {len(processed_links)}")
    print(f"[*] Have the Scraping Links: {len(scraping_links)}")
    unique_links = list(set(processed_links))
    print(f"[*] Drop Duplicate Link from Processing Links: {len(unique_links)}/{len(processed_links)}")
    scraping_unique_links = set(scraping_links) if scraping_links else set()

    for link in unique_links:
        if link in scraping_unique_links:
            print(f"[!] The link: {link} has already processed")
            continue
        try:
            scraper(link=link)
            scraping_unique_links.add(link)
            print(f"[*] The link: {link} added to link listed")
        except KeyboardInterrupt:
            print("[*] Process stopped by user ... ")
            break

    with open('scraping_links', 'w') as wf:
        scraping_links = list(scraping_unique_links)
        print(f"[*] Update the Scraping Links: {len(scraping_links)}")
        wf.writelines([f"{link}\n" for link in scraping_links if link != ''])
