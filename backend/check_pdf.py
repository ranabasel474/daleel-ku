"""
Diagnostic script — run once from the backend/ directory:
    python check_pdf.py

Prints the raw text PyMuPDF extracts from each page, and
searches for the graduation honors section.
"""
import os
import pymupdf  # fitz

PDF_PATH = os.path.join(os.path.dirname(__file__), "data", "StudnetGuide25-26.pdf")

doc = pymupdf.open(PDF_PATH)
print(f"Total pages: {len(doc)}\n")

TARGET_TERMS = ["3.67", "مرتبة الشرف", "الشرف", "honors", "honour"]

print("=" * 60)
print("Searching for graduation honors content...")
print("=" * 60)

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    for term in TARGET_TERMS:
        if term in text:
            print(f"\n>>> Found '{term}' on page {page_num + 1}")
            # Print a 300-char window around the match
            idx = text.find(term)
            start = max(0, idx - 150)
            end = min(len(text), idx + 150)
            print(repr(text[start:end]))
            break

print("\n" + "=" * 60)
print("Sample text from pages 1-3 (checking extraction quality):")
print("=" * 60)
for i in range(min(3, len(doc))):
    page = doc[i]
    text = page.get_text()
    print(f"\n--- Page {i + 1} (first 400 chars) ---")
    print(repr(text[:400]))

doc.close()
