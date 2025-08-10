"""Document transformation pipeline for cleaning text, normalizing sections, extracting menu items, and enriching restaurant metadata"""

import re
from typing import List, Dict, Any, ClassVar
from llama_index.core import Document
from llama_index.core.schema import TransformComponent

class DocumentTransformer(TransformComponent):
    MAX_METADATA_LENGTH: ClassVar[int] = 800
    
    def __call__(self, nodes: List[Document], **kwargs) -> List[Document]:
        """Transform documents with cleaning, normalization, and metadata enrichment."""
        for node in nodes:
            cleaned_text = self._clean_text(node.text)
            
            if hasattr(node, 'text_template'):
                node.text_template = cleaned_text
            else:
                try:
                    node.text = cleaned_text
                except AttributeError:
                    node.metadata["cleaned_text"] = cleaned_text
            
            self._normalize_sections(node)
            self._standardize_currency(node)
            self._extract_dietary_labels(node)
            self._extract_menu_items(node)
            self._enrich_restaurant_info(node)
            self._enrich_cuisine_type(node)
            self._enrich_dish_details(node)
            self._enrich_price_range(node)
            self._enrich_dietary_info(node)
            self._add_search_tags(node)
            self._validate_metadata_length(node)
            
        return nodes
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text by removing extra whitespace and special characters."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-\$\.\,\:\;\!\?\(\)\[\]\/]', '', text)
        text = re.sub(r'(\n\s*)+', '\n', text)
        return text.strip()
    
    def _normalize_sections(self, doc: Document):
        """Standardize menu section names (appetizers, main courses, etc.)."""
        text = doc.text
        
        section_patterns = [
            (r'(?i)appetizer[s]?', 'APPETIZERS'),
            (r'(?i)entree[s]?|main[s]?|main course[s]?', 'MAIN COURSES'),
            (r'(?i)dessert[s]?|sweet[s]?', 'DESSERTS'),
            (r'(?i)beverage[s]?|drink[s]?', 'BEVERAGES'),
            (r'(?i)side[s]?|side dish[es]?', 'SIDES'),
            (r'(?i)soup[s]?', 'SOUPS'),
            (r'(?i)salad[s]?', 'SALADS'),
            (r'(?i)special[s]?|chef[s]? special[s]?', 'SPECIALS')
        ]
        
        for pattern, replacement in section_patterns:
            text = re.sub(pattern, replacement, text)
            
        try:
            doc.text = text
        except AttributeError:
            doc.metadata["normalized_text"] = text
        
        if "section" not in doc.metadata:
            for pattern, section_name in section_patterns:
                if re.search(pattern, doc.text, re.IGNORECASE):
                    doc.metadata["section"] = section_name
                    break
    
    def _standardize_currency(self, doc: Document):
        """Convert price formats to consistent $XX.XX format and extract price statistics."""
        text = doc.text
        
        price_patterns = [
            (r'\$\s*(\d+(?:\.\d{2})?)', r'$\1'),
            (r'(\d+(?:\.\d{2})?)\s*(?:USD|usd|dollars?)', r'$\1'),
            (r'(?:price|cost):\s*(\d+(?:\.\d{2})?)', r'Price: $\1')
        ]
        
        for pattern, replacement in price_patterns:
            text = re.sub(pattern, replacement, text)
            
        try:
            doc.text = text
        except AttributeError:
            doc.metadata["standardized_text"] = text
        
        price_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', text)
        if price_matches:
            prices = [float(p) for p in price_matches]
            doc.metadata["min_price"] = min(prices)
            doc.metadata["max_price"] = max(prices)
            doc.metadata["avg_price"] = sum(prices) / len(prices)
    
    def _extract_dietary_labels(self, doc: Document):
        """Identify dietary restrictions and preferences from text."""
        dietary_patterns = {
            "vegetarian": r'(?i)\b(?:vegetarian|veggie)\b',
            "vegan": r'(?i)\bvegan\b',
            "gluten_free": r'(?i)\b(?:gluten[- ]free|gf)\b',
            "dairy_free": r'(?i)\b(?:dairy[- ]free|df)\b',
            "nut_free": r'(?i)\b(?:nut[- ]free|no nuts)\b',
            "halal": r'(?i)\bhalal\b',
            "kosher": r'(?i)\bkosher\b',
            "spicy": r'(?i)\b(?:spicy|hot|chili|jalapeño)\b',
            "organic": r'(?i)\borganic\b'
        }
        
        dietary_labels = []
        for label, pattern in dietary_patterns.items():
            if re.search(pattern, doc.text):
                dietary_labels.append(label)
                
        if dietary_labels:
            doc.metadata["dietary_labels"] = ", ".join(dietary_labels)
    
    def _extract_menu_items(self, doc: Document):
        """Parse menu items with names and prices from document text."""
        text = doc.text
        item_pattern = r'([A-Z][^$\n]*?)\s*\$(\d+(?:\.\d{2})?)'
        matches = re.findall(item_pattern, text)
        
        if matches:
            items = []
            for name, price in matches:
                name = name.strip().rstrip(':.-')
                if len(name) > 3 and len(name) < 100:
                    items.append({
                        "name": name,
                        "price": float(price)
                    })
                    
            if items:
                doc.metadata["menu_items"] = str(items)
                doc.metadata["item_count"] = len(items)
    
    def _enrich_restaurant_info(self, doc: Document):
        """Extract and normalize restaurant name from document content."""
        if "restaurant" not in doc.metadata:
            restaurant_patterns = [
                r"(?:Restaurant|Bistro|Cafe|Kitchen|Grill|House):\s*([A-Za-z\s'&]+)",
                r"Welcome to ([A-Za-z\s'&]+)",
                r"([A-Za-z\s'&]+)'s Menu"
            ]
            
            for pattern in restaurant_patterns:
                match = re.search(pattern, doc.text, re.IGNORECASE)
                if match:
                    doc.metadata["restaurant"] = match.group(1).strip()
                    break
                    
        if "restaurant" in doc.metadata:
            doc.metadata["restaurant_normalized"] = doc.metadata["restaurant"].lower().replace(" ", "_")
    
    def _enrich_cuisine_type(self, doc: Document):
        """Detect cuisine type based on food keywords and dish names."""
        cuisine_keywords = {
            "italian": ["pasta", "pizza", "risotto", "tiramisu", "marinara", "alfredo", "carbonara", "parmigiano"],
            "chinese": ["wok", "dim sum", "szechuan", "kung pao", "sweet and sour", "fried rice", "chow mein"],
            "japanese": ["sushi", "sashimi", "tempura", "ramen", "teriyaki", "miso", "yakitori", "udon"],
            "mexican": ["taco", "burrito", "enchilada", "quesadilla", "salsa", "guacamole", "fajita", "nacho"],
            "indian": ["curry", "tandoori", "naan", "tikka", "masala", "biryani", "dal", "paneer"],
            "thai": ["pad thai", "tom yum", "green curry", "massaman", "som tam", "thai basil", "coconut"],
            "french": ["croissant", "baguette", "coq au vin", "ratatouille", "crème brûlée", "bouillabaisse"],
            "american": ["burger", "bbq", "ribs", "wings", "mac and cheese", "apple pie", "meatloaf"]
        }
        
        if "cuisine" not in doc.metadata:
            text_lower = doc.text.lower()
            cuisine_scores = {}
            
            for cuisine, keywords in cuisine_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > 0:
                    cuisine_scores[cuisine] = score
                    
            if cuisine_scores:
                best_cuisine = max(cuisine_scores, key=cuisine_scores.get)
                doc.metadata["cuisine"] = best_cuisine
                doc.metadata["cuisine_confidence"] = cuisine_scores[best_cuisine] / len(cuisine_keywords[best_cuisine])
    
    def _enrich_dish_details(self, doc: Document):
        """Add detailed attributes to parsed menu items."""
        if "menu_items" in doc.metadata:
            dishes = []
            
            for item in doc.metadata["menu_items"]:
                dish_info = {
                    "name": item["name"],
                    "price": item["price"]
                }
                
                name_lower = item["name"].lower()
                
                if any(word in name_lower for word in ["spicy", "hot", "chili"]):
                    dish_info["spicy"] = True
                if any(word in name_lower for word in ["special", "chef", "signature"]):
                    dish_info["special"] = True
                if any(word in name_lower for word in ["organic", "farm", "fresh"]):
                    dish_info["premium"] = True
                    
                dishes.append(dish_info)
                
            doc.metadata["dishes"] = str(dishes)
            
            if len(dishes) == 1:
                doc.metadata["primary_dish"] = dishes[0]["name"]
                doc.metadata["primary_price"] = dishes[0]["price"]
    
    def _enrich_price_range(self, doc: Document):
        """Categorize documents by price range (budget, moderate, upscale, luxury)."""
        if "min_price" in doc.metadata and "max_price" in doc.metadata:
            avg_price = doc.metadata["avg_price"]
            
            if avg_price < 15:
                doc.metadata["price_category"] = "budget"
            elif avg_price < 30:
                doc.metadata["price_category"] = "moderate"
            elif avg_price < 50:
                doc.metadata["price_category"] = "upscale"
            else:
                doc.metadata["price_category"] = "luxury"
    
    def _enrich_dietary_info(self, doc: Document):
        """Add comprehensive dietary option tags to document metadata."""
        dietary_info = {
            "vegetarian": ["vegetarian", "veggie", "meatless"],
            "vegan": ["vegan", "plant-based"],
            "gluten_free": ["gluten-free", "gluten free", "gf", "celiac"],
            "dairy_free": ["dairy-free", "dairy free", "lactose-free"],
            "nut_free": ["nut-free", "nut free", "no nuts", "allergy friendly"],
            "halal": ["halal"],
            "kosher": ["kosher"],
            "organic": ["organic", "farm-to-table", "locally sourced"],
            "healthy": ["healthy", "low-calorie", "light", "fresh"],
            "spicy": ["spicy", "hot", "chili", "jalapeño", "habanero"]
        }
        
        text_lower = doc.text.lower()
        dietary_tags = []
        
        for diet_type, keywords in dietary_info.items():
            if any(keyword in text_lower for keyword in keywords):
                dietary_tags.append(diet_type)
                
        if dietary_tags:
            doc.metadata["dietary_options"] = ", ".join(dietary_tags)
            doc.metadata["dietary_friendly"] = True
        else:
            doc.metadata["dietary_friendly"] = False
    
    def _add_search_tags(self, doc: Document):
        """Generate searchable tags for efficient metadata filtering."""
        tags = []
        
        if "section" in doc.metadata:
            tags.append(f"section:{doc.metadata['section'].lower()}")
            
        if "cuisine" in doc.metadata:
            tags.append(f"cuisine:{doc.metadata['cuisine']}")
            
        if "price_category" in doc.metadata:
            tags.append(f"price:{doc.metadata['price_category']}")
            
        if "dietary_options" in doc.metadata and doc.metadata["dietary_options"]:
            diet_options = doc.metadata["dietary_options"].split(", ")
            for option in diet_options:
                tags.append(f"diet:{option}")
                
        if "restaurant_normalized" in doc.metadata:
            tags.append(f"restaurant:{doc.metadata['restaurant_normalized']}")
            
        doc.metadata["search_tags"] = ", ".join(tags)
    
    def _validate_metadata_length(self, doc: Document):
        """Truncate metadata to stay within Astra DB limits."""
        total_length = 0
        keys_to_remove = []
        
        for key, value in doc.metadata.items():
            if isinstance(value, str):
                if len(value) > self.MAX_METADATA_LENGTH:
                    doc.metadata[key] = value[:self.MAX_METADATA_LENGTH] + "..."
                total_length += len(str(value))
            else:
                total_length += len(str(value))
        
        if total_length > 800:
            non_critical_keys = ["menu_items", "dishes", "normalized_text", "standardized_text", "cleaned_text", "optimized_text", "search_tags", "dietary_labels", "dietary_options"]
            for key in non_critical_keys:
                if key in doc.metadata:
                    keys_to_remove.append(key)
                    
            for key in keys_to_remove:
                del doc.metadata[key]
                
            total_length = sum(len(str(value)) for value in doc.metadata.values())
            if total_length > 800:
                for key, value in list(doc.metadata.items()):
                    if isinstance(value, str) and len(value) > 100:
                        doc.metadata[key] = value[:100] + "..."
                        
            total_length = sum(len(str(value)) for value in doc.metadata.values())
            if total_length > 800:
                critical_keys = ["doc_id", "ingestion_timestamp", "file_type", "source_dir", "restaurant", "cuisine"]
                for key in list(doc.metadata.keys()):
                    if key not in critical_keys:
                        del doc.metadata[key]

