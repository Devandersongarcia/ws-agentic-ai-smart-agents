"""
Supabase vector store client for managing embeddings and similarity search.
Uses vecs library for pgvector operations and Supabase for storage.
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import vecs
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from database.models import Document, DocumentChunk, Restaurant, Coupon, AllergenInfo


class SupabaseVectorStore:
    """
    Manages vector operations with Supabase using pgvector.
    Handles embedding storage, retrieval, and similarity search.
    """

    def __init__(self):
        """Initialize Supabase clients and collections."""
        self.settings = get_settings()
        
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_key
        )
        
        self.vx = vecs.create_client(self.settings.supabase_db_url)
        
        self._initialize_collections()

    def _initialize_collections(self) -> None:
        """Create or get vector collections for each data type."""
        dimension = self.settings.openai_embedding_dimension
        
        self.menus_collection = self.vx.get_or_create_collection(
            name=self.settings.supabase_collection_menus,
            dimension=dimension
        )
        
        self.restaurants_collection = self.vx.get_or_create_collection(
            name=self.settings.supabase_collection_restaurants,
            dimension=dimension
        )
        
        self.coupons_collection = self.vx.get_or_create_collection(
            name=self.settings.supabase_collection_coupons,
            dimension=dimension
        )
        
        self.allergens_collection = self.vx.get_or_create_collection(
            name=self.settings.supabase_collection_allergens,
            dimension=dimension
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def upsert_document_chunks(self, chunks: List[DocumentChunk], collection_name: str) -> List[str]:
        """
        Store document chunks with embeddings in specified collection.
        
        Args:
            chunks: List of document chunks with embeddings
            collection_name: Name of the collection to store in
            
        Returns:
            List of stored chunk IDs
        """
        collection = self._get_collection(collection_name)
        
        records = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            
            metadata = {
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "source": chunk.metadata.source,
                "doc_type": chunk.metadata.doc_type.value,
                "content": chunk.content[:1000],
            }
            
            if chunk.metadata.cuisine_type:
                metadata["cuisine_type"] = chunk.metadata.cuisine_type.value
            if chunk.metadata.page_number:
                metadata["page_number"] = chunk.metadata.page_number
            
            records.append((
                str(chunk.id),
                chunk.embedding,
                metadata
            ))
        
        if records:
            collection.upsert(records=records)
        
        return [str(chunk.id) for chunk in chunks if chunk.embedding]

    def search_similar(
        self,
        query_embedding: List[float],
        collection_name: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors in a collection.
        
        Args:
            query_embedding: Query vector
            collection_name: Collection to search in
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of (id, similarity_score, metadata) tuples
        """
        collection = self._get_collection(collection_name)
        
        results = collection.query(
            data=query_embedding,
            limit=limit,
            filters=filters or {},
            measure="cosine_distance",
            include_value=True,
            include_metadata=True
        )
        
        return results

    def hybrid_search(
        self,
        query_embedding: List[float],
        collection_name: str,
        metadata_filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and metadata filtering.
        
        Args:
            query_embedding: Query vector
            collection_name: Collection to search in
            metadata_filters: Metadata filters to apply
            limit: Maximum number of results
            
        Returns:
            List of search results with scores and metadata
        """
        results = self.search_similar(
            query_embedding=query_embedding,
            collection_name=collection_name,
            limit=limit * 2,
            filters=metadata_filters
        )
        
        ranked_results = []
        for id, similarity, metadata in results:
            similarity_score = 1 - similarity
            
            boost = 1.0
            if metadata.get("cuisine_type") == metadata_filters.get("cuisine_type"):
                boost *= 1.2
            
            combined_score = similarity_score * boost
            
            ranked_results.append({
                "id": id,
                "score": combined_score,
                "similarity": similarity_score,
                "metadata": metadata,
                "content": metadata.get("content", "")
            })
        
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        return ranked_results[:limit]

    def store_restaurant(self, restaurant: Restaurant, embedding: List[float]) -> str:
        """
        Store restaurant information with embedding.
        
        Args:
            restaurant: Restaurant object
            embedding: Restaurant description embedding
            
        Returns:
            Restaurant ID
        """
        metadata = {
            "name": restaurant.name,
            "cuisine_type": restaurant.cuisine_type.value,
            "address": restaurant.address,
            "price_range": restaurant.price_range,
            "rating": restaurant.rating,
            "dietary_options": json.dumps(restaurant.dietary_options),
            "allergen_info": json.dumps(restaurant.allergen_info),
            "description": restaurant.description[:1000]
        }
        
        self.restaurants_collection.upsert(
            records=[(str(restaurant.id), embedding, metadata)]
        )
        
        self._store_restaurant_table(restaurant)
        
        return str(restaurant.id)

    def store_coupon(self, coupon: Coupon, embedding: List[float]) -> str:
        """
        Store coupon information with embedding.
        
        Args:
            coupon: Coupon object
            embedding: Coupon description embedding
            
        Returns:
            Coupon ID
        """
        metadata = {
            "restaurant_id": str(coupon.restaurant_id),
            "restaurant_name": coupon.restaurant_name,
            "code": coupon.code,
            "discount_percentage": coupon.discount_percentage,
            "discount_amount": coupon.discount_amount,
            "minimum_order": coupon.minimum_order,
            "valid_from": coupon.valid_from.isoformat(),
            "valid_until": coupon.valid_until.isoformat(),
            "description": coupon.description[:1000]
        }
        
        self.coupons_collection.upsert(
            records=[(str(coupon.id), embedding, metadata)]
        )
        
        return str(coupon.id)

    def store_allergen_info(self, allergen_info: AllergenInfo, embedding: List[float]) -> str:
        """
        Store allergen information with embedding.
        
        Args:
            allergen_info: AllergenInfo object
            embedding: Allergen description embedding
            
        Returns:
            AllergenInfo ID
        """
        metadata = {
            "allergen_type": allergen_info.allergen_type.value,
            "common_names": json.dumps(allergen_info.common_names),
            "severity_level": allergen_info.severity_level,
            "symptoms": json.dumps(allergen_info.symptoms),
            "hidden_sources": json.dumps(allergen_info.hidden_sources),
            "safe_alternatives": json.dumps(allergen_info.safe_alternatives),
            "description": allergen_info.description[:1000]
        }
        
        self.allergens_collection.upsert(
            records=[(str(allergen_info.id), embedding, metadata)]
        )
        
        return str(allergen_info.id)

    def create_index(self, collection_name: str, index_type: str = "ivfflat") -> None:
        """
        Create an index on a collection for faster queries.
        
        Args:
            collection_name: Collection to index
            index_type: Type of index (ivfflat or hnsw)
        """
        collection = self._get_collection(collection_name)
        
        if index_type == "ivfflat":
            collection.create_index(
                measure=vecs.IndexMeasure.cosine_distance,
                method=vecs.IndexMethod.ivfflat,
                probes=10
            )
        elif index_type == "hnsw":
            collection.create_index(
                measure=vecs.IndexMeasure.cosine_distance,
                method=vecs.IndexMethod.hnsw,
                m=16,
                ef_construction=64
            )

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection and all its data.
        
        Args:
            collection_name: Collection to delete
        """
        collection = self._get_collection(collection_name)
        collection.delete()

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Dictionary with collection statistics
        """
        collection = self._get_collection(collection_name)
        
        stats = {
            "name": collection_name,
            "dimension": collection.dimension,
            "count": len(collection),
        }
        
        return stats

    def _get_collection(self, collection_name: str):
        """
        Get collection by name.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection object
            
        Raises:
            ValueError: If collection name is invalid
        """
        collections = {
            self.settings.supabase_collection_menus: self.menus_collection,
            self.settings.supabase_collection_restaurants: self.restaurants_collection,
            self.settings.supabase_collection_coupons: self.coupons_collection,
            self.settings.supabase_collection_allergens: self.allergens_collection,
        }
        
        if collection_name not in collections:
            raise ValueError(f"Invalid collection name: {collection_name}")
        
        return collections[collection_name]

    def _store_restaurant_table(self, restaurant: Restaurant) -> None:
        """
        Store restaurant in Supabase table for structured queries.
        
        Args:
            restaurant: Restaurant object to store
        """
        restaurant_data = {
            "id": str(restaurant.id),
            "name": restaurant.name,
            "cuisine_type": restaurant.cuisine_type.value,
            "address": restaurant.address,
            "phone": restaurant.phone,
            "email": restaurant.email,
            "website": restaurant.website,
            "price_range": restaurant.price_range,
            "rating": restaurant.rating,
            "allergen_info": restaurant.allergen_info,
            "dietary_options": restaurant.dietary_options,
            "hours": restaurant.hours,
            "description": restaurant.description,
            "specialties": restaurant.specialties
        }
        
        self.supabase.table("restaurants").upsert(restaurant_data).execute()

    def close(self) -> None:
        """Close connections to Supabase."""
        pass