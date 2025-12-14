import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-fast-non-reasoning")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

if not GROK_API_KEY:
    print("WARNING: GROK_API_KEY is not set.")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is not set.")
