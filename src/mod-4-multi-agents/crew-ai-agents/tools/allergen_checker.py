"""
Allergen checking tool for validating food safety and dietary restrictions.
Searches allergen guidelines and cross-references with menu items.
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import Field

from .base_tool import BaseSupabaseTool


class AllergenCheckerTool(BaseSupabaseTool):
    """
    Tool for checking allergen information and dietary safety.
    Validates menu items against allergen restrictions and provides safety recommendations.
    """

    name: str = "allergen_checker"
    description: str = (
        "Check for allergens in menu items and validate dietary restrictions. "
        "Provides safety information and alternative recommendations."
    )

    def _run(
        self,
        menu_item: str,
        allergens_to_avoid: List[str],
        restaurant_name: Optional[str] = None,
        strict_mode: bool = True
    ) -> str:
        """
        Check menu item for allergens and safety concerns.
        
        Args:
            menu_item: Name or description of menu item
            allergens_to_avoid: List of allergens to check for
            restaurant_name: Optional restaurant name for specific search
            strict_mode: If True, flag potential cross-contamination risks
            
        Returns:
            Safety assessment and recommendations
        """
        allergen_results = self._search_allergen_info(allergens_to_avoid)
        
        menu_filters = {"restaurant_name": restaurant_name} if restaurant_name else None
        menu_results = self.search_collection(
            query=menu_item,
            collection_name=self.settings.supabase_collection_menus,
            limit=5,
            filters=menu_filters
        )
        
        safety_analysis = self._analyze_safety(
            menu_item,
            menu_results,
            allergen_results,
            allergens_to_avoid,
            strict_mode
        )
        
        output = f"🔍 **Allergen Safety Check for: {menu_item}**\n\n"
        
        if restaurant_name:
            output += f"Restaurant: {restaurant_name}\n\n"
        
        output += f"**Allergens to Avoid:** {', '.join(allergens_to_avoid)}\n\n"
        
        if safety_analysis["is_safe"]:
            output += "✅ **Status: LIKELY SAFE**\n\n"
        else:
            output += "⚠️ **Status: POTENTIAL RISK DETECTED**\n\n"
        
        if safety_analysis["detected_allergens"]:
            output += "**Detected Allergens:**\n"
            for allergen in safety_analysis["detected_allergens"]:
                output += f"  • {allergen}\n"
            output += "\n"
        
        if strict_mode and safety_analysis["cross_contamination_risks"]:
            output += "**Cross-Contamination Risks:**\n"
            for risk in safety_analysis["cross_contamination_risks"]:
                output += f"  • {risk}\n"
            output += "\n"
        
        if safety_analysis["hidden_sources"]:
            output += "**Potential Hidden Sources:**\n"
            for source in safety_analysis["hidden_sources"]:
                output += f"  • {source}\n"
            output += "\n"
        
        if safety_analysis["safe_alternatives"]:
            output += "**Recommended Safe Alternatives:**\n"
            for alternative in safety_analysis["safe_alternatives"]:
                output += f"  • {alternative}\n"
            output += "\n"
        
        output += f"**Confidence Level:** {safety_analysis['confidence_level']}\n\n"
        
        output += "**Recommendations:**\n"
        if safety_analysis["is_safe"]:
            output += "  • This item appears safe based on available information\n"
            output += "  • Always confirm with restaurant staff about preparation methods\n"
            output += "  • Ask about cross-contamination prevention measures\n"
        else:
            output += "  • Avoid this item or request modifications\n"
            output += "  • Inform staff about your allergen restrictions\n"
            output += "  • Consider alternative menu items\n"
            output += "  • Request allergen-free preparation area if available\n"
        
        return output

    def _search_allergen_info(self, allergens: List[str]) -> List[Dict[str, Any]]:
        """
        Search for allergen information in the database.
        
        Args:
            allergens: List of allergens to search for
            
        Returns:
            Allergen information results
        """
        all_results = []
        
        for allergen in allergens:
            results = self.search_collection(
                query=f"{allergen} allergy symptoms hidden sources",
                collection_name=self.settings.supabase_collection_allergens,
                limit=3
            )
            all_results.extend(results)
        
        return all_results

    def _analyze_safety(
        self,
        menu_item: str,
        menu_results: List[Dict[str, Any]],
        allergen_results: List[Dict[str, Any]],
        allergens_to_avoid: List[str],
        strict_mode: bool
    ) -> Dict[str, Any]:
        """
        Analyze safety of menu item based on allergen information.
        
        Args:
            menu_item: Menu item being checked
            menu_results: Search results for menu item
            allergen_results: Allergen information results
            allergens_to_avoid: List of allergens to avoid
            strict_mode: Whether to check for cross-contamination
            
        Returns:
            Safety analysis dictionary
        """
        analysis = {
            "is_safe": True,
            "detected_allergens": [],
            "cross_contamination_risks": [],
            "hidden_sources": [],
            "safe_alternatives": [],
            "confidence_level": "Medium"
        }
        
        menu_text = ""
        for result in menu_results:
            content = result.get("content", "").lower()
            metadata = result.get("metadata", {})
            menu_text += content + " "
            
            for allergen in allergens_to_avoid:
                allergen_lower = allergen.lower()
                if allergen_lower in content:
                    analysis["detected_allergens"].append(allergen)
                    analysis["is_safe"] = False
                
                allergen_variations = self._get_allergen_variations(allergen_lower)
                for variation in allergen_variations:
                    if variation in content:
                        if allergen not in analysis["detected_allergens"]:
                            analysis["detected_allergens"].append(allergen)
                        analysis["is_safe"] = False
        
        for result in allergen_results:
            metadata = result.get("metadata", {})
            
            hidden_sources_str = metadata.get("hidden_sources", "[]")
            if isinstance(hidden_sources_str, str):
                try:
                    hidden_sources = json.loads(hidden_sources_str)
                    analysis["hidden_sources"].extend(hidden_sources)
                except:
                    pass
            
            safe_alt_str = metadata.get("safe_alternatives", "[]")
            if isinstance(safe_alt_str, str):
                try:
                    safe_alternatives = json.loads(safe_alt_str)
                    analysis["safe_alternatives"].extend(safe_alternatives)
                except:
                    pass
        
        if strict_mode:
            cross_contamination_keywords = [
                "fried in same oil",
                "shared equipment",
                "same preparation area",
                "may contain traces",
                "processed in facility"
            ]
            
            for keyword in cross_contamination_keywords:
                if keyword in menu_text:
                    analysis["cross_contamination_risks"].append(keyword)
        
        if menu_results:
            if len(menu_results) >= 3:
                analysis["confidence_level"] = "High"
            elif len(menu_results) >= 1:
                analysis["confidence_level"] = "Medium"
        else:
            analysis["confidence_level"] = "Low"
        
        analysis["detected_allergens"] = list(set(analysis["detected_allergens"]))
        analysis["hidden_sources"] = list(set(analysis["hidden_sources"]))[:5]
        analysis["safe_alternatives"] = list(set(analysis["safe_alternatives"]))[:5]
        analysis["cross_contamination_risks"] = list(set(analysis["cross_contamination_risks"]))
        
        return analysis

    def _get_allergen_variations(self, allergen: str) -> List[str]:
        """
        Get common variations of allergen names.
        
        Args:
            allergen: Base allergen name
            
        Returns:
            List of variations
        """
        variations_map = {
            "nuts": ["peanut", "almond", "cashew", "walnut", "pecan", "hazelnut", "tree nut"],
            "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "lactose", "whey", "casein"],
            "eggs": ["egg", "albumin", "mayonnaise", "meringue", "egg white", "egg yolk"],
            "gluten": ["wheat", "barley", "rye", "flour", "bread", "pasta", "cereal"],
            "shellfish": ["shrimp", "lobster", "crab", "oyster", "clam", "mussel", "scallop"],
            "soy": ["soybean", "tofu", "tempeh", "edamame", "soy sauce", "miso"],
            "fish": ["salmon", "tuna", "cod", "halibut", "tilapia", "anchovy", "sardine"],
            "sesame": ["tahini", "sesame seed", "sesame oil", "hummus"]
        }
        
        return variations_map.get(allergen, [allergen])