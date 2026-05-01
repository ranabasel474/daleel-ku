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
from ingestion.document_store import document_already_ingested, upsert_document  # noqa: E402
from rag.classify import classify_source, classify_document, fetch_colleges, fetch_topics, fetch_majors  # noqa: E402
from rag.store import chunk_and_store  # noqa: E402

POSTS_PER_ACCOUNT = 20  # limits Apify actor cost per source run

_INSTAGRAM_HANDLE_RE = re.compile(r"instagram\.com/([^/?#]+)")
_X_HANDLE_RE = re.compile(r"(?:twitter\.com|x\.com)/([^/?#]+)")


# Extracts the Instagram account handle from a profile URL; returns None for non-profile paths
def _extract_instagram_handle(url: str) -> str | None:
    match = _INSTAGRAM_HANDLE_RE.search(url)
    if match:
        handle = match.group(1).strip("/")
        if handle not in ("p", "reel", "stories", "explore"):
            return handle
    return None


# Extracts the X/Twitter account handle from a profile URL; returns None for non-profile paths
def _extract_x_handle(url: str) -> str | None:
    match = _X_HANDLE_RE.search(url)
    if match:
        handle = match.group(1).strip("/")
        if handle not in ("status", "search", "explore", "home", "i"):
            return handle
    return None


# Downloads an image from a URL and returns its base64-encoded content; image bytes are not stored
def _image_to_base64(image_url: str) -> str | None:
    try:
        resp = requests.get(image_url, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception as exc:
        print(f"[social] Failed to download image: {exc}")
        return None


# Sends a base64-encoded image to GPT-4o Vision and returns extracted text (Arabic or English)
def _ocr_image(image_base64: str) -> str:
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


# Fetches recent posts from an Instagram profile via the Apify Instagram scraper actor
def _scrape_instagram(handle: str) -> list[dict]:
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "posts",
        "resultsLimit": POSTS_PER_ACCOUNT,
        "addParentData": False,
    }
    print(f"[social] Scraping @{handle} (limit={POSTS_PER_ACCOUNT})...")
    try:
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)  # Apify Instagram Scraper actor
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[social] Got {len(items)} posts from @{handle}")
        return items
    except Exception as exc:
        print(f"[social] Apify scrape failed for @{handle}: {exc}")
        return []


# Fetches recent tweets from an X/Twitter profile via the Apify Twitter scraper actor
def _scrape_x(handle: str) -> list[dict]:
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
        "handles": [handle],
        "tweetsDesired": POSTS_PER_ACCOUNT,
        "addUserInfo": False,
    }
    print(f"[social] Scraping X @{handle} (limit={POSTS_PER_ACCOUNT})...")
    try:
        run = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)  # Apify Twitter/X Scraper actor
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[social] Got {len(items)} tweets from @{handle}")
        return items
    except Exception as exc:
        print(f"[social] Apify scrape failed for X @{handle}: {exc}")
        return []


# Fetches the bio text of an Instagram profile to use for college auto-classification
def _fetch_instagram_bio(handle: str) -> str:
    client = ApifyClient(APIFY_API_KEY)
    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/"],
        "resultsType": "details",
        "resultsLimit": 1,
    }
    print(f"[social] Fetching bio for @{handle}...")
    try:
        run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)  # Apify Instagram Scraper actor
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if items:
            return items[0].get("biography") or ""
    except Exception as exc:
        print(f"[social] Failed to fetch bio for @{handle}: {exc}")
    return ""


# Extracts text from a post (caption + OCR on all images), classifies, and ingests into pgvector
def _handle_post(
    post: dict,
    handle: str,
    source_id: str,
    platform: str = "instagram",
    college_id: int = None,
) -> None:
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

    if document_already_ingested(post_url):
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

    # Merge caption and OCR text into a single content string
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
        colleges = fetch_colleges()
        topics   = fetch_topics()
        majors   = fetch_majors()
        classification = classify_document(full_text, colleges, topics, majors, forced_college_id=college_id)

        document_id = upsert_document(
            title=title,
            document_type=platform,
            source_url=post_url,
            source_id=source_id,
            major_id=classification["major_id"],
        )

        chunk_and_store(
            text=full_text,
            document_id=document_id,
            source_id=source_id,
            college_id=classification["college_id"],
            major_id=classification["major_id"],
            topic_id=classification["topic_id"],
            file_name=title,
        )
    except Exception as exc:
        print(f"[social] Failed to ingest post {post_url}: {exc}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

# Fetches all Instagram and X sources with status='pending' and scrapes each one
def scrape_pending_social() -> None:
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

        # Auto-classify college from account bio if not already set on source row
        if college_id is None:
            if platform == "instagram":
                bio_text = _fetch_instagram_bio(handle)
            else:
                bio_text = ""
            if bio_text.strip():
                colleges = fetch_colleges()
                college_id = classify_source(bio_text, colleges)
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
