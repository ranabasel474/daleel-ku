from datetime import datetime, timezone
from config import supabase_admin


# Returns True if a document with this source_url has already been ingested
def document_already_ingested(source_url: str) -> bool:
    result = (
        supabase_admin.table("document")
        .select("document_id")
        .eq("source_url", source_url)
        .execute()
    )
    return bool(result.data)


# Inserts or updates a document row and returns its document_id
def upsert_document(
    title: str,
    document_type: str,
    source_url: str,
    source_id: str,
    major_id: int = None,
    admin_id=None,
) -> str:
    row = {
        "title": title,
        "document_type": document_type,
        "source_url": source_url,
        "source_id": source_id,
        "major_id": major_id,
        "date_added": datetime.now(timezone.utc).isoformat(),
        "admin_id": admin_id,
    }
    result = (
        supabase_admin.table("document")
        .upsert(row, on_conflict="source_url")
        .execute()
    )
    return result.data[0]["document_id"]
