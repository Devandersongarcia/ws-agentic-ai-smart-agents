"""Ingestion module for document processing and vector storage."""

from .docling_processor import DoclingProcessor
from .supabase_client import SupabaseVectorStore
from .embeddings import EmbeddingGenerator
from .pipeline import IngestionPipeline

__all__ = [
    "DoclingProcessor",
    "SupabaseVectorStore",
    "EmbeddingGenerator",
    "IngestionPipeline",
]