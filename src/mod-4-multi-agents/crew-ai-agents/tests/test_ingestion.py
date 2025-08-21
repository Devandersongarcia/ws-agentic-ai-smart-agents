"""Tests for ingestion pipeline."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

from ingestion.docling_processor import DoclingProcessor
from ingestion.embeddings import EmbeddingGenerator
from ingestion.vector_store import SupabaseVectorStore
from ingestion.orchestrator import IngestionOrchestrator


class TestDoclingProcessor:
    """Test suite for Docling document processor."""

    @pytest.fixture
    def processor(self):
        """Create a DoclingProcessor instance."""
        with patch("config.settings.Settings"):
            return DoclingProcessor()

    def test_process_pdf_document(self, processor):
        """Test processing PDF documents."""
        with patch("docling.Document") as mock_doc:
            mock_doc.load.return_value.export_to_dict.return_value = {
                "text": "Restaurant menu content",
                "metadata": {"pages": 2}
            }
            
            result = processor.process_pdf(Path("test.pdf"))
            
            assert result["content"] == "Restaurant menu content"
            assert result["metadata"]["pages"] == 2
            assert result["document_type"] == "pdf"

    def test_process_json_document(self, processor):
        """Test processing JSON documents."""
        test_data = {
            "restaurant": "Test Restaurant",
            "cuisine": "Italian",
            "items": ["Pizza", "Pasta"]
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
            result = processor.process_json(Path("test.json"))
            
            assert "Test Restaurant" in result["content"]
            assert "Italian" in result["content"]
            assert result["document_type"] == "json"

    def test_process_csv_document(self, processor):
        """Test processing CSV documents."""
        df = pd.DataFrame({
            "coupon_code": ["SAVE20", "SAVE30"],
            "discount": [20, 30],
            "restaurant": ["Restaurant A", "Restaurant B"]
        })
        
        with patch("pandas.read_csv", return_value=df):
            result = processor.process_csv(Path("test.csv"))
            
            assert "SAVE20" in result["content"]
            assert "Restaurant A" in result["content"]
            assert result["document_type"] == "csv"

    def test_process_docx_document(self, processor):
        """Test processing DOCX documents."""
        with patch("docling.Document") as mock_doc:
            mock_doc.load.return_value.export_to_dict.return_value = {
                "text": "Allergen guidelines document",
                "metadata": {"author": "Health Department"}
            }
            
            result = processor.process_docx(Path("test.docx"))
            
            assert result["content"] == "Allergen guidelines document"
            assert result["metadata"]["author"] == "Health Department"
            assert result["document_type"] == "docx"

    def test_chunk_document(self, processor):
        """Test document chunking."""
        long_text = " ".join(["word"] * 1000)
        document = {
            "content": long_text,
            "metadata": {"source": "test.txt"},
            "document_type": "text"
        }
        
        chunks = processor.chunk_document(document, chunk_size=100, overlap=10)
        
        assert len(chunks) > 1
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all(chunk["metadata"]["chunk_index"] >= 0 for chunk in chunks)

    def test_process_batch(self, processor):
        """Test batch processing of documents."""
        files = [Path("test1.pdf"), Path("test2.json"), Path("test3.csv")]
        
        with patch.object(processor, "process_pdf") as mock_pdf:
            with patch.object(processor, "process_json") as mock_json:
                with patch.object(processor, "process_csv") as mock_csv:
                    mock_pdf.return_value = {"content": "pdf content"}
                    mock_json.return_value = {"content": "json content"}
                    mock_csv.return_value = {"content": "csv content"}
                    
                    results = processor.process_batch(files)
                    
                    assert len(results) == 3
                    mock_pdf.assert_called_once()
                    mock_json.assert_called_once()
                    mock_csv.assert_called_once()


class TestEmbeddingGenerator:
    """Test suite for embedding generation."""

    @pytest.fixture
    def generator(self):
        """Create an EmbeddingGenerator instance."""
        with patch("config.settings.Settings"):
            with patch("openai.OpenAI"):
                return EmbeddingGenerator()

    def test_generate_single_embedding(self, generator):
        """Test generating a single embedding."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        generator.client.embeddings.create.return_value = mock_response
        
        embedding = generator.generate_embedding("Test text")
        
        assert len(embedding) == 3
        assert embedding == [0.1, 0.2, 0.3]
        generator.client.embeddings.create.assert_called_once()

    def test_generate_batch_embeddings(self, generator):
        """Test generating batch embeddings."""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4]),
            MagicMock(embedding=[0.5, 0.6])
        ]
        generator.client.embeddings.create.return_value = mock_response
        
        embeddings = generator.generate_batch(texts)
        
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 2
        assert embeddings[1] == [0.3, 0.4]

    @pytest.mark.asyncio
    async def test_generate_async_embedding(self, generator):
        """Test async embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.7, 0.8, 0.9])]
        
        with patch.object(generator, "generate_embedding", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = [0.7, 0.8, 0.9]
            
            embedding = await generator.generate_async("Async text")
            
            assert len(embedding) == 3
            assert embedding == [0.7, 0.8, 0.9]

    def test_embedding_with_metadata(self, generator):
        """Test embedding generation with metadata."""
        document = {
            "content": "Restaurant menu text",
            "metadata": {"restaurant_id": "rest-001", "type": "menu"}
        }
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.5] * 1536)]
        generator.client.embeddings.create.return_value = mock_response
        
        result = generator.generate_with_metadata(document)
        
        assert "embedding" in result
        assert len(result["embedding"]) == 1536
        assert result["metadata"]["restaurant_id"] == "rest-001"

    def test_embedding_error_handling(self, generator):
        """Test error handling in embedding generation."""
        generator.client.embeddings.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            generator.generate_embedding("Test text")
        
        assert "API Error" in str(exc_info.value)


class TestSupabaseVectorStore:
    """Test suite for Supabase vector store."""

    @pytest.fixture
    def vector_store(self):
        """Create a SupabaseVectorStore instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                with patch("vecs.create_client"):
                    return SupabaseVectorStore()

    @pytest.mark.asyncio
    async def test_create_collection(self, vector_store):
        """Test creating a vector collection."""
        mock_collection = MagicMock()
        vector_store.vecs_client.get_or_create_collection.return_value = mock_collection
        
        collection = await vector_store.create_collection("test_collection", 1536)
        
        assert collection == mock_collection
        vector_store.vecs_client.get_or_create_collection.assert_called_once_with(
            name="test_collection",
            dimension=1536
        )

    @pytest.mark.asyncio
    async def test_upsert_documents(self, vector_store):
        """Test upserting documents to vector store."""
        documents = [
            {
                "id": "doc-001",
                "content": "Restaurant A menu",
                "embedding": [0.1] * 1536,
                "metadata": {"type": "menu"}
            },
            {
                "id": "doc-002",
                "content": "Restaurant B menu",
                "embedding": [0.2] * 1536,
                "metadata": {"type": "menu"}
            }
        ]
        
        mock_collection = MagicMock()
        vector_store.collections["menus"] = mock_collection
        
        await vector_store.upsert_batch("menus", documents)
        
        mock_collection.upsert.assert_called_once()
        call_args = mock_collection.upsert.call_args[0][0]
        assert len(call_args) == 2

    @pytest.mark.asyncio
    async def test_search_similar(self, vector_store):
        """Test similarity search in vector store."""
        query_embedding = [0.5] * 1536
        mock_collection = MagicMock()
        mock_collection.query.return_value = [
            ("doc-001", 0.95, {"content": "Result 1"}),
            ("doc-002", 0.85, {"content": "Result 2"})
        ]
        vector_store.collections["restaurants"] = mock_collection
        
        results = await vector_store.search(
            collection_name="restaurants",
            query_embedding=query_embedding,
            limit=2
        )
        
        assert len(results) == 2
        assert results[0][1] == 0.95
        mock_collection.query.assert_called_once_with(
            data=query_embedding,
            limit=2,
            include_value=True,
            include_metadata=True
        )

    @pytest.mark.asyncio
    async def test_hybrid_search(self, vector_store):
        """Test hybrid search with filters."""
        query_embedding = [0.3] * 1536
        mock_collection = MagicMock()
        mock_collection.query.return_value = [
            ("doc-003", 0.92, {"content": "Italian restaurant", "cuisine": "Italian"}),
            ("doc-004", 0.88, {"content": "French restaurant", "cuisine": "French"})
        ]
        vector_store.collections["restaurants"] = mock_collection
        
        results = await vector_store.hybrid_search(
            collection_name="restaurants",
            query_embedding=query_embedding,
            filters={"cuisine": "Italian"},
            limit=5
        )
        
        assert len(results) <= 5
        mock_collection.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_documents(self, vector_store):
        """Test deleting documents from vector store."""
        document_ids = ["doc-001", "doc-002", "doc-003"]
        mock_collection = MagicMock()
        vector_store.collections["menus"] = mock_collection
        
        await vector_store.delete_batch("menus", document_ids)
        
        mock_collection.delete.assert_called_once_with(ids=document_ids)


