# Entry point for the social media scraper; run from backend/: python ingestion/scrape_social.py

import os
import sys

# Add backend/ to path so config, rag, and ingestion packages resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ingestion.social import scrape_pending_social

if __name__ == "__main__":
    scrape_pending_social()