class DocumentValidator:
    
    @staticmethod
    def validate_document(doc: Document) -> Dict[str, Any]:
        """Validate individual document for required and recommended metadata fields."""
        required_fields = ["doc_id", "ingestion_timestamp", "file_type"]
        recommended_fields = ["restaurant", "cuisine", "section", "price_category"]
        
        validation = {
            "is_valid": True,
            "missing_required": [],
            "missing_recommended": [],
            "warnings": []
        }
        
        for field in required_fields:
            if field not in doc.metadata:
                validation["missing_required"].append(field)
                validation["is_valid"] = False
                
        for field in recommended_fields:
            if field not in doc.metadata:
                validation["missing_recommended"].append(field)
                
        if "min_price" in doc.metadata and "max_price" in doc.metadata:
            if doc.metadata["min_price"] > doc.metadata["max_price"]:
                validation["warnings"].append("price_min > price_max")
                
        if len(doc.text.strip()) < 10:
            validation["warnings"].append("document_text_too_short")
            
        return validation
    
    @staticmethod
    def validate_batch(documents: List[Document]) -> Dict[str, Any]:
        """Validate batch of documents and calculate quality metrics."""
        results = {
            "total_documents": len(documents),
            "valid_documents": 0,
            "invalid_documents": 0,
            "quality_score": 0.0,
            "common_issues": {}
        }
        
        for doc in documents:
            validation = DocumentValidator.validate_document(doc)
            if validation["is_valid"]:
                results["valid_documents"] += 1
            else:
                results["invalid_documents"] += 1
                
            for issue in validation["missing_required"] + validation["missing_recommended"] + validation["warnings"]:
                results["common_issues"][issue] = results["common_issues"].get(issue, 0) + 1
                
        results["quality_score"] = results["valid_documents"] / results["total_documents"] * 100
        
        return results

def create_transformation_pipeline() -> List[DocumentTransformer]:
    """Create transformation pipeline with document transformer."""
    return [DocumentTransformer()]