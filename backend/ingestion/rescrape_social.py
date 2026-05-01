import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from config import supabase_admin
from ingestion.social import scrape_pending_social


def rescrape_social():
    """Reset all scraped social sources to pending, then scrape for new posts."""
    result = (
        supabase_admin.table("source")
        .update({"status": "pending"})
        .in_("source_type", ["instagram", "x"])
        .eq("status", "scraped")
        .execute()
    )
    count = len(result.data) if result.data else 0
    print(f"[rescrape] Reset {count} social source(s) to pending.")

    scrape_pending_social()


if __name__ == "__main__":
    rescrape_social()
