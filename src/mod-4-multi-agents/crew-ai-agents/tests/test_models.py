"""Tests for database models."""

import pytest
from datetime import datetime
from typing import List, Dict, Any

from database.models import (
    Restaurant, Menu, MenuItem, Coupon, Allergen,
    CustomerPreference, RecommendationResult, AgentOutput
)


class TestRestaurantModel:
    """Test suite for Restaurant model."""

    def test_restaurant_creation(self):
        """Test creating a restaurant instance."""
        restaurant = Restaurant(
            id="rest-001",
            name="Test Restaurant",
            cuisine_type="Italian",
            price_range="$$",
            rating=4.5,
            location="123 Test St",
            hours="9am-10pm",
            dietary_options=["vegetarian", "vegan"],
            ambiance="casual",
            delivery_available=True,
            takeout_available=True,
            reservation_required=False
        )
        
        assert restaurant.id == "rest-001"
        assert restaurant.name == "Test Restaurant"
        assert restaurant.cuisine_type == "Italian"
        assert restaurant.rating == 4.5
        assert "vegetarian" in restaurant.dietary_options
        assert restaurant.delivery_available is True

    def test_restaurant_dict_conversion(self):
        """Test converting restaurant to dictionary."""
        restaurant = Restaurant(
            id="rest-002",
            name="Test Bistro",
            cuisine_type="French",
            price_range="$$$",
            rating=4.8,
            location="456 Bistro Ave",
            hours="11am-11pm"
        )
        
        restaurant_dict = restaurant.model_dump()
        assert restaurant_dict["name"] == "Test Bistro"
        assert restaurant_dict["cuisine_type"] == "French"
        assert restaurant_dict["rating"] == 4.8

    def test_restaurant_validation(self):
        """Test restaurant field validation."""
        with pytest.raises(ValueError):
            Restaurant(
                id="rest-003",
                name="",
                cuisine_type="Italian",
                price_range="$$$$$$",
                rating=6.0,
                location="",
                hours=""
            )


class TestMenuModel:
    """Test suite for Menu and MenuItem models."""

    def test_menu_item_creation(self):
        """Test creating a menu item."""
        item = MenuItem(
            id="item-001",
            name="Margherita Pizza",
            description="Fresh tomatoes, mozzarella, basil",
            price=12.99,
            category="Main Course",
            allergens=["gluten", "dairy"],
            dietary_tags=["vegetarian"],
            calories=800,
            spice_level=1,
            preparation_time=15
        )
        
        assert item.name == "Margherita Pizza"
        assert item.price == 12.99
        assert "gluten" in item.allergens
        assert item.calories == 800

    def test_menu_creation_with_items(self):
        """Test creating a menu with items."""
        items = [
            MenuItem(
                id="item-001",
                name="Caesar Salad",
                description="Romaine, parmesan, croutons",
                price=8.99,
                category="Appetizer"
            ),
            MenuItem(
                id="item-002",
                name="Grilled Salmon",
                description="Atlantic salmon with vegetables",
                price=24.99,
                category="Main Course"
            )
        ]
        
        menu = Menu(
            id="menu-001",
            restaurant_id="rest-001",
            items=items,
            last_updated=datetime.now(),
            seasonal_items=[],
            daily_specials=[]
        )
        
        assert menu.restaurant_id == "rest-001"
        assert len(menu.items) == 2
        assert menu.items[0].name == "Caesar Salad"
        assert menu.items[1].price == 24.99

    def test_menu_item_dietary_validation(self):
        """Test dietary tag validation for menu items."""
        item = MenuItem(
            id="item-003",
            name="Vegan Burger",
            description="Plant-based patty",
            price=14.99,
            category="Main Course",
            dietary_tags=["vegan", "gluten-free"]
        )
        
        assert "vegan" in item.dietary_tags
        assert "gluten-free" in item.dietary_tags
        assert item.allergens is None or len(item.allergens) == 0


class TestCouponModel:
    """Test suite for Coupon model."""

    def test_coupon_creation(self):
        """Test creating a coupon."""
        coupon = Coupon(
            id="coup-001",
            restaurant_id="rest-001",
            code="SAVE20",
            description="20% off entire order",
            discount_percentage=20.0,
            minimum_order=30.0,
            valid_from=datetime.now(),
            valid_until=datetime(2025, 12, 31),
            usage_limit=100,
            usage_count=0,
            applicable_items=["all"],
            excluded_items=[],
            terms_conditions="Valid for dine-in only"
        )
        
        assert coupon.code == "SAVE20"
        assert coupon.discount_percentage == 20.0
        assert coupon.minimum_order == 30.0
        assert coupon.usage_count == 0

    def test_coupon_validity_check(self):
        """Test coupon validity period."""
        from datetime import timedelta
        
        now = datetime.now()
        coupon = Coupon(
            id="coup-002",
            restaurant_id="rest-001",
            code="EXPIRED",
            description="Expired coupon",
            discount_percentage=10.0,
            valid_from=now - timedelta(days=30),
            valid_until=now - timedelta(days=1),
            usage_limit=50,
            usage_count=50
        )
        
        assert coupon.valid_until < now
        assert coupon.usage_count == coupon.usage_limit


