# test_llamaparse.py
import os
from dotenv import load_dotenv
load_dotenv()

from llama_parse import LlamaParse

parser = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    language="ar"
)

documents = parser.load_data("data/Student_handbook_25-26.pdf")

print(f"Total pages extracted: {len(documents)}")
print("\n--- First 1000 chars of page 1 ---")
print(documents[0].text[:1000])