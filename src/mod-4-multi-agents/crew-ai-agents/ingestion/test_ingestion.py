"""
Test suite for the ingestion module.
Tests document processing, embedding generation, and vector storage.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

import pandas as pd
import pytest
from docx import Document as DocxDocument

from database.models import (
    Document, DocumentChunk, DocumentMetadata, DocumentType,
    Restaurant, Coupon, AllergenInfo, CuisineType, AllergenType
)
from ingestion import (
    DoclingProcessor, EmbeddingGenerator, 
    SupabaseVectorStore, IngestionPipeline
)


class TestDoclingProcessor:
    """Test suite for Docling document processor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return DoclingProcessor()

    @pytest.fixture
    def sample_json_file(self, tmp_path):
        """Create sample JSON file."""
        data = [
            {
                "name": "Test Restaurant",
                "cuisine_type": "italian",
                "description": "A test restaurant",
                "rating": 4.5
            }
        ]
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    @pytest.fixture
    def sample_csv_file(self, tmp_path):
        """Create sample CSV file."""
        df = pd.DataFrame({
            "restaurant_name": ["Test Restaurant"],
            "code": ["TEST20"],
            "discount_percentage": [20],
            "description": ["20% off"]
        })
        file_path = tmp_path / "test.csv"
        df.to_csv(file_path, index=False)
        return file_path

    def test_initialization(self, processor):
        """Test processor initialization."""
        assert processor.settings is not None
        assert processor.converter is not None
        assert processor.pipeline_options is not None

    def test_process_json(self, processor, sample_json_file):
        """Test JSON file processing."""
        document = processor.process_file(sample_json_file)
        
        assert isinstance(document, Document)
        assert document.title == "test"
        assert document.metadata.doc_type == DocumentType.JSON
        assert "Test Restaurant" in document.content
        assert document.metadata.extra["record_count"] == 1

    def test_process_csv(self, processor, sample_csv_file):
        """Test CSV file processing."""
        document = processor.process_file(sample_csv_file)
        
        assert isinstance(document, Document)
        assert document.title == "test"
        assert document.metadata.doc_type == DocumentType.CSV
        assert "TEST20" in document.content
        assert document.metadata.extra["row_count"] == 1

    def test_unsupported_file_type(self, processor, tmp_path):
        """Test handling of unsupported file types."""
        invalid_file = tmp_path / "test.xyz"
        invalid_file.touch()
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process_file(invalid_file)

    def test_file_not_found(self, processor):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            processor.process_file(Path("/nonexistent/file.pdf"))

    def test_extract_cuisine_type(self, processor):
        """Test cuisine type extraction from filename."""
        assert processor._extract_cuisine_type("italian_menu") == CuisineType.ITALIAN
        assert processor._extract_cuisine_type("chinese_restaurant") == CuisineType.CHINESE
        assert processor._extract_cuisine_type("unknown") is None

    def test_json_to_markdown(self, processor):
        """Test JSON to markdown conversion."""
        data = {"name": "Test", "items": ["item1", "item2"]}
        markdown = processor._json_to_markdown(data)
        
        assert "**name:** Test" in markdown
        assert "**items:**" in markdown
        assert "- item1" in markdown
        assert "- item2" in markdown

    def test_dataframe_to_markdown(self, processor):
        """Test DataFrame to markdown conversion."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        markdown = processor._dataframe_to_markdown(df)
        
        assert "| col1 | col2 |" in markdown
        assert "| --- | --- |" in markdown
        assert "| 1 | a |" in markdown


class TestEmbeddingGenerator:
    """Test suite for embedding generator."""

    @pytest.fixture
    def embedder(self):
        """Create embedder instance with mocked OpenAI client."""
        with patch('ingestion.embeddings.OpenAI'):
            generator = EmbeddingGenerator()
            generator.client = MagicMock()
            return generator

    def test_initialization(self, embedder):
        """Test embedder initialization."""
        assert embedder.model is not None
        assert embedder.dimension == 1536
        assert embedder.encoding is not None

    def test_generate_embedding(self, embedder):
        """Test single embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        embedder.client.embeddings.create.return_value = mock_response
        
        embedding = embedder.generate_embedding("test text")
        
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        embedder.client.embeddings.create.assert_called_once()

    def test_generate_embeddings_batch(self, embedder):
        """Test batch embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536)
        ]
        embedder.client.embeddings.create.return_value = mock_response
        
        texts = ["text1", "text2"]
        embeddings = embedder.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        assert len(embeddings[1]) == 1536

    def test_chunk_text(self, embedder):
        """Test text chunking."""
        long_text = "This is a test. " * 100
        chunks = embedder.chunk_text(long_text, max_tokens=50)
        
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunk_text_short(self, embedder):
        """Test chunking of short text."""
        short_text = "This is short."
        chunks = embedder.chunk_text(short_text, max_tokens=100)
        
        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_count_tokens(self, embedder):
        """Test token counting."""
        text = "This is a test text."
        token_count = embedder.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_estimate_cost(self, embedder):
        """Test cost estimation."""
        text = "This is a test text for cost estimation."
        cost = embedder.estimate_cost(text)
        
        assert isinstance(cost, float)
        assert cost > 0

    def test_validate_embedding_dimension(self, embedder):
        """Test embedding dimension validation."""
        valid_embedding = [0.1] * 1536
        invalid_embedding = [0.1] * 100
        
        assert embedder.validate_embedding_dimension(valid_embedding) is True
        assert embedder.validate_embedding_dimension(invalid_embedding) is False

    def test_process_document(self, embedder):
        """Test document processing with chunks."""
        document = Document(
            title="Test Document",
            content="This is test content. " * 50,
            metadata=DocumentMetadata(
                source="test.txt",
                doc_type=DocumentType.MARKDOWN
            )
        )
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        embedder.client.embeddings.create.return_value = mock_response
        
        processed = embedder.process_document(document)
        
        assert len(processed.chunks) > 0
        assert all(chunk.embedding is not None for chunk in processed.chunks)
        assert all(chunk.document_id == document.id for chunk in processed.chunks)


class TestSupabaseVectorStore:
    """Test suite for Supabase vector store."""

    @pytest.fixture
    def vector_store(self):
        """Create vector store instance with mocked clients."""
        with patch('ingestion.supabase_client.create_client'), \
             patch('ingestion.supabase_client.vecs.create_client'):
            store = SupabaseVectorStore()
            store.supabase = MagicMock()
            store.vx = MagicMock()
            store.menus_collection = MagicMock()
            store.restaurants_collection = MagicMock()
            store.coupons_collection = MagicMock()
            store.allergens_collection = MagicMock()
            return store

    def test_initialization(self, vector_store):
        """Test vector store initialization."""
        assert vector_store.supabase is not None
        assert vector_store.vx is not None
        assert vector_store.menus_collection is not None

    def test_upsert_document_chunks(self, vector_store):
        """Test upserting document chunks."""
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Test content",
                embedding=[0.1] * 1536,
                metadata=DocumentMetadata(
                    source="test.pdf",
                    doc_type=DocumentType.PDF
                ),
                chunk_index=0,
                token_count=10
            )
        ]
        
        chunk_ids = vector_store.upsert_document_chunks(chunks, "menus")
        
        assert len(chunk_ids) == 1
        vector_store.menus_collection.upsert.assert_called_once()

    def test_search_similar(self, vector_store):
        """Test similarity search."""
        query_embedding = [0.1] * 1536
        mock_results = [
            ("id1", 0.1, {"content": "result1"}),
            ("id2", 0.2, {"content": "result2"})
        ]
        vector_store.menus_collection.query.return_value = mock_results
        
        results = vector_store.search_similar(
            query_embedding, 
            "menus",
            limit=10
        )
        
        assert len(results) == 2
        assert results[0][0] == "id1"
        vector_store.menus_collection.query.assert_called_once()

    def test_hybrid_search(self, vector_store):
        """Test hybrid search with metadata filtering."""
        query_embedding = [0.1] * 1536
        metadata_filters = {"cuisine_type": "italian"}
        
        mock_results = [
            ("id1", 0.1, {"content": "result1", "cuisine_type": "italian"}),
            ("id2", 0.2, {"content": "result2", "cuisine_type": "mexican"})
        ]
        vector_store.menus_collection.query.return_value = mock_results
        
        results = vector_store.hybrid_search(
            query_embedding,
            "menus",
            metadata_filters,
            limit=5
        )
        
        assert len(results) <= 5
        assert all("score" in r for r in results)
        assert all("metadata" in r for r in results)

    def test_store_restaurant(self, vector_store):
        """Test storing restaurant with embedding."""
        restaurant = Restaurant(
            name="Test Restaurant",
            cuisine_type=CuisineType.ITALIAN,
            address="123 Test St",
            phone="555-0123",
            price_range="$$",
            rating=4.5,
            description="A test restaurant"
        )
        embedding = [0.1] * 1536
        
        restaurant_id = vector_store.store_restaurant(restaurant, embedding)
        
        assert restaurant_id == str(restaurant.id)
        vector_store.restaurants_collection.upsert.assert_called_once()
        vector_store.supabase.table.assert_called_with("restaurants")

    def test_create_index(self, vector_store):
        """Test index creation."""
        vector_store.create_index("menus", "ivfflat")
        
        vector_store.menus_collection.create_index.assert_called_once()

    def test_get_collection_stats(self, vector_store):
        """Test getting collection statistics."""
        vector_store.menus_collection.dimension = 1536
        vector_store.menus_collection.__len__ = MagicMock(return_value=100)
        
        stats = vector_store.get_collection_stats("menus")
        
        assert stats["name"] == "menus"
        assert stats["dimension"] == 1536


class TestIngestionPipeline:
    """Test suite for complete ingestion pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance with mocked components."""
        with patch('ingestion.pipeline.DoclingProcessor'), \
             patch('ingestion.pipeline.EmbeddingGenerator'), \
             patch('ingestion.pipeline.SupabaseVectorStore'):
            pipeline = IngestionPipeline()
            pipeline.processor = MagicMock()
            pipeline.embedder = MagicMock()
            pipeline.vector_store = MagicMock()
            return pipeline

    def test_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.processor is not None
        assert pipeline.embedder is not None
        assert pipeline.vector_store is not None
        assert pipeline.stats is not None

    def test_validate_ingestion(self, pipeline):
        """Test ingestion validation."""
        pipeline.vector_store.get_collection_stats.return_value = {
            "count": 10,
            "dimension": 1536
        }
        
        is_valid = pipeline.validate_ingestion()
        
        assert is_valid is True
        assert pipeline.vector_store.get_collection_stats.call_count == 4

    def test_create_restaurant_from_json(self, pipeline):
        """Test restaurant creation from JSON."""
        data = {
            "name": "Test Restaurant",
            "cuisine_type": "italian",
            "address": "123 Test St",
            "phone": "555-0123",
            "price_range": "$$",
            "rating": 4.5,
            "description": "Test description",
            "specialties": ["pasta", "pizza"]
        }
        
        restaurant = pipeline._create_restaurant_from_json(data)
        
        assert isinstance(restaurant, Restaurant)
        assert restaurant.name == "Test Restaurant"
        assert restaurant.cuisine_type == CuisineType.ITALIAN
        assert restaurant.rating == 4.5

    def test_create_coupon_from_csv(self, pipeline):
        """Test coupon creation from CSV row."""
        row = pd.Series({
            "restaurant_name": "Test Restaurant",
            "code": "TEST20",
            "description": "20% off",
            "discount_percentage": 20,
            "valid_from": "2024-01-01",
            "valid_until": "2024-12-31",
            "terms_conditions": "Valid for dine-in only"
        })
        
        coupon = pipeline._create_coupon_from_csv(row)
        
        assert isinstance(coupon, Coupon)
        assert coupon.restaurant_name == "Test Restaurant"
        assert coupon.code == "TEST20"
        assert coupon.discount_percentage == 20