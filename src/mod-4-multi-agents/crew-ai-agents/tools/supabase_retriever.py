"""
General Supabase retriever tool for flexible data access.
Provides direct access to any collection for advanced queries.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_tool import BaseSupabaseTool


class SupabaseRetrieverTool(BaseSupabaseTool):
    """
    General-purpose tool for retrieving data from Supabase collections.
    Provides flexible search across all collections with custom filters.
    """

    name: str = "supabase_retriever"
    description: str = (
        "Retrieve data from any Supabase collection using semantic search. "
        "Supports custom filters and can access menus, restaurants, coupons, or allergen data."
    )

    def _run(
        self,
        query: str,
        collection: str = "restaurants",
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        return_raw: bool = False
    ) -> str:
        """
        Retrieve data from specified collection.
        
        Args:
            query: Search query text
            collection: Collection name (menus, restaurants, coupons, allergens)
            limit: Maximum number of results
            filters: Optional metadata filters
            return_raw: If True, return raw data structure
            
        Returns:
            Formatted results or raw data
        """
        collection_map = {
            "menus": self.settings.supabase_collection_menus,
            "restaurants": self.settings.supabase_collection_restaurants,
            "coupons": self.settings.supabase_collection_coupons,
            "allergens": self.settings.supabase_collection_allergens
        }
        
        collection_name = collection_map.get(collection)
        if not collection_name:
            return f"Invalid collection: {collection}. Choose from: menus, restaurants, coupons, allergens"
        
        results = self.search_collection(
            query=query,
            collection_name=collection_name,
            limit=limit,
            filters=filters
        )
        
        if return_raw:
            return str(results)
        
        if collection == "menus":
            return self._format_menu_results(results, query)
        elif collection == "restaurants":
            return self._format_restaurant_results(results, query)
        elif collection == "coupons":
            return self._format_coupon_results(results, query)
        elif collection == "allergens":
            return self._format_allergen_results(results, query)
        else:
            return self.format_results(results)

    def _format_menu_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format menu search results.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Formatted menu information
        """
        if not results:
            return f"No menu items found for '{query}'"
        
        output = f"📜 **Menu Search Results for '{query}'**\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")[:300]
            
            output += f"**{i}. Menu Item**\n"
            
            cuisine = metadata.get("cuisine_type", "Unknown")
            if cuisine and cuisine != "Unknown":
                output += f"   🍽️ Cuisine: {cuisine}\n"
            
            source = metadata.get("source", "")
            if source:
                import os
                output += f"   📄 Source: {os.path.basename(source)}\n"
            
            page = metadata.get("page_number")
            if page:
                output += f"   📖 Page: {page}\n"
            
            output += f"   📝 Content: {content}...\n"
            output += f"   🎯 Relevance: {result.get('score', 0):.3f}\n\n"
        
        return output

    def _format_restaurant_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format restaurant search results.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Formatted restaurant information
        """
        if not results:
            return f"No restaurants found for '{query}'"
        
        output = f"🏪 **Restaurant Search Results for '{query}'**\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            
            output += f"**{i}. {metadata.get('name', 'Unknown Restaurant')}**\n"
            output += f"   🍽️ Cuisine: {metadata.get('cuisine_type', 'N/A')}\n"
            output += f"   💰 Price: {metadata.get('price_range', 'N/A')}\n"
            output += f"   ⭐ Rating: {metadata.get('rating', 'N/A')}/5\n"
            output += f"   📍 Address: {metadata.get('address', 'N/A')}\n"
            
            dietary = metadata.get("dietary_options", "[]")
            if dietary and dietary != "[]":
                import json
                try:
                    options = json.loads(dietary) if isinstance(dietary, str) else dietary
                    if options:
                        output += f"   🥗 Dietary: {', '.join(options)}\n"
                except:
                    pass
            
            output += f"   🎯 Relevance: {result.get('score', 0):.3f}\n\n"
        
        return output

    def _format_coupon_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format coupon search results.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Formatted coupon information
        """
        if not results:
            return f"No coupons found for '{query}'"
        
        output = f"🎟️ **Coupon Search Results for '{query}'**\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            
            output += f"**{i}. {metadata.get('restaurant_name', 'Unknown')} - {metadata.get('code', 'N/A')}**\n"
            
            discount_pct = metadata.get("discount_percentage")
            discount_amt = metadata.get("discount_amount")
            
            if discount_pct:
                output += f"   💰 Discount: {discount_pct}% off\n"
            elif discount_amt:
                output += f"   💰 Discount: ${discount_amt} off\n"
            
            min_order = metadata.get("minimum_order")
            if min_order:
                output += f"   🛒 Min Order: ${min_order}\n"
            
            valid_until = metadata.get("valid_until", "")
            if valid_until:
                output += f"   ⏰ Valid Until: {valid_until.split('T')[0]}\n"
            
            output += f"   📝 Description: {metadata.get('description', 'N/A')[:100]}...\n"
            output += f"   🎯 Relevance: {result.get('score', 0):.3f}\n\n"
        
        return output

    def _format_allergen_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format allergen search results.
        
        Args:
            results: Search results
            query: Original query
            
        Returns:
            Formatted allergen information
        """
        if not results:
            return f"No allergen information found for '{query}'"
        
        output = f"⚠️ **Allergen Information for '{query}'**\n\n"
        
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            content = result.get("content", "")[:400]
            
            output += f"**{i}. Allergen Information**\n"
            
            allergen_type = metadata.get("allergen_type")
            if allergen_type:
                output += f"   🔍 Type: {allergen_type}\n"
            
            severity = metadata.get("severity_level")
            if severity:
                output += f"   ⚠️ Severity: {severity}\n"
            
            output += f"   📝 Information: {content}...\n"
            
            symptoms = metadata.get("symptoms", "[]")
            if symptoms and symptoms != "[]":
                import json
                try:
                    symptom_list = json.loads(symptoms) if isinstance(symptoms, str) else symptoms
                    if symptom_list:
                        output += f"   🏥 Symptoms: {', '.join(symptom_list[:3])}\n"
                except:
                    pass
            
            output += f"   🎯 Relevance: {result.get('score', 0):.3f}\n\n"
        
        return output

    def get_collection_info(self, collection: str) -> str:
        """
        Get information about a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Collection statistics and information
        """
        collection_map = {
            "menus": self.settings.supabase_collection_menus,
            "restaurants": self.settings.supabase_collection_restaurants,
            "coupons": self.settings.supabase_collection_coupons,
            "allergens": self.settings.supabase_collection_allergens
        }
        
        collection_name = collection_map.get(collection)
        if not collection_name:
            return f"Invalid collection: {collection}"
        
        try:
            stats = self.vector_store.get_collection_stats(collection_name)
            
            output = f"📊 **Collection: {collection}**\n"
            output += f"  • Name: {collection_name}\n"
            output += f"  • Dimension: {stats.get('dimension', 'N/A')}\n"
            output += f"  • Count: {stats.get('count', 'N/A')} vectors\n"
            
            return output
        except Exception as e:
            return f"Error getting collection info: {str(e)}"