"""Tests for agent tools."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any
import json

from tools.restaurant_search import RestaurantSearchTool
from tools.menu_analyzer import MenuAnalyzerTool
from tools.allergen_checker import AllergenCheckerTool
from tools.coupon_finder import CouponFinderTool
from tools.recommendation_engine import RecommendationEngineTool


class TestRestaurantSearchTool:
    """Test suite for Restaurant Search Tool."""

    @pytest.fixture
    def search_tool(self):
        """Create a RestaurantSearchTool instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                with patch("vecs.create_client"):
                    return RestaurantSearchTool()

    def test_search_tool_initialization(self, search_tool):
        """Test search tool initialization."""
        assert search_tool is not None
        assert hasattr(search_tool, "vector_store")
        assert hasattr(search_tool, "supabase_client")

    @pytest.mark.asyncio
    async def test_search_by_cuisine(self, search_tool):
        """Test searching restaurants by cuisine type."""
        mock_results = [
            {
                "id": "rest-001",
                "name": "Luigi's",
                "cuisine_type": "Italian",
                "rating": 4.5
            },
            {
                "id": "rest-002",
                "name": "Mama's Kitchen",
                "cuisine_type": "Italian",
                "rating": 4.8
            }
        ]
        
        with patch.object(search_tool, "search_restaurants", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            results = await search_tool.search_by_cuisine("Italian")
            
            assert len(results) == 2
            assert all(r["cuisine_type"] == "Italian" for r in results)
            mock_search.assert_called_once_with(cuisine="Italian")

    @pytest.mark.asyncio
    async def test_search_by_price_range(self, search_tool):
        """Test searching restaurants by price range."""
        mock_results = [
            {
                "id": "rest-003",
                "name": "Budget Bites",
                "price_range": "$",
                "rating": 4.2
            }
        ]
        
        with patch.object(search_tool, "search_restaurants", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            results = await search_tool.search_by_price("$")
            
            assert len(results) == 1
            assert results[0]["price_range"] == "$"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_tool):
        """Test searching with multiple filters."""
        filters = {
            "cuisine_type": "Japanese",
            "price_range": "$$",
            "delivery_available": True,
            "min_rating": 4.0
        }
        
        mock_results = [
            {
                "id": "rest-004",
                "name": "Sushi Place",
                "cuisine_type": "Japanese",
                "price_range": "$$",
                "delivery_available": True,
                "rating": 4.6
            }
        ]
        
        with patch.object(search_tool, "search_restaurants", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            results = await search_tool.search_with_filters(filters)
            
            assert len(results) == 1
            assert results[0]["cuisine_type"] == "Japanese"
            assert results[0]["delivery_available"] is True

    @pytest.mark.asyncio
    async def test_search_nearby(self, search_tool):
        """Test searching nearby restaurants."""
        user_location = {"lat": 40.7128, "lng": -74.0060}
        
        mock_results = [
            {
                "id": "rest-005",
                "name": "Corner Cafe",
                "distance": 0.5,
                "location": "123 Main St"
            }
        ]
        
        with patch.object(search_tool, "search_nearby_restaurants", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results
            
            results = await search_tool.search_nearby(user_location, radius=1.0)
            
            assert len(results) == 1
            assert results[0]["distance"] == 0.5

    def test_run_method(self, search_tool):
        """Test the run method for CrewAI compatibility."""
        with patch.object(search_tool, "search_restaurants") as mock_search:
            mock_search.return_value = [{"name": "Test Restaurant"}]
            
            result = search_tool.run("Italian restaurants under $$")
            
            assert isinstance(result, str)
            assert "Test Restaurant" in result


class TestMenuAnalyzerTool:
    """Test suite for Menu Analyzer Tool."""

    @pytest.fixture
    def menu_tool(self):
        """Create a MenuAnalyzerTool instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                with patch("vecs.create_client"):
                    return MenuAnalyzerTool()

    def test_menu_tool_initialization(self, menu_tool):
        """Test menu analyzer tool initialization."""
        assert menu_tool is not None
        assert hasattr(menu_tool, "vector_store")
        assert hasattr(menu_tool, "embedding_generator")

    @pytest.mark.asyncio
    async def test_get_menu_items(self, menu_tool):
        """Test retrieving menu items for a restaurant."""
        restaurant_id = "rest-001"
        mock_items = [
            {
                "id": "item-001",
                "name": "Margherita Pizza",
                "price": 12.99,
                "category": "Main Course"
            },
            {
                "id": "item-002",
                "name": "Caesar Salad",
                "price": 8.99,
                "category": "Appetizer"
            }
        ]
        
        with patch.object(menu_tool, "get_restaurant_menu", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_items
            
            items = await menu_tool.get_menu_items(restaurant_id)
            
            assert len(items) == 2
            assert items[0]["name"] == "Margherita Pizza"

    @pytest.mark.asyncio
    async def test_analyze_menu_categories(self, menu_tool):
        """Test analyzing menu categories."""
        menu_items = [
            {"category": "Appetizer", "name": "Soup"},
            {"category": "Main Course", "name": "Steak"},
            {"category": "Appetizer", "name": "Salad"},
            {"category": "Dessert", "name": "Cake"}
        ]
        
        analysis = menu_tool.analyze_categories(menu_items)
        
        assert analysis["Appetizer"] == 2
        assert analysis["Main Course"] == 1
        assert analysis["Dessert"] == 1

    @pytest.mark.asyncio
    async def test_find_dietary_options(self, menu_tool):
        """Test finding dietary options in menu."""
        menu_items = [
            {
                "name": "Vegan Burger",
                "dietary_tags": ["vegan", "gluten-free"]
            },
            {
                "name": "Grilled Chicken",
                "dietary_tags": ["gluten-free"]
            },
            {
                "name": "Pasta Carbonara",
                "dietary_tags": []
            }
        ]
        
        vegan_options = menu_tool.filter_by_dietary("vegan", menu_items)
        gluten_free_options = menu_tool.filter_by_dietary("gluten-free", menu_items)
        
        assert len(vegan_options) == 1
        assert len(gluten_free_options) == 2

    @pytest.mark.asyncio
    async def test_price_analysis(self, menu_tool):
        """Test menu price analysis."""
        menu_items = [
            {"name": "Item 1", "price": 10.00},
            {"name": "Item 2", "price": 15.00},
            {"name": "Item 3", "price": 20.00},
            {"name": "Item 4", "price": 12.00}
        ]
        
        analysis = menu_tool.analyze_prices(menu_items)
        
        assert analysis["min_price"] == 10.00
        assert analysis["max_price"] == 20.00
        assert analysis["avg_price"] == 14.25

    def test_run_method(self, menu_tool):
        """Test the run method for CrewAI compatibility."""
        with patch.object(menu_tool, "get_restaurant_menu") as mock_get:
            mock_get.return_value = [{"name": "Pizza", "price": 12.99}]
            
            result = menu_tool.run("Analyze menu for restaurant rest-001")
            
            assert isinstance(result, str)
            assert "Pizza" in result or "menu" in result.lower()


class TestAllergenCheckerTool:
    """Test suite for Allergen Checker Tool."""

    @pytest.fixture
    def allergen_tool(self):
        """Create an AllergenCheckerTool instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                with patch("vecs.create_client"):
                    return AllergenCheckerTool()

    def test_allergen_tool_initialization(self, allergen_tool):
        """Test allergen checker tool initialization."""
        assert allergen_tool is not None
        assert hasattr(allergen_tool, "vector_store")
        assert hasattr(allergen_tool, "strict_mode")

    @pytest.mark.asyncio
    async def test_check_allergens_in_dish(self, allergen_tool):
        """Test checking allergens in a specific dish."""
        dish = {
            "name": "Pad Thai",
            "allergens": ["peanuts", "shellfish", "soy"]
        }
        customer_allergens = ["peanuts", "dairy"]
        
        result = allergen_tool.check_dish_safety(dish, customer_allergens)
        
        assert result["safe"] is False
        assert "peanuts" in result["found_allergens"]
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_check_cross_contamination(self, allergen_tool):
        """Test checking for cross-contamination risks."""
        menu_item = {
            "name": "Grilled Fish",
            "allergens": [],
            "preparation_notes": "Cooked on shared grill"
        }
        customer_allergens = ["shellfish"]
        
        result = allergen_tool.check_cross_contamination(menu_item, customer_allergens)
        
        assert result["risk_level"] in ["low", "medium", "high"]
        assert "cross_contamination" in result

    @pytest.mark.asyncio
    async def test_get_allergen_alternatives(self, allergen_tool):
        """Test getting alternatives for allergen-containing dishes."""
        dish_with_allergen = {
            "name": "Cheese Pizza",
            "allergens": ["dairy", "gluten"]
        }
        
        alternatives = allergen_tool.get_alternatives(dish_with_allergen)
        
        assert isinstance(alternatives, list)
        assert any("vegan" in alt.lower() or "gluten-free" in alt.lower() 
                  for alt in alternatives)

    @pytest.mark.asyncio
    async def test_strict_mode_behavior(self, allergen_tool):
        """Test strict mode allergen checking."""
        allergen_tool.strict_mode = True
        
        dish = {
            "name": "Mystery Dish",
            "allergens": None
        }
        customer_allergens = ["peanuts"]
        
        result = allergen_tool.check_dish_safety(dish, customer_allergens)
        
        assert result["safe"] is False
        assert "unknown" in result["reason"].lower()

    def test_run_method(self, allergen_tool):
        """Test the run method for CrewAI compatibility."""
        query = "Check if Pad Thai is safe for peanut allergy"
        
        result = allergen_tool.run(query)
        
        assert isinstance(result, str)
        assert "peanut" in result.lower() or "allergen" in result.lower()


class TestCouponFinderTool:
    """Test suite for Coupon Finder Tool."""

    @pytest.fixture
    def coupon_tool(self):
        """Create a CouponFinderTool instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                return CouponFinderTool()

    def test_coupon_tool_initialization(self, coupon_tool):
        """Test coupon finder tool initialization."""
        assert coupon_tool is not None
        assert hasattr(coupon_tool, "supabase_client")
        assert hasattr(coupon_tool, "min_discount")

    @pytest.mark.asyncio
    async def test_find_restaurant_coupons(self, coupon_tool):
        """Test finding coupons for a specific restaurant."""
        restaurant_id = "rest-001"
        mock_coupons = [
            {
                "id": "coup-001",
                "code": "SAVE20",
                "discount_percentage": 20,
                "restaurant_id": restaurant_id
            },
            {
                "id": "coup-002",
                "code": "SAVE30",
                "discount_percentage": 30,
                "restaurant_id": restaurant_id
            }
        ]
        
        with patch.object(coupon_tool, "get_restaurant_coupons", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_coupons
            
            coupons = await coupon_tool.find_restaurant_coupons(restaurant_id)
            
            assert len(coupons) == 2
            assert coupons[0]["code"] == "SAVE20"

    @pytest.mark.asyncio
    async def test_validate_coupon(self, coupon_tool):
        """Test coupon validation."""
        from datetime import datetime, timedelta
        
        valid_coupon = {
            "code": "VALID20",
            "valid_until": datetime.now() + timedelta(days=30),
            "usage_limit": 100,
            "usage_count": 50
        }
        
        expired_coupon = {
            "code": "EXPIRED20",
            "valid_until": datetime.now() - timedelta(days=1),
            "usage_limit": 100,
            "usage_count": 50
        }
        
        assert coupon_tool.is_valid(valid_coupon) is True
        assert coupon_tool.is_valid(expired_coupon) is False

    @pytest.mark.asyncio
    async def test_calculate_savings(self, coupon_tool):
        """Test calculating savings with coupons."""
        coupon = {
            "discount_percentage": 25,
            "minimum_order": 30.00
        }
        order_total = 50.00
        
        savings = coupon_tool.calculate_savings(coupon, order_total)
        
        assert savings == 12.50

    @pytest.mark.asyncio
    async def test_find_best_coupon(self, coupon_tool):
        """Test finding the best applicable coupon."""
        coupons = [
            {"discount_percentage": 10, "minimum_order": 0},
            {"discount_percentage": 20, "minimum_order": 30},
            {"discount_percentage": 30, "minimum_order": 100}
        ]
        order_total = 50.00
        
        best = coupon_tool.find_best_coupon(coupons, order_total)
        
        assert best["discount_percentage"] == 20

    def test_run_method(self, coupon_tool):
        """Test the run method for CrewAI compatibility."""
        with patch.object(coupon_tool, "get_restaurant_coupons") as mock_get:
            mock_get.return_value = [{"code": "SAVE20", "discount": 20}]
            
            result = coupon_tool.run("Find coupons for restaurant rest-001")
            
            assert isinstance(result, str)
            assert "SAVE20" in result or "coupon" in result.lower()


class TestRecommendationEngineTool:
    """Test suite for Recommendation Engine Tool."""

    @pytest.fixture
    def recommendation_tool(self):
        """Create a RecommendationEngineTool instance."""
        with patch("config.settings.Settings"):
            with patch("supabase.create_client"):
                with patch("vecs.create_client"):
                    return RecommendationEngineTool()

    def test_recommendation_tool_initialization(self, recommendation_tool):
        """Test recommendation engine tool initialization."""
        assert recommendation_tool is not None
        assert hasattr(recommendation_tool, "vector_store")
        assert hasattr(recommendation_tool, "embedding_generator")

    @pytest.mark.asyncio
    async def test_generate_recommendation(self, recommendation_tool):
        """Test generating restaurant recommendations."""
        preferences = {
            "cuisine": "Italian",
            "price_range": "$$",
            "dietary": ["vegetarian"],
            "location": "downtown"
        }
        
        mock_results = [
            {
                "restaurant_id": "rest-001",
                "name": "Luigi's",
                "score": 0.95,
                "reasoning": "Perfect match for preferences"
            }
        ]
        
        with patch.object(recommendation_tool, "generate_recommendations", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_results
            
            results = await recommendation_tool.recommend(preferences)
            
            assert len(results) == 1
            assert results[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_personalized_recommendations(self, recommendation_tool):
        """Test personalized recommendations based on history."""
        customer_id = "cust-001"
        history = [
            {"restaurant_id": "rest-001", "rating": 5},
            {"restaurant_id": "rest-002", "rating": 4}
        ]
        
        with patch.object(recommendation_tool, "get_customer_history", new_callable=AsyncMock) as mock_hist:
            mock_hist.return_value = history
            
            with patch.object(recommendation_tool, "generate_personalized", new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = [{"restaurant_id": "rest-003", "score": 0.88}]
                
                results = await recommendation_tool.personalized_recommend(customer_id)
                
                assert len(results) == 1
                mock_hist.assert_called_once_with(customer_id)

    @pytest.mark.asyncio
    async def test_similarity_scoring(self, recommendation_tool):
        """Test similarity scoring between preferences and restaurants."""
        preference_embedding = [0.5] * 1536
        restaurant_embeddings = [
            ([0.6] * 1536, {"id": "rest-001", "name": "Restaurant A"}),
            ([0.3] * 1536, {"id": "rest-002", "name": "Restaurant B"})
        ]
        
        scores = recommendation_tool.calculate_similarity(
            preference_embedding,
            restaurant_embeddings
        )
        
        assert len(scores) == 2
        assert scores[0]["id"] == "rest-001"
        assert scores[0]["score"] > scores[1]["score"]

    def test_run_method(self, recommendation_tool):
        """Test the run method for CrewAI compatibility."""
        query = "Recommend Italian restaurants for vegetarians"
        
        with patch.object(recommendation_tool, "generate_recommendations") as mock_gen:
            mock_gen.return_value = [{"name": "Veggie Italian", "score": 0.9}]
            
            result = recommendation_tool.run(query)
            
            assert isinstance(result, str)
            assert "Italian" in result or "recommendation" in result.lower()