class TestIngestionOrchestrator:
    """Test suite for ingestion orchestration."""

    @pytest.fixture
    def orchestrator(self):
        """Create an IngestionOrchestrator instance."""
        with patch("config.settings.Settings"):
            with patch.object(DoclingProcessor, "__init__", return_value=None):
                with patch.object(EmbeddingGenerator, "__init__", return_value=None):
                    with patch.object(SupabaseVectorStore, "__init__", return_value=None):
                        return IngestionOrchestrator()

    @pytest.mark.asyncio
    async def test_ingest_single_file(self, orchestrator):
        """Test ingesting a single file."""
        file_path = Path("test_menu.pdf")
        
        with patch.object(orchestrator.processor, "process_pdf") as mock_process:
            with patch.object(orchestrator.embedding_generator, "generate_embedding") as mock_embed:
                with patch.object(orchestrator.vector_store, "upsert_batch") as mock_upsert:
                    mock_process.return_value = {
                        "content": "Menu content",
                        "metadata": {"type": "menu"}
                    }
                    mock_embed.return_value = [0.5] * 1536
                    
                    result = await orchestrator.ingest_file(file_path, "menus")
                    
                    assert result["status"] == "success"
                    assert result["file"] == str(file_path)
                    mock_process.assert_called_once()
                    mock_embed.assert_called()
                    mock_upsert.assert_called()

    @pytest.mark.asyncio
    async def test_ingest_directory(self, orchestrator):
        """Test ingesting all files in a directory."""
        directory = Path("test_data")
        
        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = [
                Path("menu1.pdf"),
                Path("menu2.pdf"),
                Path("restaurants.json")
            ]
            
            with patch.object(orchestrator, "ingest_file") as mock_ingest:
                mock_ingest.return_value = {"status": "success"}
                
                results = await orchestrator.ingest_directory(directory)
                
                assert len(results) == 3
                assert mock_ingest.call_count == 3

    @pytest.mark.asyncio
    async def test_ingest_with_chunking(self, orchestrator):
        """Test ingestion with document chunking."""
        file_path = Path("large_document.pdf")
        
        with patch.object(orchestrator.processor, "process_pdf") as mock_process:
            with patch.object(orchestrator.processor, "chunk_document") as mock_chunk:
                with patch.object(orchestrator.embedding_generator, "generate_batch") as mock_embed:
                    with patch.object(orchestrator.vector_store, "upsert_batch") as mock_upsert:
                        mock_process.return_value = {
                            "content": "Very long document " * 1000,
                            "metadata": {"type": "document"}
                        }
                        mock_chunk.return_value = [
                            {"content": "Chunk 1", "metadata": {"chunk": 0}},
                            {"content": "Chunk 2", "metadata": {"chunk": 1}}
                        ]
                        mock_embed.return_value = [[0.1] * 1536, [0.2] * 1536]
                        
                        result = await orchestrator.ingest_file(
                            file_path,
                            "documents",
                            chunk_size=500
                        )
                        
                        assert result["status"] == "success"
                        mock_chunk.assert_called_once()
                        mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_error_handling(self, orchestrator):
        """Test error handling during ingestion."""
        file_path = Path("error_file.pdf")
        
        with patch.object(orchestrator.processor, "process_pdf") as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            result = await orchestrator.ingest_file(file_path, "menus")
            
            assert result["status"] == "error"
            assert "Processing error" in result["error"]

    @pytest.mark.asyncio
    async def test_parallel_ingestion(self, orchestrator):
        """Test parallel ingestion of multiple files."""
        files = [Path(f"file{i}.pdf") for i in range(5)]
        
        with patch.object(orchestrator, "ingest_file") as mock_ingest:
            mock_ingest.return_value = {"status": "success"}
            
            results = await orchestrator.ingest_parallel(files, "menus", max_workers=3)
            
            assert len(results) == 5
            assert all(r["status"] == "success" for r in results)


def mock_open(read_data):
    """Helper function to mock file opening."""
    import builtins
    from unittest.mock import mock_open as base_mock_open
    return patch.object(builtins, "open", base_mock_open(read_data=read_data))