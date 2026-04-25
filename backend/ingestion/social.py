"""
Social media scraper for the Daleel KU ingestion pipeline.

Reads pending Instagram and X (Twitter) sources from the `source` table,
fetches recent posts via Apify, extracts captions/tweets and OCRs images
with GPT-4o Vision, then ingests everything into pgvector.

Prerequisites — the `source` table must have:
    - source_type column (enum: 'web', 'instagram', 'x')
    - status column (default 'pending')
    - college_id column (nullable integer)
"""

import os
import sys
import base64
import re
from datetime import datetime, timezone

import requests
from apify_client import ApifyClient

_BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import supabase_admin, APIFY_API_KEY, OPENAI_API_KEY  # noqa: E402
from rag.ingest import (  # noqa: E402
    _classify_document,
    _classify_source,
    _clean_arabic,
    _SPLITTER,
    _UUID_METADATA_KEYS,
    _fetch_colleges,
    _fetch_topics,
    _fetch_majors,
)
from ingestion.scraper import _upsert_document, _ingest_web_markdown, _document_already_ingested  # noqa: E402

POSTS_PER_ACCOUNT = 20

_INSTAGRAM_HANDLE_RE = re.compile(r"instagram\.com/([^/?#]+)")
_X_HANDLE_RE = re.compile(r"(?:twitter\.com|x\.com)/([^/?#]+)")


def _extract_instagram_handle(url: str) -> str | None:
    match = _INSTAGRAM_HANDLE_RE.search(url)
    if match:
        handle = match.group(1).strip("/")
        if handle not in ("p", "reel", "stories", "explore"):
            return handle
    return None


def _extract_x_handle(url: str) -> str | None:
    match = _X_HANDLE_RE.search(url)
    if match:
        handle = match.group(1).strip("/")
        if handle not in ("status", "search", "explore", "home", "i"):
            return handle
    return None


def _image_to_base64(image_url: str) -> str | None:
    try:
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception as exc:
        print(f"[social] Failed to download image: {exc}")
        return None


def _ocr_image(image_base64: str) -> str:
    """Extract text from an image using GPT-4o Vision. Returns extracted text or empty string."""
    from openai import OpenAI as OpenAIClient
    client = OpenAIClient(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract ALL text from this image. The text may be in Arabic or English. "
                            "Return only the extracted text, nothing else. "
                            "If there is no readable text in the image, return an empty string."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ],
            }],
            max_tokens=1000,
            temperature=0,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[social] OCR failed: {exc}")
        return ""


def _scrape_instagram(handle: str) -> list[dict]:
    """Fetch recent posts from an Instagram profile using Apify."""
    client = ApifyClient(APIFY_API_KEY)

    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": POSTS_PER_ACCOUNT,
        "addParentData": False,
    }

    print(f"[social] Scraping @{handle} (limit={POSTS_PER_ACCOUNT})...")
    try:
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[social] Got {len(items)} posts from @{handle}")
        return items
    except Exception as exc:
        print(f"[social] Apify scrape failed for @{handle}: {exc}")
        return []


def _scrape_x(handle: str) -> list[dict]:
    """Fetch recent tweets from an X/Twitter profile using Apify."""
    client = ApifyClient(APIFY_API_KEY)

    run_input = {
        "handles": [handle],
        "tweetsDesired": POSTS_PER_ACCOUNT,
        "addUserInfo": False,
    }

    print(f"[social] Scraping X @{handle} (limit={POSTS_PER_ACCOUNT})...")
    try:
        run = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[social] Got {len(items)} tweets from @{handle}")
        return items
    except Exception as exc:
        print(f"[social] Apify scrape failed for X @{handle}: {exc}")
        return []


def _fetch_instagram_bio(handle: str) -> str:
    """Fetch the bio/description of an Instagram profile using Apify."""
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "details",
        "resultsLimit": 1,
    }
    print(f"[social] Fetching bio for @{handle}...")
    try:
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if items:
            return items[0].get("biography") or ""
    except Exception as exc:
        print(f"[social] Failed to fetch bio for @{handle}: {exc}")
    return ""


