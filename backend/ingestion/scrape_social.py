"""
Entry point for the social media scraper.

Run from the backend/ directory:
    python ingestion/scrape_social.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ingestion.social import scrape_pending_social

if __name__ == "__main__":
    scrape_pending_social()
