"""
Restaurant search tool for finding restaurants based on various criteria.
Searches across menus and restaurant information collections.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_tool import BaseSupabaseTool


class RestaurantSearchTool(BaseSupabaseTool):
    """
    Tool for searching restaurants by cuisine, location, price range, and preferences.
    Combines menu content search with restaurant metadata filtering.
    """

    name: str = "restaurant_search"
    description: str = (
        "Search for restaurants based on cuisine type, price range, dietary options, "
        "and specific dish preferences. Returns relevant restaurant information."
    )

    def _run(
        self,
        query: str,
        cuisine_type: Optional[str] = None,
        price_range: Optional[str] = None,
        min_rating: Optional[float] = None,
        dietary_options: Optional[List[str]] = None
    ) -> str:
        """
        Search for restaurants matching criteria.
        
        Args:
            query: Search query for menu items or restaurant features
            cuisine_type: Type of cuisine (italian, chinese, etc.)
            price_range: Price range ($, $$, $$$, $$$$)
            min_rating: Minimum rating threshold
            dietary_options: Required dietary options (vegetarian, vegan, etc.)
            
        Returns:
            Formatted search results
        """
        filters = {}
        if cuisine_type:
            filters["cuisine_type"] = cuisine_type.lower()
        if price_range:
            filters["price_range"] = price_range
        
        restaurant_results = self.search_collection(
            query=query,
            collection_name=self.settings.supabase_collection_restaurants,
            limit=5,
            filters=filters if filters else None
        )
        
        menu_results = self.search_collection(
            query=query,
            collection_name=self.settings.supabase_collection_menus,
            limit=5,
            filters={"cuisine_type": cuisine_type} if cuisine_type else None
        )
        
        combined_results = self._combine_results(
            restaurant_results, 
            menu_results,
            min_rating,
            dietary_options
        )
        
        if not combined_results:
            return f"No restaurants found matching criteria: {query}"
        
        output = f"Found {len(combined_results)} restaurants matching '{query}':\n\n"
        
        for i, result in enumerate(combined_results[:5], 1):
            metadata = result.get("metadata", {})
            output += (
                f"{i}. **{metadata.get('name', 'Unknown Restaurant')}**\n"
                f"   Cuisine: {metadata.get('cuisine_type', 'N/A')}\n"
                f"   Price Range: {metadata.get('price_range', 'N/A')}\n"
                f"   Rating: {metadata.get('rating', 'N/A')}/5\n"
                f"   Address: {metadata.get('address', 'N/A')}\n"
            )
            
            if metadata.get('dietary_options'):
                options = metadata.get('dietary_options', [])
                if isinstance(options, str):
                    import json
                    try:
                        options = json.loads(options)
                    except:
                        options = []
                output += f"   Dietary Options: {', '.join(options)}\n"
            
            if metadata.get('description'):
                output += f"   Description: {metadata.get('description', '')[:150]}...\n"
            
            output += f"   Relevance Score: {result.get('score', 0):.3f}\n\n"
        
        return output

    def _combine_results(
        self,
        restaurant_results: List[Dict[str, Any]],
        menu_results: List[Dict[str, Any]],
        min_rating: Optional[float],
        dietary_options: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Combine and filter results from multiple searches.
        
        Args:
            restaurant_results: Results from restaurant collection
            menu_results: Results from menu collection
            min_rating: Minimum rating filter
            dietary_options: Required dietary options
            
        Returns:
            Combined and filtered results
        """
        restaurant_map = {}
        
        for result in restaurant_results:
            metadata = result.get("metadata", {})
            restaurant_id = result.get("id")
            
            if min_rating and metadata.get("rating", 0) < min_rating:
                continue
            
            if dietary_options:
                available_options = metadata.get("dietary_options", [])
                if isinstance(available_options, str):
                    import json
                    try:
                        available_options = json.loads(available_options)
                    except:
                        available_options = []
                
                if not any(opt in available_options for opt in dietary_options):
                    continue
            
            restaurant_map[restaurant_id] = result
        
        for result in menu_results:
            metadata = result.get("metadata", {})
            doc_id = metadata.get("document_id", result.get("id"))
            
            if doc_id not in restaurant_map:
                if min_rating:
                    continue
                
                restaurant_map[doc_id] = result
        
        combined = list(restaurant_map.values())
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return combined