class TestAllergenModel:
    """Test suite for Allergen model."""

    def test_allergen_creation(self):
        """Test creating an allergen entry."""
        allergen = Allergen(
            id="allerg-001",
            name="Peanuts",
            category="Tree Nuts",
            severity="severe",
            common_dishes=["Pad Thai", "Satay"],
            symptoms=["anaphylaxis", "hives", "swelling"],
            alternatives=["almonds", "cashews"],
            cross_contamination_risk=True,
            heat_stable=True
        )
        
        assert allergen.name == "Peanuts"
        assert allergen.severity == "severe"
        assert "anaphylaxis" in allergen.symptoms
        assert allergen.cross_contamination_risk is True

    def test_allergen_safety_information(self):
        """Test allergen safety and alternative information."""
        allergen = Allergen(
            id="allerg-002",
            name="Lactose",
            category="Dairy",
            severity="moderate",
            common_dishes=["Pizza", "Ice Cream"],
            symptoms=["digestive issues", "bloating"],
            alternatives=["almond milk", "oat milk", "soy milk"]
        )
        
        assert allergen.category == "Dairy"
        assert len(allergen.alternatives) == 3
        assert "almond milk" in allergen.alternatives


class TestCustomerPreferenceModel:
    """Test suite for CustomerPreference model."""

    def test_customer_preference_creation(self):
        """Test creating customer preferences."""
        preference = CustomerPreference(
            id="pref-001",
            customer_id="cust-001",
            cuisine_preferences=["Italian", "Japanese"],
            dietary_restrictions=["gluten-free"],
            allergens=["peanuts", "shellfish"],
            price_range="$$",
            preferred_ambiance=["casual", "romantic"],
            distance_preference=5.0,
            meal_type="dinner",
            party_size=2,
            special_requirements="Wheelchair accessible"
        )
        
        assert preference.customer_id == "cust-001"
        assert "Italian" in preference.cuisine_preferences
        assert "gluten-free" in preference.dietary_restrictions
        assert preference.party_size == 2

    def test_preference_with_empty_lists(self):
        """Test preferences with empty preference lists."""
        preference = CustomerPreference(
            id="pref-002",
            customer_id="cust-002",
            cuisine_preferences=[],
            dietary_restrictions=[],
            allergens=[],
            price_range="$"
        )
        
        assert len(preference.cuisine_preferences) == 0
        assert len(preference.dietary_restrictions) == 0
        assert preference.price_range == "$"


class TestRecommendationResultModel:
    """Test suite for RecommendationResult model."""

    def test_recommendation_creation(self):
        """Test creating a recommendation result."""
        recommendation = RecommendationResult(
            id="rec-001",
            customer_id="cust-001",
            restaurant_id="rest-001",
            confidence_score=0.95,
            reasoning="Perfect match for Italian cuisine preference",
            menu_items=["item-001", "item-002"],
            applicable_coupons=["coup-001"],
            allergen_warnings=[],
            estimated_cost=45.50,
            distance=2.5,
            wait_time=15,
            created_at=datetime.now()
        )
        
        assert recommendation.confidence_score == 0.95
        assert recommendation.restaurant_id == "rest-001"
        assert len(recommendation.menu_items) == 2
        assert recommendation.estimated_cost == 45.50

    def test_recommendation_with_warnings(self):
        """Test recommendation with allergen warnings."""
        recommendation = RecommendationResult(
            id="rec-002",
            customer_id="cust-001",
            restaurant_id="rest-002",
            confidence_score=0.75,
            reasoning="Good match but contains allergens",
            menu_items=["item-003"],
            applicable_coupons=[],
            allergen_warnings=["Contains traces of peanuts"],
            estimated_cost=30.00
        )
        
        assert recommendation.confidence_score == 0.75
        assert len(recommendation.allergen_warnings) == 1
        assert "peanuts" in recommendation.allergen_warnings[0].lower()


class TestAgentOutputModel:
    """Test suite for AgentOutput model."""

    def test_agent_output_creation(self):
        """Test creating agent output."""
        output = AgentOutput(
            agent_name="Restaurant Concierge",
            task_name="Find Italian Restaurant",
            output_type="recommendation",
            content={
                "restaurant": "Luigi's",
                "reason": "Best Italian in town"
            },
            confidence=0.9,
            execution_time=2.5,
            tokens_used=150,
            cost=0.003,
            timestamp=datetime.now()
        )
        
        assert output.agent_name == "Restaurant Concierge"
        assert output.confidence == 0.9
        assert output.tokens_used == 150
        assert output.content["restaurant"] == "Luigi's"

    def test_agent_output_metadata(self):
        """Test agent output with metadata."""
        output = AgentOutput(
            agent_name="Dietary Specialist",
            task_name="Check Allergens",
            output_type="analysis",
            content={"safe": True, "warnings": []},
            confidence=1.0,
            execution_time=1.2,
            metadata={
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "trace_id": "abc123"
            }
        )
        
        assert output.metadata["model"] == "gpt-4o-mini"
        assert output.metadata["trace_id"] == "abc123"
        assert output.confidence == 1.0