import uuid
from rag.ingest import ingest_document

doc_id = str(uuid.uuid4())
source_id = str(uuid.uuid4())

count = ingest_document(
    document_id=doc_id,
    source_id=source_id,
    pdf_path="data/Student_handbook_25-26.pdf"
)

print(f"Ingested {count} chunks")