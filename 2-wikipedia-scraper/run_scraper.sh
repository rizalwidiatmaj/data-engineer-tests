#!/bin/bash
set -e

if [ $# -lt 1 ]; then
  echo "Usage: ./run_scraper.sh \"search phrase\" [proxy_url]"
  exit 1
fi

QUERY=$1
PROXY=$2

python3 "$(dirname "$0")/scraper.py" "$QUERY" "$PROXY"