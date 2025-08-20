"""Configuration settings for RAG preprocessing pipeline including Astra DB, OpenAI, and Langfuse credentials"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
OUTPUT_DIR = BASE_DIR / "src" / "rag-llama-index" / "output"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASTRA_DB_TOKEN = os.getenv("ASTRA_DB_TOKEN")
ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")

ASTRA_DB_COLLECTION_NAME = os.getenv("ASTRA_DB_COLLECTION_NAME", "restaurant")
ASTRA_DB_COLLECTION_MENUS = os.getenv("ASTRA_DB_COLLECTION_MENUS", "menu")
ASTRA_DB_COLLECTION_RESTAURANTS = os.getenv("ASTRA_DB_COLLECTION_RESTAURANTS", "restaurants")
ASTRA_DB_COLLECTION_COUPONS = os.getenv("ASTRA_DB_COLLECTION_COUPONS", "coupon")
ASTRA_DB_COLLECTION_ALLERGENS = os.getenv("ASTRA_DB_COLLECTION_ALLERGENS", "allergen")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
CHUNK_SIZE_TOKENS = 350
CHUNK_OVERLAP_TOKENS = 50

SUPPORTED_FILE_TYPES = {
    "pdf": [".pdf"],
    "json": [".json"],
    "csv": [".csv"],
    "markdown": [".md"],
    "docx": [".docx"]
}

LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")