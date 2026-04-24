"""
Utility to map all URLs on a domain before committing to a full crawl.
Use this to decide what crawl_limit to set on a source row.

Run from backend/:
    python ingestion/map_domain.py https://cls.ku.edu.kw
"""

import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import FIRECRAWL_API_KEY
from firecrawl import V1FirecrawlApp as FirecrawlApp


def get_url_count(url: str, fc: FirecrawlApp = None) -> int:
    """Return the total number of URLs found on a domain via map_url."""
    if fc is None:
        fc = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    result = fc.map_url(url)
    return len(result.links or [])


def map_domain(url: str) -> None:
    fc = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    print(f"\nMapping: {url}")
    print("This may take a few seconds...\n")

    result = fc.map_url(url)
    links = result.links or []

    if not links:
        print("No URLs found.")
        return

    depths: dict[int, list[str]] = {}
    for link in links:
        depth = len([p for p in urlparse(link).path.split("/") if p])
        depths.setdefault(depth, []).append(link)

    print(f"Total URLs found: {len(links)}\n")
    print("Breakdown by depth:")
    for depth in sorted(depths):
        print(f"  Depth {depth}: {len(depths[depth])} pages")

    print("\nSample URLs:")
    for link in links[:20]:
        print(f"  {link}")
    if len(links) > 20:
        print(f"  ... and {len(links) - 20} more")

    full  = len(links)
    half  = max(1, full // 2)
    print(f"\nSuggested limits based on crawl_depth:")
    print(f"  page → 1")
    print(f"  half → {half}")
    print(f"  full → {full}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingestion/map_domain.py <url>")
        sys.exit(1)
    map_domain(sys.argv[1])
