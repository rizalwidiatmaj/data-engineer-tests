# Wikipedia Scraper

[back to home](../README.md)

## Overview

A script to scrape Wikipedia articles, extract structured metadata, main content, and categories, and save the results as JSON Lines.

## Requirements

* Python 3.10+

## How to run

Run the Python Forward Proxy Server

```bash
chmod +x run_scraper.sh
./run_scraper.sh "Proxy Server"
# or
./run_scraper.sh "Proxy Server" "http://localhost:9919"
```

the output file will be in `output/` directory.