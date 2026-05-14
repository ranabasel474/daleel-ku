import os
import tempfile
import threading
from flask import Blueprint, request, jsonify
from config import supabase, supabase_admin
from auth.jwt import require_auth
from utils.sanitize import sanitize_text

admin_bp = Blueprint("admin", __name__)

# Authenticates an admin via Supabase Auth and returns a JWT access token
@admin_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = sanitize_text(data.get("email", ""))
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        access_token = response.session.access_token
        return jsonify({"access_token": access_token}), 200
    except Exception:
        return jsonify({"error": "Invalid credentials"}), 401

# Returns all documents enriched with college and topic names resolved from chunk metadata
@admin_bp.route("/documents", methods=["GET"])
@require_auth
def get_documents():
    try:
        doc_response = supabase_admin.table("document").select("*").order("date_added").execute()
        documents = doc_response.data

        # Fetch college and topic lookup tables
        colleges = {c["college_id"]: c["college_name"]
                    for c in (supabase_admin.table("college").select("college_id, college_name").execute().data or [])}
        topics = {t["topic_id"]: t["topic_name"]
                  for t in (supabase_admin.table("topic").select("topic_id, topic_name").execute().data or [])}

        # Fetch chunks from data_chunks to get college_id/topic_id from metadata_
        chunks = (supabase_admin.table("data_chunks")
                  .select("metadata_")
                  .execute().data or [])

        # Map db_document_id → first chunk's college/topic from metadata_
        chunk_map = {}
        for chunk in chunks:
            meta = chunk.get("metadata_") or {}
            did = meta.get("db_document_id") or meta.get("document_id")
            if did and did not in chunk_map:
                chunk_map[did] = meta

        for doc in documents:
            meta = chunk_map.get(doc["document_id"])
            if meta:
                doc["college_name"] = colleges.get(meta.get("college_id"), "—")
                doc["topic_name"] = topics.get(meta.get("topic_id"), "—")
            else:
                doc["college_name"] = "—"
                doc["topic_name"] = "—"

        return jsonify({"documents": documents}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Inserts a new document record
@admin_bp.route("/documents", methods=["POST"])
@require_auth
def add_document():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        data["admin_id"] = request.admin_payload.id
        response = supabase_admin.table("document").insert(data).execute()
        return jsonify({"document": response.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Updates an existing document record by ID
@admin_bp.route("/documents/<doc_id>", methods=["PUT"])
@require_auth
def update_document(doc_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        topic_name = data.pop("topic_name", None)
        college_name = data.pop("college_name", None)

        if data:
            supabase_admin.table("document").update(data).eq("document_id", doc_id).execute()

        # Resolve metadata updates for topic and college
        new_topic_id = None
        new_college_id = None

        if topic_name is not None:
            topic_name = " ".join(topic_name.strip().split()[:5])
            if topic_name:
                t_result = supabase_admin.table("topic").select("topic_id").eq("topic_name", topic_name).execute()
                if t_result.data:
                    new_topic_id = t_result.data[0]["topic_id"]
                else:
                    insert_result = supabase_admin.table("topic").insert({"topic_name": topic_name}).execute()
                    new_topic_id = insert_result.data[0]["topic_id"]

        if college_name is not None:
            c_result = supabase_admin.table("college").select("college_id").eq("college_name", college_name).execute()
            if not c_result.data:
                return jsonify({"error": f"College '{college_name}' not found"}), 400
            new_college_id = c_result.data[0]["college_id"]

        if new_topic_id is not None or new_college_id is not None:
            all_chunks = supabase_admin.table("data_chunks").select("id, metadata_").execute().data or []
            for chunk in all_chunks:
                meta = chunk.get("metadata_") or {}
                if meta.get("db_document_id") == doc_id:
                    if new_topic_id is not None:
                        meta["topic_id"] = new_topic_id
                    if new_college_id is not None:
                        meta["college_id"] = new_college_id
                    supabase_admin.table("data_chunks").update({"metadata_": meta}).eq("id", chunk["id"]).execute()

        doc_response = supabase_admin.table("document").select("*").eq("document_id", doc_id).execute()
        return jsonify({"document": doc_response.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Deletes a document, its chunks from data_chunks, and its file from storage
@admin_bp.route("/documents/<doc_id>", methods=["DELETE"])
@require_auth
def delete_document(doc_id):
    try:
        # 1. Get the document to find storage path
        doc_response = supabase_admin.table("document").select("source_url").eq("document_id", doc_id).execute()
        source_url = doc_response.data[0]["source_url"] if doc_response.data else None

        # 2. Delete chunks from data_chunks where metadata_ contains this document_id
        all_chunks = supabase_admin.table("data_chunks").select("id, metadata_").execute().data or []
        chunk_ids = [
            c["id"] for c in all_chunks
            if (c.get("metadata_") or {}).get("db_document_id") == doc_id
        ]
        if chunk_ids:
            supabase_admin.table("data_chunks").delete().in_("id", chunk_ids).execute()

        # 3. Delete file from storage bucket if it's a storage:// reference
        if source_url and source_url.startswith("storage://uploads/"):
            storage_path = source_url.replace("storage://uploads/", "")
            try:
                supabase_admin.storage.from_("uploads").remove([storage_path])
            except Exception:
                pass  # File may already be gone

        supabase_admin.table("document").delete().eq("document_id", doc_id).execute()

        return jsonify({"message": "Document deleted", "chunks_deleted": len(chunk_ids)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Uploads a PDF to Supabase Storage, creates a document record, and runs ingestion
@admin_bp.route("/documents/upload", methods=["POST"])
@require_auth
def upload_document():
    from rag.ingest import ingest_document

    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "A PDF file is required"}), 400

    title = sanitize_text(request.form.get("title", ""))
    if not title:
        title = file.filename

    tmp_path = None
    try:
        # 1. Save to temp file
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(tmp_fd)
        file.save(tmp_path)

        # 2. Upload to Supabase Storage
        storage_path = f"{os.urandom(8).hex()}_{file.filename}"
        with open(tmp_path, "rb") as f:
            supabase_admin.storage.from_("uploads").upload(
                storage_path, f, {"content-type": "application/pdf"}
            )
        storage_url = f"storage://uploads/{storage_path}"

        # 3. Create document row
        doc_data = {
            "title": title,
            "source_url": storage_url,
            "document_type": "PDF",
            "admin_id": request.admin_payload.id,
        }
        doc_response = supabase_admin.table("document").insert(doc_data).execute()
        document = doc_response.data[0]
        document_id = document["document_id"]

        # 4. Run ingestion pipeline (pass original filename for metadata)
        chunk_count = ingest_document(document_id=document_id, source_id=None, pdf_path=tmp_path, original_filename=file.filename)

        return jsonify({
            "document": document,
            "chunks_created": chunk_count,
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# Returns college_id and college_name for all colleges
@admin_bp.route("/colleges", methods=["GET"])
@require_auth
def get_colleges():
    try:
        response = supabase_admin.table("college").select("college_id, college_name").execute()
        return jsonify({"colleges": response.data or []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Returns topic_id and topic_name for all topics
@admin_bp.route("/topics", methods=["GET"])
@require_auth
def get_topics():
    try:
        response = supabase_admin.table("topic").select("topic_id, topic_name").execute()
        return jsonify({"topics": response.data or []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Returns all user_query rows ordered by created_at descending
@admin_bp.route("/queries", methods=["GET"])
@require_auth
def get_queries():
    try:
        response = (
            supabase_admin.table("user_query")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify({"queries": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Returns all source rows
@admin_bp.route("/sources", methods=["GET"])
@require_auth
def get_sources():
    try:
        response = supabase_admin.table("source").select("*").order("last_scraped", desc=True).execute()
        return jsonify({"sources": response.data or []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Creates a new source row for scraping
@admin_bp.route("/sources", methods=["POST"])
@require_auth
def add_source():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    source_name = sanitize_text(data.get("source_name", ""))
    url = sanitize_text(data.get("url", ""))
    source_type = data.get("source_type", "web")
    college_id = data.get("college_id")
    crawl_depth = data.get("crawl_depth", "page")

    if not source_name:
        return jsonify({"error": "source_name is required"}), 400
    if not url:
        return jsonify({"error": "url is required"}), 400
    if source_type not in ("web", "instagram"):
        return jsonify({"error": "source_type must be 'web' or 'instagram'"}), 400

    row = {
        "source_name": source_name,
        "url": url,
        "source_type": source_type,
        "status": "pending",
        "crawl_depth": crawl_depth if source_type == "web" else "page",
    }
    if college_id is not None:
        row["college_id"] = college_id

    try:
        response = supabase_admin.table("source").insert(row).execute()
        return jsonify({"source": response.data[0]}), 201
    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            return jsonify({"error": "A source with this URL already exists."}), 409
        return jsonify({"error": error_msg}), 500


# Updates editable fields on a source row
@admin_bp.route("/sources/<source_id>", methods=["PUT"])
@require_auth
def update_source(source_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    allowed = {"source_name", "url", "source_type", "crawl_depth", "status"}
    update = {k: v for k, v in data.items() if k in allowed}
    if not update:
        return jsonify({"error": "No valid fields provided"}), 400

    try:
        response = supabase_admin.table("source").update(update).eq("source_id", source_id).execute()
        return jsonify({"source": response.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Deletes a source row by ID
@admin_bp.route("/sources/<source_id>", methods=["DELETE"])
@require_auth
def delete_source(source_id):
    try:
        supabase_admin.table("source").delete().eq("source_id", source_id).execute()
        return jsonify({"message": "Source deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Triggers scraping of all pending sources in a background thread
@admin_bp.route("/scrape", methods=["POST"])
@require_auth
def trigger_scrape():
    def run_scrape():
        from ingestion.scraper import scrape_pending_sources
        from ingestion.social import scrape_pending_social
        try:
            scrape_pending_sources()
            scrape_pending_social()
        except Exception as e:
            print(f"[scrape] Background scrape error: {e}")

    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()

    return jsonify({"message": "Scraping started in the background."}), 202
