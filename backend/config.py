import os
from dotenv import load_dotenv
from supabase import create_client
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

load_dotenv()

#API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

#JWT Settings (for admin authentication) 
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

#Supabase client 
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

#LlamaIndex / OpenAI setup
llm = OpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY
)

embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# Apply globally so all LlamaIndex files use same model
Settings.llm = llm
Settings.embed_model = embed_model