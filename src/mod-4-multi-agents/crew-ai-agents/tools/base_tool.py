"""
Base tool class for all Supabase-connected tools.
Provides common functionality for vector search and data retrieval.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from crewai_tools import BaseTool
from pydantic import Field

from config import get_settings
from ingestion import EmbeddingGenerator, SupabaseVectorStore


class BaseSupabaseTool(BaseTool, ABC):
    """
    Abstract base class for tools that interact with Supabase.
    Provides embedding generation and vector store access.
    """

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    
    def __init__(self, **kwargs):
        """Initialize base tool with Supabase connections."""
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.vector_store = SupabaseVectorStore()
        self.embedder = EmbeddingGenerator()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text query.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embedder.generate_embedding(text)

    def search_collection(
        self,
        query: str,
        collection_name: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search a collection using semantic similarity.
        
        Args:
            query: Search query text
            collection_name: Collection to search
            limit: Maximum results
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        query_embedding = self.generate_embedding(query)
        
        if filters:
            results = self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                collection_name=collection_name,
                metadata_filters=filters,
                limit=limit
            )
        else:
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                collection_name=collection_name,
                limit=limit
            )
            results = [
                {
                    "id": r[0],
                    "score": 1 - r[1],
                    "metadata": r[2],
                    "content": r[2].get("content", "")
                }
                for r in results
            ]
        
        return results

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for agent consumption.
        
        Args:
            results: Search results to format
            
        Returns:
            Formatted string representation
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")[:200]
            score = result.get("score", 0)
            
            formatted.append(
                f"{i}. [Score: {score:.3f}]\n"
                f"   Content: {content}...\n"
                f"   Source: {metadata.get('source', 'Unknown')}"
            )
        
        return "\n\n".join(formatted)

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """
        Execute the tool's main functionality.
        Must be implemented by subclasses.
        """
        pass