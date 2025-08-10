"""Unified indexing module supporting single and multi-collection vector database storage with Astra DB and document optimization"""

from typing import List, Dict, Any, Optional, Union
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core import Document
from llama_index.vector_stores.astra_db import AstraDBVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.ingestion import IngestionPipeline
from tenacity import retry, stop_after_attempt, wait_exponential
try:
    from . import config
except ImportError:
    import config

class UnifiedIndexer:
    
    def __init__(
        self,
        mode: str = "multi",
        embedding_model: str = config.EMBEDDING_MODEL,
        embedding_dim: int = config.EMBEDDING_DIMENSION
    ):
        """Initialize indexer with single or multi-collection configuration."""
        self.mode = mode
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.embed_model = None
        self.collections = {}
        self.indexes = {}
        
        if mode == "multi":
            self.collection_configs = {
                config.ASTRA_DB_COLLECTION_MENUS: {
                    "description": "PDF menu content with dishes and prices",
                    "file_types": ["pdf"],
                    "source_dirs": ["pdf"],
                    "optimization": "semantic_food_focused"
                },
                config.ASTRA_DB_COLLECTION_RESTAURANTS: {
                    "description": "Restaurant details, location, hours, contact info",
                    "file_types": ["json"], 
                    "source_dirs": ["json"],
                    "optimization": "structured_metadata"
                },
                config.ASTRA_DB_COLLECTION_COUPONS: {
                    "description": "Discounts, promotions, and offers",
                    "file_types": ["csv"],
                    "source_dirs": ["csv"], 
                    "optimization": "promotional_content"
                },
                config.ASTRA_DB_COLLECTION_ALLERGENS: {
                    "description": "Critical allergy and dietary restriction info",
                    "file_types": ["docx"],
                    "source_dirs": ["doc"],
                    "optimization": "safety_critical"
                }
            }
        
    def setup(self):
        """Set up embedding model and vector store connections."""
        self.embed_model = OpenAIEmbedding(
            model=self.embedding_model,
            api_key=config.OPENAI_API_KEY,
            embed_batch_size=10
        )
        
        Settings.embed_model = self.embed_model
        
        if self.mode == "single":
            self._setup_single_collection()
        else:
            self._setup_multi_collections()
            
    def _setup_single_collection(self):
        """Configure single Astra DB collection for all document types."""
        vector_store = AstraDBVectorStore(
            token=config.ASTRA_DB_TOKEN,
            api_endpoint=config.ASTRA_DB_API_ENDPOINT,
            collection_name=config.ASTRA_DB_COLLECTION_NAME,
            embedding_dimension=self.embedding_dim
        )
        
        self.collections['main'] = {
            "vector_store": vector_store,
            "storage_context": StorageContext.from_defaults(vector_store=vector_store)
        }
        
    def _setup_multi_collections(self):
        """Configure separate Astra DB collections for each document type."""
        for collection_name, config_data in self.collection_configs.items():
            vector_store = AstraDBVectorStore(
                token=config.ASTRA_DB_TOKEN,
                api_endpoint=config.ASTRA_DB_API_ENDPOINT,
                collection_name=collection_name,
                embedding_dimension=self.embedding_dim
            )
            
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            self.collections[collection_name] = {
                "vector_store": vector_store,
                "storage_context": storage_context,
                "config": config_data
            }
    
    def categorize_documents(self, documents: List[Document]) -> Union[List[Document], Dict[str, List[Document]]]:
        """Sort documents into appropriate collections based on file type and source."""
        if self.mode == "single":
            for doc in documents:
                self._optimize_for_single_collection(doc)
            return documents
            
        categorized = {name: [] for name in self.collection_configs.keys()}
        
        for doc in documents:
            file_type = doc.metadata.get("file_type", "unknown")
            source_dir = doc.metadata.get("source_dir", "unknown")
            
            for collection_name, config_data in self.collection_configs.items():
                if (file_type in config_data["file_types"] or 
                    source_dir in config_data["source_dirs"]):
                    
                    doc.metadata["collection_type"] = collection_name
                    self._optimize_for_collection(doc, collection_name)
                    categorized[collection_name].append(doc)
                    break
                    
        return categorized
    
    def _optimize_for_single_collection(self, doc: Document):
        """Enhance document text with metadata for single collection storage."""
        text_parts = []
        
        if "restaurant" in doc.metadata:
            text_parts.append(f"Restaurant: {doc.metadata['restaurant']}")
        if "cuisine" in doc.metadata:
            text_parts.append(f"Cuisine: {doc.metadata['cuisine']}")
        if "section" in doc.metadata:
            text_parts.append(f"Section: {doc.metadata['section']}")
            
        text_parts.append(doc.text)
        
        if "primary_dish" in doc.metadata:
            text_parts.append(f"Featured: {doc.metadata['primary_dish']}")
        if "dietary_options" in doc.metadata:
            text_parts.append(f"Dietary: {', '.join(doc.metadata['dietary_options'])}")
            
        try:
            doc.text = "\n".join(text_parts)
        except AttributeError:
            doc.metadata["optimized_text"] = "\n".join(text_parts)
    
    def _optimize_for_collection(self, doc: Document, collection_name: str):
        """Apply collection-specific optimization to document."""
        optimization = self.collection_configs[collection_name]["optimization"]
        
        if optimization == "semantic_food_focused":
            self._optimize_for_menu_search(doc)
        elif optimization == "structured_metadata":
            self._optimize_for_restaurant_info(doc)
        elif optimization == "promotional_content":
            self._optimize_for_coupon_search(doc)
        elif optimization == "safety_critical":
            self._optimize_for_allergen_safety(doc)
    
    def _optimize_for_menu_search(self, doc: Document):
        """Optimize document for food and menu-related searches."""
        text_parts = []
        
        if "restaurant" in doc.metadata:
            text_parts.append(f"Restaurant: {doc.metadata['restaurant']}")
        if "cuisine" in doc.metadata:
            text_parts.append(f"Cuisine: {doc.metadata['cuisine']}")
        if "section" in doc.metadata:
            text_parts.append(f"Menu Section: {doc.metadata['section']}")
            
        text_parts.append(doc.text)
        
        if "primary_dish" in doc.metadata:
            text_parts.append(f"Featured Dish: {doc.metadata['primary_dish']}")
        if "price_category" in doc.metadata:
            text_parts.append(f"Price Range: {doc.metadata['price_category']}")
            
        try:
            doc.text = "\n".join(text_parts)
        except AttributeError:
            doc.metadata["optimized_text"] = "\n".join(text_parts)
        doc.metadata["optimized_for"] = "menu_search"
    
    def _optimize_for_restaurant_info(self, doc: Document):
        """Optimize document for restaurant business information searches."""
        text_parts = []
        
        if "name" in doc.metadata:
            text_parts.append(f"Restaurant: {doc.metadata['name']}")
        if "cuisine_type" in doc.metadata:
            text_parts.append(f"Cuisine: {doc.metadata['cuisine_type']}")
        if "neighborhood" in doc.metadata:
            text_parts.append(f"Location: {doc.metadata['neighborhood']}")
        if "rating" in doc.metadata:
            text_parts.append(f"Rating: {doc.metadata['rating']}")
            
        text_parts.append(doc.text)
        try:
            doc.text = "\n".join(text_parts)
        except AttributeError:
            doc.metadata["optimized_text"] = "\n".join(text_parts)
        doc.metadata["optimized_for"] = "restaurant_info"
    
    def _optimize_for_coupon_search(self, doc: Document):
        """Optimize document for promotional and discount searches."""
        text_parts = []
        
        if "Descrição" in doc.metadata:
            text_parts.append(f"Offer: {doc.metadata['Descrição']}")
        if "Tipo" in doc.metadata:
            text_parts.append(f"Type: {doc.metadata['Tipo']}")
        if "Categoria" in doc.metadata:
            text_parts.append(f"Category: {doc.metadata['Categoria']}")
        if "Valor" in doc.metadata:
            text_parts.append(f"Discount: {doc.metadata['Valor']}")
            
        text_parts.append(doc.text)
        try:
            doc.text = "\n".join(text_parts)
        except AttributeError:
            doc.metadata["optimized_text"] = "\n".join(text_parts)
        doc.metadata["optimized_for"] = "coupon_search"
    
    def _optimize_for_allergen_safety(self, doc: Document):
        """Optimize document for critical allergy and safety searches."""
        text_parts = ["ALLERGEN SAFETY INFORMATION", doc.text]
        
        try:
            doc.text = "\n".join(text_parts)
        except AttributeError:
            doc.metadata["optimized_text"] = "\n".join(text_parts)
        doc.metadata["optimized_for"] = "allergen_safety"
        doc.metadata["safety_critical"] = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def index_documents(
        self,
        documents: Union[List[Document], Dict[str, List[Document]]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Index documents to Astra DB with embeddings and metadata."""
        if self.mode == "single":
            return self._index_single_collection(documents, batch_size)
        else:
            return self._index_multi_collections(documents, batch_size)
    
    def _index_single_collection(self, documents: List[Document], batch_size: int) -> Dict[str, Any]:
        """Index all documents into single collection."""
        collection_data = self.collections['main']
        
        self.indexes['main'] = VectorStoreIndex.from_documents(
            documents,
            storage_context=collection_data["storage_context"],
            show_progress=True
        )
        
        return {
            "mode": "single",
            "total_documents": len(documents),
            "collections": {"main": len(documents)}
        }
    
    def _index_multi_collections(self, categorized_docs: Dict[str, List[Document]], batch_size: int) -> Dict[str, Any]:
        """Index documents into separate specialized collections."""
        results = {"mode": "multi", "collections": {}}
        
        for collection_name, documents in categorized_docs.items():
            if not documents:
                results["collections"][collection_name] = {
                    "status": "skipped", 
                    "document_count": 0,
                    "reason": "no documents"
                }
                continue
                
            try:
                collection_data = self.collections[collection_name]
                
                index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=collection_data["storage_context"],
                    embed_model=self.embed_model,
                    show_progress=True
                )
                
                self.indexes[collection_name] = index
                
                results["collections"][collection_name] = {
                    "status": "success",
                    "document_count": len(documents),
                    "config": collection_data["config"]
                }
                
            except Exception as e:
                results["collections"][collection_name] = {
                    "status": "failed",
                    "error": str(e),
                    "document_count": len(documents)
                }
        
        results["total_documents"] = sum(
            r.get("document_count", 0) 
            for r in results["collections"].values()
        )
        
        return results
    
    def get_index(self, collection_name: Optional[str] = None) -> Optional[VectorStoreIndex]:
        """Get vector store index for specified collection."""
        if self.mode == "single":
            return self.indexes.get('main')
        else:
            return self.indexes.get(collection_name) if collection_name else None
    
    def get_all_indexes(self) -> Dict[str, VectorStoreIndex]:
        """Get all available vector store indexes."""
        return self.indexes.copy()
    
    def create_ingestion_pipeline(
        self,
        transformations: List[Any],
        collection_name: Optional[str] = None
    ) -> IngestionPipeline:
        """Create ingestion pipeline for batch document processing."""
        if self.mode == "single":
            vector_store = self.collections['main']['vector_store']
        else:
            vector_store = self.collections[collection_name or config.ASTRA_DB_COLLECTION_MENUS]['vector_store']
            
        return IngestionPipeline(
            transformations=transformations + [self.embed_model],
            vector_store=vector_store
        )

def create_indexer(mode: str = "multi") -> UnifiedIndexer:
    """Create and configure unified indexer with specified mode."""
    indexer = UnifiedIndexer(mode=mode)
    indexer.setup()
    return indexer