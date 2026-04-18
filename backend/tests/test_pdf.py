import os
from dotenv import load_dotenv

#Load environment variables before creating the parser
load_dotenv()

from llama_parse import LlamaParse

#Parse the handbook PDF with LlamaParse
parser = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    language="ar"
)

#Read the PDF and return its extracted pages
documents = parser.load_data("data/Student_handbook_25-26.pdf")

#Print a quick preview to verify extraction worked
print(f"Total pages extracted: {len(documents)}")
print("\n--- First 1000 chars of page 1 ---")
print(documents[0].text[:1000])