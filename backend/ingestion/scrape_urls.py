# Entry point for the web scraper; run from backend/: python ingestion/scrape_urls.py

import os
import sys

# Add backend/ to path so config, rag, and ingestion packages resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ingestion.scraper import scrape_pending_sources

if __name__ == "__main__":
    scrape_pending_sources()
