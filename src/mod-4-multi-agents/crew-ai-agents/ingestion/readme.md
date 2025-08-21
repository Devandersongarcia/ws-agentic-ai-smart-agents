# Ingestion Module

## Purpose
Complete document processing pipeline that extracts structured content from various formats, generates embeddings, and stores them in Supabase vector database for similarity search.

## Architecture
The ingestion pipeline follows a three-stage process:
1. **Document Processing** - Docling extracts structured content preserving tables, layouts, and relationships
2. **Embedding Generation** - OpenAI creates vector embeddings with intelligent chunking
3. **Vector Storage** - Supabase stores embeddings with metadata for hybrid search

```mermaid
graph LR
    A[Raw Documents] --> B[Docling Processor]
    B --> C[Structured Content]
    C --> D[Embedding Generator]
    D --> E[Vector Embeddings]
    E --> F[Supabase Store]
    F --> G[Indexed Collections]
```

## Key Classes

- `DoclingProcessor`: Advanced document parsing with structure preservation
- `EmbeddingGenerator`: OpenAI embeddings with chunking and rate limiting
- `SupabaseVectorStore`: Vector operations using pgvector extension
- `IngestionPipeline`: Orchestrates the complete ingestion process

## Usage Example

```python
from ingestion import IngestionPipeline

pipeline = IngestionPipeline()

stats = pipeline.run_full_ingestion()

if pipeline.validate_ingestion():
    print("Ingestion completed successfully!")
    print(f"Processed {stats['total_documents']} documents")
    print(f"Created {stats['total_chunks']} chunks")
    print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
```

## Data Processing

### Supported Formats
- **PDF**: Restaurant menus with table extraction
- **JSON**: Restaurant metadata and attributes
- **CSV**: Coupon and promotion data
- **DOCX**: Allergen guidelines with formatting

### Chunking Strategy
- Maximum tokens per chunk: 500 (configurable)
- Token overlap between chunks: 50
- Intelligent sentence boundary detection
- Metadata preservation across chunks

### Embedding Generation
- Model: text-embedding-3-small (1536 dimensions)
- Batch processing for efficiency
- Rate limiting to respect API limits
- Cost estimation and tracking

## Vector Storage

### Collections
1. **menus**: Restaurant menu content from PDFs
2. **restaurants**: Restaurant information and descriptions
3. **coupons**: Promotional offers and discounts
4. **allergens**: Allergen guidelines and safety information

### Search Capabilities
- **Similarity Search**: Pure vector-based search
- **Hybrid Search**: Combines vector similarity with metadata filtering
- **Re-ranking**: Boosts results based on metadata matches

### Indexing
- IVFFlat indexing for balanced speed/accuracy
- HNSW indexing available for maximum speed
- Automatic index creation after ingestion

## Performance Optimization

### Parallel Processing
- Concurrent document processing
- Batch embedding generation
- Asynchronous vector storage

### Rate Limiting
- Respects OpenAI API limits
- Token counting and tracking
- Automatic retry with exponential backoff

### Error Handling
- Graceful failure for individual documents
- Comprehensive error logging
- Validation after ingestion

## Configuration

Key settings in `.env`:
```bash
# Chunking
INGESTION_CHUNK_SIZE=500
INGESTION_CHUNK_OVERLAP=50
INGESTION_BATCH_SIZE=10

# Processing
INGESTION_MAX_WORKERS=4
DOCLING_USE_GPU=false
DOCLING_OCR_ENABLED=true

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=40000
```

## Testing

Run ingestion tests:
```bash
pytest ingestion/test_ingestion.py -v
```

Test individual components:
```bash
pytest ingestion/test_ingestion.py::TestDoclingProcessor -v
pytest ingestion/test_ingestion.py::TestEmbeddingGenerator -v
pytest ingestion/test_ingestion.py::TestSupabaseStore -v
```

## Monitoring

The pipeline provides detailed statistics:
- Document and chunk counts
- Token usage and cost estimation
- Processing time metrics
- Error tracking and reporting

## Dependencies
- `docling>=2.0.0` - Document processing
- `openai>=1.35.0` - Embeddings
- `supabase>=2.5.0` - Vector storage
- `vecs>=0.4.0` - pgvector operations
- `pandas>=2.2.0` - CSV processing
- `python-docx>=1.1.0` - DOCX processing