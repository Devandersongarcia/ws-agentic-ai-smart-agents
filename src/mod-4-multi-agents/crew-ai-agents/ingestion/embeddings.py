"""
OpenAI embeddings generator for document vectorization.
Handles text chunking and embedding generation with rate limiting.
"""

import time
from typing import List, Optional
import tiktoken
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from database.models import Document, DocumentChunk, DocumentMetadata


class EmbeddingGenerator:
    """
    Generates embeddings for text using OpenAI's embedding models.
    Includes chunking, token counting, and rate limiting.
    """

    def __init__(self):
        """Initialize embedding generator with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_embedding_model
        self.dimension = self.settings.openai_embedding_dimension
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        self.requests_per_minute = self.settings.rate_limit_requests_per_minute
        self.tokens_per_minute = self.settings.rate_limit_tokens_per_minute
        self.last_request_time = 0
        self.token_usage = 0
        self.token_reset_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        self._apply_rate_limiting(text)
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimension
        )
        
        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            self._apply_rate_limiting(" ".join(batch))
            
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimension
            )
            
            for data in response.data:
                embeddings.append(data.embedding)
        
        return embeddings

    def chunk_text(self, text: str, max_tokens: Optional[int] = None) -> List[str]:
        """
        Split text into chunks based on token count.
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.settings.ingestion_chunk_size
        
        overlap_tokens = self.settings.ingestion_chunk_overlap
        
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = min(start + max_tokens, len(tokens))
            
            if end < len(tokens):
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)
                
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > len(chunk_text) * 0.5:
                    chunk_text = chunk_text[:break_point + 1]
                    end = start + len(self.encoding.encode(chunk_text))
            else:
                chunk_tokens = tokens[start:end]
                chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append(chunk_text.strip())
            
            start = end - overlap_tokens if end < len(tokens) else end
        
        return chunks

    def process_document(self, document: Document) -> Document:
        """
        Process a document to generate chunks with embeddings.
        
        Args:
            document: Document to process
            
        Returns:
            Document with chunks and embeddings
        """
        document.chunks = []
        
        text_chunks = self.chunk_text(document.content)
        
        embeddings = self.generate_embeddings_batch(text_chunks)
        
        for i, (text, embedding) in enumerate(zip(text_chunks, embeddings)):
            chunk = DocumentChunk(
                document_id=document.id,
                content=text,
                embedding=embedding,
                metadata=document.metadata,
                chunk_index=i,
                token_count=len(self.encoding.encode(text))
            )
            document.add_chunk(chunk)
        
        return document

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        return len(self.encoding.encode(text))

    def _apply_rate_limiting(self, text: str) -> None:
        """
        Apply rate limiting based on requests and tokens.
        
        Args:
            text: Text being processed
        """
        current_time = time.time()
        
        if current_time - self.token_reset_time >= 60:
            self.token_usage = 0
            self.token_reset_time = current_time
        
        tokens = self.count_tokens(text)
        
        if self.token_usage + tokens > self.tokens_per_minute:
            sleep_time = 60 - (current_time - self.token_reset_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.token_usage = 0
                self.token_reset_time = time.time()
        
        time_since_last = current_time - self.last_request_time
        min_interval = 60.0 / self.requests_per_minute
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.token_usage += tokens
        self.last_request_time = time.time()

    def estimate_cost(self, text: str) -> float:
        """
        Estimate embedding cost for text.
        
        Args:
            text: Text to estimate cost for
            
        Returns:
            Estimated cost in dollars
        """
        tokens = self.count_tokens(text)
        
        if "small" in self.model:
            rate = 0.02 / 1_000_000
        else:
            rate = 0.13 / 1_000_000
        
        return tokens * rate

    def validate_embedding_dimension(self, embedding: List[float]) -> bool:
        """
        Validate embedding has correct dimension.
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if dimension is correct
        """
        return len(embedding) == self.dimension