import os
from dotenv import load_dotenv
from supabase import create_client
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

load_dotenv()

#OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")


# JWT settings
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# Supabase Clients
SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is not set")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is not set")

SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)  # Auth client
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)  # Admin Database client

#LlamaIndex model setup
llm = OpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    temperature=0,
)

# Embedding model for vector search
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# Set LlamaIndex defaults for LLM and embeddings.
Settings.llm = llm
Settings.embed_model = embed_model

#ExternalIngestion API keys
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
if not LLAMA_CLOUD_API_KEY:
    raise ValueError("LLAMA_CLOUD_API_KEY environment variable is not set")

#For future ingestion integration - when Firecrawl API key is available
# FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
# if not FIRECRAWL_API_KEY:
#     raise ValueError("FIRECRAWL_API_KEY environment variable is not set")

#For future ingestion integration - when Apify API key is available
# APIFY_API_KEY = os.getenv("APIFY_API_KEY")
# if not APIFY_API_KEY:
#     raise ValueError("APIFY_API_KEY environment variable is not set")