def _handle_post(
    post: dict,
    handle: str,
    source_id: str,
    platform: str = "instagram",
    college_id: int = None,
) -> None:
    """Process a single social media post — text + image OCR."""
    if platform == "x":
        post_url = post.get("url") or f"https://x.com/{handle}/status/{post.get('id', '')}"
        caption = post.get("full_text") or post.get("text") or ""
        media = post.get("entities", {}).get("media", [])
        image_urls = [m.get("media_url_https", "") for m in media if m.get("media_url_https")]
        timestamp = post.get("created_at") or ""
    else:
        post_url = post.get("url") or f"https://www.instagram.com/p/{post.get('shortCode', '')}/"
        caption = post.get("caption") or ""
        image_urls = [img if isinstance(img, str) else img.get("url", "") for img in (post.get("images") or [])] if post.get("images") else []
        if not image_urls and post.get("displayUrl"):
            image_urls = [post.get("displayUrl")]
        timestamp = post.get("timestamp") or ""

    if _document_already_ingested(post_url):
        print(f"[social] Already ingested, skipping: {post_url}")
        return

    # OCR all images in the post (including carousel slides)
    ocr_texts = []
    for image_url in image_urls:
        if not image_url:
            continue
        img_b64 = _image_to_base64(image_url)
        if img_b64:
            text = _ocr_image(img_b64)
            if text:
                ocr_texts.append(text)
                print(f"[social] OCR extracted {len(text)} chars from image")
    ocr_text = "\n\n".join(ocr_texts)

    # Combine caption and OCR text
    full_text = ""
    if caption:
        full_text += caption
    if ocr_text:
        full_text += "\n\n" + ocr_text if full_text else ocr_text

    if not full_text.strip():
        print(f"[social] No text content for {post_url} — skipping.")
        return

    title = f"@{handle} — {timestamp[:10]}" if timestamp else f"@{handle} post"

    try:
        colleges = _fetch_colleges()
        topics = _fetch_topics()
        majors = _fetch_majors()
        classification = _classify_document(
            full_text, colleges, topics, majors, forced_college_id=college_id
        )

        document_id = _upsert_document(
            title=title,
            document_type=platform,
            source_url=post_url,
            source_id=source_id,
            major_id=classification["major_id"],
        )

        _ingest_web_markdown(
            document_id=document_id,
            source_id=source_id,
            markdown=full_text,
            title=title,
            classification=classification,
        )
    except Exception as exc:
        print(f"[social] Failed to ingest post {post_url}: {exc}")


def scrape_pending_social() -> None:
    """Fetch all sources with source_type='instagram' or 'x' and status='pending', then scrape each one."""
    result = (
        supabase_admin.table("source")
        .select("*")
        .in_("source_type", ["instagram", "x"])
        .eq("status", "pending")
        .execute()
    )
    sources = result.data or []

    if not sources:
        print("[social] No pending social media sources found.")
        return

    print(f"[social] Found {len(sources)} pending social source(s).")

    for source in sources:
        source_id = source["source_id"]
        url = source.get("url", "")
        college_id = source.get("college_id")
        platform = source.get("source_type", "instagram")

        # Extract handle based on platform
        if platform == "x":
            handle = _extract_x_handle(url)
        else:
            handle = _extract_instagram_handle(url)

        if not handle:
            print(f"[social] Could not extract handle from {url} — skipping.")
            supabase_admin.table("source").update({"status": "failed"}).eq(
                "source_id", source_id
            ).execute()
            continue

        # Scrape posts based on platform
        if platform == "x":
            posts = _scrape_x(handle)
        else:
            posts = _scrape_instagram(handle)

        if not posts:
            print(f"[social] No posts returned for @{handle} — marking failed.")
            supabase_admin.table("source").update({"status": "failed"}).eq(
                "source_id", source_id
            ).execute()
            continue

        # Auto-classify college from account bio if not set
        if college_id is None:
            if platform == "instagram":
                bio_text = _fetch_instagram_bio(handle)
            else:
                bio_text = ""
            if bio_text.strip():
                colleges = _fetch_colleges()
                college_id = _classify_source(bio_text, colleges)
                supabase_admin.table("source").update({"college_id": college_id}).eq(
                    "source_id", source_id
                ).execute()
                print(f"[social] Auto-classified source from bio as college_id={college_id}")

        for post in posts:
            _handle_post(
                post=post,
                handle=handle,
                source_id=source_id,
                platform=platform,
                college_id=college_id,
            )

        supabase_admin.table("source").update({
            "status": "scraped",
            "last_scraped": datetime.now(timezone.utc).isoformat(),
        }).eq("source_id", source_id).execute()
        print(f"[social] Source @{handle} ({platform}) marked as scraped.")
